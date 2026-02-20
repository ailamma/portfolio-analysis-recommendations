"""
TastyTrade CSV Position Export Parser.

TastyTrade exports positions via Account → Positions → Export CSV.
Real export column names (as of 2026):
  Account, Symbol, Type, Quantity, Exp Date, DTE, Strike Price, Call/Put,
  Underlying Last Price, P/L Open, P/L Opn%, Cost, Ext, P/L Day,
  Theta, / Delta, Vega, Gamma, β Delta, Mark, Ext RoR %, Net Liq

Key format notes:
- Quantity is SIGNED: negative = short, positive = long
- Theta/Delta/Vega in CSV are TOTAL for the leg (qty * multiplier already applied)
- Net Liq column = per-position BP effect, NOT account total net liq
- No "Side" column — infer from quantity sign
"""
from __future__ import annotations

import re
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from backend.models import (
    AccountSnapshot,
    OptionLeg,
    OptionSide,
    Position,
    PositionSide,
    StrategyType,
)


# ── Column name normalization ──────────────────────────────────────────────────
COLUMN_MAP = {
    # Real TastyTrade export columns
    "exp date": "expiration",
    "call/put": "option_type",       # "Call" or "Put"
    "p/l open": "unrealized_pnl",
    "/ delta": "delta",              # dollar-delta (position total)
    "β delta": "beta_delta",
    "net liq": "net_liq_effect",     # per-position BP effect, not account net liq
    "underlying last price": "underlying_price",
    "p/l day": "pnl_day",
    # Legacy / alternate names (keep for sample CSV compatibility)
    "expiration date": "expiration",
    "unrealized p/l": "unrealized_pnl",
    "unrealized p&l": "unrealized_pnl",
    "side": "side",
    "open price": "open_price",
    "underlying symbol": "underlying_symbol",
    "net liquidating value": "net_liq_account",
    "buying power effect": "buying_power_effect",
    # Common to both
    "symbol": "symbol",
    "type": "instrument_type",
    "quantity": "quantity",
    "dte": "dte",
    "strike price": "strike",
    "strike": "strike",
    "theta": "theta",
    "vega": "vega",
    "gamma": "gamma",
    "iv": "iv",
    "iv rank": "iv_rank",
    "mark": "mark",
    "multiplier": "multiplier",
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().lower() for c in df.columns]
    df = df.rename(columns={k: v for k, v in COLUMN_MAP.items() if k in df.columns})
    return df


def _parse_float(val) -> Optional[float]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        s = str(val).replace(",", "").replace("$", "").replace("%", "").strip()
        # Handle TOS bond price format like "117\"22" (32nds)
        if '"' in s:
            parts = s.split('"')
            if len(parts) == 2:
                return float(parts[0]) + float(parts[1]) / 32
        return float(s)
    except (ValueError, TypeError):
        return None


def _parse_date(val) -> Optional[date]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%b %d, %Y", "%m-%d-%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _calc_dte(expiration: Optional[date]) -> Optional[int]:
    if expiration is None:
        return None
    return max(0, (expiration - date.today()).days)


def _extract_underlying(symbol: str) -> str:
    """
    Extract root underlying from a TastyTrade symbol string.
    ./CLJ6 LO3G6 260220C65  → /CL
    ./ESM6 EW3K6 260515P5400 → /ES
    AAPL 241220C00150000     → AAPL
    /MNQH6                   → /MNQ
    """
    symbol = symbol.strip()
    # Futures options: ./CLJ6 ... or ./ESM6 ...
    m = re.match(r"^\./([A-Z]+)[A-Z0-9]", symbol)
    if m:
        return "/" + m.group(1)
    # Direct futures: /MNQH6
    m = re.match(r"^(/[A-Z]+)[A-Z0-9]", symbol)
    if m:
        return m.group(1)
    # Equity option: SYMBOL YYMMDDCSTRIKE or SYMBOL  expdate
    m = re.match(r"^([A-Z]+)\s+\d", symbol)
    if m:
        return m.group(1)
    return symbol


def _detect_strategy(legs: list[OptionLeg]) -> StrategyType:
    """Heuristic strategy detection from a group of option legs on the same underlying."""
    if not legs:
        return "unknown"

    calls = [l for l in legs if l.option_type == "call"]
    puts  = [l for l in legs if l.option_type == "put"]
    long_calls  = [l for l in calls if l.side == "long"]
    short_calls = [l for l in calls if l.side == "short"]
    long_puts   = [l for l in puts  if l.side == "long"]
    short_puts  = [l for l in puts  if l.side == "short"]

    n_long  = len(long_calls) + len(long_puts)
    n_short = len(short_calls) + len(short_puts)

    # Naked put / naked call (single short leg)
    if len(legs) == 1:
        leg = legs[0]
        if leg.side == "short":
            return "naked_put" if leg.option_type == "put" else "naked_call"
        return "unknown"

    # Strangle: short call + short put, no longs
    if short_calls and short_puts and not long_calls and not long_puts:
        return "strangle"

    # PMCC: long call (high delta, long DTE) + short call(s)
    if long_calls and short_calls and not puts:
        lc = max(long_calls, key=lambda l: l.dte or 0)
        sc = min(short_calls, key=lambda l: l.dte or 0)
        if (lc.dte or 0) > (sc.dte or 0) and abs(lc.delta or 0) > 0.4:
            return "pmcc"

    # PMCP: long put (high delta, long DTE) + short put(s)
    if long_puts and short_puts and not calls:
        lp = max(long_puts, key=lambda l: l.dte or 0)
        sp = min(short_puts, key=lambda l: l.dte or 0)
        if (lp.dte or 0) > (sp.dte or 0) and abs(lp.delta or 0) > 0.4:
            return "pmcp"

    # Richman Covered Write: long ITM put LEAP + short call
    if long_puts and short_calls and not long_calls and not short_puts:
        lp = long_puts[0]
        if (lp.dte or 0) > 180:
            return "richman"

    # 112: 1 long put + 2+ short puts, no calls
    if long_puts and len(short_puts) >= 2 and not calls:
        return "112"

    # Vertical spread: 1 long + 1 short, same type
    if len(legs) == 2:
        if long_calls and short_calls:
            return "spread"
        if long_puts and short_puts:
            return "spread"

    # Calendar: same type, opposite side, different DTE
    if len(legs) == 2:
        leg0, leg1 = legs
        if leg0.option_type == leg1.option_type and leg0.side != leg1.side:
            return "calendar"

    # Multi-leg complex
    if len(legs) >= 3:
        return "spread"

    return "unknown"


def parse_tastytrade_csv(file_path: str | Path) -> AccountSnapshot:
    """
    Parse a TastyTrade position export CSV and return an AccountSnapshot.
    Handles both the real export format and the sample format.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    raw = pd.read_csv(file_path, skiprows=0, dtype=str)
    raw = _normalize_columns(raw)

    if "symbol" not in raw.columns:
        raise ValueError(
            f"Not a valid TastyTrade CSV. Found columns: {list(raw.columns)}"
        )

    # Drop blank rows and any "Total" summary rows
    raw = raw.dropna(subset=["symbol"])
    raw = raw[~raw["symbol"].str.strip().str.upper().str.startswith("TOTAL")]

    legs_by_underlying: dict[str, list[OptionLeg]] = {}
    net_liq_account = 0.0
    buying_power_effect = 0.0

    for _, row in raw.iterrows():
        sym = str(row.get("symbol", "")).strip()
        if not sym:
            continue

        instrument_type = str(row.get("instrument_type", "")).strip().upper()

        # Skip plain futures (no option) — display only
        if instrument_type == "FUTURES":
            continue
        # Skip plain equity (stock rows if any)
        if instrument_type == "EQUITY":
            continue

        underlying = _extract_underlying(sym)

        # ── Expiration & DTE ─────────────────────────────────────────────────
        expiration = _parse_date(row.get("expiration"))
        raw_dte = _parse_float(row.get("dte"))
        dte: Optional[int] = None
        if raw_dte is not None:
            # DTE column may show "28d", "1d" — strip non-numeric suffix
            dte_str = str(row.get("dte", "")).strip().replace("d", "").replace("D", "")
            dte = int(_parse_float(dte_str) or 0)
        elif expiration:
            dte = _calc_dte(expiration)

        # ── Option type ───────────────────────────────────────────────────────
        opt_raw = str(row.get("option_type", row.get("type", "call"))).strip().lower()
        option_type: OptionSide = "put" if "put" in opt_raw or opt_raw == "p" else "call"

        # ── Side & quantity from signed quantity ───────────────────────────────
        qty_raw = _parse_float(row.get("quantity"))
        if qty_raw is None:
            continue
        # Negative quantity = short in TastyTrade export
        side_col = str(row.get("side", "")).strip().lower()
        if side_col in ("short", "s"):
            side: PositionSide = "short"
            quantity = int(abs(qty_raw))
        elif side_col in ("long", "l"):
            side = "long"
            quantity = int(abs(qty_raw))
        else:
            # Infer from sign
            side = "short" if qty_raw < 0 else "long"
            quantity = int(abs(qty_raw))

        # ── Greeks — already POSITION-TOTAL in TastyTrade export ─────────────
        # Do NOT multiply by quantity — these are already dollar-total for the leg
        theta = _parse_float(row.get("theta"))
        delta = _parse_float(row.get("delta"))
        vega  = _parse_float(row.get("vega"))
        gamma = _parse_float(row.get("gamma"))

        # ── Other fields ──────────────────────────────────────────────────────
        mark           = _parse_float(row.get("mark"))
        unrealized_pnl = _parse_float(row.get("unrealized_pnl"))
        open_price     = _parse_float(row.get("open_price") or row.get("cost"))
        iv             = _parse_float(row.get("iv"))
        iv_rank        = _parse_float(row.get("iv_rank"))
        multiplier     = _parse_float(row.get("multiplier")) or 100.0

        leg = OptionLeg(
            symbol=sym,
            underlying=underlying,
            expiration=expiration or date.today(),
            strike=_parse_float(row.get("strike")) or 0.0,
            option_type=option_type,
            side=side,
            quantity=quantity,
            multiplier=multiplier,
            dte=dte,
            mark=mark,
            delta=delta,
            theta=theta,
            vega=vega,
            gamma=gamma,
            iv=iv,
            iv_rank=iv_rank,
            open_price=open_price,
            unrealized_pnl=unrealized_pnl,
        )
        legs_by_underlying.setdefault(underlying, []).append(leg)

        # Account-level net liq (only present in legacy/sample format)
        nl = _parse_float(row.get("net_liq_account"))
        if nl and nl > 1000:  # ignore small per-position values
            net_liq_account = nl
        bpe = _parse_float(row.get("buying_power_effect"))
        if bpe:
            buying_power_effect += abs(bpe)

    # ── Group legs into positions ─────────────────────────────────────────────
    positions: list[Position] = []
    for underlying, legs in legs_by_underlying.items():
        strategy = _detect_strategy(legs)

        # Greeks are already position-total — just sum across legs
        # Sign convention: short legs earn positive theta/negative delta
        # TastyTrade already encodes P&L perspective in the sign
        net_theta = sum(l.theta or 0 for l in legs)
        net_delta = sum(l.delta or 0 for l in legs)
        net_vega  = sum(l.vega  or 0 for l in legs)

        dtes = [l.dte for l in legs if l.dte is not None]

        positions.append(Position(
            id=str(uuid.uuid4()),
            underlying=underlying,
            broker="tastytrade",
            strategy=strategy,
            legs=legs,
            net_delta=round(net_delta, 4),
            net_theta=round(net_theta, 4),
            net_vega=round(net_vega, 4),
            unrealized_pnl=sum(l.unrealized_pnl or 0 for l in legs),
            min_dte=min(dtes) if dtes else None,
            max_dte=max(dtes) if dtes else None,
        ))

    total_delta = sum(p.net_delta or 0 for p in positions)
    total_theta = sum(p.net_theta or 0 for p in positions)
    total_vega  = sum(p.net_vega  or 0 for p in positions)

    # net_liq_account = 0 when not in CSV (real TT export doesn't include it)
    # The UI will prompt the user to enter it manually
    bp_pct = (buying_power_effect / net_liq_account) if net_liq_account > 0 else 0.0

    return AccountSnapshot(
        broker="tastytrade",
        net_liq=net_liq_account,           # 0 when not in CSV
        buying_power=net_liq_account,
        buying_power_used=buying_power_effect,
        buying_power_pct=min(bp_pct, 1.0),
        positions=positions,
        total_delta=round(total_delta, 4),
        total_theta=round(total_theta, 4),
        total_vega=round(total_vega, 4),
    )
