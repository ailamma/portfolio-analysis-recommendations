"""
ThinkOrSwim (TOS) Position Statement CSV Parser.

TOS exports a "Position Statement" from the Monitor → Activity and Positions tab.
The CSV has a multi-section format:

  Section header row (e.g. "Equities", "Options", "Futures Options")
  Column header row
  Data rows for that section
  (blank line)
  Next section...

Typical option columns:
  Symbol, Description, Qty, Trade Price, Mark, Mrk Chng, P/L Open, P/L Day,
  P/L YTD, Delta, Theta, Vega, Gamma, DTE, Exp, Strike, Type (C/P)
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


OPTION_COLS = {
    "symbol": "symbol",
    "description": "description",
    "qty": "quantity",
    "trade price": "open_price",
    "mark": "mark",
    "p/l open": "unrealized_pnl",
    "delta": "delta",
    "theta": "theta",
    "vega": "vega",
    "gamma": "gamma",
    "dte": "dte",
    "exp": "expiration",
    "strike": "strike",
    "type": "option_type",
}


def _parse_float(val) -> Optional[float]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).replace(",", "").replace("$", "").replace("%", "").strip()
    s = s.replace("(", "-").replace(")", "")  # TOS uses (123.45) for negatives
    try:
        return float(s)
    except ValueError:
        return None


def _parse_date(val) -> Optional[date]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    val = str(val).strip()
    for fmt in ("%m/%d/%y", "%m/%d/%Y", "%Y-%m-%d", "%d %b %y", "%d %b %Y"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    # TOS sometimes exports "20 DEC 24" style
    m = re.match(r"(\d{1,2})\s+([A-Z]{3})\s+(\d{2,4})", val, re.IGNORECASE)
    if m:
        try:
            return datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%d %b %y").date()
        except ValueError:
            pass
    return None


def _calc_dte(expiration: Optional[date]) -> Optional[int]:
    if expiration is None:
        return None
    return max(0, (expiration - date.today()).days)


def _extract_underlying_from_tos_symbol(symbol: str) -> str:
    """
    TOS option symbols: '100 (Weeklys) 20 DEC 24 590 CALL' or '.AAPL241220C590'
    Extract root ticker from description/symbol.
    """
    symbol = str(symbol).strip()
    # dotted format
    m = re.match(r"^\.([A-Z]+)\d", symbol)
    if m:
        return m.group(1)
    # Futures: /ESZ24 or /MES
    m = re.match(r"^(\.?/[A-Z0-9]+)", symbol)
    if m:
        return m.group(1)
    return symbol


def _parse_tos_sections(file_path: Path) -> list[pd.DataFrame]:
    """
    TOS CSV has multiple sections separated by blank lines and section header rows.
    Returns a list of DataFrames, one per section containing option-like data.
    """
    with open(file_path, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    sections = []
    current_block: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_block:
                sections.append(current_block)
                current_block = []
        else:
            current_block.append(stripped)
    if current_block:
        sections.append(current_block)

    option_dfs = []
    for block in sections:
        if len(block) < 2:
            continue
        from io import StringIO

        # Find the actual column header row (first row that contains "symbol" or "qty")
        header_idx = None
        for i, line in enumerate(block):
            if any(kw in line.lower() for kw in ["symbol", "qty", "delta", "mark"]):
                header_idx = i
                break
        if header_idx is None:
            continue

        data_block = block[header_idx:]  # slice off any section title rows
        if len(data_block) < 2:
            continue

        try:
            df = pd.read_csv(StringIO("\n".join(data_block)), dtype=str)
            df.columns = [c.strip().lower() for c in df.columns]
            df = df.rename(columns={k: v for k, v in OPTION_COLS.items() if k in df.columns})
            option_dfs.append(df)
        except Exception:
            continue

    return option_dfs


def _detect_strategy(legs: list[OptionLeg]) -> StrategyType:
    """Mirror of tastytrade parser strategy detection."""
    if not legs:
        return "unknown"
    calls = [l for l in legs if l.option_type == "call"]
    puts = [l for l in legs if l.option_type == "put"]
    long_calls = [l for l in calls if l.side == "long"]
    short_calls = [l for l in calls if l.side == "short"]
    long_puts = [l for l in puts if l.side == "long"]
    short_puts = [l for l in puts if l.side == "short"]

    if long_calls and short_calls and not puts:
        lc = long_calls[0]
        sc = short_calls[0]
        if lc.dte and sc.dte and lc.dte > sc.dte and (lc.delta or 0) > 0.5:
            return "pmcc"

    if long_puts and short_puts and not calls:
        lp = long_puts[0]
        sp = short_puts[0]
        if lp.dte and sp.dte and lp.dte > sp.dte and abs(lp.delta or 0) > 0.5:
            return "pmcp"

    if long_puts and short_calls and not long_calls and not short_puts:
        lp = long_puts[0]
        if lp.dte and lp.dte > 180:
            return "richman"

    if long_puts and len(short_puts) >= 2 and not calls:
        return "112"

    if len(short_calls) == 1 and len(short_puts) == 1 and not long_calls and not long_puts:
        return "strangle"

    if len(short_puts) == 1 and not calls and not long_puts:
        return "naked_put"

    if len(short_calls) == 1 and not puts and not long_calls:
        return "naked_call"

    if (long_puts and short_puts and not calls) or (long_calls and short_calls and not puts):
        return "spread"

    return "unknown"


def parse_tos_csv(file_path: str | Path) -> AccountSnapshot:
    """
    Parse a ThinkOrSwim Position Statement CSV and return an AccountSnapshot.

    Raises:
        ValueError: if the file cannot be parsed as a TOS export.
        FileNotFoundError: if the file does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    dfs = _parse_tos_sections(file_path)
    if not dfs:
        raise ValueError(
            "Could not parse TOS CSV — no recognizable option data sections found. "
            "Export via Monitor → Activity and Positions → Position Statement."
        )

    legs_by_underlying: dict[str, list[OptionLeg]] = {}
    net_liq = 115000.0  # default; TOS CSV may not always include account-level figures
    buying_power_used = 0.0

    for df in dfs:
        for _, row in df.iterrows():
            sym = str(row.get("symbol", "")).strip()
            if not sym or sym.lower() in ("symbol", "nan", ""):
                continue

            qty_raw = _parse_float(row.get("quantity"))
            if qty_raw is None:
                continue

            # TOS quantity: positive = long, negative = short
            side: PositionSide = "long" if (qty_raw or 0) >= 0 else "short"
            quantity = int(abs(qty_raw or 1))

            opt_type_raw = str(row.get("option_type", "")).strip().upper()
            # Sometimes in description: "100 20 DEC 24 590 CALL"
            if not opt_type_raw or opt_type_raw == "NAN":
                desc = str(row.get("description", "")).upper()
                opt_type_raw = "CALL" if "CALL" in desc else "PUT" if "PUT" in desc else "CALL"
            option_type: OptionSide = "call" if "C" in opt_type_raw else "put"

            expiration = _parse_date(row.get("expiration"))
            dte_raw = _parse_float(row.get("dte"))
            dte = int(dte_raw) if dte_raw is not None else _calc_dte(expiration)

            underlying = _extract_underlying_from_tos_symbol(sym)

            leg = OptionLeg(
                symbol=sym,
                underlying=underlying,
                expiration=expiration or date.today(),
                strike=_parse_float(row.get("strike")) or 0.0,
                option_type=option_type,
                side=side,
                quantity=quantity,
                multiplier=100.0,
                dte=dte,
                mark=_parse_float(row.get("mark")),
                delta=_parse_float(row.get("delta")),
                theta=_parse_float(row.get("theta")),
                vega=_parse_float(row.get("vega")),
                gamma=_parse_float(row.get("gamma")),
                open_price=_parse_float(row.get("open_price")),
                unrealized_pnl=_parse_float(row.get("unrealized_pnl")),
            )
            legs_by_underlying.setdefault(underlying, []).append(leg)

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
            broker="tos",
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

    return AccountSnapshot(
        broker="tos",
        net_liq=net_liq,
        buying_power=net_liq * 0.6,
        buying_power_used=buying_power_used,
        buying_power_pct=0.0,
        positions=positions,
        total_delta=round(total_delta, 4),
        total_theta=round(total_theta, 4),
        total_vega=round(total_vega, 4),
    )
