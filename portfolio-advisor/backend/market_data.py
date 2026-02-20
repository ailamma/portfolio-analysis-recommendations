"""
Market data fetcher using yfinance.
Fetches VIX, per-symbol prices, and IV rank estimates.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Optional

import numpy as np
import yfinance as yf

from backend.models import MarketData, VixData


# ── VIX ───────────────────────────────────────────────────────────────────────

async def fetch_vix() -> VixData:
    """Fetch current VIX value and classify regime."""
    loop = asyncio.get_event_loop()
    value = await loop.run_in_executor(None, _fetch_vix_sync)
    return VixData.classify(value)


def _fetch_vix_sync() -> float:
    ticker = yf.Ticker("^VIX")
    hist = ticker.history(period="1d", interval="1m")
    if hist.empty:
        # Fallback: try daily
        hist = ticker.history(period="5d")
    if hist.empty:
        return 20.0  # default to "normal" regime if unavailable
    return float(hist["Close"].iloc[-1])


# ── Per-Symbol Market Data ────────────────────────────────────────────────────

# Symbols that yfinance can't resolve — map to correct ticker or skip
SYMBOL_MAP = {
    "BRKB": "BRK-B",
    "SPXW": None,    # SPX weeklies — index, no yfinance ticker; skip
    "MRUT": None,    # Russell micro — skip
}


async def fetch_market_data(symbols: list[str]) -> dict[str, MarketData]:
    """
    Fetch current price and estimated IV rank for a list of symbols.
    Futures (/ES, /CL, etc.) are skipped.
    Known problematic tickers are remapped or skipped.
    """
    now = datetime.utcnow()
    yf_symbols = []
    remap: dict[str, str] = {}   # yf_sym → original_sym

    for sym in symbols:
        if sym.startswith("/"):
            continue  # futures — no yfinance data
        mapped = SYMBOL_MAP.get(sym)
        if mapped is None and sym in SYMBOL_MAP:
            continue  # explicitly skipped
        yf_sym = mapped if mapped else sym
        yf_symbols.append(yf_sym)
        remap[yf_sym] = sym

    if not yf_symbols:
        return {}

    loop = asyncio.get_event_loop()
    raw = await loop.run_in_executor(None, _fetch_batch_sync, yf_symbols)

    # Re-key results back to original symbol names
    results: dict[str, MarketData] = {}
    for yf_sym, md in raw.items():
        orig = remap.get(yf_sym, yf_sym)
        results[orig] = MarketData(
            symbol=orig,
            price=md.price,
            iv_rank=md.iv_rank,
            historical_vol_30d=md.historical_vol_30d,
            fetched_at=md.fetched_at,
        )
    return results


def _fetch_batch_sync(symbols: list[str]) -> dict[str, MarketData]:
    """Synchronous batch fetch using yfinance download."""
    results: dict[str, MarketData] = {}
    now = datetime.utcnow()

    # yfinance download for current price
    try:
        tickers = yf.download(
            tickers=" ".join(symbols),
            period="1y",
            interval="1d",
            group_by="ticker",
            auto_adjust=True,
            progress=False,
            threads=True,
        )
    except Exception:
        tickers = None

    for sym in symbols:
        try:
            md = _build_market_data(sym, tickers, now)
            results[sym] = md
        except Exception:
            results[sym] = MarketData(symbol=sym, fetched_at=now)

    return results


def _finite(val) -> Optional[float]:
    """Return float if finite, else None. Guards against NaN/Inf from yfinance."""
    if val is None:
        return None
    try:
        f = float(val)
        return f if np.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def _build_market_data(
    symbol: str,
    tickers_data,
    now: datetime,
) -> MarketData:
    """Extract price and IV rank for a single symbol from yfinance data."""
    price: Optional[float] = None
    iv_rank: Optional[float] = None
    hv_30d: Optional[float] = None

    try:
        if tickers_data is not None and not tickers_data.empty:
            if len(tickers_data.columns.levels[0]) > 1:
                # Multi-ticker grouping
                close_col = tickers_data[symbol]["Close"] if symbol in tickers_data.columns.get_level_values(0) else None
            else:
                close_col = tickers_data["Close"]

            if close_col is not None and not close_col.empty:
                price = _finite(close_col.iloc[-1])
                # Historical volatility (30-day annualized)
                if len(close_col) >= 21:
                    returns = np.log(close_col / close_col.shift(1)).dropna()
                    hv_30d = _finite(returns.tail(21).std() * np.sqrt(252))
    except Exception:
        pass

    # Try single ticker for price if batch failed
    if price is None:
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="5d")
            if not hist.empty:
                price = _finite(hist["Close"].iloc[-1])
        except Exception:
            pass

    # Estimate IV rank using 52-week high/low of realized vol as proxy
    # (True IV rank requires options chain data — this is an approximation)
    if hv_30d is not None:
        try:
            t = yf.Ticker(symbol)
            hist_1y = t.history(period="1y")
            if len(hist_1y) >= 252:
                log_returns = np.log(hist_1y["Close"] / hist_1y["Close"].shift(1)).dropna()
                rolling_hv = log_returns.rolling(21).std() * np.sqrt(252)
                hv_min = _finite(rolling_hv.min())
                hv_max = _finite(rolling_hv.max())
                if hv_min is not None and hv_max is not None and hv_max > hv_min:
                    iv_rank = round((hv_30d - hv_min) / (hv_max - hv_min) * 100, 1)
        except Exception:
            pass

    return MarketData(
        symbol=symbol,
        price=price,
        iv_rank=iv_rank,
        historical_vol_30d=hv_30d,
        fetched_at=now,
    )


# ── Convenience ───────────────────────────────────────────────────────────────

async def fetch_all(symbols: list[str]) -> tuple[VixData, dict[str, MarketData]]:
    """Fetch VIX and all symbol market data concurrently."""
    vix_task = asyncio.create_task(fetch_vix())
    market_task = asyncio.create_task(fetch_market_data(symbols))
    vix, market = await asyncio.gather(vix_task, market_task)
    return vix, market
