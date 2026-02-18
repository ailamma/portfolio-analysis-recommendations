import React, { useState } from 'react'

const COLORS = {
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

const PRIORITY_COLORS = {
  urgent: COLORS.urgent,
  high: COLORS.danger,
  medium: COLORS.warning,
  low: COLORS.textMuted,
}

const ACTION_COLORS = {
  close: COLORS.danger,
  roll: COLORS.accent,
  hedge: COLORS.urgent,
  adjust: COLORS.warning,
  enter: COLORS.success,
  monitor: COLORS.textMuted,
}

function RecommendationCard({ rec }) {
  const [copied, setCopied] = useState(false)

  const priorityColor = PRIORITY_COLORS[rec.priority] || COLORS.text
  const actionColor = ACTION_COLORS[rec.action] || COLORS.text

  const handleCopy = () => {
    const text = `[${rec.priority.toUpperCase()}] ${rec.action.toUpperCase()} ${rec.symbol}\n${rec.rationale}\nAction: ${rec.specific_action}`
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <div style={{
      background: '#0d1117',
      border: `1px solid ${priorityColor}40`,
      borderLeft: `3px solid ${priorityColor}`,
      borderRadius: '6px',
      padding: '14px',
      marginBottom: '10px',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <span style={{
            fontSize: '11px',
            fontWeight: 700,
            color: priorityColor,
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
          }}>
            {rec.priority}
          </span>
          <span style={{
            fontSize: '11px',
            background: `${actionColor}20`,
            color: actionColor,
            padding: '2px 8px',
            borderRadius: '12px',
            fontWeight: 600,
            textTransform: 'uppercase',
          }}>
            {rec.action}
          </span>
          <span style={{ fontSize: '14px', fontWeight: 700, color: COLORS.text }}>
            {rec.symbol}
          </span>
          {rec.urgency_flag && (
            <span style={{ fontSize: '11px', color: COLORS.urgent }}>⚠ {rec.urgency_flag}</span>
          )}
        </div>
        <button
          onClick={handleCopy}
          style={{
            background: 'none',
            border: `1px solid ${COLORS.border}`,
            borderRadius: '4px',
            color: copied ? COLORS.success : COLORS.textMuted,
            fontSize: '11px',
            cursor: 'pointer',
            padding: '2px 8px',
          }}
        >
          {copied ? '✓ Copied' : 'Copy'}
        </button>
      </div>

      <p style={{ fontSize: '13px', color: COLORS.textMuted, marginBottom: '8px', lineHeight: '1.5' }}>
        {rec.rationale}
      </p>

      <div style={{
        background: '#161b22',
        border: `1px solid ${COLORS.border}`,
        borderRadius: '4px',
        padding: '8px 12px',
        fontSize: '13px',
        color: COLORS.text,
        fontFamily: 'monospace',
      }}>
        → {rec.specific_action}
      </div>

      {rec.estimated_credit !== undefined && rec.estimated_credit !== null && (
        <div style={{ fontSize: '12px', color: COLORS.textMuted, marginTop: '6px' }}>
          Est. P&L impact:{' '}
          <span style={{ color: rec.estimated_credit >= 0 ? COLORS.success : COLORS.danger }}>
            ${rec.estimated_credit >= 0 ? '+' : ''}{rec.estimated_credit.toLocaleString()}
          </span>
        </div>
      )}
    </div>
  )
}

export default function RecommendationsPanel({ recommendations, analysisText, isAnalyzing }) {
  const hasRecs = recommendations && recommendations.length > 0

  return (
    <div style={{
      background: COLORS.surface,
      border: `1px solid ${COLORS.border}`,
      borderRadius: '8px',
      padding: '16px',
      flex: 1,
    }}>
      <h2 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '16px', color: COLORS.text }}>
        AI Recommendations
        {hasRecs && (
          <span style={{ fontSize: '12px', color: COLORS.textMuted, fontWeight: 400, marginLeft: '8px' }}>
            {recommendations.length} actions
          </span>
        )}
      </h2>

      {/* Streaming analysis text */}
      {(isAnalyzing || analysisText) && (
        <div style={{
          background: '#0d1117',
          border: `1px solid ${COLORS.border}`,
          borderRadius: '6px',
          padding: '12px',
          marginBottom: '16px',
          fontSize: '13px',
          color: COLORS.textMuted,
          maxHeight: '200px',
          overflowY: 'auto',
          fontFamily: 'monospace',
          whiteSpace: 'pre-wrap',
          lineHeight: '1.6',
        }}>
          {analysisText || 'Analyzing portfolio…'}
          {isAnalyzing && <span style={{ animation: 'pulse 1s infinite' }}>▋</span>}
        </div>
      )}

      {/* Recommendations cards */}
      {hasRecs ? (
        <div>
          {/* Sort by priority */}
          {['urgent', 'high', 'medium', 'low']
            .flatMap(p => recommendations.filter(r => r.priority === p))
            .map((rec, i) => (
              <RecommendationCard key={i} rec={rec} />
            ))
          }
        </div>
      ) : !isAnalyzing && !analysisText ? (
        <div style={{
          textAlign: 'center',
          padding: '48px 0',
          color: COLORS.textMuted,
          fontSize: '13px',
        }}>
          Upload positions and click "Run AI Analysis" to get recommendations
        </div>
      ) : null}
    </div>
  )
}
