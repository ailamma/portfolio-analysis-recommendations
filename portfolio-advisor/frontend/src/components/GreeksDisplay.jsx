import React from 'react'

const C = {
  surface: '#161b22',
  border: '#30363d',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  success: '#3fb950',
  warning: '#d29922',
  danger: '#f85149',
}

function Row({ label, value, target, targetLabel, pass }) {
  const color = pass === undefined ? C.text : pass ? C.success : C.danger
  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
      padding: '8px 0', borderBottom: `1px solid ${C.border}`,
    }}>
      <span style={{ fontSize: '12px', color: C.textMuted }}>{label}</span>
      <div style={{ textAlign: 'right' }}>
        <div style={{ fontSize: '13px', fontWeight: 600, color }}>
          {value ?? '—'}
          {pass === false && ' ⚠'}
        </div>
        {targetLabel && <div style={{ fontSize: '10px', color: C.textMuted }}>{targetLabel}</div>}
      </div>
    </div>
  )
}

export default function GreeksDisplay({ portfolio }) {
  const nliq    = portfolio?.total_net_liq || 436000
  const delta   = portfolio?.combined_delta
  const theta   = portfolio?.combined_theta
  const vega    = portfolio?.combined_vega

  const maxDelta  = nliq * 0.002
  const minTheta  = nliq * 0.003
  const maxVega   = Math.abs(theta || 1) * 1.5

  const deltaOk = delta != null ? Math.abs(delta) <= maxDelta : undefined
  const thetaOk = theta != null ? Math.abs(theta) >= minTheta : undefined
  const vegaOk  = vega  != null ? Math.abs(vega) <= maxVega   : undefined

  return (
    <div style={{
      background: C.surface, border: `1px solid ${C.border}`,
      borderRadius: '8px', padding: '14px',
    }}>
      <div style={{ fontSize: '12px', fontWeight: 600, color: C.text, marginBottom: '4px' }}>
        Greeks
      </div>
      <Row
        label="Δ Delta"
        value={delta != null ? delta.toFixed(3) : null}
        targetLabel={`target ±${maxDelta.toFixed(0)}`}
        pass={deltaOk}
      />
      <Row
        label="Θ Theta / day"
        value={theta != null ? `$${Math.abs(theta).toFixed(0)}` : null}
        targetLabel={`min $${minTheta.toFixed(0)}`}
        pass={thetaOk}
      />
      <Row
        label="V Vega"
        value={vega != null ? vega.toFixed(3) : null}
        targetLabel={`max ${maxVega.toFixed(2)}`}
        pass={vegaOk}
      />
      {!portfolio && (
        <p style={{ fontSize: '11px', color: C.textMuted, marginTop: '10px', textAlign: 'center' }}>
          Upload to see Greeks
        </p>
      )}
    </div>
  )
}
