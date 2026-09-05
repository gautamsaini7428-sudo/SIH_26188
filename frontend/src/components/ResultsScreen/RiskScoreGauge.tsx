import React, { useEffect, useState } from 'react'

interface RiskScoreGaugeProps {
  score: number // 0 - 100
  verdict: 'GENUINE' | 'SUSPICIOUS' | 'FAKE' | 'REJECTED'
}

export const RiskScoreGauge: React.FC<RiskScoreGaugeProps> = ({ score, verdict }) => {
  const [displayScore, setDisplayScore] = useState(0)

  useEffect(() => {
    let start = 0
    const end = Math.min(100, Math.max(0, score))
    const duration = 1200 // ms
    const stepTime = 20
    const steps = duration / stepTime
    const increment = (end - start) / steps

    const timer = setInterval(() => {
      start += increment
      if ((increment >= 0 && start >= end) || (increment < 0 && start <= end)) {
        setDisplayScore(end)
        clearInterval(timer)
      } else {
        setDisplayScore(Math.round(start))
      }
    }, stepTime)

    return () => clearInterval(timer)
  }, [score])

  // Gauge color based on risk score & palette
  const getGaugeColor = () => {
    if (verdict === 'REJECTED') return '#755B73'
    if (displayScore <= 30) return '#0B2925' // Primary forest green (Mint accent)
    if (displayScore <= 65) return '#755B73' // Secondary muted mauve
    return '#8B1E1E' // Oxblood red
  }

  const getVerdictLabel = () => {
    if (verdict === 'GENUINE') return 'Verified Genuine'
    if (verdict === 'SUSPICIOUS') return 'Flagged for Examiner Review'
    if (verdict === 'FAKE') return 'Fraudulent Specimen'
    return 'Rejected Document'
  }

  const getVerdictBadgeStyle = () => {
    if (verdict === 'GENUINE') return 'bg-[#A7F3D0]/30 text-[#0B2925] border-[#0B2925]/30'
    if (verdict === 'SUSPICIOUS') return 'bg-[#755B73]/15 text-[#755B73] border-[#755B73]/30'
    if (verdict === 'FAKE') return 'bg-[#8B1E1E]/15 text-[#8B1E1E] border-[#8B1E1E]/30'
    return 'bg-[#755B73]/15 text-[#755B73] border-[#755B73]/30'
  }

  // SVG arc calculation (semi-circle gauge, angle -180 to 0)
  const radius = 70
  const circumference = Math.PI * radius
  const strokeDashoffset = circumference - (displayScore / 100) * circumference
  const gaugeColor = getGaugeColor()

  return (
    <div className="flex flex-col items-center justify-center p-6 text-center bg-[#FCFAF8] rounded-lg border border-[#E3DCD6] shadow-xs">
      <div className="text-[11px] font-mono tracking-widest text-[#6E6571] uppercase font-bold mb-2">
        Primary Forensic Composite Output
      </div>

      {/* Hero Arc Dial */}
      <div className="relative w-48 h-28 flex items-end justify-center overflow-hidden">
        <svg className="w-48 h-48 transform -rotate-90 overflow-visible" viewBox="0 0 160 160">
          {/* Background Arc */}
          <circle
            cx="80"
            cy="80"
            r={radius}
            fill="none"
            stroke="#E3DCD6"
            strokeWidth="12"
            strokeDasharray={`${circumference} ${circumference}`}
            strokeDashoffset="0"
            strokeLinecap="round"
          />
          {/* Animated Value Arc */}
          <circle
            cx="80"
            cy="80"
            r={radius}
            fill="none"
            stroke={gaugeColor}
            strokeWidth="12"
            strokeDasharray={`${circumference} ${circumference}`}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.8s ease-out, stroke 0.5s ease' }}
          />
        </svg>

        {/* Center Score Readout */}
        <div className="absolute bottom-1 flex flex-col items-center">
          <span className="font-editorial text-4xl font-black text-[#0B2925] tracking-tight">
            {displayScore}
          </span>
          <span className="text-[10px] font-mono text-[#6E6571] uppercase">Risk Score / 100</span>
        </div>
      </div>

      {/* Verdict Seal Badge */}
      <div className="mt-4">
        <div
          className={`inline-block px-4 py-1.5 rounded border text-xs font-editorial font-bold uppercase tracking-wider ${getVerdictBadgeStyle()}`}
        >
          {getVerdictLabel()}
        </div>
      </div>

      <div className="text-[11px] font-sans text-[#6E6571] mt-2 max-w-sm">
        Weighted composite signal: 40% Tampering + 30% Biometric + 30% Format Validation.
      </div>
    </div>
  )
}
