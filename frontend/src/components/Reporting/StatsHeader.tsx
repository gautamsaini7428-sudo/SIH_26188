import { useEffect, useState, type FC } from 'react'
import { ShieldCheck, AlertTriangle, XCircle, FileSpreadsheet } from 'lucide-react'

interface StatsHeaderProps {
  totalCount: number
  genuineCount: number
  suspiciousCount: number
  fakeCount: number
}

function useCountUp(target: number, durationMs = 1000): number {
  const [val, setVal] = useState(0)

  useEffect(() => {
    let startTimestamp: number | null = null
    let frame: number

    const step = (now: number) => {
      if (!startTimestamp) startTimestamp = now
      const progress = Math.min((now - startTimestamp) / durationMs, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setVal(Math.round(eased * target))

      if (progress < 1) {
        frame = requestAnimationFrame(step)
      }
    }

    frame = requestAnimationFrame(step)
    return () => cancelAnimationFrame(frame)
  }, [target, durationMs])

  return val
}

export const StatsHeader: FC<StatsHeaderProps> = ({
  totalCount,
  genuineCount,
  suspiciousCount,
  fakeCount,
}) => {
  const animatedTotal = useCountUp(totalCount, 1200)
  const animatedGenuine = useCountUp(genuineCount, 1200)
  const animatedSuspicious = useCountUp(suspiciousCount, 1200)
  const animatedFake = useCountUp(fakeCount, 1200)

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {/* 1. Total */}
      <div className="dossier-sheet rounded-lg p-4 bg-[#FFFFFF]">
        <div className="flex items-center gap-2 text-[11px] font-sans text-[#6E6571] uppercase font-semibold">
          <FileSpreadsheet className="w-3.5 h-3.5 text-[#0B2925]" />
          <span>Total Screened</span>
        </div>
        <div className="font-editorial text-2xl sm:text-3xl font-bold text-[#0B2925] mt-1">
          {animatedTotal}
        </div>
        <div className="text-[10px] text-[#6E6571] font-sans mt-0.5">Today&apos;s intake cycle</div>
      </div>

      {/* 2. Genuine */}
      <div className="dossier-sheet rounded-lg p-4 bg-[#FFFFFF]">
        <div className="flex items-center gap-2 text-[11px] font-sans text-[#6E6571] uppercase font-semibold">
          <ShieldCheck className="w-3.5 h-3.5 text-[#0B2925]" />
          <span>Verified Genuine</span>
        </div>
        <div className="font-editorial text-2xl sm:text-3xl font-bold text-[#0B2925] mt-1 flex items-baseline gap-1">
          <span>{animatedGenuine}</span>
          <span className="text-xs font-sans text-[#6E6571]">
            ({totalCount ? Math.round((genuineCount / totalCount) * 100) : 0}%)
          </span>
        </div>
        <div className="text-[10px] text-[#0B2925] font-sans font-medium mt-0.5">Cleared for issuance</div>
      </div>

      {/* 3. Suspicious */}
      <div className="dossier-sheet rounded-lg p-4 bg-[#FFFFFF]">
        <div className="flex items-center gap-2 text-[11px] font-sans text-[#6E6571] uppercase font-semibold">
          <AlertTriangle className="w-3.5 h-3.5 text-[#755B73]" />
          <span>Flagged Suspicious</span>
        </div>
        <div className="font-editorial text-2xl sm:text-3xl font-bold text-[#755B73] mt-1 flex items-baseline gap-1">
          <span>{animatedSuspicious}</span>
          <span className="text-xs font-sans text-[#6E6571]">
            ({totalCount ? Math.round((suspiciousCount / totalCount) * 100) : 0}%)
          </span>
        </div>
        <div className="text-[10px] text-[#755B73] font-sans font-medium mt-0.5">Referred to examiner</div>
      </div>

      {/* 4. Fake */}
      <div className="dossier-sheet rounded-lg p-4 bg-[#FFFFFF]">
        <div className="flex items-center gap-2 text-[11px] font-sans text-[#6E6571] uppercase font-semibold">
          <XCircle className="w-3.5 h-3.5 text-[#8B1E1E]" />
          <span>Fraudulent Altered</span>
        </div>
        <div className="font-editorial text-2xl sm:text-3xl font-bold text-[#8B1E1E] mt-1 flex items-baseline gap-1">
          <span>{animatedFake}</span>
          <span className="text-xs font-sans text-[#6E6571]">
            ({totalCount ? Math.round((fakeCount / totalCount) * 100) : 0}%)
          </span>
        </div>
        <div className="text-[10px] text-[#8B1E1E] font-sans font-medium mt-0.5">Critical tamper triggers</div>
      </div>
    </div>
  )
}
