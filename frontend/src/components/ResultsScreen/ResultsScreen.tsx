import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Download, FileText, RotateCcw, ChevronDown, ChevronUp, AlertTriangle, CheckCircle, XCircle, Ban } from 'lucide-react'
import type { VerifyResponse } from '../../types'
import { DossierStamp } from '../Common/DossierStamp'
import { RiskScoreGauge } from './RiskScoreGauge'
import { ValidationPanel } from './ValidationPanel'
import { CaseFileExportModal } from '../Common/CaseFileExportModal'
import { AadhaarQRCard } from '../Verification/AadhaarQRCard'
import { soundFX } from '../../utils/audio'

interface ResultsScreenProps {
  result: VerifyResponse
  documentPreviewUrl: string
  selfiePreviewUrl: string | null
  documentName: string
  onReset: () => void
}

const formatFieldKeyLabel = (key: string): string => {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace('Dob', 'Date of Birth')
    .replace('Id Number', 'Document Identifier')
    .replace('Passport Number', 'Passport Identifier')
    .replace('Visa Number', 'Visa Identifier')
    .replace('Date Of Expiry', 'Expiration Date')
}

export const ResultsScreen: React.FC<ResultsScreenProps> = ({
  result,
  documentPreviewUrl,
  selfiePreviewUrl,
  documentName,
  onReset,
}) => {
  const [stampVisible, setStampVisible] = useState(false)
  const [showTamperDetails, setShowTamperDetails] = useState(false)
  const [showBiometricDetails, setShowBiometricDetails] = useState(false)
  const [exportModalOpen, setExportModalOpen] = useState(false)

  useEffect(() => {
    const t = setTimeout(() => {
      setStampVisible(true)
      soundFX.stampImpact(
        result.verdict === 'FAKE' || result.verdict === 'REJECTED' ? 85 : result.verdict === 'SUSPICIOUS' ? 105 : 130,
      )
    }, 600)
    return () => clearTimeout(t)
  }, [result.verdict])

  const isVisa = result.document_type === 'VISA'

  // ─────────────────────────────────────────────────────────────────
  // REJECTED STATE — distinct minimal view; suppresses all data panels
  // ─────────────────────────────────────────────────────────────────
  if (result.verdict === 'REJECTED') {
    const rejectionReason = result.reason || 'No valid identity document detected in the submitted file.'

    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-5">
        {/* Case Header */}
        <div className="flex items-start justify-between gap-4 pb-4 border-b border-[#E3DCD6]">
          <div>
            <h2 className="font-editorial text-2xl sm:text-3xl font-bold text-[#0B2925]">
              Examination Findings — {result.case_number || 'CASE-26188'}
            </h2>
            <p className="text-xs text-[#6E6571] font-sans mt-1">
              Intake Review • {result.checkpoint_location || 'Attari-Wagah Border'} • {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
            </p>
          </div>
        </div>

        {/* REJECTED verdict block */}
        <div className="dossier-sheet rounded-lg overflow-hidden">
          <div className="bg-[#FCFAF8] border-b border-[#E3DCD6] p-4 sm:p-6 flex flex-col sm:flex-row items-center sm:items-start gap-6">
            <div className="flex-shrink-0 flex items-center justify-center min-h-[8rem] min-w-[8rem]">
              <AnimatePresence>
                {stampVisible && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0 }}
                  >
                    <DossierStamp
                      verdict="REJECTED"
                      caseNumber={result.case_number || 'CASE-26188'}
                    />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <div className="flex-1 min-w-0 text-center sm:text-left">
              <div className="text-[11px] font-sans text-[#6E6571] uppercase tracking-wider mb-1">
                Intake Decision
              </div>
              <h3 className="font-editorial text-2xl sm:text-3xl font-bold text-[#755B73]">
                Rejected — Not a Valid Document
              </h3>
              <p className="text-sm font-sans text-[#6E6571] mt-3 max-w-lg leading-relaxed">
                {rejectionReason}
              </p>
              <div className="mt-4 p-3.5 rounded border border-[#755B73]/30 bg-[#755B73]/05 flex gap-3 items-start text-left max-w-lg">
                <Ban className="w-4 h-4 text-[#755B73] flex-shrink-0 mt-0.5" />
                <p className="text-xs font-sans text-[#755B73] leading-relaxed">
                  No forensic analysis, field extraction, or biometric comparison has been performed.
                  Please submit a clear, unobstructed photograph of a valid government-issued identity document.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Exhibit A preview with INVALID banner */}
        <div className="dossier-sheet rounded-lg p-4">
          <div className="pb-2 mb-3 border-b border-[#E3DCD6]">
            <h4 className="font-editorial text-sm font-bold text-[#0B2925]">
              Exhibit A — Submitted File (Invalid)
            </h4>
            <p className="text-[11px] text-[#755B73] font-sans mt-0.5">{documentName} — did not pass intake validation</p>
          </div>
          <div className="relative aspect-[700/440] rounded border-2 border-dashed border-[#755B73]/40 bg-[#FCFAF8] overflow-hidden">
            <img
              src={documentPreviewUrl}
              alt="Rejected submission"
              className="w-full h-full object-contain opacity-40 grayscale"
            />
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="px-5 py-2 border-2 border-[#755B73] rounded font-editorial font-black text-lg text-[#755B73] uppercase tracking-widest transform -rotate-6 bg-[#F8F5F3]/80 select-none shadow-sm">
                INVALID
              </div>
            </div>
          </div>
        </div>

        {/* Action bar */}
        <div className="pt-4 flex flex-wrap items-center gap-3 border-t border-[#E3DCD6]">
          <button
            onClick={() => {
              soundFX.paperSlide()
              onReset()
            }}
            className="flex items-center gap-1.5 px-5 py-2.5 rounded bg-[#0B2925] hover:bg-[#16433C] text-[#FFFFFF] text-xs font-sans font-medium transition-colors cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Deposit New Document</span>
          </button>
        </div>
      </div>
    )
  }

  // ─────────────────────────────────────────────────────────────────
  // GENUINE / SUSPICIOUS / FAKE — full analysis view
  // ─────────────────────────────────────────────────────────────────
  const extractedEntries = Object.entries(result.extracted_fields || {}).filter(([k]) => k !== 'confidence')

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-5">
      {/* Case Header */}
      <div className="flex items-start justify-between gap-4 pb-4 border-b border-[#E3DCD6]">
        <div>
          <h2 className="font-editorial text-2xl sm:text-3xl font-bold text-[#0B2925]">
            Examination Findings — {result.case_number || 'CASE-26188'}
          </h2>
          <p className="text-xs text-[#6E6571] font-sans mt-1">
            {result.document_type?.replace('_', ' ')} • {result.checkpoint_location || 'Attari-Wagah Border'} • Processing time: {result.processing_time_ms || 1200} ms
          </p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={() => {
              soundFX.paperSlide()
              setExportModalOpen(true)
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded border border-[#E3DCD6] bg-[#FFFFFF] hover:bg-[#F2ECE9] text-[#27212B] text-xs font-sans transition-colors cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Dossier</span>
          </button>
        </div>
      </div>

      {/* ─── HERO ELEMENT: RISK SCORE GAUGE + VERDICT SEAL ─── */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 items-stretch">
        <div className="sm:col-span-1">
          <RiskScoreGauge score={result.risk_score} verdict={result.verdict} />
        </div>

        <div className="sm:col-span-2 dossier-sheet rounded-lg p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-[#E3DCD6] pb-2 mb-3">
              <span className="text-[11px] font-sans text-[#6E6571] uppercase tracking-wider">
                Official Case Narrative
              </span>
              <AnimatePresence>
                {stampVisible && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                    <DossierStamp verdict={result.verdict} caseNumber={result.case_number || 'CASE-26188'} />
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
            <p className="text-xs sm:text-sm font-sans text-[#27212B] leading-relaxed">
              {result.reason || 'Forensic screening complete.'}
            </p>
          </div>

          <div className="grid grid-cols-3 gap-2 pt-4 border-t border-[#E3DCD6] mt-4 text-center">
            <div>
              <div className="font-editorial text-lg font-bold text-[#0B2925]">{result.tampering_score}/100</div>
              <div className="text-[10px] font-sans text-[#6E6571]">Tampering</div>
            </div>
            <div>
              <div className="font-editorial text-lg font-bold text-[#0B2925]">
                {isVisa ? 'N/A' : `${result.face_match_score ?? 0}%`}
              </div>
              <div className="text-[10px] font-sans text-[#6E6571]">Facial Match</div>
            </div>
            <div>
              <div className="font-editorial text-lg font-bold text-[#0B2925]">
                {result.validation.issues.length === 0 ? 'Passed' : `${result.validation.issues.length} Flag(s)`}
              </div>
              <div className="text-[10px] font-sans text-[#6E6571]">Format Check</div>
            </div>
          </div>
        </div>
      </div>

      {/* ─── STANDALONE DOCUMENT VALIDATION REPORT ─── */}
      <ValidationPanel validation={result.validation} documentType={result.document_type} />

      {/* ─── DYNAMIC EXTRACTED FIELDS TABLE ─── */}
      <div className="dossier-sheet rounded-lg">
        <div className="p-4 sm:p-5 border-b border-[#E3DCD6]">
          <h4 className="font-editorial text-base font-bold text-[#0B2925]">
            Extracted Specimen Fields ({result.document_type?.replace('_', ' ')})
          </h4>
          <p className="text-[11px] text-[#6E6571] font-sans mt-0.5">
            Parsed OCR fields structured dynamically for this document type.
          </p>
        </div>

        <div className="divide-y divide-[#F2ECE9]">
          {extractedEntries.map(([key, val]) => {
            const isMono = key.includes('number') || key.includes('mrz') || key.includes('id')
            return (
              <div
                key={key}
                className="grid grid-cols-5 items-center px-4 sm:px-5 py-3 hover:bg-[#FCFAF8] transition-colors"
              >
                <div className="col-span-2 text-[11px] text-[#6E6571] font-sans font-semibold">
                  {formatFieldKeyLabel(key)}
                </div>
                <div
                  className={`col-span-3 text-sm font-sans ${
                    isMono ? 'font-mono text-xs tracking-wider text-[#0B2925] font-bold' : 'text-[#27212B]'
                  }`}
                >
                  {String(val)}
                </div>
              </div>
            )
          })}
        </div>

        {/* MRZ Zone Card if detected */}
        {result.mrz?.detected && result.mrz.raw && (
          <div className="p-4 sm:p-5 border-t border-[#E3DCD6] bg-[#FCFAF8]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-mono font-semibold uppercase text-[#0B2925]">
                Machine Readable Zone (ICAO 9303 MRZ)
              </span>
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                  result.mrz.valid
                    ? 'bg-[#A7F3D0]/30 text-[#0B2925] border-[#A7F3D0]'
                    : 'bg-[#8B1E1E]/10 text-[#8B1E1E] border-[#8B1E1E]/30'
                }`}
              >
                {result.mrz.valid ? 'Checksums Verified' : 'Check Digit Anomaly'}
              </span>
            </div>
            <div className="font-mono text-xs p-3 rounded bg-[#27212B] text-[#A7F3D0] tracking-widest leading-relaxed whitespace-pre overflow-x-auto selection:bg-[#0B2925]">
              {result.mrz.raw}
            </div>
          </div>
        )}

        {/* Aadhaar Secure QR Cryptographic Verification Card */}
        {(result.document_type === 'NATIONAL_ID' || result.aadhaar_qr) && (
          <div className="p-4 sm:p-5 border-t border-[#E3DCD6] bg-[#FCFAF8]">
            <AadhaarQRCard aadhaarQr={result.aadhaar_qr} extractedFields={result.extracted_fields} />
          </div>
        )}
      </div>

      {/* ─── EXHIBIT COMPARISON: A + B SIDE BY SIDE ─── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Exhibit A */}
        <div className="dossier-sheet rounded-lg p-4">
          <div className="pb-2 mb-3 border-b border-[#E3DCD6]">
            <h4 className="font-editorial text-sm font-bold text-[#0B2925]">
              Exhibit A — Document Specimen
            </h4>
            <p className="text-[11px] text-[#6E6571] font-sans mt-0.5">{documentName}</p>
          </div>
          <div className="aspect-[700/440] rounded border border-[#E3DCD6] bg-[#FCFAF8] overflow-hidden">
            <img src={documentPreviewUrl} alt="Exhibit A" className="w-full h-full object-contain" />
          </div>
        </div>

        {/* Exhibit B (Selfie) — Hidden for VISA */}
        {!isVisa && (
          <div className="dossier-sheet rounded-lg p-4">
            <div className="pb-2 mb-3 border-b border-[#E3DCD6]">
              <h4 className="font-editorial text-sm font-bold text-[#0B2925]">
                Exhibit B — Live Biometric Capture
              </h4>
              <p className="text-[11px] text-[#6E6571] font-sans mt-0.5">
                Facial embedding: 128-d ArcFace vector
              </p>
            </div>
            <div className="aspect-[700/440] rounded border border-[#E3DCD6] bg-[#FCFAF8] overflow-hidden flex items-center justify-center">
              {selfiePreviewUrl ? (
                <img src={selfiePreviewUrl} alt="Exhibit B" className="w-full h-full object-contain" />
              ) : (
                <div className="text-xs text-[#6E6571] font-sans p-4 text-center">
                  No biometric capture recorded
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* ─── ACCORDION: Tampering Analysis ─── */}
      <div className="dossier-sheet rounded-lg">
        <button
          onClick={() => {
            soundFX.paperSlide()
            setShowTamperDetails((v) => !v)
          }}
          className="w-full flex items-center justify-between px-4 sm:px-5 py-4 hover:bg-[#FCFAF8] transition-colors text-left"
        >
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-[#755B73]" />
            <span className="font-editorial text-sm font-bold text-[#0B2925]">
              Tampering Anomaly &amp; ELA Forensic Heatmap
            </span>
            <span className="text-[11px] font-mono bg-[#755B73]/10 text-[#755B73] px-1.5 py-0.5 rounded border border-[#755B73]/25">
              Score: {result.tampering_score}/100
            </span>
          </div>
          {showTamperDetails ? <ChevronUp className="w-4 h-4 text-[#6E6571]" /> : <ChevronDown className="w-4 h-4 text-[#6E6571]" />}
        </button>

        <AnimatePresence>
          {showTamperDetails && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.25 }}
              className="overflow-hidden border-t border-[#E3DCD6]"
            >
              <div className="p-4 sm:p-5 space-y-4">
                {/* Palette Heatmap Display */}
                {result.heatmap_image_base64 && (
                  <div className="space-y-2">
                    <div className="text-xs font-mono text-[#0B2925] font-semibold">
                      Forensic Compression Heatmap Overlay (Mint → Mauve Gradient)
                    </div>
                    <div className="max-w-md mx-auto rounded border border-[#E3DCD6] overflow-hidden bg-[#0B2925]">
                      <img src={result.heatmap_image_base64} alt="Heatmap overlay" className="w-full h-auto object-contain" />
                    </div>
                  </div>
                )}

                {/* Regions List */}
                {result.tampering_regions && result.tampering_regions.length > 0 ? (
                  <div className="space-y-2">
                    {result.tampering_regions.map((region, i) => (
                      <div key={i} className="p-3 rounded border border-[#E3DCD6] bg-[#FCFAF8] text-xs font-sans space-y-1">
                        <div className="flex items-center gap-2 font-mono text-[10px] text-[#755B73] font-semibold uppercase">
                          <span>Region {i + 1}</span>
                          {region.field && <span>— Field: {region.field}</span>}
                        </div>
                        {region.reason && <p className="text-[#6E6571]">{region.reason}</p>}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-[#6E6571] font-sans">No localized tampering regions identified.</p>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ─── ACCORDION: Facial Correlation (Hidden for VISA) ─── */}
      {!isVisa && (
        <div className="dossier-sheet rounded-lg">
          <button
            onClick={() => {
              soundFX.paperSlide()
              setShowBiometricDetails((v) => !v)
            }}
            className="w-full flex items-center justify-between px-4 sm:px-5 py-4 hover:bg-[#FCFAF8] transition-colors text-left"
          >
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 text-[#0B2925]">
                {(result.face_match_score ?? 0) >= 70 ? (
                  <CheckCircle className="w-4 h-4" />
                ) : (
                  <XCircle className="w-4 h-4 text-[#8B1E1E]" />
                )}
              </div>
              <span className="font-editorial text-sm font-bold text-[#0B2925]">
                Biometric Facial Correlation Report
              </span>
              <span
                className={`text-[11px] font-mono px-1.5 py-0.5 rounded border ${
                  (result.face_match_score ?? 0) >= 80
                    ? 'bg-[#A7F3D0]/25 text-[#0B2925] border-[#A7F3D0]'
                    : (result.face_match_score ?? 0) >= 60
                    ? 'bg-[#755B73]/10 text-[#755B73] border-[#755B73]/25'
                    : 'bg-[#8B1E1E]/10 text-[#8B1E1E] border-[#8B1E1E]/25'
                }`}
              >
                {result.face_match_score ?? 0}% correlation
              </span>
            </div>
            {showBiometricDetails ? <ChevronUp className="w-4 h-4 text-[#6E6571]" /> : <ChevronDown className="w-4 h-4 text-[#6E6571]" />}
          </button>

          <AnimatePresence>
            {showBiometricDetails && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.25 }}
                className="overflow-hidden border-t border-[#E3DCD6]"
              >
                <div className="p-4 sm:p-5 space-y-3 text-xs font-sans text-[#27212B]">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 rounded border border-[#E3DCD6] bg-[#FCFAF8]">
                      <div className="text-[10px] text-[#6E6571] uppercase mb-1">Correlation Score</div>
                      <div className="font-editorial text-2xl font-bold text-[#0B2925]">
                        {result.face_match_score}%
                      </div>
                      <div className="text-[10px] text-[#6E6571]">ArcFace-R100 • 128-d vectors</div>
                    </div>
                    <div className="p-3 rounded border border-[#E3DCD6] bg-[#FCFAF8]">
                      <div className="text-[10px] text-[#6E6571] uppercase mb-1">Decision Threshold</div>
                      <div className="font-editorial text-2xl font-bold text-[#0B2925]">70%</div>
                      <div className="text-[10px] text-[#6E6571]">Cosine similarity distance</div>
                    </div>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* ─── ACTION BAR ─── */}
      <div className="pt-4 flex flex-wrap items-center gap-3 border-t border-[#E3DCD6]">
        <button
          onClick={() => {
            soundFX.paperSlide()
            onReset()
          }}
          className="flex items-center gap-1.5 px-5 py-2.5 rounded bg-[#0B2925] hover:bg-[#16433C] text-[#FFFFFF] text-xs font-sans font-medium transition-colors cursor-pointer"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Open New Case File</span>
        </button>

        <button
          onClick={() => {
            soundFX.paperSlide()
            setExportModalOpen(true)
          }}
          className="flex items-center gap-1.5 px-5 py-2.5 rounded border border-[#E3DCD6] bg-[#FFFFFF] hover:bg-[#F2ECE9] text-[#27212B] text-xs font-sans font-medium transition-colors cursor-pointer"
        >
          <FileText className="w-3.5 h-3.5" />
          <span>Print Dossier Report</span>
        </button>
      </div>

      {/* Export Modal */}
      <CaseFileExportModal
        isOpen={exportModalOpen}
        onClose={() => setExportModalOpen(false)}
        result={result}
        documentName={documentName}
      />
    </div>
  )
}
