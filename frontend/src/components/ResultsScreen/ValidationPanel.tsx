import React, { useState } from 'react'
import { CheckCircle, AlertTriangle, XCircle, ChevronDown, ChevronUp, FileText, Ban } from 'lucide-react'
import type { ValidationResult, DocumentType } from '../../types'
import { soundFX } from '../../utils/audio'

interface ValidationPanelProps {
  validation: ValidationResult
  documentType: DocumentType
}

export const ValidationPanel: React.FC<ValidationPanelProps> = ({ validation, documentType }) => {
  const [isOpen, setIsOpen] = useState(true)

  const hasIssues = validation.issues && validation.issues.length > 0
  const isPassport = documentType === 'PASSPORT'

  return (
    <div className="dossier-sheet rounded-lg overflow-hidden border border-[#E3DCD6]">
      <button
        onClick={() => {
          soundFX.paperSlide()
          setIsOpen((v) => !v)
        }}
        className="w-full flex items-center justify-between px-4 sm:px-5 py-4 bg-[#FCFAF8] hover:bg-[#F8F5F3] transition-colors text-left border-b border-[#E3DCD6]"
      >
        <div className="flex items-center gap-2.5">
          <FileText className="w-4 h-4 text-[#0B2925]" />
          <span className="font-editorial text-sm font-bold text-[#0B2925]">
            Document Validation Report (Standalone Module)
          </span>
          <span
            className={`text-[11px] font-mono px-2 py-0.5 rounded border ${
              !hasIssues
                ? 'bg-[#A7F3D0]/30 text-[#0B2925] border-[#A7F3D0]'
                : 'bg-[#755B73]/15 text-[#755B73] border-[#755B73]/30'
            }`}
          >
            {hasIssues ? `${validation.issues.length} Issue(s)` : 'Format & Expiry Valid'}
          </span>
        </div>
        {isOpen ? <ChevronUp className="w-4 h-4 text-[#6E6571]" /> : <ChevronDown className="w-4 h-4 text-[#6E6571]" />}
      </button>

      {isOpen && (
        <div className="p-4 sm:p-5 space-y-4 bg-[#FFFFFF] text-xs font-sans">
          {/* Validation Checks Status Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* Format Valid Check */}
            <div className={`p-3 rounded border flex items-center justify-between ${validation.format_valid ? 'bg-[#A7F3D0]/20 border-[#A7F3D0]' : 'bg-[#8B1E1E]/10 border-[#8B1E1E]/30'}`}>
              <div>
                <div className="text-[10px] font-mono text-[#6E6571] uppercase">Format Structure</div>
                <div className="font-editorial text-sm font-bold text-[#0B2925] mt-0.5">
                  {validation.format_valid ? 'Format Valid' : 'Format Invalid'}
                </div>
              </div>
              {validation.format_valid ? (
                <CheckCircle className="w-5 h-5 text-[#0B2925]" />
              ) : (
                <XCircle className="w-5 h-5 text-[#8B1E1E]" />
              )}
            </div>

            {/* Expiry Valid Check */}
            <div className={`p-3 rounded border flex items-center justify-between ${validation.expiry_valid ? 'bg-[#A7F3D0]/20 border-[#A7F3D0]' : 'bg-[#8B1E1E]/10 border-[#8B1E1E]/30'}`}>
              <div>
                <div className="text-[10px] font-mono text-[#6E6571] uppercase">Document Expiry</div>
                <div className="font-editorial text-sm font-bold text-[#0B2925] mt-0.5">
                  {validation.expiry_valid ? 'Valid / In Date' : 'Document Expired'}
                </div>
              </div>
              {validation.expiry_valid ? (
                <CheckCircle className="w-5 h-5 text-[#0B2925]" />
              ) : (
                <XCircle className="w-5 h-5 text-[#8B1E1E]" />
              )}
            </div>

            {/* MRZ Checksum Row (Shown for PASSPORT or when MRZ is present) */}
            {(isPassport || validation.mrz_valid !== null && validation.mrz_valid !== undefined) && (
              <div
                className={`p-3 rounded border flex items-center justify-between ${
                  validation.mrz_valid === true
                    ? 'bg-[#A7F3D0]/20 border-[#A7F3D0]'
                    : validation.mrz_valid === false
                    ? 'bg-[#8B1E1E]/10 border-[#8B1E1E]/30'
                    : 'bg-[#FCFAF8] border-[#E3DCD6]'
                }`}
              >
                <div>
                  <div className="text-[10px] font-mono text-[#6E6571] uppercase">MRZ Checksum (ICAO 9303)</div>
                  <div className="font-editorial text-sm font-bold text-[#0B2925] mt-0.5">
                    {validation.mrz_valid === true
                      ? 'MRZ Checksum: Valid'
                      : validation.mrz_valid === false
                      ? 'MRZ Checksum: Invalid'
                      : 'MRZ Not Present'}
                  </div>
                </div>
                {validation.mrz_valid === true ? (
                  <CheckCircle className="w-5 h-5 text-[#0B2925]" />
                ) : validation.mrz_valid === false ? (
                  <XCircle className="w-5 h-5 text-[#8B1E1E]" />
                ) : (
                  <AlertTriangle className="w-5 h-5 text-[#6E6571]" />
                )}
              </div>
            )}
          </div>

          {/* Issues List */}
          {hasIssues ? (
            <div className="space-y-2 pt-2 border-t border-[#E3DCD6]">
              <div className="text-[11px] font-mono font-semibold text-[#755B73] uppercase">
                Detected Validation Anomalies ({validation.issues.length})
              </div>
              <ul className="space-y-1.5">
                {validation.issues.map((issue, idx) => (
                  <li
                    key={idx}
                    className="p-2.5 rounded border border-[#755B73]/20 bg-[#755B73]/05 text-[#755B73] font-medium flex items-start gap-2 text-xs"
                  >
                    <Ban className="w-4 h-4 shrink-0 mt-0.5 text-[#755B73]" />
                    <span>{issue}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="p-3 rounded bg-[#A7F3D0]/10 border border-[#A7F3D0]/30 text-[#0B2925] text-xs font-sans">
              All document format parameters, expiration thresholds, and watchlist checks passed.
            </div>
          )}
        </div>
      )}
    </div>
  )
}
