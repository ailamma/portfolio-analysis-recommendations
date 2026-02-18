"""
FastAPI application entry point for Portfolio Advisor.
"""
import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.models import AccountSnapshot, PortfolioSnapshot
from backend.parsers.tasty_parser import parse_tastytrade_csv
from backend.parsers.tos_parser import parse_tos_csv
from backend.portfolio_aggregator import aggregate

load_dotenv()

# ── Ensure data directories exist ────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
UPLOADS_DIR = Path(os.getenv("UPLOADS_DIR", str(BASE_DIR / "data" / "uploads")))
PROCESSED_DIR = Path(os.getenv("PROCESSED_DIR", str(BASE_DIR / "data" / "processed")))
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ── In-memory account state (cleared on server restart) ──────────────────────
_accounts: dict[str, AccountSnapshot] = {}  # keyed by broker: "tastytrade" | "tos"


def _current_portfolio() -> PortfolioSnapshot:
    return aggregate(list(_accounts.values()))


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Portfolio Advisor API starting up…")
    yield
    print("Portfolio Advisor API shutting down…")


app = FastAPI(
    title="Portfolio Advisor API",
    version="0.1.0",
    description="AI-powered options portfolio analysis for TastyTrade & ThinkOrSwim",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


# ── Upload endpoints ──────────────────────────────────────────────────────────

@app.post("/upload/tastytrade")
async def upload_tastytrade(file: UploadFile = File(...)):
    """Accept a TastyTrade position CSV export, parse it, return AccountSnapshot."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    content = await file.read()
    save_path = UPLOADS_DIR / f"tastytrade_{file.filename}"
    save_path.write_bytes(content)

    try:
        loop = asyncio.get_event_loop()
        account = await loop.run_in_executor(None, parse_tastytrade_csv, save_path)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=422, detail=f"Parse error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    _accounts["tastytrade"] = account
    return {
        "broker": "tastytrade",
        "positions_parsed": len(account.positions),
        "net_liq": account.net_liq,
        "buying_power_pct": account.buying_power_pct,
        "total_delta": account.total_delta,
        "total_theta": account.total_theta,
        "total_vega": account.total_vega,
        "account": account.model_dump(),
        "warnings": [],
    }


@app.post("/upload/tos")
async def upload_tos(file: UploadFile = File(...)):
    """Accept a ThinkOrSwim position statement CSV, parse it, return AccountSnapshot."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    content = await file.read()
    save_path = UPLOADS_DIR / f"tos_{file.filename}"
    save_path.write_bytes(content)

    try:
        loop = asyncio.get_event_loop()
        account = await loop.run_in_executor(None, parse_tos_csv, save_path)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=422, detail=f"Parse error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    _accounts["tos"] = account
    return {
        "broker": "tos",
        "positions_parsed": len(account.positions),
        "net_liq": account.net_liq,
        "buying_power_pct": account.buying_power_pct,
        "total_delta": account.total_delta,
        "total_theta": account.total_theta,
        "total_vega": account.total_vega,
        "account": account.model_dump(),
        "warnings": [],
    }


# ── Portfolio endpoint ────────────────────────────────────────────────────────

@app.get("/portfolio")
async def get_portfolio():
    """Return the latest aggregated portfolio snapshot from all loaded accounts."""
    if not _accounts:
        raise HTTPException(status_code=404, detail="No accounts loaded. Upload a CSV first.")
    portfolio = _current_portfolio()
    return portfolio.model_dump()


# ── Market data endpoint ──────────────────────────────────────────────────────

@app.get("/market-data")
async def get_market_data():
    """Return current VIX and per-symbol market data."""
    # TODO (F012-F014): implement full market data fetch
    return {"status": "not_implemented", "message": "Implement market_data.py fetch"}


# ── Analysis endpoint ─────────────────────────────────────────────────────────

@app.post("/analyze")
async def analyze_portfolio():
    """Trigger the AI trading analysis agent and stream the response."""
    # TODO (F021-F024): wire to agent/harness.py
    async def stream():
        yield "data: {\"status\": \"not_implemented\"}\n\n"
    return StreamingResponse(stream(), media_type="text/event-stream")
