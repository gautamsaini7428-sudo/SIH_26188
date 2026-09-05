import React, { useEffect, useState } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../ui/dialog'
import { Badge } from '../ui/badge'
import type { VerificationRecord, VerifyResponse } from '../../types'
import { getVerificationById } from '../../services/api'
import { FileSearch } from 'lucide-react'

interface CaseDetailDialogProps {
  record: VerificationRecord | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

export const CaseDetailDialog: React.FC<CaseDetailDialogProps> = ({ record, open, onOpenChange }) => {
  const [fullDetail, setFullDetail] = useState<VerifyResponse | null>(null)

  useEffect(() => {
    if (open && record) {
      const numId = parseInt(record.id.replace(/\D/g, ''), 10)
      if (!isNaN(numId) && numId > 0 && !record.id.startsWith('audit-')) {
        getVerificationById(numId)
          .then((res) => setFullDetail(res))
          .catch(() => setFullDetail(null))
      } else {
        setFullDetail(null)
      }
    } else {
      setFullDetail(null)
    }
  }, [open, record])

  if (!record) return null

  const isGenuine = record.verdict === 'GENUINE'
  const isSuspicious = record.verdict === 'SUSPICIOUS'
  const isFake = record.verdict === 'FAKE'

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between pr-6">
            <DialogTitle className="font-mono text-lg font-bold text-foreground">
              {record.caseNumber}
            </DialogTitle>
            <Badge
              variant={
                isGenuine
                  ? 'success'
                  : isSuspicious
                  ? 'warning'
                  : isFake
                  ? 'destructive'
                  : 'rejected'
              }
              className="font-mono text-xs px-2.5 py-0.5 uppercase"
            >
              {record.verdict}
            </Badge>
          </div>
          <DialogDescription className="text-xs text-muted-foreground font-mono">
            Examined on {new Date(record.date).toLocaleString()} • Checkpoint: {record.checkpointLocation || 'Attari-Wagah Border'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 pt-2">
          {/* Main Attributes Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 p-3 rounded-xl bg-secondary/50 border border-border text-xs font-mono">
            <div>
              <span className="text-muted-foreground block text-[10px]">SUBJECT NAME</span>
              <span className="font-bold text-foreground text-sm">{record.subjectName}</span>
            </div>
            <div>
              <span className="text-muted-foreground block text-[10px]">DOCUMENT CATEGORY</span>
              <span className="font-bold text-foreground">{record.documentType}</span>
            </div>
            <div>
              <span className="text-muted-foreground block text-[10px]">SCREENED BY</span>
              <span className="font-bold text-primary truncate block">{record.officerEmail || record.examiner}</span>
            </div>
          </div>

          {/* Scores Breakdown */}
          <div className="grid grid-cols-3 gap-3 text-center">
            <div className="p-3 rounded-xl border border-border bg-card">
              <span className="text-[10px] font-mono text-muted-foreground block uppercase font-bold">COMPOSITE RISK</span>
              <span className={`text-lg font-bold font-mono ${record.riskScore > 65 ? 'text-destructive' : record.riskScore > 30 ? 'text-yellow-600 dark:text-yellow-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
                {record.riskScore}/100
              </span>
            </div>
            <div className="p-3 rounded-xl border border-border bg-card">
              <span className="text-[10px] font-mono text-muted-foreground block uppercase font-bold">TAMPER SCORE</span>
              <span className="text-lg font-bold font-mono text-foreground">{record.tamperingScore}/100</span>
            </div>
            <div className="p-3 rounded-xl border border-border bg-card">
              <span className="text-[10px] font-mono text-muted-foreground block uppercase font-bold">FACE MATCH</span>
              <span className="text-lg font-bold font-mono text-foreground">
                {record.faceMatchScore !== undefined && record.faceMatchScore !== null
                  ? `${record.faceMatchScore}%`
                  : 'N/A'}
              </span>
            </div>
          </div>

          {/* Deep Canonical Detail when available */}
          {fullDetail && (
            <div className="space-y-3 p-3 rounded-xl bg-muted/30 border border-border text-xs">
              <span className="font-mono font-bold text-[11px] text-foreground flex items-center gap-1.5">
                <FileSearch className="w-3.5 h-3.5 text-primary" />
                CANONICAL EVIDENCE &amp; EXTRACTED DATA
              </span>

              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                {fullDetail.extracted_fields && Object.keys(fullDetail.extracted_fields).length > 0 ? (
                  Object.entries(fullDetail.extracted_fields).map(([k, v]) => (
                    <div key={k} className="p-2 rounded bg-background border border-border">
                      <span className="text-[10px] text-muted-foreground uppercase block">{k.replace(/_/g, ' ')}</span>
                      <span className="font-semibold text-foreground break-all">{String(v || 'N/A')}</span>
                    </div>
                  ))
                ) : (
                  <div className="col-span-2 text-muted-foreground italic text-[11px]">
                    No OCR fields extracted or document fast-failed intake gate.
                  </div>
                )}
              </div>

              {fullDetail.reason && (
                <div className="p-2.5 rounded bg-background border border-border font-mono text-[11px] text-muted-foreground">
                  <span className="font-bold text-foreground block mb-0.5">DECISION RATIONALE</span>
                  {fullDetail.reason}
                </div>
              )}

              {fullDetail.mrz && (
                <div className="p-2.5 rounded bg-background border border-border font-mono text-[11px]">
                  <span className="font-bold text-foreground block mb-0.5">MRZ CHECKSUM TELEMETRY</span>
                  <div className="flex gap-3 text-muted-foreground">
                    <span>Valid: <strong className={fullDetail.mrz.valid ? 'text-emerald-600' : 'text-destructive'}>{fullDetail.mrz.valid ? 'PASS' : 'FAIL'}</strong></span>
                    <span>Doc #: <strong>{fullDetail.mrz.fields?.document_number || 'N/A'}</strong></span>
                    <span>Nationality: <strong>{fullDetail.mrz.fields?.nationality || 'N/A'}</strong></span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Audit Notation */}
          <div className="p-3 rounded-xl bg-muted/40 border border-border text-[11px] font-mono text-muted-foreground">
            Audit Trail // Record signed digitally by {record.officerEmail || record.examiner}. Tamper check executed in {record.processingMs}ms.
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
