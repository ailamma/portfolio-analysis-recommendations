# TRADE PLAN — Options Income Portfolio
# Accounts: TastyTrade ($321K NetLiq) + ThinkOrSwim ($115K NetLiq) = $436K Total

## GOAL
- 3% per month NetLiq growth (compounding ~43%/year)
- Target: ~$13,080/month increase on $436K base
- Growth measured on NetLiq, not just realized P&L
- Long-term: grow account to $1M+ by 2029

## STRATEGY MIX
| Strategy         | Description                                                                          | Allocation |
|------------------|--------------------------------------------------------------------------------------|------------|
| 112 (Calendarized) | Buy PDS long-term + Sell 2 naked puts short-term. Creates TRAP + TAIL structure.   | 30-40%     |
| IPMCC (Income PMCC) | Long LEAP call (70-90Δ, 180-365+DTE) + Short near-term call (ATM/ITM, 7-30DTE)  | 20-25%     |
| RMCW (Richman)   | Long ITM Put LEAP (60Δ, 350+DTE) + Short-term OTM Call (0.20-0.30Δ, 21DTE)        | 15-20%     |
| 90DTE Strangles  | Futures strangles (ES/GC/CL/ZB) at 6-7Δ shorts, 80-100DTE entry                  | 10-15%     |
| Naked Puts       | High-quality stocks, 30-60DTE, 0.20-0.30Δ, close at 50-60%                        | 5-10%      |
| Jade Lizard      | Short put + short call credit spread. No upside risk if total credit > spread width | 5-10%      |
| 0-DTE Spreads    | Directional credit spreads on SPX/SPY using momentum indicators                     | 0-5% spec  |
| BIL/T-Bills      | Unused cash deployed for ~4.5% APY, PM margin 7% (effective ~20% APR on margin)   | 3% of NLiq |

## GREEKS TARGETS
- Portfolio Delta: NEUTRAL to slightly positive. Max ±0.2% of NetLiq BETA-weighted to SPY
  → On $436K: max ±$872 per delta unit (absolute max ±0.3% = ±$1,308)
- Daily Theta: Minimum 0.3% of NetLiq → ~$1,308/day ($9,156/week)
- Vega: 1-1.5× Theta or less to reduce volatility exposure. Balance long/short vega.

## BUYING POWER RULES
- Target: 40-50% of available BP used (with futures & SPAN margin accounted for)
- Hard limit: Never exceed 85% BP — must take action immediately
- New trade limit: If BP > 60%, NO new trades until back under 60%
- High vol exception: Can exceed 50% when VIX spikes, but stay alert to margin changes
- Strategy limit: No single strategy uses more than 40% of available BP
- Max 2% of total NetLiq risk on any single trade

## VIX REGIME RULES
- VIX < 18: Selective. Reduce short vega. Add more PMCC (long vega). Keep BP to 45%.
- VIX 18-25: Normal operations. Sell premium actively. Target 50-55% BP.
- VIX 25-35: Aggressive premium selling. Add RMCWs. Can go to 55-60% BP max.
- VIX > 35: Defensive. Reduce size. Buy protection. Widen spreads. Never exceed 60% BP.
- When VIX spikes double digits: Start adding RMCWs within max BP of 60%

## BP REDUCTION PRIORITY (if at alert/concern level)
1. Close a winning trade
2. Close short puts of a 112 PDS
3. Close smaller losers
4. Close BIL position
5. Add a hedge using long put

## ENTRY RULES BY STRATEGY

### 112 (Calendarized 11x on /ES, /GC, etc.)
- PDS entry: 150DTE (or 120DTE), long put at 15-20Δ, ~$8-10 debit
- NP financing: 2 naked puts at 60DTE, 7-9Δ, target $15-16cr per pair
- Goal: 6% in the TAIL, 4-5× that in the TRAP
- Size: MAL = 2% of total NetLiq

### IPMCC (Income PMCC)
- Long call: 70-90Δ (ideal .80Δ), 180-365+ DTE — high-quality up-trending stocks
- Short call: ATM or ITM, 7-30DTE. Target 0.75-1% extrinsic to stock price
- Sell ATM when 8EMA > 21EMA; sell ITM when 8EMA < 21EMA
- Technicals: Up-trending weekly, 8EMA > 21EMA, RSI < 50, bouncing off support
- Close long when loss (minus CC gains) > 30% OR entire trade > 50% gain

### RMCW (Richman Covered Write)
- Long ITM Put: 60Δ, 350+ DTE on high-quality stocks
- Short Call: 21DTE, 0.20-0.30Δ (neutral to bullish bias; adjust by chart position)
- Don't enter around earnings; good to enter right after
- Size: MAL = 5-10% of NetLiq if assigned

### 90DTE Strangles on Futures
- Underlyings: /ES, /GC, /CL, /ZB, /6A, /HG preferred
- Entry: 80-100DTE, calls at 6Δ, puts at 7Δ
- Chart setup: Weekly in middle of 3-ATR bands, RSI 40-60
- Size: Max initial credit = 1-1.3% of NetLiq (1.5× credit max loss ≤ 2%)

### Naked Puts
- High-quality stocks (rising revenue+earnings 10yr, $10B+ market cap)
- DTE: 30-60DTE at entry
- Delta: 0.20-0.30Δ below 21EMA; 0.10-0.15Δ at 21EMA; no puts well above 21EMA
- Min credit: 3-5% return on BP per month
- Size: MAL = 5-10% of NetLiq if assigned

### 0-DTE Directional Credit Spreads
- Indicators: MACD, RSI, 21/50 EMAs, STOMO, 3ATR Keltner (15min + 3min)
- Wait 30-45 min after open before entering
- Sell at 5Δ shorts, 30-wide, target $0.50-0.70cr per spread
- Size: MAL < 0.5% of NetLiq

## EXIT / ROLL RULES

### Universal Profit Targets
- 112 NPs: Close at 90% of credit (freed BP + nearly free PDS hedge)
- 112 PDS: Close at 50-90% of max TRAP profit
- IPMCC short calls: Close at 80-90% extrinsic captured OR 50%+ profit in ≤50% of time
- Strangles: 50% winner
- Naked puts: 50-60% of credit
- Jade Lizard: 50-90% of credit
- 0-DTE: 50% of credit

### Universal Stop Losses
- 112 NPs: 3× credit (2× max loss)
- 112 PDS: 3× credit (2× max loss)
- Strangles: 2.5× credit (held if centered + vol spike causing 2× loss may be tolerated)
- Naked puts: 2× loss
- IPMCC long: Close entire trade if short so deep ITM rolling makes no sense
- Jade Lizard: 3× credit
- 0-DTE: 3× credit

### Roll Rules
- Roll trigger: DTE < 21 days OR position approaching max loss threshold
- Roll direction: Tested puts → roll down + out. Tested calls → roll up + out.
- Max rolls per position: 3 before accepting loss and closing
- Never let a short option be exercised/assigned if avoidable
- IPMCC: If approaching expiration on LEAP (< 2-3 months), close entire trade (theta decay)

## POSITION SIZING
- Max 5% of total NetLiq per underlying (~$21,800 at $436K)
- Futures: Use micros (/MES, /MNQ) for granular sizing
- Keep TastyTrade buying power use < 50% of net liq
- Keep TOS maintenance margin < 60% of net liq
- Never invest more than 40% of max allowed BP on any one strategy

## DIVERSIFICATION
- Spread across: Tech (NVDA/AAPL/QQQ), Financials, Commodities (/GC, /CL), Indices (/ES, /NQ)
- Always hold some tail hedge (SPX/SPY puts or long VIX calls)
- IRAs: SPYI, QQQI, BTCI (~50%) + SPY/QQQ PMCCs

## TRADE RULES (IRON LAWS)
1. Plan your trade and then trade your plan. NEVER trade without a plan for exit and entry!
2. NEVER modify or break the trade rules during a trade.
3. Stay mechanical and trade without emotion.
4. NEVER chase the entry — there will be another trade.
5. If you have to ask whether you should be in the trade, get out.
6. NEVER revenge trade. The market is always right.
7. NEVER average down or add to a losing position.
8. Nothing wrong with closing a winner — getting back in is just another trade away.
9. Never trade looking at profits first — look at max loss and size accordingly.
10. NEVER trade just because you are bored.
11. Track EVERY trade by strategy and analyze on a weekly & monthly basis.
12. Hope is not a trading strategy — if hoping, exit.
13. NEVER try to time the market. Don't leg into trades.
14. Hedge ONLY what needs to be hedged. Keep it simple: "Simplify to Multiply!"

## MONTHLY GOAL TRACKING
- Baseline: $436K total NetLiq
- Monthly 3% target: +$13,080/month
- Weekly theta floor: $9,156/week ($1,308/day)
- Track: Realized P&L + mark-to-market NetLiq change
- If behind target by week 2: Add premium-selling trades within BP limits
- If ahead of target: Consider taking off risk, locking in gains
