import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'

interface RiskGaugeProps {
  score: number // 0 to 100
  verdict: 'GENUINE' | 'SUSPICIOUS' | 'FAKE' | 'REJECTED'
}

export const RiskGauge: React.FC<RiskGaugeProps> = ({ score, verdict }) => {
  const [displayScore, setDisplayScore] = useState(0)

  useEffect(() => {
    let start = 0
    const end = score
    const duration = 1200 // ms
    const stepTime = 20
    const steps = duration / stepTime
    const increment = (end - start) / steps

    const timer = setInterval(() => {
      start += increment
      if (start >= end) {
        setDisplayScore(end)
        clearInterval(timer)
      } else {
        setDisplayScore(Math.round(start))
      }
    }, stepTime)

    return () => clearInterval(timer)
  }, [score])

  // SVG Gauge calculations
  const radius = 70
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (displayScore / 100) * circumference

  const getGaugeColor = () => {
    if (verdict === 'REJECTED') return 'stroke-destructive text-destructive'
    if (score >= 65) return 'stroke-destructive text-destructive'
    if (score >= 30) return 'stroke-amber-500 text-amber-500'
    return 'stroke-emerald-500 text-emerald-500'
  }

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <div className="relative w-44 h-44 flex items-center justify-center">
        {/* Background Track */}
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 160 160">
          <circle
            cx="80"
            cy="80"
            r={radius}
            className="stroke-secondary fill-none"
            strokeWidth="12"
          />
          {/* Animated Gauge Arc */}
          <motion.circle
            cx="80"
            cy="80"
            r={radius}
            className={`fill-none ${getGaugeColor()}`}
            strokeWidth="12"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1.2, ease: 'easeOut' }}
          />
        </svg>

        {/* Center Score Counter */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="text-4xl font-bold font-mono text-foreground tracking-tight">
            {displayScore}
          </span>
          <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider font-bold">
            Risk Index / 100
          </span>
        </div>
      </div>
    </div>
  )
}
