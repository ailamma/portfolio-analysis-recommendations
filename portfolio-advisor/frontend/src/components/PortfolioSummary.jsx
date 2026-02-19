import React from 'react'

const C = {
  surface: '#161b22',
  border: '#30363d',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  accent: '#58a6ff',
  success: '#3fb950',
  warning: '#d29922',
  danger: '#f85149',
  urgent: '#ff7b72',
}

const VIX_META = {
  low:      { color: C.textMuted, label: 'LOW',      hint: 'Selective — reduce short vega' },
  normal:   { color: C.success,   label: 'NORMAL',   hint: 'Active premium selling' },
  elevated: { color: C.warning,   label: 'ELEVATED', hint: 'Aggressive — add RMCWs' },
  extreme:  { color: C.danger,    label: 'EXTREME',  hint: 'Defensive — reduce size' },
}

export function VixBadge({ vix }) {
  if (!vix) return null
  const meta = VIX_META[vix.regime] || VIX_META.normal
  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: '8px',
      background: '#0d1117', border: `1px solid ${meta.color}40`,
      borderRadius: '6px', padding: '6px 12px',
    }}>
      <div style={{ width: '7px', height: '7px', borderRadius: '50%', background: meta.color }} />
      <span style={{ fontSize: '13px', fontWeight: 700, color: meta.color }}>
        VIX {vix.value.toFixed(2)}
      </span>
      <span style={{ fontSize: '11px', color: C.textMuted }}>{meta.label} · {meta.hint}</span>
    </div>
  )
}

function StatCard({ label, value, subtext, color, warn }) {
  return (
    <div style={{
      background: '#0d1117',
      border: `1px solid ${warn ? C.warning + '60' : C.border}`,
      borderRadius: '8px', padding: '12px 14px', flex: 1, minWidth: '130px',
    }}>
      <div style={{ fontSize: '10px', color: C.textMuted, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        {label}
      </div>
      <div style={{ fontSize: '20px', fontWeight: 700, color: color || C.text, marginTop: '4px', whiteSpace: 'nowrap' }}>
        {value}
      </div>
      {subtext && <div style={{ fontSize: '11px', color: C.textMuted, marginTop: '2px' }}>{subtext}</div>}
    </div>
  )
}

function GreekBar({ label, value, min, max, target, unit = '', isPositiveGood }) {
  // value within [min, max]; target line shown; color based on pass/fail
  const pct = max !== min ? Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100)) : 0
  const targetPct = max !== min ? Math.min(100, Math.max(0, ((target - min) / (max - min)) * 100)) : 0
  const pass = isPositiveGood ? value >= target : Math.abs(value) <= target
  const barColor = pass ? C.success : C.danger

  return (
    <div style={{ marginBottom: '12px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: '12px' }}>
        <span style={{ color: C.textMuted }}>{label}</span>
        <span style={{ color: barColor, fontWeight: 600 }}>
          {unit === '$' ? `$${value.toFixed(0)}` : value.toFixed(3)}{unit !== '$' ? unit : ''}
          {!pass && <span style={{ marginLeft: '6px', fontSize: '10px' }}>⚠</span>}
        </span>
      </div>
      <div style={{ position: 'relative', height: '6px', background: '#1c2128', borderRadius: '3px' }}>
        <div style={{
          height: '100%', width: `${pct}%`, background: barColor,
          borderRadius: '3px', transition: 'width 0.4s',
        }} />
        {/* Target marker */}
        <div style={{
          position: 'absolute', top: '-3px', left: `${targetPct}%`,
          width: '2px', height: '12px', background: C.textMuted,
          transform: 'translateX(-50%)',
        }} />
      </div>
      <div style={{ fontSize: '10px', color: C.textMuted, marginTop: '3px', textAlign: 'right' }}>
        target: {unit === '$' ? `$${target.toFixed(0)}` : target.toFixed(2)}{unit !== '$' ? unit : ''}
      </div>
    </div>
  )
}

function BpBar({ label, pct, broker }) {
  const color = pct > 0.85 ? C.urgent : pct > 0.60 ? C.danger : pct > 0.50 ? C.warning : C.success
  const status = pct > 0.85 ? 'CRITICAL' : pct > 0.60 ? 'HIGH — no new trades' : pct > 0.50 ? 'ELEVATED' : 'OK'
  return (
    <div style={{ marginBottom: '10px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
        <span style={{ color: C.textMuted }}>{label}</span>
        <span style={{ color, fontWeight: 600 }}>{(pct * 100).toFixed(1)}% <span style={{ fontSize: '10px', fontWeight: 400 }}>{status}</span></span>
      </div>
      <div style={{ height: '5px', background: '#1c2128', borderRadius: '3px' }}>
        <div style={{ height: '100%', width: `${Math.min(100, pct * 100)}%`, background: color, borderRadius: '3px' }} />
      </div>
    </div>
  )
}

function MonthlyProgress({ netLiq, realizedPnl }) {
  const target = netLiq * 0.03
  const pct = target > 0 ? Math.min(1, realizedPnl / target) : 0
  const color = pct >= 1 ? C.success : pct >= 0.5 ? C.accent : pct >= 0.25 ? C.warning : C.textMuted
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '4px' }}>
        <span style={{ color: C.textMuted }}>Monthly progress (3% goal)</span>
        <span style={{ color, fontWeight: 600 }}>
          ${realizedPnl.toLocaleString('en-US', { maximumFractionDigits: 0 })} / ${target.toLocaleString('en-US', { maximumFractionDigits: 0 })}
          <span style={{ color: C.textMuted, fontWeight: 400 }}> ({(pct * 100).toFixed(0)}%)</span>
        </span>
      </div>
      <div style={{ height: '8px', background: '#1c2128', borderRadius: '4px', overflow: 'hidden' }}>
        <div style={{
          height: '100%', width: `${pct * 100}%`, background: color,
          borderRadius: '4px', transition: 'width 0.5s',
        }} />
      </div>
    </div>
  )
}

export default function PortfolioSummary({ portfolio, vix, marketData }) {
  if (!portfolio) {
    return (
      <div style={{
        background: C.surface, border: `1px solid ${C.border}`,
        borderRadius: '8px', padding: '20px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '13px', color: C.textMuted }}>Upload positions to see portfolio summary</span>
          {vix && <VixBadge vix={vix} />}
        </div>
      </div>
    )
  }

  const netLiq = portfolio.total_net_liq || 436000
  const realizedPnl = portfolio.all_positions?.reduce((s, p) => s + (p.unrealized_pnl || 0), 0) || 0

  // Trade plan thresholds
  const maxDelta   = netLiq * 0.002          // ±0.2% of NetLiq
  const minTheta   = netLiq * 0.003          // 0.3% of NetLiq / day
  const maxVega    = Math.abs(portfolio.combined_theta || 1) * 1.5

  const delta      = portfolio.combined_delta || 0
  const theta      = portfolio.combined_theta || 0
  const vega       = portfolio.combined_vega  || 0

  const urgentCount = portfolio.all_positions?.filter(p => p.min_dte != null && p.min_dte < 21).length || 0

  return (
    <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: '8px', padding: '16px' }}>
      {/* Top row: VIX + urgent count */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
        {vix ? <VixBadge vix={vix} /> : <div />}
        {urgentCount > 0 && (
          <div style={{
            background: '#2d1317', border: `1px solid ${C.urgent}`,
            borderRadius: '6px', padding: '4px 10px',
            fontSize: '12px', color: C.urgent, fontWeight: 600,
          }}>
            ⚠ {urgentCount} position{urgentCount > 1 ? 's' : ''} DTE &lt; 21
          </div>
        )}
      </div>

      {/* NetLiq stat cards */}
      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '14px' }}>
        <StatCard
          label="Total NetLiq"
          value={`$${netLiq.toLocaleString('en-US', { maximumFractionDigits: 0 })}`}
          subtext={`${portfolio.accounts?.length || 0} accounts`}
          color={C.accent}
        />
        <StatCard
          label="Monthly Target"
          value={`$${(netLiq * 0.03).toLocaleString('en-US', { maximumFractionDigits: 0 })}`}
          subtext="3% of NetLiq"
        />
        <StatCard
          label="Positions"
          value={portfolio.all_positions?.length ?? 0}
          subtext={urgentCount > 0 ? `${urgentCount} urgent` : 'all clear'}
          color={urgentCount > 0 ? C.urgent : C.text}
        />
        <StatCard
          label="Daily θ Target"
          value={`$${minTheta.toFixed(0)}`}
          subtext="min 0.3% of NLiq"
        />
      </div>

      {/* Per-account row */}
      <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '14px' }}>
        {portfolio.accounts?.map(acct => {
          const bpPct = acct.buying_power_pct || 0
          const bpColor = bpPct > 0.85 ? C.urgent : bpPct > 0.60 ? C.danger : bpPct > 0.50 ? C.warning : C.success
          const configuredNliq = acct.broker === 'tastytrade' ? 321000 : 115000
          const displayNliq = acct.net_liq > 0 ? acct.net_liq : configuredNliq
          return (
            <div key={acct.broker} style={{
              flex: 1, minWidth: '180px',
              background: '#0d1117', border: `1px solid ${C.border}`,
              borderRadius: '8px', padding: '10px 14px',
            }}>
              <div style={{ fontSize: '11px', color: C.textMuted, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>
                {acct.broker === 'tastytrade' ? 'TastyTrade' : 'ThinkOrSwim'}
              </div>
              <div style={{ fontSize: '18px', fontWeight: 700, color: C.accent, marginBottom: '6px' }}>
                ${displayNliq.toLocaleString('en-US', { maximumFractionDigits: 0 })}
              </div>
              <div style={{ fontSize: '11px', marginBottom: '6px' }}>
                <span style={{ color: C.textMuted }}>{acct.positions?.length ?? 0} positions</span>
              </div>
              <BpBar label="Buying Power" pct={bpPct} />
            </div>
          )
        })}
      </div>

      {/* Greeks vs trade plan */}
      <div style={{ marginBottom: '14px' }}>
        <div style={{ fontSize: '11px', color: C.textMuted, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px' }}>
          Greeks vs Trade Plan
        </div>
        <GreekBar
          label="Portfolio Delta (β-wtd)"
          value={Math.abs(delta)}
          min={0} max={maxDelta * 2} target={maxDelta}
          unit="" isPositiveGood={false}
        />
        <GreekBar
          label="Daily Theta"
          value={Math.abs(theta)}
          min={0} max={minTheta * 3} target={minTheta}
          unit="$" isPositiveGood={true}
        />
        <GreekBar
          label="Vega (abs)"
          value={Math.abs(vega)}
          min={0} max={maxVega * 2} target={maxVega}
          unit="" isPositiveGood={false}
        />
      </div>

      {/* Monthly P&L progress */}
      <MonthlyProgress netLiq={netLiq} realizedPnl={realizedPnl} />
    </div>
  )
}
