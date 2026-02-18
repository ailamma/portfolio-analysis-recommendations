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

function GreekRow({ label, value, target, unit = '', isGood }) {
  const color = isGood === undefined ? COLORS.text :
                isGood ? COLORS.success : COLORS.danger

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '8px 0',
      borderBottom: `1px solid ${COLORS.border}`,
      fontSize: '13px',
    }}>
      <span style={{ color: COLORS.textMuted }}>{label}</span>
      <div style={{ textAlign: 'right' }}>
        <span style={{ color, fontWeight: 600 }}>
          {value !== undefined && value !== null ? `${Number(value).toFixed(2)}${unit}` : '—'}
        </span>
        {target && (
          <div style={{ fontSize: '11px', color: COLORS.textMuted }}>{target}</div>
        )}
      </div>
    </div>
  )
}

export default function GreeksDisplay({ portfolio }) {
  // Default targets based on $436K portfolio
  const NET_LIQ = portfolio?.total_net_liq || 436000
  const maxDelta = NET_LIQ * 0.002
  const minTheta = NET_LIQ * 0.003

  const delta = portfolio?.combined_delta
  const theta = portfolio?.combined_theta
  const vega = portfolio?.combined_vega

  const deltaOk = delta !== undefined ? Math.abs(delta) <= maxDelta : undefined
  const thetaOk = theta !== undefined ? theta >= minTheta : undefined
  const vegaOk = vega !== undefined && theta !== undefined
    ? Math.abs(vega) <= Math.abs(theta) * 1.5 : undefined

  return (
    <div style={{
      background: COLORS.surface,
      border: `1px solid ${COLORS.border}`,
      borderRadius: '8px',
      padding: '16px',
    }}>
      <h2 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: COLORS.text }}>
        Portfolio Greeks
      </h2>

      <GreekRow
        label="Delta (β-wtd)"
        value={delta}
        target={`Target: ±${maxDelta.toFixed(0)}`}
        isGood={deltaOk}
      />
      <GreekRow
        label="Theta/day"
        value={theta}
        unit=" $"
        target={`Min: $${minTheta.toFixed(0)}/day`}
        isGood={thetaOk}
      />
      <GreekRow
        label="Vega"
        value={vega}
        target={theta ? `Max: ${(Math.abs(theta) * 1.5).toFixed(2)}` : '≤ 1.5× theta'}
        isGood={vegaOk}
      />

      {!portfolio && (
        <p style={{ fontSize: '12px', color: COLORS.textMuted, marginTop: '12px', textAlign: 'center' }}>
          Upload positions to see Greeks
        </p>
      )}
    </div>
  )
}
