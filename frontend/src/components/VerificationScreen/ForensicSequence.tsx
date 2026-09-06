import React, { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { soundFX } from '../../utils/audio'
import { STEPPER_STAGES, DOCUMENT_FIELD_MARKERS } from '../../utils/mockData'

interface ForensicSequenceProps {
  documentPreviewUrl: string
  currentStageIndex: number
}

export const ForensicSequence: React.FC<ForensicSequenceProps> = ({
  documentPreviewUrl,
  currentStageIndex,
}) => {
  const [revealedMarkers, setRevealedMarkers] = useState<string[]>([])

  useEffect(() => {
    if (currentStageIndex < 1) return

    // Stagger field marker reveals during "Extracting text" stage
    const timers: ReturnType<typeof setTimeout>[] = []

    DOCUMENT_FIELD_MARKERS.forEach((marker, i) => {
      const t = setTimeout(
        () => {
          soundFX.fieldInkLand()
          setRevealedMarkers((prev) => [...prev, marker.id])
        },
        300 + i * 500,
      )
      timers.push(t)
    })

    return () => timers.forEach(clearTimeout)
  }, [currentStageIndex])

  return (
    <div className="space-y-6">
      {/* Document Image with Ink-Stamp Field Markers */}
      <div className="dossier-sheet rounded-lg p-4 sm:p-5">
        <div className="text-xs font-sans text-[#6E6571] mb-3 pb-2 border-b border-[#E3DCD6]">
          <span className="font-editorial text-sm font-bold text-[#0B2925]">Exhibit A</span>
          {' '}— Document forensic analysis in progress
        </div>

        <div className="relative aspect-[700/440] w-full rounded border border-[#E3DCD6] bg-[#FCFAF8] overflow-hidden">
          {/* Document Preview Background */}
          <img
            src={documentPreviewUrl}
            alt="Document under analysis"
            className="absolute inset-0 w-full h-full object-contain"
          />

          {/* Subtle scanning overlay when in stage 0 */}
          {currentStageIndex === 0 && (
            <motion.div
              className="absolute left-0 right-0 h-0.5 pointer-events-none"
              style={{
                background:
                  'linear-gradient(180deg, transparent, rgba(11,41,37,0.15) 45%, rgba(167,243,208,0.35) 50%, rgba(11,41,37,0.15) 55%, transparent)',
                height: '48px',
              }}
              initial={{ top: '0%' }}
              animate={{ top: '100%' }}
              transition={{ duration: 2.8, ease: 'linear', repeat: Infinity }}
            />
          )}

          {/* Field Ink-Stamp Markers: revealed during extraction stage */}
          {DOCUMENT_FIELD_MARKERS.map((marker) => {
            const isRevealed = revealedMarkers.includes(marker.id)
            if (!isRevealed) return null

            const isFlagged = currentStageIndex >= 2 && marker.confidence < 65

            return (
              <div
                key={marker.id}
                className="absolute pointer-events-none animate-ink-stamp"
                style={{
                  top: marker.box.top,
                  left: marker.box.left,
                  width: marker.box.width,
                  height: marker.box.height,
                }}
              >
                {/* Corner brackets — ink-stamp field indicator */}
                <div
                  className={`absolute inset-0 ${isFlagged ? 'border-[#755B73]' : 'border-[#0B2925]'}`}
                  style={{
                    borderWidth: '0',
                    boxShadow: `inset 0 0 0 2px ${isFlagged ? 'rgba(117,91,115,0.4)' : 'rgba(11,41,37,0.22)'}`,
                    borderRadius: '2px',
                  }}
                />
                {/* Top-left corner bracket */}
                <div
                  className={`absolute top-0 left-0 w-3 h-3 border-t-2 border-l-2 ${isFlagged ? 'border-[#755B73]' : 'border-[#0B2925]'}`}
                />
                {/* Bottom-right corner bracket */}
                <div
                  className={`absolute bottom-0 right-0 w-3 h-3 border-b-2 border-r-2 ${isFlagged ? 'border-[#755B73]' : 'border-[#0B2925]'}`}
                />

                {/* Field Label Tag */}
                <div
                  className={`absolute -top-5 left-0 px-1.5 py-0.5 text-[9px] font-mono font-semibold rounded ${
                    isFlagged
                      ? 'bg-[#755B73] text-[#FFFFFF]'
                      : 'bg-[#0B2925] text-[#FFFFFF]'
                  }`}
                >
                  {marker.label}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Quiet 4-Stage Stepper */}
      <div className="dossier-sheet rounded-lg p-4 sm:p-5">
        <div className="text-xs font-sans text-[#6E6571] mb-4 pb-2 border-b border-[#E3DCD6]">
          <span className="font-editorial text-sm font-bold text-[#0B2925]">Analysis Sequence</span>
          {' '}— Forensic examination pipeline
        </div>

        <div className="space-y-0">
          {STEPPER_STAGES.map((stage, i) => {
            const isActive = i === currentStageIndex
            const isDone = i < currentStageIndex

            return (
              <div key={stage.id} className="flex items-start gap-3 py-3 border-b border-[#F2ECE9] last:border-b-0">
                {/* Stage Line Indicator */}
                <div className="flex flex-col items-center mt-0.5 flex-shrink-0">
                  <div
                    className={`w-5 h-5 rounded-full flex items-center justify-center border text-[10px] font-mono font-semibold transition-all duration-500 ${
                      isDone
                        ? 'bg-[#A7F3D0] border-[#0B2925] text-[#0B2925]'
                        : isActive
                        ? 'bg-[#0B2925] border-[#0B2925] text-[#FFFFFF]'
                        : 'bg-[#FFFFFF] border-[#E3DCD6] text-[#C8BEB7]'
                    }`}
                  >
                    {isDone ? '✓' : i + 1}
                  </div>
                  {i < STEPPER_STAGES.length - 1 && (
                    <div
                      className={`w-px h-6 mt-1 transition-all duration-700 ${isDone ? 'bg-[#0B2925]' : 'bg-[#E3DCD6]'}`}
                    />
                  )}
                </div>

                {/* Stage Text */}
                <div className="flex-1 min-w-0 pb-1">
                  <div
                    className={`text-xs sm:text-sm font-sans font-semibold transition-colors ${
                      isDone
                        ? 'text-[#0B2925]'
                        : isActive
                        ? 'text-[#0B2925]'
                        : 'text-[#C8BEB7]'
                    }`}
                  >
                    {stage.label}
                    {isActive && (
                      <motion.span
                        animate={{ opacity: [1, 0.3, 1] }}
                        transition={{ repeat: Infinity, duration: 1.2 }}
                        className="ml-2 text-[11px] font-normal font-sans text-[#6E6571]"
                      >
                        Working…
                      </motion.span>
                    )}
                  </div>
                  {(isActive || isDone) && (
                    <div className="text-[11px] text-[#6E6571] font-sans mt-0.5">
                      {stage.description}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
