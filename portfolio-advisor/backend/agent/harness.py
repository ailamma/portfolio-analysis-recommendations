"""
Long-running agent harness for the Portfolio Advisor trading analysis agent.

Implements the Anthropic long-running agent pattern:
- Reads portfolio snapshot + market data
- Loads trade_plan.md as system context
- Calls Claude with streaming for real-time response
- Returns structured JSON recommendations

Usage:
    from backend.agent.harness import run_analysis
    async for chunk in run_analysis(portfolio, vix, market_data):
        yield chunk  # Server-Sent Event data
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import AsyncGenerator

import anthropic

from backend.agent.prompts import ANALYSIS_USER_PROMPT_TEMPLATE, SYSTEM_PROMPT
from backend.models import MarketData, PortfolioSnapshot, VixData

# Load trade plan once at module level
_TRADE_PLAN_PATH = Path(__file__).parent.parent.parent / "docs" / "trade_plan.md"


def _load_trade_plan() -> str:
    if _TRADE_PLAN_PATH.exists():
        return _TRADE_PLAN_PATH.read_text()
    return "Trade plan not found. Proceed with general options best practices."


TRADE_PLAN_TEXT = _load_trade_plan()

# Full system prompt = base prompt + trade plan
FULL_SYSTEM_PROMPT = SYSTEM_PROMPT + "\n\n## TRADE PLAN (your operating framework)\n\n" + TRADE_PLAN_TEXT


def _build_user_message(
    portfolio: PortfolioSnapshot,
    vix: VixData,
    market_data: dict[str, MarketData],
) -> str:
    """Format the portfolio state into the analysis prompt."""
    net_liq = portfolio.total_net_liq

    # Account summary
    acct_lines = []
    for acct in portfolio.accounts:
        acct_lines.append(
            f"- {acct.broker.upper()}: NetLiq=${acct.net_liq:,.0f} | "
            f"BP used={acct.buying_power_pct*100:.1f}% | "
            f"Positions={len(acct.positions)}"
        )
    account_summary = "\n".join(acct_lines) or "No accounts loaded."

    # Market data
    md_lines = []
    for sym, md in market_data.items():
        parts = [f"  - {sym}: price=${md.price:.2f}" if md.price else f"  - {sym}"]
        if md.iv_rank is not None:
            parts.append(f"IVR={md.iv_rank:.0f}")
        if md.historical_vol_30d is not None:
            parts.append(f"HV30={md.historical_vol_30d*100:.1f}%")
        md_lines.append(" | ".join(parts))
    market_data_section = "\n".join(md_lines) or "  No market data available."

    # BP section
    bp_lines = []
    for acct in portfolio.accounts:
        status = "✓ OK"
        if acct.buying_power_pct > 0.85:
            status = "⚠️ CRITICAL — TAKE ACTION"
        elif acct.buying_power_pct > 0.60:
            status = "⚠️ HIGH — no new trades"
        elif acct.buying_power_pct > 0.50:
            status = "⚡ ELEVATED"
        bp_lines.append(
            f"  - {acct.broker.upper()}: {acct.buying_power_pct*100:.1f}% used {status}"
        )
    bp_section = "\n".join(bp_lines)

    # Attention flags
    from backend.portfolio_aggregator import get_positions_needing_attention
    flags = get_positions_needing_attention(portfolio)
    if flags:
        flag_lines = []
        for f in flags:
            flag_lines.append(
                f"  - [{f['broker'].upper()}] {f['underlying']} ({f['strategy']}): {'; '.join(f['reasons'])}"
            )
        attention_flags = "\n".join(flag_lines)
    else:
        attention_flags = "  None — all positions within normal parameters."

    # Positions JSON (truncated for context window safety)
    positions_data = []
    for p in portfolio.all_positions:
        positions_data.append({
            "id": p.id,
            "broker": p.broker,
            "underlying": p.underlying,
            "strategy": p.strategy,
            "net_delta": p.net_delta,
            "net_theta": p.net_theta,
            "net_vega": p.net_vega,
            "unrealized_pnl": p.unrealized_pnl,
            "min_dte": p.min_dte,
            "max_dte": p.max_dte,
            "legs": len(p.legs),
        })
    positions_json = json.dumps(positions_data, indent=2)

    # Thresholds
    max_delta_target = round(net_liq * 0.002, 0)
    theta_target = round(net_liq * 0.003, 0)
    vega_target = round(abs(portfolio.combined_theta) * 1.5, 2)

    return ANALYSIS_USER_PROMPT_TEMPLATE.format(
        snapshot_time=portfolio.snapshot_time.strftime("%Y-%m-%d %H:%M UTC"),
        account_summary=account_summary,
        vix_value=f"{vix.value:.2f}",
        vix_regime=vix.regime,
        market_data_section=market_data_section,
        combined_delta=portfolio.combined_delta,
        max_delta_target=max_delta_target,
        combined_theta=portfolio.combined_theta,
        theta_target=theta_target,
        combined_vega=portfolio.combined_vega,
        vega_target=vega_target,
        bp_section=bp_section,
        attention_flags=attention_flags,
        positions_json=positions_json,
        baseline_net_liq=net_liq,
        current_net_liq=net_liq,
        monthly_target=net_liq * 0.03,
        realized_pnl=sum(p.unrealized_pnl or 0 for p in portfolio.all_positions),
    )


async def run_analysis(
    portfolio: PortfolioSnapshot,
    vix: VixData,
    market_data: dict[str, MarketData],
    model: str | None = None,
) -> AsyncGenerator[str, None]:
    """
    Run the trading analysis agent and yield Server-Sent Event strings.

    Each yielded string is a SSE data line:
      data: {"type": "text", "content": "..."}
      data: {"type": "done", "recommendations": [...]}

    The client should parse these and display streaming text, then
    handle the final "done" event to extract structured recommendations.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        yield 'data: {"type": "error", "message": "ANTHROPIC_API_KEY not set"}\n\n'
        return

    model = model or os.getenv("CLAUDE_MODEL", "claude-opus-4-6")
    user_message = _build_user_message(portfolio, vix, market_data)

    client = anthropic.AsyncAnthropic(api_key=api_key)

    full_text = ""
    try:
        async with client.messages.stream(
            model=model,
            max_tokens=4096,
            system=FULL_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            async for text_chunk in stream.text_stream:
                full_text += text_chunk
                payload = json.dumps({"type": "text", "content": text_chunk})
                yield f"data: {payload}\n\n"

        # Try to extract JSON recommendations from the full response
        recommendations = _extract_recommendations(full_text)
        done_payload = json.dumps({
            "type": "done",
            "recommendations": recommendations,
            "full_text": full_text,
        })
        yield f"data: {done_payload}\n\n"

    except anthropic.APIError as e:
        error_payload = json.dumps({"type": "error", "message": str(e)})
        yield f"data: {error_payload}\n\n"


def _extract_recommendations(text: str) -> list[dict]:
    """
    Extract the JSON recommendations object from the agent's text response.
    Claude is instructed to return JSON — try to parse it out.
    """
    import re

    # Try to find a JSON block in the response
    json_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if not json_match:
        # Try bare JSON object
        json_match = re.search(r"(\{[^{}]*\"recommendations\"\s*:\s*\[.*?\]\s*\})", text, re.DOTALL)

    if json_match:
        try:
            parsed = json.loads(json_match.group(1))
            return parsed.get("recommendations", [])
        except json.JSONDecodeError:
            pass

    return []
