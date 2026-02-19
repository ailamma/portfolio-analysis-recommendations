import React, { useState, useEffect, useCallback, useRef } from 'react'
import UploadPanel from './components/UploadPanel.jsx'
import PortfolioSummary from './components/PortfolioSummary.jsx'
import RecommendationsPanel from './components/RecommendationsPanel.jsx'
import GreeksDisplay from './components/GreeksDisplay.jsx'
import PositionsTable from './components/PositionsTable.jsx'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const MARKET_REFRESH_MS = 5 * 60 * 1000  // 5 minutes

const C = {
  bg: '#0d1117', surface: '#161b22', border: '#30363d',
  text: '#c9d1d9', textMuted: '#8b949e', accent: '#58a6ff',
  success: '#3fb950', warning: '#d29922', danger: '#f85149',
}

function Section({ title, children, action }) {
  return (
    <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: '8px', overflow: 'hidden' }}>
      {title && (
        <div style={{
          padding: '10px 16px', borderBottom: `1px solid ${C.border}`,
          fontSize: '13px', fontWeight: 600, color: C.text,
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <span>{title}</span>
          {action}
        </div>
      )}
      {children}
    </div>
  )
}

export default function App() {
  const [portfolio,     setPortfolio]     = useState(null)
  const [vix,           setVix]           = useState(null)
  const [marketData,    setMarketData]    = useState({})
  const [marketAge,     setMarketAge]     = useState(null)   // Date of last fetch
  const [recommendations, setRecommendations] = useState([])
  const [analysisText,  setAnalysisText]  = useState('')
  const [isAnalyzing,   setIsAnalyzing]   = useState(false)
  const [uploadStatus,  setUploadStatus]  = useState({ tastytrade: null, tos: null })
  const [errors,        setErrors]        = useState([])
  const [activeTab,     setActiveTab]     = useState('positions')
  const timerRef = useRef(null)

  // ── Market data polling ───────────────────────────────────────────────────
  const refreshMarketData = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/market-data`)
      if (!res.ok) return
      const data = await res.json()
      if (data.vix) {
        setVix(data.vix)
        setMarketData(data.symbols || {})
        setMarketAge(new Date())
      }
    } catch {}
  }, [])

  // Fetch market data once on load and whenever portfolio changes
  useEffect(() => {
    refreshMarketData()
    timerRef.current = setInterval(refreshMarketData, MARKET_REFRESH_MS)
    return () => clearInterval(timerRef.current)
  }, [refreshMarketData])

  // Also refresh market data after a new upload
  const refreshPortfolio = useCallback(async () => {
    const res = await fetch(`${API_BASE}/portfolio`)
    if (res.ok) {
      const pf = await res.json()
      setPortfolio(pf)
      // Kick a market data refresh to pick up any new symbols
      await refreshMarketData()
    }
  }, [refreshMarketData])

  // ── Upload handler ────────────────────────────────────────────────────────
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
      await refreshPortfolio()
    } catch (err) {
      setUploadStatus(s => ({ ...s, [broker]: 'error' }))
      setErrors(e => [...e, `${broker}: ${err.message}`])
    }
  }

  // ── Analysis handler ──────────────────────────────────────────────────────
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
        for (const line of decoder.decode(value).split('\n').filter(l => l.startsWith('data: '))) {
          try {
            const p = JSON.parse(line.slice(6))
            if (p.type === 'text') setAnalysisText(t => t + p.content)
            else if (p.type === 'done') setRecommendations(p.recommendations || [])
          } catch {}
        }
      }
    } catch (err) {
      setErrors(e => [...e, `Analysis failed: ${err.message}`])
    } finally {
      setIsAnalyzing(false)
    }
  }

  const hasPositions = (portfolio?.all_positions?.length || 0) > 0
  const positions    = portfolio?.all_positions || []

  const tabStyle = (active) => ({
    padding: '8px 16px', fontSize: '13px',
    fontWeight: active ? 600 : 400,
    color: active ? C.accent : C.textMuted,
    background: 'none', border: 'none',
    borderBottom: active ? `2px solid ${C.accent}` : '2px solid transparent',
    cursor: 'pointer',
  })

  // Format last-updated time
  const ageLabel = marketAge
    ? `Updated ${marketAge.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
    : null

  return (
    <div style={{ minHeight: '100vh', background: C.bg, color: C.text }}>
      {/* ── Header ── */}
      <header style={{
        background: C.surface, borderBottom: `1px solid ${C.border}`,
        padding: '10px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div>
          <div style={{ fontSize: '16px', fontWeight: 700, color: C.accent }}>Portfolio Advisor</div>
          <div style={{ fontSize: '11px', color: C.textMuted }}>TastyTrade + ThinkOrSwim · 3% monthly NetLiq goal</div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {ageLabel && <span style={{ fontSize: '11px', color: C.textMuted }}>{ageLabel}</span>}
          <button
            onClick={refreshMarketData}
            style={{
              background: 'none', border: `1px solid ${C.border}`, borderRadius: '5px',
              color: C.textMuted, fontSize: '12px', padding: '4px 10px', cursor: 'pointer',
            }}
          >
            ↻ Refresh
          </button>
        </div>
      </header>

      {/* ── Body ── */}
      <div style={{
        maxWidth: '1440px', margin: '0 auto', padding: '20px 24px',
        display: 'grid', gridTemplateColumns: '268px 1fr', gap: '16px', alignItems: 'start',
      }}>
        {/* Sidebar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <UploadPanel
            uploadStatus={uploadStatus}
            onUpload={handleUpload}
            onAnalyze={handleAnalyze}
            isAnalyzing={isAnalyzing}
          />
          <GreeksDisplay portfolio={portfolio} />
        </div>

        {/* Main */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', minWidth: 0 }}>
          {errors.length > 0 && (
            <div style={{
              background: '#2d1317', border: `1px solid ${C.danger}`,
              borderRadius: '6px', padding: '10px 14px',
              color: C.danger, fontSize: '13px',
              display: 'flex', justifyContent: 'space-between',
            }}>
              <span>{errors.join(' · ')}</span>
              <button onClick={() => setErrors([])} style={{ background: 'none', border: 'none', color: C.danger, cursor: 'pointer', marginLeft: '12px' }}>✕</button>
            </div>
          )}

          {/* Portfolio summary (always shown, adjusts based on loaded state) */}
          <PortfolioSummary portfolio={portfolio} vix={vix} marketData={marketData} />

          {/* Tab bar */}
          {hasPositions && (
            <div style={{ display: 'flex', borderBottom: `1px solid ${C.border}` }}>
              <button style={tabStyle(activeTab === 'positions')} onClick={() => setActiveTab('positions')}>
                Positions ({positions.length})
              </button>
              <button style={tabStyle(activeTab === 'analysis')} onClick={() => setActiveTab('analysis')}>
                AI Analysis{recommendations.length > 0 ? ` (${recommendations.length})` : ''}
              </button>
            </div>
          )}

          {/* Positions table */}
          {activeTab === 'positions' && hasPositions && (
            <Section title={`${positions.length} Positions · Click row to expand legs`}>
              <PositionsTable positions={positions} marketData={marketData} />
            </Section>
          )}

          {/* AI analysis panel */}
          {(activeTab === 'analysis' || !hasPositions) && (
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
