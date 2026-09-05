import React from 'react'

interface ExhibitCardProps {
  label: string // e.g. "Exhibit A: Scanned Identification Document"
  subtext?: string
  previewUrl: string
  isPdf?: boolean
  className?: string
  actionSlot?: React.ReactNode
}

export const ExhibitCard: React.FC<ExhibitCardProps> = ({
  label,
  subtext,
  previewUrl,
  isPdf = false,
  className = '',
  actionSlot,
}) => {
  return (
    <div className={`dossier-sheet rounded-lg p-4 sm:p-5 relative ${className}`}>
      {/* Exhibit Label Header */}
      <div className="flex items-center justify-between pb-3 border-b border-[#E3DCD6] mb-3.5">
        <div>
          <h4 className="font-editorial text-sm sm:text-base font-bold text-[#0B2925]">
            {label}
          </h4>
          {subtext && (
            <p className="text-[11px] text-[#6E6571] font-sans mt-0.5">
              {subtext}
            </p>
          )}
        </div>
        {actionSlot && <div>{actionSlot}</div>}
      </div>

      {/* Mounted Image Frame */}
      <div className="relative aspect-[700/440] w-full rounded border border-[#E3DCD6] bg-[#FCFAF8] overflow-hidden flex items-center justify-center p-2">
        {isPdf ? (
          <div className="text-center p-6 space-y-2">
            <div className="w-12 h-12 mx-auto rounded bg-[#F2ECE9] border border-[#E3DCD6] flex items-center justify-center text-[#0B2925] font-serif font-bold text-lg">
              PDF
            </div>
            <span className="text-xs font-sans text-[#27212B] font-medium block">
              Official Document Attached (PDF)
            </span>
          </div>
        ) : (
          <img
            src={previewUrl}
            alt={label}
            className="w-full h-full object-contain rounded select-none"
          />
        )}
      </div>
    </div>
  )
}
