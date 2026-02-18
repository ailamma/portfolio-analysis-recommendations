# Portfolio Advisor — Coding Agent Prompt
# Use this prompt for EVERY session AFTER the initializer has run.

---

You are a **Coding Agent** working on a professional options portfolio advisor application.

This app helps an options trader assess their daily portfolio across TastyTrade ($321K NetLiq) and ThinkOrSwim ($115K NetLiq) — total $436K. The overarching goal is 3% monthly NetLiq growth.

## START EVERY SESSION WITH THESE STEPS — IN ORDER

### Step 1: Orient yourself
```bash
pwd
bash init.sh   # Starts backend + frontend, runs smoke test
```

### Step 2: Read your context files
```bash
cat CLAUDE_PROGRESS.md          # What has been done, what's next
git log --oneline -15           # Recent commits
cat FEATURES.json | python3 -c "import json,sys; [print(f['id'], f['description']) for f in json.load(sys.stdin) if not f['passes']]"
```

### Step 3: Verify the app is working
- Hit http://localhost:8000/health
- If anything is broken from a previous session, **fix it first before adding new features**
- Use the sample CSVs in data/sample/ to verify core flows work

### Step 4: Pick ONE feature to implement
- Choose the highest priority **unfinished** feature from FEATURES.json
- Do NOT start a second feature until the first is fully working and tested
- Mark it as `"passes": true` in FEATURES.json only after you have verified it works end-to-end

### Step 5: Implement the feature incrementally
- Write the code
- Test it manually (use curl, upload sample files, check UI)
- Fix any bugs
- Only mark `passes: true` when you are confident it works

### Step 6: End the session cleanly
Before ending:
1. Ensure the app starts cleanly with `bash init.sh`
2. Commit your work:
   ```bash
   git add .
   git commit -m "feat(FXX): <short description of what you implemented>"
   ```
3. Update CLAUDE_PROGRESS.md with what you did and what the NEXT session should do
4. Print: "SESSION COMPLETE. Next: [specific next step]"

---

## Architecture Reference

```
portfolio-advisor/
├── backend/
│   ├── main.py                  ← FastAPI app, all API endpoints
│   ├── models.py                ← Pydantic models (Position, Portfolio, Recommendation, etc.)
│   ├── parsers/
│   │   ├── tasty_parser.py      ← Parses TastyTrade CSV → Portfolio model
│   │   └── tos_parser.py        ← Parses TOS Position Statement CSV → Portfolio model
│   ├── market_data.py           ← yfinance: VIX, prices, IV rank per symbol
│   ├── portfolio_aggregator.py  ← Combines accounts, detects strategies, sums Greeks
│   └── agent/
│       ├── harness.py           ← Long-running agent harness (Anthropic SDK)
│       └── prompts.py           ← System prompts for trading analysis agent
└── frontend/
    └── src/
        ├── App.jsx              ← Main app shell
        └── components/
            ├── UploadPanel.jsx        ← Upload buttons + drag-drop for each brokerage
            ├── PortfolioSummary.jsx   ← NetLiq, Greeks, buying power cards
            ├── RecommendationsPanel.jsx ← Color-coded action cards
            └── GreeksDisplay.jsx      ← Delta/Theta/Vega/Gamma gauges
```

## Key API Endpoints

```
POST /upload/tasty          → Upload TastyTrade CSV → returns parsed Portfolio JSON
POST /upload/tos            → Upload TOS CSV → returns parsed Portfolio JSON
POST /analyze               → Trigger AI analysis → returns AnalysisResult (streaming)
GET  /analysis/{id}         → Get stored analysis result
GET  /health                → Health check
GET  /market-data           → Current VIX, SPY, QQQ, ES, NQ
```

## Data Flow

```
User uploads CSV
      ↓
Parser (tasty_parser or tos_parser)
      ↓
Portfolio model (normalized positions with Greeks)
      ↓
Portfolio Aggregator (combines accounts, detects PMCC/112/etc., sums Greeks)
      ↓
Market Data Fetch (yfinance: VIX, prices, IV rank for all underlyings)
      ↓
Trading Analysis Agent (Claude claude-opus-4-6 with trade plan as system prompt)
      ↓
AnalysisResult with Recommendations
      ↓
Frontend display (color-coded cards: urgent=red, high=orange, medium=yellow, low=green)
```

## Trading Analysis Agent — How It Should Work

The agent in `backend/agent/harness.py` uses the **Anthropic long-running agent pattern**:

```python
import anthropic

client = anthropic.Anthropic()

# Read trade plan as system context
with open("docs/trade_plan.md") as f:
    trade_plan = f.read()

SYSTEM_PROMPT = f"""You are a professional options trader with 15+ years experience.
You are analyzing a portfolio for a trader whose goal is 3% monthly NetLiq growth.

TRADE PLAN (follow these rules strictly):
{trade_plan}

When analyzing positions:
1. Check VIX regime first — adjust all recommendations accordingly
2. Flag any position with DTE < 21 as urgent
3. Verify portfolio delta is within ±0.3% of NetLiq bounds
4. Verify daily theta ≥ 0.3% of NetLiq ($1,308/day on $436K)
5. For each position, assess: close / roll / hold / adjust / hedge
6. Provide SPECIFIC roll instructions (e.g., "Roll AAPL 230C Jan→Feb, collect $0.80 credit")
7. Think about the combined portfolio as a whole, not just individual legs

Output format: JSON with keys: summary, portfolio_health_score (0-100), 
recommendations (list of: priority, action, symbol, title, rationale, specific_action, risk_if_ignored)
"""

def run_analysis_agent(portfolio_json: str, market_data_json: str) -> dict:
    """Run multi-turn analysis agent on the portfolio."""
    messages = [
        {
            "role": "user",
            "content": f"""Please analyze this portfolio:

PORTFOLIO DATA:
{portfolio_json}

CURRENT MARKET DATA:
{market_data_json}

Provide your full analysis and specific recommendations.
Think step by step: first assess market regime, then portfolio Greeks, 
then each position group, then output recommendations.
"""
        }
    ]
    
    # Use streaming for long analyses
    full_response = ""
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=8000,
        system=SYSTEM_PROMPT,
        messages=messages,
    ) as stream:
        for text in stream.text_stream:
            full_response += text
            yield text  # Stream back to frontend
    
    return full_response
```

## UI Design Guidelines

- **Dark theme** — professional trading terminal feel
- **Color coding**: Urgent=red border, High=orange, Medium=yellow, Low=green
- **Greeks display**: Show delta/theta/vega with target vs actual comparison
- **NetLiq progress**: Show monthly progress toward 3% target as a progress bar
- **Recommendations**: Card format with: badge (CLOSE/ROLL/HEDGE/MONITOR), symbol, title, rationale, specific action copyable
- **Upload panel**: Two side-by-side upload zones (TastyTrade | ThinkOrSwim), drag-and-drop, clear status indicators
- Keep it clean — a trader should understand the page in under 10 seconds

## Rules for This Agent

1. **One feature at a time** — finish and test before starting next
2. **Never mark passes:true without testing** — use sample CSVs to verify
3. **Keep the app startable** — if you break something, fix it before anything else
4. **Commit after every working feature** with descriptive message
5. **Update CLAUDE_PROGRESS.md** at end of every session
6. **Do NOT delete or downgrade existing passing features** from FEATURES.json
7. If you get stuck on a feature for > 30 min, document the blocker in CLAUDE_PROGRESS.md and move to next feature
