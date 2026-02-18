"""
Portfolio Aggregator — combines multiple AccountSnapshots into a
unified PortfolioSnapshot with aggregate Greeks and strategy summary.
"""
from __future__ import annotations

from backend.models import AccountSnapshot, PortfolioSnapshot


def aggregate(accounts: list[AccountSnapshot]) -> PortfolioSnapshot:
    """
    Merge all account snapshots into a single PortfolioSnapshot.
    Computes combined Greeks and flattens the position list.
    """
    total_net_liq = sum(a.net_liq for a in accounts)
    combined_delta = sum(a.total_delta or 0 for a in accounts)
    combined_theta = sum(a.total_theta or 0 for a in accounts)
    combined_vega = sum(a.total_vega or 0 for a in accounts)
    all_positions = [p for a in accounts for p in a.positions]

    return PortfolioSnapshot(
        accounts=accounts,
        total_net_liq=total_net_liq,
        combined_delta=round(combined_delta, 4),
        combined_theta=round(combined_theta, 4),
        combined_vega=round(combined_vega, 4),
        all_positions=all_positions,
    )


def check_greeks_vs_plan(portfolio: PortfolioSnapshot) -> list[str]:
    """
    Return a list of warning strings for any Greek that is out of trade plan bounds.
    Used by the analysis agent to flag issues without AI.
    """
    warnings: list[str] = []
    net_liq = portfolio.total_net_liq
    if net_liq <= 0:
        return warnings

    # Delta: max ±0.2% of NetLiq BETA-weighted to SPY
    # We treat each delta unit as $1 of SPY exposure (approximation)
    max_delta = net_liq * 0.002
    abs_delta = abs(portfolio.combined_delta)
    if abs_delta > max_delta:
        warnings.append(
            f"DELTA OUT OF BOUNDS: {portfolio.combined_delta:.2f} delta units "
            f"(max ±{max_delta:.0f} per trade plan)"
        )

    # Theta: minimum 0.3% of NetLiq per day
    min_theta = net_liq * 0.003
    if portfolio.combined_theta < min_theta:
        warnings.append(
            f"THETA BELOW TARGET: ${portfolio.combined_theta:.0f}/day "
            f"(target ≥ ${min_theta:.0f}/day)"
        )

    # Vega: should be ≤ 1.5× theta (short vega bias)
    if portfolio.combined_vega > abs(portfolio.combined_theta) * 1.5:
        warnings.append(
            f"VEGA TOO HIGH: {portfolio.combined_vega:.2f} vega vs "
            f"{portfolio.combined_theta:.2f} theta (target vega ≤ 1.5× theta)"
        )

    return warnings


def get_positions_needing_attention(portfolio: PortfolioSnapshot) -> list[dict]:
    """
    Return positions that may need immediate action, with reason.
    Rules from trade plan:
    - DTE < 21 on any short leg → gamma risk flag
    - Unrealized P&L loss > 2× assumed credit → stop loss alert
    """
    flags = []
    for pos in portfolio.all_positions:
        reasons = []
        # DTE flag
        if pos.min_dte is not None and pos.min_dte < 21:
            reasons.append(f"DTE={pos.min_dte} — gamma risk, consider rolling or closing")
        # Rough loss check (if pnl is very negative)
        if pos.unrealized_pnl is not None and pos.unrealized_pnl < -2000:
            reasons.append(f"Large unrealized loss: ${pos.unrealized_pnl:,.0f}")
        if reasons:
            flags.append({
                "position_id": pos.id,
                "underlying": pos.underlying,
                "broker": pos.broker,
                "strategy": pos.strategy,
                "reasons": reasons,
            })
    return flags
