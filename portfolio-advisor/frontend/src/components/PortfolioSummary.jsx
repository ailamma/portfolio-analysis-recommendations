import React from 'react'

const COLORS = {
  surface: '#161b22',
  border: '#30363d',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  accent: '#58a6ff',
  success: '#3fb950',
  warning: '#d29922',
  danger: '#f85149',
}

function StatCard({ label, value, subtext, color }) {
  return (
    <div style={{
      background: '#0d1117',
      border: `1px solid ${COLORS.border}`,
      borderRadius: '8px',
      padding: '14px 16px',
      flex: 1,
      minWidth: '160px',
    }}>
      <div style={{ fontSize: '11px', color: COLORS.textMuted, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        {label}
      </div>
      <div style={{ fontSize: '22px', fontWeight: 700, color: color || COLORS.text, marginTop: '4px' }}>
        {value}
      </div>
      {subtext && (
        <div style={{ fontSize: '11px', color: COLORS.textMuted, marginTop: '4px' }}>{subtext}</div>
      )}
    </div>
  )
}

function VixBadge({ vix }) {
  if (!vix) return null
  const colors = {
    low: COLORS.textMuted,
    normal: COLORS.success,
    elevated: COLORS.warning,
    extreme: COLORS.danger,
  }
  const labels = {
    low: 'LOW — Selective',
    normal: 'NORMAL — Active',
    elevated: 'ELEVATED — Aggressive',
    extreme: 'EXTREME — Defensive',
  }
  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '8px',
      background: '#0d1117',
      border: `1px solid ${colors[vix.regime]}`,
      borderRadius: '16px',
      padding: '4px 12px',
      fontSize: '12px',
      color: colors[vix.regime],
    }}>
      <span style={{ fontWeight: 700 }}>VIX {vix.value.toFixed(2)}</span>
      <span>{labels[vix.regime]}</span>
    </div>
  )
}

export default function PortfolioSummary({ portfolio, vix }) {
  if (!portfolio) {
    return (
      <div style={{
        background: COLORS.surface,
        border: `1px solid ${COLORS.border}`,
        borderRadius: '8px',
        padding: '24px',
        textAlign: 'center',
      }}>
        <div style={{ fontSize: '14px', color: COLORS.textMuted }}>
          Upload positions to see portfolio summary
        </div>
        {vix && (
          <div style={{ marginTop: '16px' }}>
            <VixBadge vix={vix} />
          </div>
        )}
      </div>
    )
  }

  const netLiq = portfolio.total_net_liq
  const monthlyTarget = netLiq * 0.03

  return (
    <div style={{
      background: COLORS.surface,
      border: `1px solid ${COLORS.border}`,
      borderRadius: '8px',
      padding: '16px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <h2 style={{ fontSize: '14px', fontWeight: 600, color: COLORS.text }}>Portfolio Summary</h2>
        {vix && <VixBadge vix={vix} />}
      </div>

      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '16px' }}>
        <StatCard
          label="Total NetLiq"
          value={`$${netLiq.toLocaleString('en-US', { maximumFractionDigits: 0 })}`}
          subtext="TastyTrade + TOS"
          color={COLORS.accent}
        />
        <StatCard
          label="Monthly Goal"
          value={`$${monthlyTarget.toLocaleString('en-US', { maximumFractionDigits: 0 })}`}
          subtext="3% of NetLiq"
        />
        <StatCard
          label="Positions"
          value={portfolio.all_positions?.length ?? 0}
          subtext="across all accounts"
        />
      </div>

      {/* Per-account breakdown */}
      {portfolio.accounts?.map(acct => (
        <div key={acct.broker} style={{
          background: '#0d1117',
          border: `1px solid ${COLORS.border}`,
          borderRadius: '6px',
          padding: '12px',
          marginBottom: '8px',
          fontSize: '13px',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
            <span style={{ fontWeight: 600 }}>{acct.broker.toUpperCase()}</span>
            <span style={{ color: COLORS.accent }}>
              ${(acct.net_liq || 0).toLocaleString('en-US', { maximumFractionDigits: 0 })}
            </span>
          </div>
          <div style={{ display: 'flex', gap: '16px', color: COLORS.textMuted, fontSize: '12px' }}>
            <span>BP: {((acct.buying_power_pct || 0) * 100).toFixed(1)}%</span>
            <span>{acct.positions?.length ?? 0} positions</span>
          </div>
        </div>
      ))}
    </div>
  )
}
