import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card'
import { Progress } from '../ui/progress'
import { soundFX } from '../../utils/audio'
import { STEPPER_STAGES, DOCUMENT_FIELD_MARKERS } from '../../utils/mockData'

interface VerificationProgressProps {
  documentPreviewUrl: string
  selfiePreviewUrl?: string | null
  isDone?: boolean
  onComplete: () => void
}

export const VerificationProgress: React.FC<VerificationProgressProps> = ({
  documentPreviewUrl,
  isDone = false,
  onComplete,
}) => {
  const [currentStageIndex, setCurrentStageIndex] = useState(0)
  const [revealedMarkers, setRevealedMarkers] = useState<string[]>([])

  useEffect(() => {
    soundFX.paperSlide()

    // Smooth stage stepping that holds at final stage until backend isDone=true
    const stageInterval = setInterval(() => {
      setCurrentStageIndex((prev) => {
        if (prev < STEPPER_STAGES.length - 1) {
          return prev + 1
        }
        return prev
      })
    }, 1200)

    return () => clearInterval(stageInterval)
  }, [])

  // Trigger onComplete only when isDone is true AND stepper reached the final stage (or after brief finish)
  useEffect(() => {
    if (isDone) {
      setCurrentStageIndex(STEPPER_STAGES.length - 1)
      const timer = setTimeout(() => {
        onComplete()
      }, 500)
      return () => clearTimeout(timer)
    }
  }, [isDone, onComplete])

  useEffect(() => {
    if (currentStageIndex < 1) return

    const timers: ReturnType<typeof setTimeout>[] = []
    DOCUMENT_FIELD_MARKERS.forEach((marker, i) => {
      const t = setTimeout(() => {
        soundFX.fieldInkLand()
        setRevealedMarkers((prev) => [...prev, marker.id])
      }, 300 + i * 400)
      timers.push(t)
    })

    return () => timers.forEach(clearTimeout)
  }, [currentStageIndex])

  const progressPercentage = ((currentStageIndex + 1) / STEPPER_STAGES.length) * 100

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      {/* Top Banner */}
      <Card className="border-border bg-card p-6 text-center space-y-3">
        <h2 className="text-xl sm:text-2xl font-bold text-foreground">
          Executing Identity Verification Pipeline
        </h2>
        <p className="text-xs sm:text-sm text-muted-foreground">
          Running OCR field extraction, standalone validation, ELA tampering detection, &amp; facial biometric correlation.
        </p>

        {/* Global Progress Bar */}
        <div className="space-y-1.5 pt-2 max-w-md mx-auto">
          <Progress value={progressPercentage} className="h-2.5" />
          <div className="flex justify-between text-[11px] font-mono text-muted-foreground font-semibold">
            <span>{STEPPER_STAGES[currentStageIndex]?.label}</span>
            <span>{Math.round(progressPercentage)}%</span>
          </div>
        </div>
      </Card>

      {/* Exhibit Viewport with Scanning Motion Line */}
      <Card className="p-4 sm:p-5 border-border bg-card">
        <CardHeader className="p-0 pb-3">
          <CardTitle className="text-xs font-mono font-bold uppercase tracking-wider text-foreground">
            Exhibit A Forensic Scanner Viewport
          </CardTitle>
        </CardHeader>

        <CardContent className="p-0">
          <div className="relative aspect-[700/440] w-full rounded-xl border border-border bg-secondary/60 overflow-hidden flex items-center justify-center">
            <img
              src={documentPreviewUrl}
              alt="Document under forensic analysis"
              className="absolute inset-0 w-full h-full object-contain"
            />

            {/* Scanning Motion Line */}
            {currentStageIndex < 3 && (
              <motion.div
                className="absolute left-0 right-0 pointer-events-none"
                style={{
                  background:
                    'linear-gradient(180deg, transparent, rgba(167,243,208,0.4) 50%, transparent)',
                  height: '40px',
                }}
                initial={{ top: '0%' }}
                animate={{ top: '100%' }}
                transition={{ duration: 2.2, ease: 'linear', repeat: Infinity }}
              />
            )}

            {/* Field Markers */}
            {DOCUMENT_FIELD_MARKERS.map((marker) => {
              const isRevealed = revealedMarkers.includes(marker.id)
              if (!isRevealed) return null

              return (
                <div
                  key={marker.id}
                  className="absolute pointer-events-none animate-stamp-impact"
                  style={{
                    top: marker.box.top,
                    left: marker.box.left,
                    width: marker.box.width,
                    height: marker.box.height,
                  }}
                >
                  <div className="absolute inset-0 border-2 border-primary/60 rounded bg-primary/10" />
                  <div className="absolute -top-5 left-0 px-1.5 py-0.5 text-[9px] font-mono font-bold bg-primary text-primary-foreground rounded">
                    {marker.label}
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Stepper Breakdown */}
      <Card className="p-5 border-border bg-card">
        <div className="space-y-3">
          {STEPPER_STAGES.map((stage, i) => {
            const isActive = i === currentStageIndex
            const isDone = i < currentStageIndex

            return (
              <div key={stage.id} className="flex items-start gap-3 py-2.5 border-b border-border/50 last:border-b-0">
                <div className="flex flex-col items-center mt-0.5 shrink-0">
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-mono font-bold transition-all ${
                      isDone
                        ? 'bg-emerald-500 text-white'
                        : isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-secondary text-muted-foreground'
                    }`}
                  >
                    {isDone ? '✓' : i + 1}
                  </div>
                </div>

                <div className="flex-1 min-w-0">
                  <div className={`text-xs sm:text-sm font-semibold ${isDone || isActive ? 'text-foreground' : 'text-muted-foreground'}`}>
                    {stage.label}
                    {isActive && (
                      <motion.span
                        animate={{ opacity: [1, 0.3, 1] }}
                        transition={{ repeat: Infinity, duration: 1.2 }}
                        className="ml-2 text-xs font-normal text-muted-foreground font-mono"
                      >
                        Analyzing…
                      </motion.span>
                    )}
                  </div>
                  {(isActive || isDone) && (
                    <div className="text-xs text-muted-foreground mt-0.5">{stage.description}</div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </Card>
    </div>
  )
}
