"""
FastAPI application entry point for Portfolio Advisor.
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

load_dotenv()

# ── Ensure data directories exist ────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
UPLOADS_DIR = Path(os.getenv("UPLOADS_DIR", BASE_DIR / "data" / "uploads"))
PROCESSED_DIR = Path(os.getenv("PROCESSED_DIR", BASE_DIR / "data" / "processed"))
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Portfolio Advisor API starting up…")
    yield
    # Shutdown
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
    """Accept a TastyTrade position CSV export and parse it."""
    # TODO (F001): implement TastyTrade CSV parse
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")
    content = await file.read()
    save_path = UPLOADS_DIR / f"tastytrade_{file.filename}"
    save_path.write_bytes(content)
    return {"status": "received", "filename": file.filename, "bytes": len(content)}


@app.post("/upload/tos")
async def upload_tos(file: UploadFile = File(...)):
    """Accept a ThinkOrSwim position statement CSV and parse it."""
    # TODO (F002): implement TOS CSV parse
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")
    content = await file.read()
    save_path = UPLOADS_DIR / f"tos_{file.filename}"
    save_path.write_bytes(content)
    return {"status": "received", "filename": file.filename, "bytes": len(content)}


# ── Portfolio / Analysis endpoints ────────────────────────────────────────────

@app.get("/portfolio")
async def get_portfolio():
    """Return the latest aggregated portfolio snapshot."""
    # TODO (F016): return PortfolioSnapshot
    return {"status": "not_implemented", "message": "Implement portfolio aggregator"}


@app.get("/market-data")
async def get_market_data():
    """Return current VIX and per-symbol market data."""
    # TODO (F012-F014): return VixData + dict[symbol, MarketData]
    return {"status": "not_implemented", "message": "Implement market_data.py"}


@app.post("/analyze")
async def analyze_portfolio():
    """Trigger the AI trading analysis agent and stream the response."""
    # TODO (F021-F024): trigger agent/harness.py and stream response
    async def stream():
        yield "data: {\"status\": \"not_implemented\"}\n\n"
    return StreamingResponse(stream(), media_type="text/event-stream")
