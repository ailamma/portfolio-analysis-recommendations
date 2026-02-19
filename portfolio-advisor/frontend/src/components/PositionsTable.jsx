import React, { useState } from 'react'

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
  rowHover: '#1c2128',
}

const STRATEGY_COLORS = {
  pmcc:       { bg: '#1a2d4a', text: '#58a6ff', label: 'PMCC' },
  pmcp:       { bg: '#1a2d4a', text: '#79c0ff', label: 'PMCP' },
  '112':      { bg: '#2d1f4a', text: '#d2a8ff', label: '112' },
  richman:    { bg: '#1f3a2d', text: '#56d364', label: 'RMCW' },
  strangle:   { bg: '#3a2d1a', text: '#e3b341', label: 'STRANGLE' },
  naked_put:  { bg: '#3a2020', text: '#f85149', label: 'NAKED PUT' },
  naked_call: { bg: '#3a2020', text: '#f85149', label: 'NAKED CALL' },
  spread:     { bg: '#2d2a1a', text: '#d29922', label: 'SPREAD' },
  jade_lizard:{ bg: '#1f3a2d', text: '#3fb950', label: 'JADE' },
  '0dte':     { bg: '#3a1a1a', text: '#ff7b72', label: '0-DTE' },
  unknown:    { bg: '#1c2128', text: '#8b949e', label: '?' },
}

function StrategyBadge({ strategy }) {
  const s = STRATEGY_COLORS[strategy] || STRATEGY_COLORS.unknown
  return (
    <span style={{
      background: s.bg,
      color: s.text,
      fontSize: '10px',
      fontWeight: 700,
      padding: '2px 6px',
      borderRadius: '4px',
      letterSpacing: '0.3px',
      whiteSpace: 'nowrap',
    }}>
      {s.label}
    </span>
  )
}

function DteBadge({ dte }) {
  if (dte == null) return <span style={{ color: C.textMuted }}>—</span>
  const color = dte < 7 ? C.urgent : dte < 21 ? C.danger : dte < 45 ? C.warning : C.success
  return (
    <span style={{ color, fontWeight: dte < 21 ? 700 : 400 }}>
      {dte < 21 && '⚠ '}{dte}d
    </span>
  )
}

function fmt(val, decimals = 2, prefix = '') {
  if (val == null) return '—'
  const n = Number(val)
  if (isNaN(n)) return '—'
  return `${prefix}${n.toFixed(decimals)}`
}

function fmtPnl(val) {
  if (val == null) return '—'
  const n = Number(val)
  if (isNaN(n)) return '—'
  const color = n >= 0 ? C.success : C.danger
  return <span style={{ color }}>{n >= 0 ? '+' : ''}${n.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</span>
}

function ExpandedLegs({ legs }) {
  return (
    <tr>
      <td colSpan={9} style={{ padding: 0 }}>
        <div style={{
          background: '#0d1117',
          borderTop: `1px solid ${C.border}`,
          padding: '8px 16px 8px 32px',
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
            <thead>
              <tr style={{ color: C.textMuted }}>
                <td style={{ padding: '4px 8px' }}>Side</td>
                <td style={{ padding: '4px 8px' }}>Qty</td>
                <td style={{ padding: '4px 8px' }}>Strike</td>
                <td style={{ padding: '4px 8px' }}>Type</td>
                <td style={{ padding: '4px 8px' }}>Exp</td>
                <td style={{ padding: '4px 8px' }}>DTE</td>
                <td style={{ padding: '4px 8px' }}>Mark</td>
                <td style={{ padding: '4px 8px' }}>Δ</td>
                <td style={{ padding: '4px 8px' }}>Θ</td>
                <td style={{ padding: '4px 8px' }}>IV</td>
              </tr>
            </thead>
            <tbody>
              {legs.map((leg, i) => (
                <tr key={i} style={{ color: C.text }}>
                  <td style={{ padding: '4px 8px', color: leg.side === 'long' ? C.success : C.danger, fontWeight: 600 }}>
                    {leg.side.toUpperCase()}
                  </td>
                  <td style={{ padding: '4px 8px' }}>{leg.quantity}</td>
                  <td style={{ padding: '4px 8px' }}>{leg.strike}</td>
                  <td style={{ padding: '4px 8px', color: leg.option_type === 'call' ? C.accent : C.warning }}>
                    {leg.option_type.toUpperCase()}
                  </td>
                  <td style={{ padding: '4px 8px', color: C.textMuted }}>{leg.expiration}</td>
                  <td style={{ padding: '4px 8px' }}><DteBadge dte={leg.dte} /></td>
                  <td style={{ padding: '4px 8px' }}>{fmt(leg.mark)}</td>
                  <td style={{ padding: '4px 8px' }}>{fmt(leg.delta, 3)}</td>
                  <td style={{ padding: '4px 8px' }}>{fmt(leg.theta, 3)}</td>
                  <td style={{ padding: '4px 8px', color: C.textMuted }}>
                    {leg.iv ? `${(leg.iv * 100).toFixed(0)}%` : '—'}
                    {leg.iv_rank != null ? <span style={{ color: C.textMuted }}> ({leg.iv_rank.toFixed(0)})</span> : null}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </td>
    </tr>
  )
}

export default function PositionsTable({ positions, broker, marketData = {} }) {
  const [expanded, setExpanded] = useState(new Set())

  if (!positions || positions.length === 0) return null

  const filtered = broker ? positions.filter(p => p.broker === broker) : positions

  const toggleExpand = (id) => {
    setExpanded(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const thStyle = {
    padding: '8px 12px',
    textAlign: 'left',
    fontSize: '11px',
    fontWeight: 600,
    color: C.textMuted,
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    borderBottom: `1px solid ${C.border}`,
    whiteSpace: 'nowrap',
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
        <thead>
          <tr style={{ background: C.surface }}>
            <th style={thStyle}></th>
            <th style={thStyle}>Underlying</th>
            <th style={thStyle}>Strategy</th>
            <th style={thStyle}>Broker</th>
            <th style={thStyle}>Price</th>
            <th style={thStyle}>Min DTE</th>
            <th style={{ ...thStyle, textAlign: 'right' }}>Δ Net</th>
            <th style={{ ...thStyle, textAlign: 'right' }}>Θ Net</th>
            <th style={{ ...thStyle, textAlign: 'right' }}>P&L</th>
          </tr>
        </thead>
        <tbody>
          {filtered.map((pos) => {
            const isOpen = expanded.has(pos.id)
            const urgent = pos.min_dte != null && pos.min_dte < 21
            return (
              <React.Fragment key={pos.id}>
                <tr
                  onClick={() => toggleExpand(pos.id)}
                  style={{
                    cursor: 'pointer',
                    background: urgent ? '#1a0f0f' : 'transparent',
                    borderLeft: urgent ? `3px solid ${C.urgent}` : `3px solid transparent`,
                    transition: 'background 0.1s',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = urgent ? '#200f0f' : C.rowHover}
                  onMouseLeave={e => e.currentTarget.style.background = urgent ? '#1a0f0f' : 'transparent'}
                >
                  <td style={{ padding: '10px 8px 10px 12px', color: C.textMuted, fontSize: '11px' }}>
                    {isOpen ? '▼' : '▶'}
                  </td>
                  <td style={{ padding: '10px 12px', fontWeight: 600, color: urgent ? C.urgent : C.text }}>
                    {pos.underlying}
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <StrategyBadge strategy={pos.strategy} />
                  </td>
                  <td style={{ padding: '10px 12px', color: C.textMuted, fontSize: '12px' }}>
                    {pos.broker === 'tastytrade' ? 'TT' : 'TOS'}
                  </td>
                  <td style={{ padding: '10px 12px', fontSize: '12px', color: C.textMuted }}>
                    {marketData[pos.underlying]?.price
                      ? `$${marketData[pos.underlying].price.toFixed(2)}`
                      : '—'}
                  </td>
                  <td style={{ padding: '10px 12px' }}>
                    <DteBadge dte={pos.min_dte} />
                  </td>
                  <td style={{ padding: '10px 12px', textAlign: 'right', color: (pos.net_delta || 0) >= 0 ? C.success : C.danger }}>
                    {fmt(pos.net_delta, 3)}
                  </td>
                  <td style={{ padding: '10px 12px', textAlign: 'right', color: (pos.net_theta || 0) >= 0 ? C.success : C.textMuted }}>
                    {fmt(pos.net_theta, 2)}
                  </td>
                  <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                    {fmtPnl(pos.unrealized_pnl)}
                  </td>
                </tr>
                {isOpen && <ExpandedLegs legs={pos.legs || []} />}
                <tr>
                  <td colSpan={9} style={{ padding: 0, borderBottom: `1px solid ${C.border}` }} />
                </tr>
              </React.Fragment>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
