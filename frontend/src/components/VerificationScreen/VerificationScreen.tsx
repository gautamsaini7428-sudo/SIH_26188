import { useEffect, useState, type FC } from 'react'
import { ForensicSequence } from './ForensicSequence'
import { STEPPER_STAGES } from '../../utils/mockData'
import { soundFX } from '../../utils/audio'

interface VerificationScreenProps {
  documentPreviewUrl: string
  selfiePreviewUrl: string | null
  onComplete: () => void
}

export const VerificationScreen: FC<VerificationScreenProps> = ({
  documentPreviewUrl,
  selfiePreviewUrl,
  onComplete,
}) => {
  const [currentStageIndex, setCurrentStageIndex] = useState(0)

  useEffect(() => {
    // Advance through the 4 stages with appropriate delays
    const stageDurations = [2800, 2400, 2200, 1800] // ms per stage
    let cumulativeDelay = 0

    const timers: ReturnType<typeof setTimeout>[] = []

    STEPPER_STAGES.forEach((_, i) => {
      if (i === 0) {
        // First stage is already active (currentStageIndex = 0)
        cumulativeDelay += stageDurations[0]
        return
      }

      cumulativeDelay += stageDurations[i - 1]
      const t = setTimeout(() => {
        soundFX.fieldInkLand()
        setCurrentStageIndex(i)
      }, cumulativeDelay)

      timers.push(t)
    })

    // Final completion — after last stage runs
    cumulativeDelay += stageDurations[STEPPER_STAGES.length - 1]
    const completionTimer = setTimeout(() => {
      onComplete()
    }, cumulativeDelay)

    timers.push(completionTimer)

    return () => timers.forEach(clearTimeout)
  }, [])

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-6">
      {/* Header */}
      <div className="space-y-1">
        <h2 className="font-editorial text-2xl sm:text-3xl font-bold text-[#0B2925]">
          Forensic Examination In Progress
        </h2>
        <p className="text-xs sm:text-sm text-[#6E6571] font-sans">
          AI forensic systems are evaluating the submitted case exhibits. Please hold.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Main Forensic Sequence: takes 2/3 */}
        <div className="lg:col-span-2">
          <ForensicSequence
            documentPreviewUrl={documentPreviewUrl}
            currentStageIndex={currentStageIndex}
          />
        </div>

        {/* Exhibit B thumbnail + notes */}
        <div className="space-y-4">
          {/* Exhibit B Preview */}
          <div className="dossier-sheet rounded-lg p-4">
            <div className="text-xs font-sans text-[#6E6571] mb-3 pb-2 border-b border-[#E3DCD6]">
              <span className="font-editorial text-sm font-bold text-[#0B2925]">Exhibit B</span>
              {' '}— Live biometric capture
            </div>

            <div className="aspect-[4/3] w-full rounded border border-[#E3DCD6] bg-[#FCFAF8] overflow-hidden flex items-center justify-center">
              {selfiePreviewUrl ? (
                <img
                  src={selfiePreviewUrl}
                  alt="Biometric Exhibit B"
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="text-center p-4 space-y-1">
                  <div className="w-8 h-8 mx-auto rounded bg-[#F2ECE9] border border-[#E3DCD6] flex items-center justify-center">
                    <span className="text-xs text-[#6E6571]">No photo</span>
                  </div>
                </div>
              )}
            </div>

            {/* Biometric processing status */}
            {currentStageIndex >= 2 && (
              <div className="mt-3 p-2 rounded bg-[#F8F5F3] border border-[#E3DCD6] text-[11px] font-sans text-[#6E6571]">
                Comparing 512-dimensional facial embedding vectors…
              </div>
            )}
          </div>

          {/* Case file metadata */}
          <div className="dossier-sheet rounded-lg p-4 space-y-2.5">
            <span className="text-[11px] font-editorial font-bold text-[#0B2925] block">
              Examination Parameters
            </span>
            <div className="space-y-2 text-[11px] font-sans text-[#6E6571]">
              <div className="flex justify-between">
                <span>MRZ Parse Mode</span>
                <span className="text-[#27212B] font-mono">ICAO 9303</span>
              </div>
              <div className="flex justify-between">
                <span>ELA Sensitivity</span>
                <span className="text-[#27212B] font-mono">95%</span>
              </div>
              <div className="flex justify-between">
                <span>Face Model</span>
                <span className="text-[#27212B] font-mono">ArcFace-R100</span>
              </div>
              <div className="flex justify-between">
                <span>Threshold Score</span>
                <span className="text-[#27212B] font-mono">70 / 100</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
