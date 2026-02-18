import React, { useState } from 'react'
import UploadPanel from './components/UploadPanel.jsx'
import PortfolioSummary from './components/PortfolioSummary.jsx'
import RecommendationsPanel from './components/RecommendationsPanel.jsx'
import GreeksDisplay from './components/GreeksDisplay.jsx'
import PositionsTable from './components/PositionsTable.jsx'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const C = {
  bg: '#0d1117',
  surface: '#161b22',
  border: '#30363d',
  text: '#c9d1d9',
  textMuted: '#8b949e',
  accent: '#58a6ff',
  success: '#3fb950',
  warning: '#d29922',
  danger: '#f85149',
}

function Section({ title, children }) {
  return (
    <div style={{
      background: C.surface,
      border: `1px solid ${C.border}`,
      borderRadius: '8px',
      overflow: 'hidden',
    }}>
      {title && (
        <div style={{
          padding: '12px 16px',
          borderBottom: `1px solid ${C.border}`,
          fontSize: '13px',
          fontWeight: 600,
          color: C.text,
        }}>
          {title}
        </div>
      )}
      {children}
    </div>
  )
}

export default function App() {
  const [portfolio, setPortfolio] = useState(null)   // PortfolioSnapshot
  const [vix, setVix] = useState(null)
  const [recommendations, setRecommendations] = useState([])
  const [analysisText, setAnalysisText] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [uploadStatus, setUploadStatus] = useState({ tastytrade: null, tos: null })
  const [errors, setErrors] = useState([])
  const [activeTab, setActiveTab] = useState('positions') // 'positions' | 'analysis'

  const handleUpload = async (broker, file) => {
    setUploadStatus(s => ({ ...s, [broker]: 'uploading' }))
    setErrors([])

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_BASE}/upload/${broker}`, { method: 'POST', body: formData })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Upload failed')

      setUploadStatus(s => ({ ...s, [broker]: 'done' }))

      // Refresh aggregated portfolio after each upload
      const pfRes = await fetch(`${API_BASE}/portfolio`)
      if (pfRes.ok) {
        const pf = await pfRes.json()
        setPortfolio(pf)
      }
    } catch (err) {
      setUploadStatus(s => ({ ...s, [broker]: 'error' }))
      setErrors(e => [...e, `${broker}: ${err.message}`])
    }
  }

  const handleAnalyze = async () => {
    setIsAnalyzing(true)
    setAnalysisText('')
    setRecommendations([])
    setActiveTab('analysis')

    try {
      const res = await fetch(`${API_BASE}/analyze`, { method: 'POST' })
      const reader = res.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const text = decoder.decode(value)
        for (const line of text.split('\n').filter(l => l.startsWith('data: '))) {
          try {
            const payload = JSON.parse(line.slice(6))
            if (payload.type === 'text') setAnalysisText(t => t + payload.content)
            else if (payload.type === 'done') setRecommendations(payload.recommendations || [])
          } catch {}
        }
      }
    } catch (err) {
      setErrors(e => [...e, `Analysis failed: ${err.message}`])
    } finally {
      setIsAnalyzing(false)
    }
  }

  const bothUploaded = uploadStatus.tastytrade === 'done' || uploadStatus.tos === 'done'
  const positions = portfolio?.all_positions || []

  const tabStyle = (active) => ({
    padding: '8px 16px',
    fontSize: '13px',
    fontWeight: active ? 600 : 400,
    color: active ? C.accent : C.textMuted,
    borderBottom: active ? `2px solid ${C.accent}` : '2px solid transparent',
    cursor: 'pointer',
    background: 'none',
    border: 'none',
    borderBottom: active ? `2px solid ${C.accent}` : '2px solid transparent',
  })

  return (
    <div style={{ minHeight: '100vh', background: C.bg, color: C.text }}>
      {/* Header */}
      <header style={{
        background: C.surface,
        borderBottom: `1px solid ${C.border}`,
        padding: '12px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div>
          <div style={{ fontSize: '17px', fontWeight: 700, color: C.accent, letterSpacing: '0.3px' }}>
            Portfolio Advisor
          </div>
          <div style={{ fontSize: '11px', color: C.textMuted, marginTop: '2px' }}>
            TastyTrade + ThinkOrSwim · Goal: 3% monthly NetLiq growth
          </div>
        </div>
        {vix && (
          <div style={{
            fontSize: '13px',
            color: vix.regime === 'low' ? C.textMuted : vix.regime === 'normal' ? C.success : vix.regime === 'elevated' ? C.warning : C.danger,
          }}>
            VIX {vix.value.toFixed(2)} · {vix.regime.toUpperCase()}
          </div>
        )}
      </header>

      {/* Main layout */}
      <div style={{
        maxWidth: '1440px',
        margin: '0 auto',
        padding: '20px 24px',
        display: 'grid',
        gridTemplateColumns: '280px 1fr',
        gap: '16px',
        alignItems: 'start',
      }}>
        {/* Left sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <UploadPanel
            uploadStatus={uploadStatus}
            onUpload={handleUpload}
            onAnalyze={handleAnalyze}
            isAnalyzing={isAnalyzing}
          />
          <GreeksDisplay portfolio={portfolio} />
        </div>

        {/* Right main content */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', minWidth: 0 }}>
          {/* Errors */}
          {errors.length > 0 && (
            <div style={{
              background: '#2d1317',
              border: `1px solid ${C.danger}`,
              borderRadius: '6px',
              padding: '10px 14px',
              color: C.danger,
              fontSize: '13px',
              display: 'flex',
              justifyContent: 'space-between',
            }}>
              <div>{errors.join(' · ')}</div>
              <button onClick={() => setErrors([])} style={{ background: 'none', border: 'none', color: C.danger, cursor: 'pointer' }}>✕</button>
            </div>
          )}

          {/* Portfolio summary cards */}
          <PortfolioSummary portfolio={portfolio} vix={vix} />

          {/* Tab bar */}
          {bothUploaded && (
            <div style={{
              display: 'flex',
              borderBottom: `1px solid ${C.border}`,
              gap: '0',
            }}>
              <button style={tabStyle(activeTab === 'positions')} onClick={() => setActiveTab('positions')}>
                Positions {positions.length > 0 && `(${positions.length})`}
              </button>
              <button style={tabStyle(activeTab === 'analysis')} onClick={() => setActiveTab('analysis')}>
                AI Analysis {recommendations.length > 0 && `(${recommendations.length})`}
              </button>
            </div>
          )}

          {/* Tab content */}
          {activeTab === 'positions' && positions.length > 0 && (
            <Section title={`All Positions — ${positions.length} across ${portfolio?.accounts?.length || 0} accounts`}>
              <PositionsTable positions={positions} />
            </Section>
          )}

          {(activeTab === 'analysis' || !bothUploaded) && (
            <RecommendationsPanel
              recommendations={recommendations}
              analysisText={analysisText}
              isAnalyzing={isAnalyzing}
            />
          )}
        </div>
      </div>
    </div>
  )
}
