import { useEffect, useState, type FC } from 'react'
import { motion } from 'framer-motion'
import { CheckCircle2, AlertTriangle, XCircle } from 'lucide-react'

interface SimilarityRingProps {
  score: number // 0 to 100
  durationMs?: number
  onComplete?: () => void
}

export const SimilarityRing: FC<SimilarityRingProps> = ({
  score,
  durationMs = 1400,
  onComplete,
}) => {
  const [displayNumber, setDisplayNumber] = useState(0)

  // SVG circle calculations: radius 58 -> circumference 2 * PI * 58 ≈ 364.42
  const radius = 58
  const circumference = 2 * Math.PI * radius
  const targetOffset = circumference - (score / 100) * circumference

  useEffect(() => {
    let startTimestamp: number | null = null
    let animFrame: number

    const step = (timestamp: number) => {
      if (!startTimestamp) startTimestamp = timestamp
      const progress = Math.min((timestamp - startTimestamp) / durationMs, 1)
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3)
      setDisplayNumber(Math.round(eased * score))

      if (progress < 1) {
        animFrame = requestAnimationFrame(step)
      } else {
        if (onComplete) onComplete()
      }
    }

    animFrame = requestAnimationFrame(step)
    return () => cancelAnimationFrame(animFrame)
  }, [score, durationMs, onComplete])

  const isMatch = score >= 70
  const isUncertain = score >= 50 && score < 70

  const strokeColor = isMatch ? '#0B2925' : isUncertain ? '#755B73' : '#8B1E1E'

  return (
    <div className="flex flex-col items-center justify-center text-center select-none">
      <div className="relative w-40 h-40 flex items-center justify-center">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 140 140">
          {/* Background circle track */}
          <circle
            cx="70"
            cy="70"
            r={radius}
            fill="transparent"
            stroke="#E3DCD6"
            strokeWidth="8"
          />
          {/* Animated fill progress ring */}
          <motion.circle
            cx="70"
            cy="70"
            r={radius}
            fill="transparent"
            stroke={strokeColor}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: targetOffset }}
            transition={{ duration: durationMs / 1000, ease: [0.22, 1, 0.36, 1] }}
          />
        </svg>

        {/* Inner Counter Text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="font-editorial text-3xl font-bold tracking-tight text-[#0B2925]">
            {displayNumber}
            <span className="text-lg font-sans text-[#6E6571]">%</span>
          </span>
          <span className="text-[10px] font-sans font-medium uppercase tracking-wider text-[#6E6571] mt-0.5">
            Similarity
          </span>
        </div>
      </div>

      {/* Verdict Indicator Badge */}
      <motion.div
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: (durationMs / 1000) * 0.7, duration: 0.3 }}
        className="mt-3"
      >
        <div
          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-sans font-semibold border ${
            isMatch
              ? 'bg-[#A7F3D0]/30 border-[#0B2925] text-[#0B2925]'
              : isUncertain
              ? 'bg-[#755B73]/15 border-[#755B73] text-[#755B73]'
              : 'bg-[#8B1E1E]/15 border-[#8B1E1E] text-[#8B1E1E]'
          }`}
        >
          {isMatch ? (
            <CheckCircle2 className="w-3.5 h-3.5" />
          ) : isUncertain ? (
            <AlertTriangle className="w-3.5 h-3.5" />
          ) : (
            <XCircle className="w-3.5 h-3.5" />
          )}
          <span>
            {isMatch ? 'Biometric Match' : isUncertain ? 'Borderline Similarity' : 'Biometric Mismatch'}
          </span>
        </div>
      </motion.div>
    </div>
  )
}
