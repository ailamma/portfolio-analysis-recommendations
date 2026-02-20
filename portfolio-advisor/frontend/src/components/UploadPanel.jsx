import React, { useRef, useState } from 'react'

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
    uploading: { label: '⟳ Uploading…', color: COLORS.accent },
    done:      { label: '✓ Parsed',     color: COLORS.success },
    error:     { label: '✗ Error',      color: COLORS.danger },
  }
  if (!status) return null
  const { label, color } = map[status] || {}
  return <span style={{ fontSize: '11px', color, marginLeft: '8px' }}>{label}</span>
}

function UploadRow({ label, broker, status, onUpload }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)

  const handleChange = (e) => {
    const file = e.target.files[0]
    if (file) onUpload(broker, file)
    e.target.value = ''
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) onUpload(broker, file)
  }

  const borderColor = status === 'done'
    ? COLORS.success
    : dragging
    ? COLORS.accent
    : COLORS.border

  const bgColor = dragging ? '#1c2d3d' : '#0d1117'

  return (
    <div style={{ marginBottom: '12px' }}>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '6px' }}>
        <span style={{ fontSize: '13px', color: COLORS.text }}>{label}</span>
        <StatusBadge status={status} />
      </div>
      <div
        role="button"
        tabIndex={0}
        style={{
          border: `1px dashed ${borderColor}`,
          borderRadius: '6px',
          padding: '10px',
          textAlign: 'center',
          cursor: 'pointer',
          background: bgColor,
          transition: 'border-color 0.15s, background 0.15s',
          outline: 'none',
        }}
        onClick={() => inputRef.current?.click()}
        onKeyDown={e => e.key === 'Enter' && inputRef.current?.click()}
        onDragEnter={() => setDragging(true)}
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
      >
        <div style={{ fontSize: '12px', color: dragging ? COLORS.accent : COLORS.textMuted }}>
          {dragging ? '↓ Drop to upload' : status === 'done' ? 'Re-upload CSV' : 'Drop CSV or click to browse'}
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

// Analysis status pipeline: uploaded → analyzing → done
function AnalysisStatusBar({ uploadStatus, isAnalyzing, hasRecs }) {
  const uploaded = uploadStatus.tastytrade === 'done' || uploadStatus.tos === 'done'
  if (!uploaded) return null

  const steps = [
    { key: 'upload',   label: 'Uploaded',  done: uploaded },
    { key: 'analyze',  label: 'Analyzing', done: hasRecs || (!isAnalyzing && hasRecs) },
    { key: 'complete', label: 'Done',       done: hasRecs },
  ]

  const activeIdx = isAnalyzing ? 1 : hasRecs ? 2 : 0

  return (
    <div style={{ display: 'flex', alignItems: 'center', marginBottom: '10px', gap: '4px' }}>
      {steps.map((step, i) => {
        const isActive = i === activeIdx
        const isDone   = i < activeIdx
        const color    = isDone ? COLORS.success : isActive ? COLORS.accent : COLORS.border
        return (
          <React.Fragment key={step.key}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '2px' }}>
              <div style={{
                width: '8px', height: '8px', borderRadius: '50%',
                background: isDone ? COLORS.success : isActive ? COLORS.accent : '#1c2128',
                border: `1px solid ${color}`,
                transition: 'all 0.2s',
              }} />
              <span style={{ fontSize: '9px', color, whiteSpace: 'nowrap' }}>{step.label}</span>
            </div>
            {i < steps.length - 1 && (
              <div style={{
                flex: 1, height: '1px',
                background: isDone ? COLORS.success : COLORS.border,
                marginBottom: '10px',
                transition: 'background 0.3s',
              }} />
            )}
          </React.Fragment>
        )
      })}
    </div>
  )
}

export default function UploadPanel({ uploadStatus, onUpload, onAnalyze, isAnalyzing, hasRecs }) {
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

      <AnalysisStatusBar
        uploadStatus={uploadStatus}
        isAnalyzing={isAnalyzing}
        hasRecs={hasRecs}
      />

      <button
        onClick={onAnalyze}
        disabled={!bothUploaded || isAnalyzing}
        style={{
          width: '100%',
          padding: '10px',
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
        {isAnalyzing ? '⟳ Analyzing…' : hasRecs ? '↺ Re-run Analysis' : '▶ Run AI Analysis'}
      </button>

      {!bothUploaded && (
        <p style={{ fontSize: '11px', color: COLORS.textMuted, marginTop: '8px', textAlign: 'center' }}>
          Upload at least one account to enable analysis
        </p>
      )}
    </div>
  )
}
