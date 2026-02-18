# Portfolio Advisor — Claude Code Bootstrap

This folder contains the harness files to build the **Portfolio Advisor** app using Claude Code across multiple sessions, following the [Anthropic long-running agents pattern](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents).

## What This Builds

A professional options portfolio assessment tool that:
- Ingests position exports from **TastyTrade** and **ThinkOrSwim**
- Fetches live market data (VIX, prices, IV rank)
- Uses Claude to analyze positions against your trade plan
- Outputs specific recommendations: **CLOSE / ROLL / HEDGE / MONITOR**
- Tracks progress toward your 3% monthly NetLiq growth goal

**Accounts**: TastyTrade ($321K) + ThinkOrSwim ($115K) = $436K total

---

## Files in This Bootstrap Package

| File | Purpose |
|------|---------|
| `INIT_PROMPT.md` | Prompt for the **first session only** — sets up project scaffold |
| `CODING_AGENT_PROMPT.md` | Prompt for **every subsequent session** — incremental feature work |
| `launch.sh` | Convenience script to launch Claude Code with the right prompt |
| `README.md` | This file |

---

## How to Use

### Prerequisites
```bash
# Install Claude Code if you haven't
npm install -g @anthropic-ai/claude-code

# Set your API key
export ANTHROPIC_API_KEY=sk-ant-...
```

### Session 1 — Initialize (run once)
```bash
cd portfolio-advisor-bootstrap

# Option A: Using launch script
bash launch.sh init

# Option B: Manual
cat INIT_PROMPT.md | claude --print --dangerously-skip-permissions
```

This creates the full project scaffold in `portfolio-advisor/` with:
- All directory structure
- `FEATURES.json` (feature checklist)
- `CLAUDE_PROGRESS.md` (agent memory log)
- `init.sh` (dev server startup)
- `docs/trade_plan.md` (your trading rules)
- Sample CSV files for testing
- All stub files

### Session 2+ — Incremental Development
```bash
cd portfolio-advisor   # Go into the actual project dir

# Option A: Using launch script (from bootstrap dir)
bash ../portfolio-advisor-bootstrap/launch.sh

# Option B: Manual
cat ../portfolio-advisor-bootstrap/CODING_AGENT_PROMPT.md | claude --print --dangerously-skip-permissions

# Option C: Interactive Claude Code (recommended for debugging)
claude
# Then paste the contents of CODING_AGENT_PROMPT.md as your first message
```

### Recommended Session Cadence
Each session takes ~15-30 min. After ~8-12 sessions, the app should be fully featured.

**Suggested feature order** (Claude will pick from FEATURES.json, but this is the logical order):
1. TastyTrade CSV upload + parse → show positions table
2. TOS CSV upload + parse → show positions table  
3. Market data fetch (VIX, prices, IV rank)
4. Portfolio aggregator (combine accounts, detect strategies, compute Greeks)
5. Trading analysis agent (Claude analyzing portfolio, streaming response)
6. Recommendations display (color-coded cards)
7. Portfolio summary UI (NetLiq cards, Greeks gauges, monthly progress)
8. Upload panel UI (drag-drop, status indicators)
9. Roll/close specifics (exact trade instructions in recommendations)
10. PDF export of analysis

---

## Architecture Overview

```
TastyTrade CSV ─┐
                ├→ Parsers → Normalized Portfolio → Portfolio Aggregator
TOS CSV ────────┘                                          │
                                                           ↓
                                                   Market Data (yfinance)
                                                   VIX + prices + IV rank
                                                           │
                                                           ↓
                                              Trading Analysis Agent (Claude)
                                              reads docs/trade_plan.md
                                                           │
                                                           ↓
                                                  Recommendations JSON
                                                           │
                                                           ↓
                                                   React Frontend UI
                                                  (dark theme, card-based)
```

---

## Key Trading Context

- **Goal**: 3% monthly NetLiq growth on $436K total
- **Strategies**: 112s on futures/stocks, PMCC, Richman Covered Writes, PMCP
- **Delta target**: Neutral, max ±0.3% of NetLiq per unit
- **Theta target**: Minimum 0.3% of NetLiq/day (~$1,308/day)
- **VIX rules**: Defensive <18, normal 18-25, aggressive 25-35, survival mode >35
- **Roll trigger**: DTE < 21 OR 50% profit target hit
- **Loss limit**: 2× credit received

---

## Troubleshooting

**Agent marks too many features done too fast**: The CODING_AGENT_PROMPT.md instructs it to test before marking `passes: true`. If this happens, reset suspect features to `false` in FEATURES.json.

**App broken at start of session**: The prompt instructs the agent to fix existing bugs before adding new features. If it tries to skip this, remind it: "Check init.sh first."

**Agent goes off-script**: Paste the CODING_AGENT_PROMPT.md again and add: "Start from Step 1. Don't skip steps."

**Session ends mid-feature**: The git history and CLAUDE_PROGRESS.md will tell the next agent exactly where to pick up.
