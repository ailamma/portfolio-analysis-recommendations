"""
TastyTrade CSV Position Export Parser.

TastyTrade exports positions via Account → Positions → Export CSV.
The file has a header row followed by one row per option leg or stock position.

Typical columns (may vary by account type):
  Symbol, Type, Side, Quantity, Open Price, Mark, Unrealized P/L,
  Delta, Theta, Vega, Gamma, IV, IV Rank, DTE, Expiration Date, Strike Price,
  Instrument Type, Multiplier, Net Liquidating Value
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


# ── Column name normalization map ─────────────────────────────────────────────
COLUMN_MAP = {
    "symbol": "symbol",
    "type": "option_type",
    "instrument type": "instrument_type",
    "side": "side",
    "quantity": "quantity",
    "open price": "open_price",
    "mark": "mark",
    "unrealized p/l": "unrealized_pnl",
    "unrealized p&l": "unrealized_pnl",
    "delta": "delta",
    "theta": "theta",
    "vega": "vega",
    "gamma": "gamma",
    "iv": "iv",
    "iv rank": "iv_rank",
    "dte": "dte",
    "expiration date": "expiration",
    "strike price": "strike",
    "strike": "strike",
    "multiplier": "multiplier",
    "net liquidating value": "net_liq",
    "buying power effect": "buying_power_effect",
    "underlying symbol": "underlying",
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase and strip column names, then rename via COLUMN_MAP."""
    df.columns = [c.strip().lower() for c in df.columns]
    df = df.rename(columns={k: v for k, v in COLUMN_MAP.items() if k in df.columns})
    return df


def _parse_float(val) -> Optional[float]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    try:
        return float(str(val).replace(",", "").replace("$", "").replace("%", "").strip())
    except (ValueError, TypeError):
        return None


def _parse_date(val) -> Optional[date]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(str(val).strip(), fmt).date()
        except ValueError:
            continue
    return None


def _calc_dte(expiration: Optional[date]) -> Optional[int]:
    if expiration is None:
        return None
    return max(0, (expiration - date.today()).days)


def _extract_underlying(symbol: str) -> str:
    """
    TastyTrade option symbols look like:  AAPL  241220C00150000
    Futures options look like:            ./ESZ24 EW4Z4 241204P5750
    Strip to the root underlying.
    """
    symbol = symbol.strip()
    # Futures: starts with / or ./
    m = re.match(r"^\.?(/[A-Z0-9]+)", symbol)
    if m:
        return m.group(1)
    # Standard equity option: SYMBOL followed by digits
    m = re.match(r"^([A-Z]+)\s+\d", symbol)
    if m:
        return m.group(1)
    # Plain stock/ETF
    return symbol


def _detect_strategy(legs: list[OptionLeg]) -> StrategyType:
    """
    Heuristic strategy detection from a group of option legs on the same underlying.
    Returns one of the StrategyType literals.
    """
    if not legs:
        return "unknown"

    calls = [l for l in legs if l.option_type == "call"]
    puts = [l for l in legs if l.option_type == "put"]
    long_calls = [l for l in calls if l.side == "long"]
    short_calls = [l for l in calls if l.side == "short"]
    long_puts = [l for l in puts if l.side == "long"]
    short_puts = [l for l in puts if l.side == "short"]

    # PMCC: 1 long call (high delta / long DTE) + 1+ short calls
    if long_calls and short_calls and not puts:
        lc = long_calls[0]
        sc = short_calls[0]
        if lc.dte and sc.dte and lc.dte > sc.dte and (lc.delta or 0) > 0.5:
            return "pmcc"

    # PMCP: 1 long put (high delta / long DTE) + 1+ short puts
    if long_puts and short_puts and not calls:
        lp = long_puts[0]
        sp = short_puts[0]
        if lp.dte and sp.dte and lp.dte > sp.dte and abs(lp.delta or 0) > 0.5:
            return "pmcp"

    # Richman Covered Write: long ITM put (long DTE) + short call
    if long_puts and short_calls and not long_calls and not short_puts:
        lp = long_puts[0]
        if lp.dte and lp.dte > 180:
            return "richman"

    # 112 structure: 1 long put + 1 short put (PDS) + 2 naked short puts
    # Detect as: ≥1 long put + ≥2 short puts (or mixed DTE grouping)
    if long_puts and len(short_puts) >= 2 and not calls:
        return "112"

    # Strangle: 1 short call + 1 short put (no longs)
    if len(short_calls) == 1 and len(short_puts) == 1 and not long_calls and not long_puts:
        return "strangle"

    # Naked put
    if len(short_puts) == 1 and not calls and not long_puts:
        return "naked_put"

    # Naked call
    if len(short_calls) == 1 and not puts and not long_calls:
        return "naked_call"

    # Spread
    if (long_puts and short_puts and not calls) or (long_calls and short_calls and not puts):
        return "spread"

    return "unknown"


def parse_tastytrade_csv(file_path: str | Path) -> AccountSnapshot:
    """
    Parse a TastyTrade position export CSV and return an AccountSnapshot.

    Raises:
        ValueError: if the file is not a valid TastyTrade export.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Read raw — TastyTrade sometimes has a summary footer; skip non-data rows
    raw = pd.read_csv(file_path, skiprows=0, dtype=str)
    raw = _normalize_columns(raw)

    required = {"symbol"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(
            f"TastyTrade CSV missing required columns: {missing}. "
            f"Found: {list(raw.columns)}"
        )

    # Drop summary/blank rows
    raw = raw.dropna(subset=["symbol"])
    raw = raw[~raw["symbol"].str.strip().str.startswith("Total")]

    legs_by_underlying: dict[str, list[OptionLeg]] = {}
    net_liq = 0.0
    buying_power_effect = 0.0

    for _, row in raw.iterrows():
        sym = str(row.get("symbol", "")).strip()
        instrument_type = str(row.get("instrument_type", "Equity Option")).strip().lower()

        if "equity" in instrument_type and "option" not in instrument_type:
            # Plain stock — skip for now (TODO: StockLeg handling)
            continue

        underlying = _extract_underlying(sym)
        expiration = _parse_date(row.get("expiration"))
        dte = _parse_float(row.get("dte")) or _calc_dte(expiration)

        option_type_raw = str(row.get("option_type", row.get("type", "call"))).strip().lower()
        option_type: OptionSide = "call" if "call" in option_type_raw or option_type_raw == "c" else "put"

        side_raw = str(row.get("side", "long")).strip().lower()
        side: PositionSide = "short" if "short" in side_raw or side_raw == "s" else "long"

        leg = OptionLeg(
            symbol=sym,
            underlying=underlying,
            expiration=expiration or date.today(),
            strike=_parse_float(row.get("strike")) or 0.0,
            option_type=option_type,
            side=side,
            quantity=int(_parse_float(row.get("quantity")) or 1),
            multiplier=_parse_float(row.get("multiplier")) or 100.0,
            dte=int(dte) if dte is not None else None,
            mark=_parse_float(row.get("mark")),
            delta=_parse_float(row.get("delta")),
            theta=_parse_float(row.get("theta")),
            vega=_parse_float(row.get("vega")),
            gamma=_parse_float(row.get("gamma")),
            iv=_parse_float(row.get("iv")),
            iv_rank=_parse_float(row.get("iv_rank")),
            open_price=_parse_float(row.get("open_price")),
            unrealized_pnl=_parse_float(row.get("unrealized_pnl")),
        )

        legs_by_underlying.setdefault(underlying, []).append(leg)

        # Accumulate account-level stats from summary rows if present
        nl = _parse_float(row.get("net_liq"))
        if nl:
            net_liq = nl
        bpe = _parse_float(row.get("buying_power_effect"))
        if bpe:
            buying_power_effect += abs(bpe)

    # Group legs into positions and detect strategies
    positions: list[Position] = []
    for underlying, legs in legs_by_underlying.items():
        strategy = _detect_strategy(legs)
        net_delta = sum((l.delta or 0) * (1 if l.side == "long" else -1) * l.quantity for l in legs)
        net_theta = sum((l.theta or 0) * (1 if l.side == "long" else -1) * l.quantity for l in legs)
        net_vega = sum((l.vega or 0) * (1 if l.side == "long" else -1) * l.quantity for l in legs)
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
    total_vega = sum(p.net_vega or 0 for p in positions)
    bp_pct = (buying_power_effect / net_liq) if net_liq > 0 else 0.0

    return AccountSnapshot(
        broker="tastytrade",
        net_liq=net_liq,
        buying_power=net_liq,
        buying_power_used=buying_power_effect,
        buying_power_pct=min(bp_pct, 1.0),
        positions=positions,
        total_delta=round(total_delta, 4),
        total_theta=round(total_theta, 4),
        total_vega=round(total_vega, 4),
    )
