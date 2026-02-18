import React, { useRef } from 'react'

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

function StatusBadge({ status }) {
  const map = {
    uploading: { label: 'Uploading…', color: COLORS.accent },
    done: { label: '✓ Parsed', color: COLORS.success },
    error: { label: '✗ Error', color: COLORS.danger },
  }
  if (!status) return null
  const { label, color } = map[status] || {}
  return (
    <span style={{ fontSize: '11px', color, marginLeft: '8px' }}>{label}</span>
  )
}

function UploadRow({ label, broker, status, onUpload }) {
  const inputRef = useRef(null)

  const handleChange = (e) => {
    const file = e.target.files[0]
    if (file) onUpload(broker, file)
  }

  return (
    <div style={{ marginBottom: '12px' }}>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '6px' }}>
        <span style={{ fontSize: '13px', color: COLORS.text }}>{label}</span>
        <StatusBadge status={status} />
      </div>
      <div
        style={{
          border: `1px dashed ${status === 'done' ? COLORS.success : COLORS.border}`,
          borderRadius: '6px',
          padding: '10px',
          textAlign: 'center',
          cursor: 'pointer',
          background: '#0d1117',
          transition: 'border-color 0.2s',
        }}
        onClick={() => inputRef.current?.click()}
        onDragOver={e => e.preventDefault()}
        onDrop={e => {
          e.preventDefault()
          const file = e.dataTransfer.files[0]
          if (file) onUpload(broker, file)
        }}
      >
        <div style={{ fontSize: '12px', color: COLORS.textMuted }}>
          {status === 'done' ? 'Re-upload CSV' : 'Drop CSV or click to browse'}
        </div>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept=".csv"
        style={{ display: 'none' }}
        onChange={handleChange}
      />
    </div>
  )
}

export default function UploadPanel({ uploadStatus, onUpload, onAnalyze, isAnalyzing }) {
  const bothUploaded = uploadStatus.tastytrade === 'done' || uploadStatus.tos === 'done'

  return (
    <div style={{
      background: COLORS.surface,
      border: `1px solid ${COLORS.border}`,
      borderRadius: '8px',
      padding: '16px',
    }}>
      <h2 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '16px', color: COLORS.text }}>
        Upload Positions
      </h2>

      <UploadRow
        label="TastyTrade Export"
        broker="tastytrade"
        status={uploadStatus.tastytrade}
        onUpload={onUpload}
      />
      <UploadRow
        label="ThinkOrSwim Statement"
        broker="tos"
        status={uploadStatus.tos}
        onUpload={onUpload}
      />

      <button
        onClick={onAnalyze}
        disabled={!bothUploaded || isAnalyzing}
        style={{
          width: '100%',
          padding: '10px',
          marginTop: '8px',
          background: bothUploaded && !isAnalyzing ? COLORS.accent : '#1c2128',
          color: bothUploaded && !isAnalyzing ? '#0d1117' : COLORS.textMuted,
          border: 'none',
          borderRadius: '6px',
          fontSize: '13px',
          fontWeight: 600,
          cursor: bothUploaded && !isAnalyzing ? 'pointer' : 'not-allowed',
          transition: 'all 0.2s',
        }}
      >
        {isAnalyzing ? '⟳ Analyzing…' : '▶ Run AI Analysis'}
      </button>

      {!bothUploaded && (
        <p style={{ fontSize: '11px', color: COLORS.textMuted, marginTop: '8px', textAlign: 'center' }}>
          Upload at least one account to enable analysis
        </p>
      )}
    </div>
  )
}
