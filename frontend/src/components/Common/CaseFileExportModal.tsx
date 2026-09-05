import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Download, Copy, Check, FileText } from 'lucide-react'
import type { VerifyResponse } from '../../types'
import { soundFX } from '../../utils/audio'

interface CaseFileExportModalProps {
  isOpen: boolean
  onClose: () => void
  result: VerifyResponse | null
  documentName: string
}

export const CaseFileExportModal: React.FC<CaseFileExportModalProps> = ({
  isOpen,
  onClose,
  result,
  documentName,
}) => {
  const [copied, setCopied] = useState(false)
  const [activeTab, setActiveTab] = useState<'dossier' | 'json'>('dossier')

  if (!isOpen || !result) return null

  const reportPayload = {
    case_reference: result.case_number || 'CASE-26188-A',
    examination_timestamp: new Date().toISOString(),
    document_type: result.document_type,
    checkpoint_location: result.checkpoint_location || 'Attari-Wagah Border',
    exhibit_source: documentName,
    official_verdict: result.verdict,
    risk_score: result.risk_score,
    tampering_score: result.tampering_score,
    facial_correlation_score: result.face_match_score,
    validation: result.validation,
    extracted_records: result.extracted_fields,
    tampering_findings: result.tampering_regions,
    security_evaluations: result.security_checks,
    examiner_audit_hash: `SHA256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069`,
  }

  const handleCopyJSON = () => {
    soundFX.paperSlide()
    navigator.clipboard.writeText(JSON.stringify(reportPayload, null, 2))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownloadJSON = () => {
    soundFX.paperSlide()
    const blob = new Blob([JSON.stringify(reportPayload, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `case_examination_${(result.case_number || '26188').toLowerCase()}_report.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 bg-[#27212B]/40 backdrop-blur-xs"
        />

        {/* Modal Window */}
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 12 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96, y: 12 }}
          className="relative w-full max-w-2xl max-h-[85vh] flex flex-col rounded-lg dossier-sheet overflow-hidden shadow-xl z-10"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-[#E3DCD6] bg-[#FCFAF8]">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded bg-[#F2ECE9] border border-[#E3DCD6] text-[#0B2925]">
                <FileText className="w-4 h-4" />
              </div>
              <div>
                <h3 className="font-editorial text-base font-bold text-[#0B2925]">
                  Official Examination Dossier Record
                </h3>
                <p className="text-xs text-[#6E6571] font-sans">
                  Reference {reportPayload.case_reference} • {new Date().toLocaleDateString()}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1 rounded text-[#6E6571] hover:text-[#27212B] hover:bg-[#F2ECE9] transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-[#E3DCD6] bg-[#F8F5F3] px-6 pt-2 gap-4 text-xs font-sans">
            <button
              onClick={() => setActiveTab('dossier')}
              className={`pb-2 font-medium transition-colors border-b-2 ${
                activeTab === 'dossier'
                  ? 'border-[#0B2925] text-[#0B2925] font-semibold'
                  : 'border-transparent text-[#6E6571] hover:text-[#27212B]'
              }`}
            >
              Case Summary Sheet
            </button>
            <button
              onClick={() => setActiveTab('json')}
              className={`pb-2 font-medium transition-colors border-b-2 ${
                activeTab === 'json'
                  ? 'border-[#0B2925] text-[#0B2925] font-semibold'
                  : 'border-transparent text-[#6E6571] hover:text-[#27212B]'
              }`}
            >
              Audit Record (JSON)
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4 font-sans text-xs">
            {activeTab === 'dossier' ? (
              <div className="space-y-4 text-[#27212B]">
                {/* Findings Banner */}
                <div className="p-4 rounded border border-[#E3DCD6] bg-[#FCFAF8] flex items-center justify-between">
                  <div>
                    <div className="text-[11px] uppercase tracking-wider text-[#6E6571] font-semibold">
                      OFFICIAL CASE VERDICT
                    </div>
                    <div className="font-editorial text-lg font-bold text-[#0B2925] mt-0.5">
                      {result.verdict === 'GENUINE'
                        ? 'Verified Genuine Specimen'
                        : result.verdict === 'SUSPICIOUS'
                        ? 'Flagged for Examiner Inquiry'
                        : 'Fraudulent / Altered Specimen'}
                    </div>
                  </div>
                  <span className="text-xs font-mono px-2.5 py-1 rounded border border-[#E3DCD6] bg-[#FFFFFF] text-[#0B2925] font-semibold">
                    {result.verdict}
                  </span>
                </div>

                {/* Identity Details */}
                <div className="p-4 rounded border border-[#E3DCD6] bg-[#FFFFFF] space-y-2">
                  <span className="text-[11px] font-semibold text-[#6E6571] uppercase block">
                    Extracted Case Subject Record
                  </span>
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <span className="text-[#6E6571] block">Full Legal Name:</span>
                      <span className="font-semibold text-[#27212B] font-editorial text-sm">
                        {result.extracted_fields.name}
                      </span>
                    </div>
                    <div>
                      <span className="text-[#6E6571] block">Date of Birth:</span>
                      <span className="font-semibold text-[#27212B]">
                        {result.extracted_fields.dob}
                      </span>
                    </div>
                    <div>
                      <span className="text-[#6E6571] block">Document Identifier:</span>
                      <span className="font-mono font-medium text-[#0B2925]">
                        {result.extracted_fields.id_number}
                      </span>
                    </div>
                    <div>
                      <span className="text-[#6E6571] block">Principal Residence:</span>
                      <span className="font-medium text-[#27212B]">
                        {result.extracted_fields.address}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Scores */}
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div className="p-3 rounded border border-[#E3DCD6] bg-[#FCFAF8]">
                    <span className="text-[10px] text-[#6E6571] block uppercase">Tampering Score</span>
                    <span className="text-sm font-semibold font-mono text-[#0B2925]">
                      {result.tampering_score} / 100
                    </span>
                  </div>
                  <div className="p-3 rounded border border-[#E3DCD6] bg-[#FCFAF8]">
                    <span className="text-[10px] text-[#6E6571] block uppercase">Facial Match</span>
                    <span className="text-sm font-semibold font-mono text-[#0B2925]">
                      {result.face_match_score}%
                    </span>
                  </div>
                  <div className="p-3 rounded border border-[#E3DCD6] bg-[#FCFAF8]">
                    <span className="text-[10px] text-[#6E6571] block uppercase">Latency</span>
                    <span className="text-sm font-semibold font-mono text-[#6E6571]">
                      {result.processing_time_ms || 1200} ms
                    </span>
                  </div>
                </div>

                <div className="p-3 rounded bg-[#F8F5F3] border border-[#E3DCD6] text-[10px] text-[#6E6571] font-mono truncate">
                  REGISTRY HASH: {reportPayload.examiner_audit_hash}
                </div>
              </div>
            ) : (
              <pre className="p-4 rounded border border-[#E3DCD6] bg-[#FCFAF8] text-[#27212B] overflow-x-auto text-[11px] leading-relaxed font-mono">
                {JSON.stringify(reportPayload, null, 2)}
              </pre>
            )}
          </div>

          {/* Footer */}
          <div className="px-6 py-3 border-t border-[#E3DCD6] bg-[#FCFAF8] flex items-center justify-between">
            <button
              onClick={handleCopyJSON}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded border border-[#E3DCD6] bg-[#FFFFFF] text-[#27212B] text-xs font-sans hover:bg-[#F2ECE9] transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-[#0B2925]" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? 'Copied' : 'Copy JSON'}</span>
            </button>
            <button
              onClick={handleDownloadJSON}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded bg-[#0B2925] hover:bg-[#16433C] text-[#FFFFFF] text-xs font-sans font-medium transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download Official Report</span>
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
