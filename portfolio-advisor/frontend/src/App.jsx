import React, { useState } from 'react'
import UploadPanel from './components/UploadPanel.jsx'
import PortfolioSummary from './components/PortfolioSummary.jsx'
import RecommendationsPanel from './components/RecommendationsPanel.jsx'
import GreeksDisplay from './components/GreeksDisplay.jsx'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Dark theme color tokens
const colors = {
  bg: '#0d1117',
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

export default function App() {
  const [portfolio, setPortfolio] = useState(null)
  const [vix, setVix] = useState(null)
  const [recommendations, setRecommendations] = useState([])
  const [analysisText, setAnalysisText] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [uploadStatus, setUploadStatus] = useState({
    tastytrade: null, // null | 'uploading' | 'done' | 'error'
    tos: null,
  })
  const [errors, setErrors] = useState([])

  const handleUpload = async (broker, file) => {
    setUploadStatus(s => ({ ...s, [broker]: 'uploading' }))
    setErrors([])

    const formData = new FormData()
    formData.append('file', file)

    try {
      const res = await fetch(`${API_BASE}/upload/${broker}`, {
        method: 'POST',
        body: formData,
      })
      const data = await res.json()

      if (!res.ok) {
        throw new Error(data.detail || 'Upload failed')
      }

      setUploadStatus(s => ({ ...s, [broker]: 'done' }))
      // TODO: update portfolio state from response (F001/F002)
    } catch (err) {
      setUploadStatus(s => ({ ...s, [broker]: 'error' }))
      setErrors(e => [...e, `${broker}: ${err.message}`])
    }
  }

  const handleAnalyze = async () => {
    setIsAnalyzing(true)
    setAnalysisText('')
    setRecommendations([])

    try {
      const res = await fetch(`${API_BASE}/analyze`, { method: 'POST' })
      const reader = res.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const text = decoder.decode(value)
        const lines = text.split('\n').filter(l => l.startsWith('data: '))

        for (const line of lines) {
          try {
            const payload = JSON.parse(line.slice(6))
            if (payload.type === 'text') {
              setAnalysisText(t => t + payload.content)
            } else if (payload.type === 'done') {
              setRecommendations(payload.recommendations || [])
            }
          } catch {}
        }
      }
    } catch (err) {
      setErrors(e => [...e, `Analysis failed: ${err.message}`])
    } finally {
      setIsAnalyzing(false)
    }
  }

  const styles = {
    app: {
      minHeight: '100vh',
      background: colors.bg,
      color: colors.text,
    },
    header: {
      background: colors.surface,
      borderBottom: `1px solid ${colors.border}`,
      padding: '12px 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
    },
    title: {
      fontSize: '18px',
      fontWeight: 600,
      color: colors.accent,
      letterSpacing: '0.5px',
    },
    subtitle: {
      fontSize: '12px',
      color: colors.textMuted,
      marginTop: '2px',
    },
    main: {
      maxWidth: '1400px',
      margin: '0 auto',
      padding: '24px',
      display: 'grid',
      gridTemplateColumns: '320px 1fr',
      gridTemplateRows: 'auto auto 1fr',
      gap: '16px',
    },
    sidebar: {
      gridColumn: '1',
      gridRow: '1 / 4',
      display: 'flex',
      flexDirection: 'column',
      gap: '16px',
    },
    content: {
      gridColumn: '2',
      gridRow: '1 / 4',
      display: 'flex',
      flexDirection: 'column',
      gap: '16px',
    },
    errorBanner: {
      background: '#2d1317',
      border: `1px solid ${colors.danger}`,
      borderRadius: '6px',
      padding: '12px 16px',
      color: colors.danger,
      fontSize: '13px',
    },
  }

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <div>
          <div style={styles.title}>Portfolio Advisor</div>
          <div style={styles.subtitle}>
            TastyTrade + ThinkOrSwim | Goal: 3% monthly NetLiq growth
          </div>
        </div>
        {vix && (
          <div style={{
            fontSize: '13px',
            color: vix.regime === 'low' ? colors.textMuted :
                   vix.regime === 'normal' ? colors.success :
                   vix.regime === 'elevated' ? colors.warning : colors.danger,
          }}>
            VIX: {vix.value.toFixed(2)} ({vix.regime.toUpperCase()})
          </div>
        )}
      </header>

      <main style={styles.main}>
        <div style={styles.sidebar}>
          <UploadPanel
            uploadStatus={uploadStatus}
            onUpload={handleUpload}
            onAnalyze={handleAnalyze}
            isAnalyzing={isAnalyzing}
          />
          <GreeksDisplay portfolio={portfolio} />
        </div>

        <div style={styles.content}>
          {errors.length > 0 && (
            <div style={styles.errorBanner}>
              {errors.map((e, i) => <div key={i}>{e}</div>)}
            </div>
          )}
          <PortfolioSummary portfolio={portfolio} vix={vix} />
          <RecommendationsPanel
            recommendations={recommendations}
            analysisText={analysisText}
            isAnalyzing={isAnalyzing}
          />
        </div>
      </main>
    </div>
  )
}
