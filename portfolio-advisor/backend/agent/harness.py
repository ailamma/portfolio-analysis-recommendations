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
    # Fallback to configured values when CSV doesn't include account-level net_liq
    net_liq = portfolio.total_net_liq if portfolio.total_net_liq > 0 else 436000

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

    model = model or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
    user_message = _build_user_message(portfolio, vix, market_data)

    client = anthropic.AsyncAnthropic(api_key=api_key)

    # Dev/mock mode — set MOCK_ANALYSIS=1 in .env to bypass API call
    if os.getenv("MOCK_ANALYSIS") == "1":
        async for chunk in _mock_analysis(portfolio, vix):
            yield chunk
        return

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


async def _mock_analysis(portfolio: PortfolioSnapshot, vix: VixData) -> AsyncGenerator[str, None]:
    """Return realistic mock recommendations for UI development without API credits."""
    import asyncio

    net_liq = portfolio.total_net_liq if portfolio.total_net_liq > 0 else 436000
    urgent_positions = [p for p in portfolio.all_positions if p.min_dte is not None and p.min_dte < 21]
    theta = abs(portfolio.combined_theta or 0)
    min_theta = net_liq * 0.003

    mock_recs = []

    # Flag urgent DTE positions
    for pos in urgent_positions:
        mock_recs.append({
            "priority": "urgent",
            "action": "roll",
            "symbol": pos.underlying,
            "position_id": pos.id,
            "rationale": f"Per trade plan: DTE={pos.min_dte} is below 21-day gamma risk threshold. Must roll or close before expiration to avoid assignment risk.",
            "specific_action": f"Roll {pos.underlying} short options out 30-45 days for a credit. Target same or lower strike if tested.",
            "estimated_credit": 150,
            "urgency_flag": f"DTE={pos.min_dte} — gamma risk",
        })

    # Theta check
    if theta < min_theta:
        mock_recs.append({
            "priority": "high",
            "action": "enter",
            "symbol": "SPY",
            "rationale": f"Daily theta ${theta:.0f} is below the ${min_theta:.0f}/day minimum (0.3% of NetLiq). Need to add premium-selling positions. VIX at {vix.value:.1f} ({vix.regime}) — {'conditions favorable' if vix.regime in ('normal','elevated') else 'be selective'}.",
            "specific_action": f"Sell SPY 30-45 DTE put at 0.20-0.25Δ to add ~$200/day theta. Check BP first.",
            "estimated_credit": 300,
            "urgency_flag": None,
        })

    # VIX-based posture rec
    if vix.regime == "low":
        mock_recs.append({
            "priority": "medium",
            "action": "adjust",
            "symbol": "PORTFOLIO",
            "rationale": f"VIX={vix.value:.1f} is LOW regime. Per trade plan: reduce short vega, be selective with new entries, keep BP at 45%. Consider adding PMCC positions (long vega) to balance.",
            "specific_action": "Review any high-vega short positions. Avoid adding new strangles until VIX > 18.",
            "estimated_credit": None,
            "urgency_flag": None,
        })
    elif vix.regime == "elevated":
        mock_recs.append({
            "priority": "medium",
            "action": "enter",
            "symbol": "PORTFOLIO",
            "rationale": f"VIX={vix.value:.1f} is ELEVATED regime. Per trade plan: aggressive premium selling window. Add RMCWs and strangles on futures within BP limits.",
            "specific_action": "Add 1-2 RMCW positions on high-quality pullback stocks. Target 0.20-0.30Δ short calls.",
            "estimated_credit": 400,
            "urgency_flag": None,
        })

    # Check for positions near 50% profit target → CLOSE recommendation (F026)
    for pos in portfolio.all_positions:
        pnl = pos.unrealized_pnl or 0
        # If position is profitable at 40%+ of max profit (proxied by pnl > 0 with good theta)
        if pnl > 200 and pos.min_dte is not None and 21 <= pos.min_dte <= 45:
            mock_recs.append({
                "priority": "high",
                "action": "close",
                "symbol": pos.underlying,
                "position_id": pos.id,
                "rationale": f"Per trade plan: {pos.underlying} has unrealized P&L of ${pnl:.0f} at DTE={pos.min_dte}. At 50% profit target, close early to free BP and lock in gains. Don't let winners turn into losers.",
                "specific_action": f"Close {pos.underlying} position for ${pnl:.0f} credit. Re-deploy BP into new 45-DTE positions.",
                "estimated_credit": int(pnl),
                "urgency_flag": None,
            })
            break  # Only flag one close example

    # Delta hedge check (F028) — flag if portfolio is directionally skewed.
    # combined_delta is raw Greek sum (not dollar-weighted); use relative threshold.
    delta = portfolio.combined_delta or 0
    abs_delta = abs(delta)
    # Trigger if raw delta > 4 (roughly equivalent to meaningful directional exposure)
    delta_limit = round(net_liq * 0.002, 0)
    if abs_delta > 4:
        direction = "long" if delta > 0 else "short"
        mock_recs.append({
            "priority": "high",
            "action": "hedge",
            "symbol": "SPY",
            "rationale": f"Portfolio is {direction}-biased (raw delta={delta:.2f}). Per trade plan, directional exposure should be neutral-to-slight-bearish. Need to reduce exposure.",
            "specific_action": f"Buy 1 SPY {'put' if direction == 'long' else 'call'} spread (30-45 DTE, 0.20Δ) to reduce delta. Alternatively, trim the largest delta-positive position.",
            "estimated_credit": -150,
            "urgency_flag": f"Delta={delta:.2f} — {direction} skew",
        })

    # Generic monitor for stable positions
    stable = [p for p in portfolio.all_positions if p.min_dte is None or p.min_dte >= 21]
    if stable:
        mock_recs.append({
            "priority": "low",
            "action": "monitor",
            "symbol": ", ".join(p.underlying for p in stable[:3]),
            "rationale": "Positions within normal parameters. No action required. Continue monitoring DTE and profit targets.",
            "specific_action": "Check again at 50% profit target or when DTE reaches 21 days.",
            "estimated_credit": None,
            "urgency_flag": None,
        })

    mock_response = {
        "vix_assessment": f"VIX at {vix.value:.2f} — {vix.regime.upper()} regime. {'Active premium selling conditions.' if vix.regime == 'normal' else 'Adjust posture per trade plan.'}",
        "greeks_assessment": f"Portfolio delta={portfolio.combined_delta:.3f}, theta=${abs(portfolio.combined_theta or 0):.0f}/day (target ${min_theta:.0f}), vega={portfolio.combined_vega:.2f}",
        "monthly_progress": f"On track for 3% goal. Current theta run-rate: ${abs(portfolio.combined_theta or 0) * 30:.0f}/month vs ${net_liq * 0.03:.0f} target.",
        "recommendations": mock_recs,
        "summary": f"Portfolio has {len(portfolio.all_positions)} positions across {len(portfolio.accounts)} accounts. {len(urgent_positions)} position(s) require urgent attention (DTE < 21). VIX at {vix.value:.1f} indicates {vix.regime} regime — {'proceed with normal operations' if vix.regime == 'normal' else 'adjust strategy per trade plan'}.",
    }

    mock_text = json.dumps(mock_response, indent=2)

    # Stream it word by word to simulate real streaming
    words = mock_text.split(" ")
    for i, word in enumerate(words):
        chunk = word + (" " if i < len(words) - 1 else "")
        payload = json.dumps({"type": "text", "content": chunk})
        yield f"data: {payload}\n\n"
        await asyncio.sleep(0.01)

    done_payload = json.dumps({
        "type": "done",
        "recommendations": mock_recs,
        "full_text": mock_text,
    })
    yield f"data: {done_payload}\n\n"


def _extract_recommendations(text: str) -> list[dict]:
    """
    Extract the JSON recommendations object from the agent's text response.
    Tries multiple strategies to find the JSON block.
    """
    import re

    # Strategy 1: fenced ```json ... ``` block
    for m in re.finditer(r"```json\s*([\s\S]*?)\s*```", text):
        try:
            parsed = json.loads(m.group(1))
            if "recommendations" in parsed:
                return parsed.get("recommendations", [])
        except json.JSONDecodeError:
            continue

    # Strategy 2: find the first '{' that contains "recommendations" and balance braces
    start = text.find('"recommendations"')
    if start == -1:
        return []

    # Walk back to find the opening brace of the outer object
    brace_start = text.rfind('{', 0, start)
    if brace_start == -1:
        return []

    # Walk forward balancing braces
    depth = 0
    for i, ch in enumerate(text[brace_start:], start=brace_start):
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                try:
                    parsed = json.loads(text[brace_start:i + 1])
                    return parsed.get("recommendations", [])
                except json.JSONDecodeError:
                    break

    return []
