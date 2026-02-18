# Portfolio Advisor — Initializer Agent Prompt
# Use this prompt ONLY for the very first Claude Code session.
# After init is complete, switch to CODING_AGENT_PROMPT.md for all subsequent sessions.

---

You are the **Initializer Agent** for a professional options portfolio advisor application.

Your job in this session is to **set up the project environment** so that future coding agents can make incremental progress without confusion. Do NOT try to build the entire app. Focus on scaffolding, structure, and documentation.

## Your Tasks in This Session

### 1. Run pwd and orient yourself
```bash
pwd
ls
```

### 2. Create the project scaffold
Set up the following directory structure and all boilerplate files:

```
portfolio-advisor/
├── CLAUDE_PROGRESS.md          ← Agent progress log (YOU maintain this)
├── FEATURES.json               ← Feature checklist (all start as false)
├── init.sh                     ← Script to start dev server + basic smoke test
├── .env.example                ← Environment variable template
├── README.md                   ← Project overview
├── pyproject.toml              ← Poetry config
├── backend/
│   ├── __init__.py
│   ├── main.py                 ← FastAPI app entry point (stub)
│   ├── models.py               ← Pydantic data models
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── tasty_parser.py     ← TastyTrade CSV parser
│   │   └── tos_parser.py       ← ThinkOrSwim CSV parser
│   ├── market_data.py          ← yfinance market data fetcher
│   ├── portfolio_aggregator.py ← Combine accounts, detect strategies, compute Greeks
│   └── agent/
│       ├── __init__.py
│       ├── harness.py          ← Long-running agent harness (Anthropic pattern)
│       └── prompts.py          ← System prompts for the trading analysis agent
├── frontend/
│   ├── package.json
│   ├── index.html
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       └── components/
│           ├── UploadPanel.jsx
│           ├── PortfolioSummary.jsx
│           ├── RecommendationsPanel.jsx
│           └── GreeksDisplay.jsx
├── docs/
│   └── trade_plan.md           ← Trade plan (YOU create this from context below)
└── data/
    ├── uploads/                ← Raw uploaded CSVs land here
    ├── processed/              ← Normalized JSON snapshots
    └── sample/
        ├── sample_tasty.csv    ← Realistic sample TastyTrade export
        └── sample_tos.csv      ← Realistic sample TOS export
```

### 3. Populate docs/trade_plan.md with this content:

```
# TRADE PLAN — Options Income Portfolio
# Accounts: TastyTrade ($321K NetLiq) + ThinkOrSwim ($115K NetLiq) = $436K Total

## GOAL
- 3% per month NetLiq growth (compounding ~43%/year)
- Target: ~$13,080/month increase on $436K base
- Growth measured on NetLiq, not just realized P&L

## STRATEGY MIX
| Strategy         | Description                                                         | Allocation |
|------------------|---------------------------------------------------------------------|------------|
| 1-1-2 (112s)     | Buy 1 call + Buy 1 put + Sell 2 OTM options. On futures & stocks.  | 30-40%     |
| PMCC             | Long LEAP call (70-80Δ, 1-2yr) + Short near-term call (0.30Δ)      | 20-25%     |
| Richman CW       | LEAP Short Put (long delta) + Short-term Short Call (income both)   | 15-20%     |
| PMCP             | Long LEAP Put (70-80Δ) + Short near-term Put (0.30Δ)               | 10-15%     |
| Cash-Secured/Std | Short puts, strangles, spreads                                      | Remainder  |

## GREEKS TARGETS
- Portfolio Delta: NEUTRAL to slightly positive. Max ±0.3% of NetLiq per delta unit
  → On $436K: max ±$1,308 per delta unit
- Daily Theta: Minimum 0.3% of NetLiq → ~$1,308/day ($9,156/week)
- Vega: Balanced; increase short vega when VIX elevated

## VIX REGIME RULES
- VIX < 18: Selective. Reduce short vega. Be choosy with entries.
- VIX 18-25: Normal operations. Sell premium actively.
- VIX 25-35: Aggressive premium selling. Manage width carefully.
- VIX > 35: Defensive. Reduce size. Buy protection. Widen spreads.

## ENTRY RULES
- Short options: 21-45 DTE at entry
- Short options target delta: 0.20-0.30
- PMCC/PMCP LEAP: 70-80 delta, 1-2 years out
- Richman: LEAP short put 0.30-0.40Δ, short-term call 0.20-0.30Δ

## EXIT / ROLL RULES
- Profit target: Close at 50% of max profit
- Loss limit: Manage when loss = 2× credit received
- Roll trigger: DTE < 21 days OR > 50% profit (re-enter)
- Roll direction: For tested puts → roll down + out. For tested calls → roll up + out.
- Max rolls per position: 3 before accepting loss
- Never let a short option be exercised/assigned if avoidable

## POSITION SIZING
- Max 5% of total NetLiq per underlying (~$21,800)
- Futures: Use micros (/MES, /MNQ) for granular sizing
- Keep TastyTrade buying power use < 50% of net liq
- Keep TOS maintenance margin < 60% of net liq

## DIVERSIFICATION
- Spread across: Tech (NVDA/AAPL/QQQ), Financials, Commodities (/GC, /CL), Indices (/ES, /NQ)
- Always hold some tail hedge (SPX/SPY puts or long VIX calls)
```

### 4. Create FEATURES.json with all features set to `false`:

The features list should include all major capabilities the app needs. Structure each feature as:
```json
{
  "id": "F001",
  "category": "upload",
  "description": "User can upload TastyTrade CSV and see positions parsed",
  "passes": false
}
```

Include at minimum these feature categories:
- **Upload**: TastyTrade CSV upload, TOS CSV upload, validation errors shown
- **Parsing**: Greek values extracted, strategy detection (PMCC/PMCP/112/Richman), DTE calculated
- **Market Data**: VIX fetched and regime shown, per-symbol price + IV rank fetched
- **Portfolio View**: Aggregate Greeks displayed, NetLiq shown per account + combined, buying power shown
- **Analysis**: Agent triggered after upload, streaming response shown, recommendations displayed
- **Recommendations**: Close recommendations with rationale, Roll recommendations with specifics, Hedge alerts, Monthly progress toward 3% target shown
- **UI/UX**: Dark theme professional UI, mobile responsive, copy recommendation to clipboard, export analysis as PDF

### 5. Create pyproject.toml:
```toml
[tool.poetry]
name = "portfolio-advisor"
version = "0.1.0"
description = "AI options portfolio advisor for TastyTrade & ThinkOrSwim"
authors = ["Trader"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.111.0"
uvicorn = {extras = ["standard"], version = "^0.30.0"}
anthropic = "^0.34.0"
pandas = "^2.2.0"
numpy = "^1.26.0"
python-multipart = "^0.0.9"
httpx = "^0.27.0"
python-dotenv = "^1.0.0"
yfinance = "^0.2.40"
aiofiles = "^23.2.1"
pydantic = "^2.7.0"
pydantic-settings = "^2.3.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.2.0"
pytest-asyncio = "^0.23.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### 6. Create init.sh:
```bash
#!/bin/bash
# init.sh - Start dev environment and run smoke test
set -e

echo "=== Portfolio Advisor Dev Environment ==="

# Install backend deps
cd "$(dirname "$0")"
poetry install --no-root

# Install frontend deps
cd frontend && npm install && cd ..

# Start backend in background
poetry run uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Start frontend dev server in background  
cd frontend && npm run dev &
FRONTEND_PID=$!
cd ..

echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo ""
echo "Smoke test: checking /health endpoint..."
sleep 3
curl -s http://localhost:8000/health && echo " ✓ Backend healthy"

echo ""
echo "PIDs: backend=$BACKEND_PID frontend=$FRONTEND_PID"
echo "To stop: kill $BACKEND_PID $FRONTEND_PID"
```

### 7. Create realistic sample CSV files in data/sample/:

**sample_tasty.csv** — A realistic TastyTrade position export with:
- 2-3 PMCC positions (e.g., AAPL, NVDA)
- 1-2 Richman Covered Writes
- 1-2 112 structures on /ES or /NQ
- 1 short strangle
- Include realistic Greek values, IV, IV rank, P&L columns

**sample_tos.csv** — TOS position statement format with:
- 2-3 different positions using TOS export format
- Include DTE, mark, delta, theta columns

### 8. Write CLAUDE_PROGRESS.md initial entry:

```markdown
# Claude Agent Progress Log

## Session 1 — Initializer — [DATE]
**Status**: COMPLETE
**What was done**:
- Created full project scaffold
- Wrote trade_plan.md with all strategy rules
- Created FEATURES.json with N features (all false)
- Created sample CSV files for both brokerages
- Created pyproject.toml, init.sh, .env.example
- Created stub files for backend and frontend

**Next session should**:
1. Run `bash init.sh` to verify environment starts
2. Read FEATURES.json and pick the first unpassed feature
3. Implement F001 (TastyTrade CSV upload + parse) end to end
4. Test by uploading sample_tasty.csv and verifying positions appear

**Known issues / notes**:
- None yet. Fresh start.

**Git log**: (see git log)
```

### 9. Initialize git and make initial commit:
```bash
git init
git add .
git commit -m "init: project scaffold from initializer agent"
```

---

## Important Rules for This Session

1. **Do NOT implement full features** — stubs and structure only for complex files
2. **DO fully implement**: models.py, parsers, market_data.py (these are well-defined)
3. Create sample CSVs with realistic data — they are critical for testing
4. After writing CLAUDE_PROGRESS.md, **commit everything to git**
5. End your session by printing: "INITIALIZATION COMPLETE. Switch to CODING_AGENT_PROMPT.md for next session."

---

## Context for the AI Agent Prompts You Will Write

The backend agent (backend/agent/harness.py and backend/agent/prompts.py) should implement the **Anthropic long-running agent pattern** where:
- An `initializer_agent` prompt sets up context
- A `coding_agent` prompt does incremental work
- Progress is tracked via CLAUDE_PROGRESS.md + git

The **trading analysis agent** (separate from the coding agent) should:
- Receive the normalized portfolio JSON + market data
- Read docs/trade_plan.md as its system context
- Use extended thinking or multi-turn to analyze each position
- Return structured JSON recommendations: {priority, action, symbol, rationale, specific_action}
- Actions include: close, roll, adjust, hedge, enter, monitor
- Think like a professional experienced options trader with 15+ years experience
- Always reference the 3% monthly NetLiq growth goal
- Always check VIX regime before recommending aggressive positions
- Flag any positions with DTE < 21 immediately
- Check that portfolio delta and theta are within trade plan bounds
