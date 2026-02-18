# Claude Agent Progress Log

## Session 1 — Initializer — 2026-02-17
**Status**: COMPLETE
**What was done**:
- Created full project scaffold under `portfolio-advisor/`
- Wrote `docs/trade_plan.md` with complete strategy rules derived from trader's actual 2025/2026 trading plan document (IPMCC, 112 calendarized, RMCW, strangles, naked puts, jade lizard, 0-DTE, BIL)
- Created `FEATURES.json` with 38 features across 6 categories (all `passes: false`)
- Created realistic sample CSVs:
  - `data/sample/sample_tasty.csv` — AAPL PMCC, NVDA PMCC, MSFT Richman CW, /ES 112 structure, QQQ strangle, SPY naked put
  - `data/sample/sample_tos.csv` — TSLA PMCC, META Richman CW, /GC 112 structure
- Created `pyproject.toml` with all backend dependencies (FastAPI, Anthropic, yfinance, pandas, pydantic)
- Created `init.sh` for dev environment startup + smoke test
- Created `.env.example` with all environment variable documentation
- **Fully implemented**:
  - `backend/models.py` — complete Pydantic models (OptionLeg, Position, AccountSnapshot, PortfolioSnapshot, VixData, MarketData, Recommendation, AnalysisResult, etc.)
  - `backend/parsers/tasty_parser.py` — full TastyTrade CSV parser with strategy detection
  - `backend/parsers/tos_parser.py` — full TOS position statement parser with multi-section support
  - `backend/market_data.py` — yfinance-based VIX + price + IV rank fetcher (async)
  - `backend/portfolio_aggregator.py` — merge accounts, check Greeks vs trade plan
  - `backend/agent/prompts.py` — complete system prompt + analysis prompt template
  - `backend/agent/harness.py` — Anthropic streaming agent harness (SSE)
- **Stubs** (TODO comments mark where to implement):
  - `backend/main.py` — FastAPI app with /health, /upload/tastytrade, /upload/tos, /analyze, /portfolio, /market-data
  - `frontend/src/App.jsx` — main app shell with state management
  - `frontend/src/components/UploadPanel.jsx` — drag-drop upload UI
  - `frontend/src/components/PortfolioSummary.jsx` — NetLiq + account cards
  - `frontend/src/components/GreeksDisplay.jsx` — Greeks vs target display
  - `frontend/src/components/RecommendationsPanel.jsx` — streaming + recommendation cards with copy button

**Next session should**:
1. Run `cd portfolio-advisor && bash init.sh` to verify environment starts
2. Check `/health` returns `{"status": "ok"}`
3. Read `FEATURES.json` and pick **F001** (TastyTrade CSV upload + parse)
4. Wire up `backend/main.py` `/upload/tastytrade` to call `tasty_parser.py` and return a real `UploadResponse`
5. Update the frontend to display the parsed positions table when upload completes
6. Test using `data/sample/sample_tasty.csv` — verify positions appear in UI
7. Mark F001 `passes: true` in FEATURES.json only after manual verification
8. Commit: `git add . && git commit -m "feat: F001 TastyTrade CSV upload + parse"`

**Key architectural decisions made**:
- Strategy detection is heuristic-based (delta + DTE + leg count), not symbol-parsing
- TOS parser handles multi-section CSV format (separate headers per section)
- Market data uses yfinance with HV-30d as IV rank proxy (true IVR needs options chain)
- Agent harness uses SSE streaming so the frontend can show real-time analysis
- Anthropic model: `claude-opus-4-6` (configurable via `CLAUDE_MODEL` env var)

**Known issues / notes**:
- `sample_tos.csv` uses a simplified format; real TOS exports may have more header rows
- IV rank calculation is approximated from historical vol — real IV rank requires options chain data
- TOS parser assumes net_liq=$115,000 as default until we parse account summary rows
- Frontend components are stubs — they render correctly but show placeholder data

**Feature count**: 38 features defined, 0 passing

**Git log**:
```
init: project scaffold from initializer agent
```
