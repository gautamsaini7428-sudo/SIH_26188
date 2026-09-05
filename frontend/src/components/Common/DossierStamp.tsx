import { useEffect } from 'react'
import { soundFX } from '../../utils/audio'

interface DossierStampProps {
  verdict: 'GENUINE' | 'SUSPICIOUS' | 'FAKE' | 'REJECTED'
  caseNumber?: string
  date?: string
}

export const DossierStamp: React.FC<DossierStampProps> = ({
  verdict,
  caseNumber = 'CASE-26188',
  date = new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }),
}) => {
  useEffect(() => {
    soundFX.stampImpact(verdict === 'FAKE' || verdict === 'REJECTED' ? 85 : verdict === 'SUSPICIOUS' ? 110 : 130)
  }, [verdict])

  if (verdict === 'GENUINE') {
    return (
      <div className="relative inline-block animate-stamp-impact select-none">
        <div className="relative border-4 border-double border-[#0B2925] rounded-full p-4 w-44 h-44 flex flex-col items-center justify-center text-center bg-[#A7F3D0]/25 shadow-sm transform -rotate-6">
          <div className="text-[10px] font-mono tracking-widest text-[#0B2925] uppercase font-bold">
            FORENSIC REGISTRY
          </div>
          <div className="my-1 border-t border-b border-[#0B2925] py-0.5 w-32">
            <span className="font-editorial text-lg font-bold tracking-wider text-[#0B2925] block uppercase">
              GENUINE
            </span>
          </div>
          <div className="text-[9px] font-sans font-semibold text-[#0B2925]/80 uppercase">
            VERIFIED &amp; RECORDED
          </div>
          <div className="text-[8px] font-mono text-[#0B2925]/70 mt-1">
            {caseNumber} • {date}
          </div>
        </div>
      </div>
    )
  }

  if (verdict === 'SUSPICIOUS') {
    return (
      <div className="relative inline-block animate-stamp-impact select-none">
        <div className="relative border-3 border-solid border-[#755B73] rounded-sm px-6 py-3.5 text-center bg-[#755B73]/10 shadow-sm transform -rotate-3">
          <div className="text-[9px] font-mono tracking-widest text-[#755B73] uppercase font-bold">
            EXAMINER HOLD
          </div>
          <div className="font-editorial text-xl font-bold tracking-wide text-[#755B73] uppercase my-0.5">
            SUSPICIOUS
          </div>
          <div className="text-[9px] font-sans font-semibold text-[#755B73] uppercase">
            REFERRED FOR INQUIRY
          </div>
          <div className="text-[8px] font-mono text-[#755B73]/80 mt-1">
            {caseNumber} • {date}
          </div>
        </div>
      </div>
    )
  }

  if (verdict === 'REJECTED') {
    return (
      <div className="relative inline-block animate-stamp-impact select-none">
        {/* Cross-barred rectangular stamp — distinct shape from the GENUINE circle and FAKE rectangle */}
        <div className="relative px-7 py-4 text-center transform rotate-6" style={{
          border: '4px solid #755B73',
          borderRadius: '2px',
          background: 'rgba(117,91,115,0.08)',
          boxShadow: '0 2px 8px rgba(117,91,115,0.18)',
        }}>
          {/* Diagonal slash bars across the stamp */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none" style={{ borderRadius: '2px' }}>
            <svg width="100%" height="100%" viewBox="0 0 160 80" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
              <line x1="0" y1="0" x2="160" y2="80" stroke="#755B73" strokeWidth="2" strokeOpacity="0.35" />
              <line x1="160" y1="0" x2="0" y2="80" stroke="#755B73" strokeWidth="2" strokeOpacity="0.35" />
            </svg>
          </div>
          <div className="relative z-10">
            <div className="text-[9px] font-mono tracking-widest text-[#755B73] uppercase font-bold">
              INTAKE DIVISION
            </div>
            <div className="font-editorial text-xl font-black tracking-wide text-[#755B73] uppercase my-1 border-t-2 border-b-2 border-[#755B73] py-0.5">
              REJECTED
            </div>
            <div className="text-[9px] font-sans font-bold text-[#755B73] uppercase tracking-wide">
              NOT A VALID DOCUMENT
            </div>
            <div className="text-[8px] font-mono text-[#755B73]/80 mt-1">
              {caseNumber} • {date}
            </div>
          </div>
        </div>
      </div>
    )
  }

  // FAKE / FRAUDULENT
  return (
    <div className="relative inline-block animate-stamp-impact select-none">
      <div className="relative border-4 border-solid border-[#8B1E1E] rounded-sm px-7 py-4 text-center bg-[#8B1E1E]/10 shadow-sm transform -rotate-8">
        <div className="text-[9px] font-mono tracking-widest text-[#8B1E1E] uppercase font-extrabold">
          SECURITY DIVISION
        </div>
        <div className="font-editorial text-2xl font-black tracking-widest text-[#8B1E1E] uppercase my-0.5 border-t-2 border-b-2 border-[#8B1E1E] py-0.5">
          FRAUDULENT
        </div>
        <div className="text-[9.5px] font-sans font-bold text-[#8B1E1E] uppercase tracking-wide">
          SECURITY REJECTED • VOID
        </div>
        <div className="text-[8px] font-mono text-[#8B1E1E]/80 mt-1">
          {caseNumber} • {date}
        </div>
      </div>
    </div>
  )
}
