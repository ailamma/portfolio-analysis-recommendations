"""
Pydantic data models for the Portfolio Advisor application.
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# Enums / Literals
# ─────────────────────────────────────────────

BrokerType = Literal["tastytrade", "tos"]
OptionSide = Literal["call", "put"]
PositionSide = Literal["long", "short"]
StrategyType = Literal[
    "pmcc",        # Poor Man's Covered Call (IPMCC)
    "pmcp",        # Poor Man's Covered Put
    "112",         # 1-1-2 / Calendarized 11x (PDS + 2 NPs)
    "richman",     # Richman Covered Write (long ITM put LEAP + short call)
    "strangle",    # Short strangle
    "naked_put",   # Single short put
    "naked_call",  # Single short call
    "jade_lizard", # Short put + call credit spread
    "spread",      # Generic vertical spread (bull/bear put/call spread)
    "0dte",        # 0-DTE credit spread
    "stock",       # Equity/ETF position
    "futures",     # Outright futures
    "unknown",
]
ActionType = Literal["close", "roll", "hedge", "adjust", "enter", "monitor"]
Priority = Literal["urgent", "high", "medium", "low"]
VixRegime = Literal["low", "normal", "elevated", "extreme"]


# ─────────────────────────────────────────────
# Core Position Models
# ─────────────────────────────────────────────

class OptionLeg(BaseModel):
    """A single option leg within a position."""
    symbol: str
    underlying: str
    expiration: date
    strike: float
    option_type: OptionSide
    side: PositionSide          # long or short
    quantity: int               # always positive; side conveys direction
    multiplier: float = 100.0   # 100 for equity options, varies for futures
    dte: Optional[int] = None   # calculated at parse time
    mark: Optional[float] = None
    delta: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    gamma: Optional[float] = None
    iv: Optional[float] = None  # implied volatility as decimal (0.35 = 35%)
    open_price: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    # TastyTrade-specific
    iv_rank: Optional[float] = None


class StockLeg(BaseModel):
    """A stock or ETF equity position."""
    symbol: str
    side: PositionSide
    quantity: int
    mark: Optional[float] = None
    cost_basis: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    delta: float = 1.0  # 1.0 per share for long stock, -1.0 for short


class Position(BaseModel):
    """
    A logical trading position, which may consist of multiple legs.
    Strategies like PMCC = [long LEAP call, short near-term call].
    """
    id: str                     # unique identifier (uuid or composite key)
    underlying: str
    broker: BrokerType
    strategy: StrategyType
    legs: list[OptionLeg | StockLeg] = Field(default_factory=list)
    net_delta: Optional[float] = None
    net_theta: Optional[float] = None
    net_vega: Optional[float] = None
    net_gamma: Optional[float] = None
    net_premium: Optional[float] = None   # total credit received / debit paid
    unrealized_pnl: Optional[float] = None
    note: Optional[str] = None
    # Parsed metadata
    min_dte: Optional[int] = None   # shortest DTE leg (most urgent)
    max_dte: Optional[int] = None   # longest DTE leg (LEAP)


# ─────────────────────────────────────────────
# Account / Portfolio Models
# ─────────────────────────────────────────────

class AccountSnapshot(BaseModel):
    """State of a single brokerage account at parse time."""
    broker: BrokerType
    net_liq: float
    buying_power: float
    buying_power_used: float
    buying_power_pct: float         # 0.0-1.0
    positions: list[Position] = Field(default_factory=list)
    total_delta: Optional[float] = None
    total_theta: Optional[float] = None
    total_vega: Optional[float] = None
    snapshot_time: datetime = Field(default_factory=datetime.utcnow)


class PortfolioSnapshot(BaseModel):
    """Combined view of all accounts."""
    accounts: list[AccountSnapshot] = Field(default_factory=list)
    total_net_liq: float = 0.0
    combined_delta: float = 0.0
    combined_theta: float = 0.0
    combined_vega: float = 0.0
    all_positions: list[Position] = Field(default_factory=list)
    snapshot_time: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────
# Market Data Models
# ─────────────────────────────────────────────

class MarketData(BaseModel):
    """Live market data for a single underlying."""
    symbol: str
    price: Optional[float] = None
    iv_rank: Optional[float] = None   # 0-100
    iv_percentile: Optional[float] = None
    historical_vol_30d: Optional[float] = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


class VixData(BaseModel):
    """Current VIX reading and regime classification."""
    value: float
    regime: VixRegime
    fetched_at: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    def classify(cls, vix_value: float) -> "VixData":
        if vix_value < 18:
            regime: VixRegime = "low"
        elif vix_value < 25:
            regime = "normal"
        elif vix_value <= 35:
            regime = "elevated"
        else:
            regime = "extreme"
        return cls(value=vix_value, regime=regime)


# ─────────────────────────────────────────────
# Analysis / Recommendation Models
# ─────────────────────────────────────────────

class Recommendation(BaseModel):
    """A single AI-generated trading recommendation."""
    priority: Priority
    action: ActionType
    symbol: str
    position_id: Optional[str] = None
    rationale: str
    specific_action: str        # e.g. "Close AAPL 2024-12-20 200C short @ market"
    estimated_credit: Optional[float] = None  # expected P&L impact
    urgency_flag: Optional[str] = None        # e.g. "DTE < 21 — gamma risk"


class MonthlyProgress(BaseModel):
    """Progress tracking toward the 3% monthly NetLiq goal."""
    baseline_net_liq: float
    current_net_liq: float
    target_growth_pct: float = 0.03
    target_monthly_gain: float = 0.0
    realized_pnl_mtd: float = 0.0
    unrealized_pnl_change: float = 0.0
    total_progress: float = 0.0
    progress_pct: float = 0.0   # % of monthly goal achieved
    days_elapsed: int = 0
    daily_theta: float = 0.0
    theta_vs_target: float = 0.0  # daily_theta / (net_liq * 0.003/30)

    def model_post_init(self, __context):
        self.target_monthly_gain = self.baseline_net_liq * self.target_growth_pct
        if self.target_monthly_gain > 0:
            self.progress_pct = self.total_progress / self.target_monthly_gain


class AnalysisResult(BaseModel):
    """Full output from the trading analysis agent."""
    portfolio: PortfolioSnapshot
    vix: VixData
    market_data: dict[str, MarketData] = Field(default_factory=dict)
    recommendations: list[Recommendation] = Field(default_factory=list)
    monthly_progress: Optional[MonthlyProgress] = None
    analysis_text: str = ""     # raw streaming text from Claude
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)


# ─────────────────────────────────────────────
# API Request / Response Models
# ─────────────────────────────────────────────

class UploadResponse(BaseModel):
    """Returned after a successful CSV upload and parse."""
    broker: BrokerType
    positions_parsed: int
    account: AccountSnapshot
    warnings: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
