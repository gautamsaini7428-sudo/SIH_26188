import { useState, type FC } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  AlertTriangle,
  XCircle,
  ChevronDown,
  ChevronUp,
  CheckCheck,
  Clock,
  ShieldAlert,
  UserCheck,
  FileSearch,
  CheckCircle2,
  Lock,
} from 'lucide-react'
import type { CaseAlert, UserAuth } from '../../types'
import { soundFX } from '../../utils/audio'
import { Card } from '../ui/card'
import { Badge } from '../ui/badge'
import { Button } from '../ui/button'

interface AlertHistoryListProps {
  alerts: CaseAlert[]
  currentUser?: UserAuth | null
  onMarkAllRead: () => void
  onInspect?: (alert: CaseAlert) => void
  onReviewAlert?: (alertId: number, status: 'REVIEWED' | 'RESOLVED' | 'ESCALATED', notes?: string) => Promise<void>
}

export const AlertHistoryList: FC<AlertHistoryListProps> = ({
  alerts,
  currentUser,
  onMarkAllRead,
  onInspect,
  onReviewAlert,
}) => {
  const [expandedId, setExpandedId] = useState<string | number | null>(null)
  const [filter, setFilter] = useState<'all' | 'unreviewed' | 'critical' | 'high' | 'resolved'>('all')
  const [notesState, setNotesState] = useState<Record<string, string>>({})
  const [isSubmitting, setIsSubmitting] = useState<Record<string, boolean>>({})

  const isSupervisor = currentUser?.role === 'SUPERVISOR'

  const filtered = alerts.filter((a) => {
    const sev = (a.severity || '').toLowerCase()
    const stat = (a.status || 'UNREVIEWED').toUpperCase()

    if (filter === 'unreviewed') return stat === 'UNREVIEWED'
    if (filter === 'critical') return sev === 'critical'
    if (filter === 'high') return sev === 'high' || sev === 'critical'
    if (filter === 'resolved') return stat === 'RESOLVED'
    return true
  })

  const toggleRow = (id: string | number) => {
    soundFX.paperSlide()
    setExpandedId((prev) => (prev === id ? null : id))
  }

  const handleReviewAction = async (alertId: number, status: 'REVIEWED' | 'RESOLVED' | 'ESCALATED') => {
    if (!onReviewAlert) return
    const key = String(alertId)
    setIsSubmitting((prev) => ({ ...prev, [key]: true }))
    try {
      soundFX.paperSlide()
      await onReviewAlert(alertId, status, notesState[key] || undefined)
      if (status === 'RESOLVED') {
        soundFX.badgeUnlock()
      } else if (status === 'ESCALATED') {
        soundFX.tamperAlert()
      }
    } finally {
      setIsSubmitting((prev) => ({ ...prev, [key]: false }))
    }
  }

  const getSeverityBadge = (severity: string) => {
    const s = severity.toUpperCase()
    if (s === 'CRITICAL') {
      return (
        <Badge variant="destructive" className="text-[9.5px] bg-[#8A2323] text-white">
          CRITICAL
        </Badge>
      )
    }
    if (s === 'HIGH') {
      return (
        <Badge variant="warning" className="text-[9.5px] bg-[#A25A38] text-white">
          HIGH RISK
        </Badge>
      )
    }
    if (s === 'MEDIUM' || s === 'WARNING') {
      return (
        <Badge variant="warning" className="text-[9.5px] bg-[#755B73] text-white">
          SUSPICIOUS
        </Badge>
      )
    }
    return (
      <Badge variant="outline" className="text-[9.5px] bg-[#A7F3D0]/40 text-[#0B2925] border-[#0B2925]/30">
        LOW RISK
      </Badge>
    )
  }

  const getStatusBadge = (status?: string) => {
    const st = (status || 'UNREVIEWED').toUpperCase()
    if (st === 'RESOLVED') {
      return (
        <Badge variant="outline" className="text-[9.5px] bg-[#A7F3D0]/30 text-[#0B2925] border-[#0B2925]/40 font-mono">
          RESOLVED
        </Badge>
      )
    }
    if (st === 'ESCALATED') {
      return (
        <Badge variant="destructive" className="text-[9.5px] bg-[#8A2323]/20 text-[#8A2323] border border-[#8A2323]/40 font-mono">
          ESCALATED
        </Badge>
      )
    }
    if (st === 'REVIEWED') {
      return (
        <Badge variant="outline" className="text-[9.5px] bg-[#EBE0E9] text-[#755B73] border-[#755B73]/30 font-mono">
          REVIEWED
        </Badge>
      )
    }
    return (
      <Badge variant="outline" className="text-[9.5px] bg-[#FFF2F2] text-[#8A2323] border-[#8A2323]/30 font-mono animate-pulse">
        UNREVIEWED
      </Badge>
    )
  }

  return (
    <Card className="rounded-2xl overflow-hidden border-[#E5DDD8] bg-[#FFFFFF] shadow-xs">
      {/* Header Bar */}
      <div className="p-4 sm:p-5 border-b border-[#E5DDD8] flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-[#FCFAF8]">
        <div>
          <h3 className="font-editorial text-base sm:text-lg font-bold text-[#27212B]">
            Flagged Case Records Registry
          </h3>
          <p className="text-xs text-[#755B73] font-sans">
            Live database feed of automated security alerts and supervisor oversight dispositions.
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center bg-[#FFFFFF] p-1 rounded-xl border border-[#E5DDD8] text-xs flex-wrap">
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1 rounded-lg font-semibold transition-all cursor-pointer ${
                filter === 'all'
                  ? 'bg-[#A7F3D0] text-[#0B2925] shadow-2xs'
                  : 'text-[#755B73] hover:text-[#27212B]'
              }`}
            >
              All ({alerts.length})
            </button>
            <button
              onClick={() => setFilter('unreviewed')}
              className={`px-3 py-1 rounded-lg font-semibold transition-all cursor-pointer ${
                filter === 'unreviewed'
                  ? 'bg-[#FFF2F2] text-[#8A2323] shadow-2xs'
                  : 'text-[#755B73] hover:text-[#8A2323]'
              }`}
            >
              Pending ({alerts.filter((a) => (a.status || 'UNREVIEWED') === 'UNREVIEWED').length})
            </button>
            <button
              onClick={() => setFilter('critical')}
              className={`px-3 py-1 rounded-lg font-semibold transition-all cursor-pointer ${
                filter === 'critical'
                  ? 'bg-[#FBDADA] text-[#8A2323] shadow-2xs'
                  : 'text-[#755B73] hover:text-[#8A2323]'
              }`}
            >
              Critical ({alerts.filter((a) => (a.severity || '').toLowerCase() === 'critical').length})
            </button>
            <button
              onClick={() => setFilter('resolved')}
              className={`px-3 py-1 rounded-lg font-semibold transition-all cursor-pointer ${
                filter === 'resolved'
                  ? 'bg-[#A7F3D0]/60 text-[#0B2925] shadow-2xs'
                  : 'text-[#755B73] hover:text-[#0B2925]'
              }`}
            >
              Resolved ({alerts.filter((a) => a.status === 'RESOLVED').length})
            </button>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={onMarkAllRead}
            className="gap-1 text-xs border-[#E5DDD8] text-[#755B73] hover:text-[#27212B] bg-[#FFFFFF] hover:bg-[#F8F5F3] cursor-pointer"
          >
            <CheckCheck className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Acknowledge All</span>
          </Button>
        </div>
      </div>

      {/* List Rows */}
      {filtered.length === 0 ? (
        <div className="p-12 text-center text-xs text-[#755B73] font-sans">
          No security alerts found in this category.
        </div>
      ) : (
        <div className="divide-y divide-[#E5DDD8]">
          {filtered.map((alert, idx) => {
            const isExpanded = expandedId === alert.id
            const sev = (alert.severity || '').toLowerCase()
            const isCritical = sev === 'critical'
            const numericId = typeof alert.id === 'number' ? alert.id : parseInt(String(alert.id).replace(/\D/g, ''), 10) || 0

            return (
              <motion.div
                key={alert.id}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.02 }}
                className={`transition-colors ${isExpanded ? 'bg-[#FCFAF8]' : 'hover:bg-[#FCFAF8]/60'}`}
              >
                <div
                  onClick={() => toggleRow(alert.id)}
                  className="p-4 flex items-center justify-between gap-3 cursor-pointer select-none"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="shrink-0">
                      {isCritical ? (
                        <XCircle className="w-4 h-4 text-[#8A2323]" />
                      ) : (
                        <AlertTriangle className="w-4 h-4 text-[#755B73]" />
                      )}
                    </div>

                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono text-[11px] font-bold text-[#0B2925]">
                          {alert.caseNumber}
                        </span>
                        {getSeverityBadge(alert.severity)}
                        {getStatusBadge(alert.status)}
                        {alert.status === 'UNREVIEWED' && (
                          <span className="w-1.5 h-1.5 rounded-full bg-[#8A2323]" />
                        )}
                      </div>
                      <div className="font-editorial text-sm font-bold text-[#27212B] truncate mt-0.5">
                        {alert.subjectName || alert.title || 'Security Anomaly'}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 shrink-0">
                    <div className="text-right hidden sm:block">
                      <span className="text-[11px] font-mono text-[#755B73] flex items-center gap-1 justify-end">
                        <Clock className="w-3 h-3" />
                        {alert.timestamp}
                      </span>
                      <span className="text-[10px] text-[#755B73] block">
                        Risk Score: <strong className="text-[#27212B]">{alert.score}/100</strong>
                      </span>
                    </div>

                    <div className="text-[#755B73]">
                      {isExpanded ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )}
                    </div>
                  </div>
                </div>

                {/* Expanded Anomaly Detail & Supervisor Review Section */}
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden border-t border-[#E5DDD8] bg-[#FFFFFF] px-4 sm:px-6 py-4 space-y-4 text-xs"
                    >
                      {/* Alert Metadata Grid */}
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-[#FCFAF8] p-3 rounded-xl border border-[#E5DDD8] text-[11px]">
                        <div>
                          <span className="text-[#755B73] block text-[10px] uppercase font-semibold">Document Type</span>
                          <span className="font-medium text-[#27212B]">{alert.documentType || 'IDENTITY_DOC'}</span>
                        </div>
                        <div>
                          <span className="text-[#755B73] block text-[10px] uppercase font-semibold">Document Number</span>
                          <span className="font-mono font-medium text-[#27212B]">{alert.documentNumber || 'N/A'}</span>
                        </div>
                        <div>
                          <span className="text-[#755B73] block text-[10px] uppercase font-semibold">Checkpoint</span>
                          <span className="font-medium text-[#27212B] truncate block">{alert.checkpoint || 'Attari-Wagah'}</span>
                        </div>
                        <div>
                          <span className="text-[#755B73] block text-[10px] uppercase font-semibold">Screening Officer</span>
                          <span className="font-mono text-[#27212B] truncate block">{alert.officerEmail || 'officer@mha.gov.in'}</span>
                        </div>
                      </div>

                      {/* Forensic Indicators */}
                      <div>
                        <span className="text-[10px] uppercase font-bold text-[#755B73] block mb-1">
                          Forensic Anomaly Details &amp; Indicators:
                        </span>
                        {alert.details && alert.details.length > 0 ? (
                          <ul className="space-y-1 bg-[#FFFDFB] p-2.5 rounded-lg border border-[#E5DDD8]">
                            {alert.details.map((indicator, i) => (
                              <li key={i} className="flex items-start gap-2 text-[#27212B] font-sans">
                                <span className="text-[#8A2323] font-bold">•</span>
                                <span>{indicator}</span>
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-[#27212B] leading-relaxed bg-[#FFFDFB] p-2.5 rounded-lg border border-[#E5DDD8]">
                            {alert.reason || alert.message}
                          </p>
                        )}
                      </div>

                      {/* Historical Review Disposition Info if present */}
                      {alert.reviewedBy && (
                        <div className="bg-[#EBE0E9]/30 p-3 rounded-xl border border-[#755B73]/20 space-y-1 text-[11px]">
                          <div className="flex items-center justify-between text-[#755B73]">
                            <span className="font-semibold flex items-center gap-1">
                              <UserCheck className="w-3.5 h-3.5 text-[#0B2925]" />
                              Supervisor Disposition Logged:
                            </span>
                            <span className="font-mono text-[10px]">{alert.reviewedAt || 'Recorded'}</span>
                          </div>
                          <div className="text-[#27212B]">
                            <strong>Reviewer:</strong> {alert.reviewedBy} • <strong>Status:</strong> {alert.status}
                          </div>
                          {alert.reviewNotes && (
                            <div className="text-[#755B73] italic">
                              &ldquo;{alert.reviewNotes}&rdquo;
                            </div>
                          )}
                        </div>
                      )}

                      {/* Supervisor Review Action Panel */}
                      <div className="pt-2 border-t border-[#E5DDD8] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        {onInspect && (
                          <Button
                            onClick={() => onInspect(alert)}
                            variant="outline"
                            size="sm"
                            className="border-[#E5DDD8] text-[#0B2925] hover:bg-[#F8F5F3] text-xs font-semibold cursor-pointer gap-1.5 self-start"
                          >
                            <FileSearch className="w-3.5 h-3.5" />
                            Open Verification Record
                          </Button>
                        )}

                        {isSupervisor ? (
                          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 flex-1 sm:justify-end">
                            <input
                              type="text"
                              placeholder="Supervisor disposition notes..."
                              value={notesState[String(alert.id)] || ''}
                              onChange={(e) =>
                                setNotesState((prev) => ({ ...prev, [String(alert.id)]: e.target.value }))
                              }
                              className="px-3 py-1.5 text-xs rounded-lg border border-[#E5DDD8] bg-white text-[#27212B] focus:outline-none focus:border-[#0B2925]"
                            />
                            <div className="flex items-center gap-1.5 flex-wrap">
                              <Button
                                size="sm"
                                disabled={isSubmitting[String(alert.id)]}
                                onClick={() => handleReviewAction(numericId, 'REVIEWED')}
                                variant="outline"
                                className="border-[#755B73]/30 text-[#755B73] hover:bg-[#EBE0E9]/50 text-xs font-semibold cursor-pointer"
                              >
                                Mark Reviewed
                              </Button>
                              <Button
                                size="sm"
                                disabled={isSubmitting[String(alert.id)]}
                                onClick={() => handleReviewAction(numericId, 'RESOLVED')}
                                className="bg-[#0B2925] hover:bg-[#133D37] text-white text-xs font-semibold cursor-pointer gap-1"
                              >
                                <CheckCircle2 className="w-3 h-3" />
                                Resolve / Clear
                              </Button>
                              <Button
                                size="sm"
                                disabled={isSubmitting[String(alert.id)]}
                                onClick={() => handleReviewAction(numericId, 'ESCALATED')}
                                className="bg-[#8A2323] hover:bg-[#6D1B1B] text-white text-xs font-semibold cursor-pointer gap-1"
                              >
                                <ShieldAlert className="w-3 h-3" />
                                Escalate
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <div className="text-[11px] text-[#755B73] flex items-center gap-1">
                            <Lock className="w-3 h-3" />
                            <span>Supervisor access required to record review dispositions.</span>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            )
          })}
        </div>
      )}
    </Card>
  )
}
