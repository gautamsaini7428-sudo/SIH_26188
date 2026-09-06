import React, { useState, useMemo, useEffect, useCallback } from 'react'
import { Search, Download, ShieldCheck, AlertTriangle, XCircle, CheckCircle2, ShieldAlert, RefreshCw, Link as LinkIcon } from 'lucide-react'
import { Card, CardHeader, CardContent } from '../ui/card'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { Input } from '../ui/input'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../ui/table'
import { AnalyticsCharts } from './AnalyticsCharts'
import { CaseDetailDialog } from './CaseDetailDialog'
import { exportRecordsToCSV } from './reportingData'
import type { VerificationRecord, AuditChainVerifyResult, StatsResponse } from '../../types'
import { verifyAuditChainIntegrity, fetchVerificationHistory, fetchStats } from '../../services/api'
import { soundFX } from '../../utils/audio'

export const SupervisorConsole: React.FC = () => {
  const [records, setRecords] = useState<VerificationRecord[]>([])
  const [stats, setStats] = useState<StatsResponse | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [verdictFilter, setVerdictFilter] = useState<'ALL' | 'GENUINE' | 'SUSPICIOUS' | 'FAKE' | 'REJECTED'>('ALL')
  const [selectedRecord, setSelectedRecord] = useState<VerificationRecord | null>(null)
  const [isDialogChangeOpen, setIsDialogChangeOpen] = useState(false)
  const [isVerifyingChain, setIsVerifyingChain] = useState(false)
  const [chainVerifyResult, setChainVerifyResult] = useState<AuditChainVerifyResult | null>(null)
  const [isLiveChainLoaded, setIsLiveChainLoaded] = useState(false)

  // Fetch real verification history and operational stats
  const loadRealData = useCallback(async () => {
    try {
      // 1. Fetch real verification records from database
      const histData = await fetchVerificationHistory({
        limit: 100,
        verdict: verdictFilter !== 'ALL' ? verdictFilter : undefined,
        q: searchQuery.trim() || undefined,
      })

      if (histData && histData.items && histData.items.length > 0) {
        const mappedRecords: VerificationRecord[] = histData.items.map((item: any) => ({
          id: String(item.id),
          caseNumber: `CASE-26188-${String(item.id).padStart(3, '0')}`,
          date: item.timestamp,
          subjectName: item.extracted_name || item.filename || `Subject #${item.id}`,
          documentType: item.document_type || 'IDENTITY_DOC',
          checkpointLocation: item.checkpoint_location || 'Attari-Wagah Border',
          officerEmail: item.officer_email || 'officer@mha.gov.in',
          verdict: item.verdict as 'GENUINE' | 'SUSPICIOUS' | 'FAKE' | 'REJECTED',
          tamperingScore: item.tampering_score ?? 0,
          faceMatchScore: item.face_match_score ?? undefined,
          riskScore: item.risk_score ?? 0,
          processingMs: item.processing_time_ms ?? 950,
          examiner: item.officer_email || `Officer #${item.id}`,
        }))
        setRecords(mappedRecords)
        setIsLiveChainLoaded(true)
      } else {
        // The audit ledger does not contain the complete verification record.
        // Do not fabricate case fields or derived risk values from it.
        setRecords([])
        setIsLiveChainLoaded(false)
      }

      // 2. Fetch live stats
      const statsData = await fetchStats()
      setStats(statsData)
    } catch (err) {
      console.error('Failed to load operational data:', err)
      setRecords([])
    }
  }, [verdictFilter, searchQuery])

  useEffect(() => {
    loadRealData()
  }, [loadRealData])

  const handleVerifyChain = async () => {
    soundFX.paperSlide()
    setIsVerifyingChain(true)
    try {
      const result = await verifyAuditChainIntegrity()
      setChainVerifyResult(result)
      if (result.valid) {
        soundFX.badgeUnlock()
      } else {
        soundFX.tamperAlert()
      }
    } catch (err: any) {
      setChainVerifyResult({
        valid: false,
        entries_checked: 0,
        tampered_index: null,
        reason: err.message || 'Failed to connect to audit log verification service.',
      })
      soundFX.tamperAlert()
    } finally {
      setIsVerifyingChain(false)
    }
  }

  // Live counts
  const counts = useMemo(() => {
    if (stats) {
      return {
        GENUINE: stats.genuine,
        SUSPICIOUS: stats.suspicious,
        FAKE: stats.fake,
        REJECTED: stats.rejected,
        total: stats.total,
      }
    }
    return records.reduce(
      (acc, r) => {
        acc[r.verdict] = (acc[r.verdict] || 0) + 1
        acc.total += 1
        return acc
      },
      { GENUINE: 0, SUSPICIOUS: 0, FAKE: 0, REJECTED: 0, total: 0 }
    )
  }, [stats, records])

  // Filtered dataset
  const filteredRecords = useMemo(() => {
    return records.filter((r) => {
      if (verdictFilter !== 'ALL' && r.verdict !== verdictFilter) return false
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase()
        return (
          r.subjectName.toLowerCase().includes(q) ||
          r.caseNumber.toLowerCase().includes(q) ||
          r.documentType.toLowerCase().includes(q) ||
          (r.checkpointLocation && r.checkpointLocation.toLowerCase().includes(q)) ||
          (r.officerEmail && r.officerEmail.toLowerCase().includes(q)) ||
          r.examiner.toLowerCase().includes(q)
        )
      }
      return true
    })
  }, [records, verdictFilter, searchQuery])

  const handleRowClick = (rec: VerificationRecord) => {
    soundFX.paperSlide()
    setSelectedRecord(rec)
    setIsDialogChangeOpen(true)
  }

  const handleExport = () => {
    soundFX.paperSlide()
    exportRecordsToCSV(filteredRecords)
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Console Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl sm:text-3xl font-bold text-[var(--page-heading)] tracking-tight font-editorial">
              Supervisor Review &amp; Audit Console
            </h2>
            {isLiveChainLoaded && (
              <Badge variant="outline" className="text-[10px] bg-[#EAF0FF] dark:bg-[#1C345C] text-[#3C467B] dark:text-[#DEF4F2] border-[#636CCB]/30">
                <LinkIcon className="w-3 h-3 mr-1 inline" />
                Live SHA-256 Chain
              </Badge>
            )}
          </div>
          <p className="text-xs sm:text-sm text-[var(--page-secondary)]">
            Tamper-Evident SHA-256 Audit Trail • Real-time Border Identity Screening Analytics
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0 flex-wrap">
          <Button
            onClick={handleVerifyChain}
            disabled={isVerifyingChain}
            className="gap-2 bg-[#3C467B] dark:bg-[#334FE0] hover:bg-[#50589C] dark:hover:bg-[#3D8FD8] text-white font-bold border border-[#6E8CFB]/40 shadow-xs cursor-pointer"
          >
            {isVerifyingChain ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <ShieldCheck className="w-4 h-4 text-[#A7F3D0]" />
            )}
            <span>{isVerifyingChain ? 'Verifying Chain...' : 'Verify Chain Integrity'}</span>
          </Button>

          <Button
            onClick={handleExport}
            variant="outline"
            className="gap-2 border-[#DDE4FF] dark:border-[#1C345C] !text-[#3C467B] dark:!text-[#DEF4F2] hover:bg-[#F3F6FF] dark:hover:bg-[#111C30] font-semibold cursor-pointer"
          >
            <Download className="w-4 h-4" />
            <span>Export CSV</span>
          </Button>
        </div>
      </div>

      {/* CHAIN INTEGRITY VERIFICATION BANNER */}
      {chainVerifyResult && (
        <Card
          className={`p-4 border transition-all duration-300 animate-in fade-in-50 ${
            chainVerifyResult.valid
              ? 'bg-[#A7F3D0]/25 border-[#0B2925]/30 text-[#0B2925]'
              : 'bg-[#DC2626]/10 border-[#DC2626]/40 text-[#DC2626]'
          }`}
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-3">
              {chainVerifyResult.valid ? (
                <div className="p-2 rounded-xl bg-[#0B2925] text-[#A7F3D0] shrink-0 mt-0.5">
                  <ShieldCheck className="w-5 h-5" />
                </div>
              ) : (
                <div className="p-2 rounded-xl bg-[#DC2626] text-white shrink-0 mt-0.5">
                  <ShieldAlert className="w-5 h-5" />
                </div>
              )}
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-bold text-sm">
                    {chainVerifyResult.valid
                      ? 'Audit Chain Integrity Validated (Tamper-Proof)'
                      : 'Audit Chain Cryptographic Integrity Failed!'}
                  </span>
                  <Badge
                    variant={chainVerifyResult.valid ? 'success' : 'destructive'}
                    className="text-[10px]"
                  >
                    {chainVerifyResult.valid ? 'VALID' : 'TAMPERED'}
                  </Badge>
                </div>
                <p className="text-xs opacity-90 leading-relaxed font-mono">
                  {chainVerifyResult.reason}
                </p>
                <div className="flex items-center gap-4 pt-1 text-[11px] opacity-75 font-mono">
                  <span>Entries Verified: <strong>{chainVerifyResult.entries_checked}</strong></span>
                  {chainVerifyResult.tampered_index !== null && (
                    <span className="text-[#DC2626] font-bold">Tampered Index: #{chainVerifyResult.tampered_index}</span>
                  )}
                  <span>Genesis: <strong>0000...0000</strong></span>
                </div>
              </div>
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => setChainVerifyResult(null)}
              className="text-xs h-7 px-2 opacity-60 hover:opacity-100 cursor-pointer"
            >
              Dismiss
            </Button>
          </div>
        </Card>
      )}


      {/* STATS COUNTER CARDS */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="border-[#E5DDD8] bg-[#FFFFFF] p-4 space-y-1 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#755B73]">Total Screened</span>
            <ShieldCheck className="w-4 h-4 text-[#0B2925]" />
          </div>
          <div className="text-2xl sm:text-3xl font-bold font-mono text-[#0B2925]">{counts.total}</div>
          <span className="text-[10px] text-[#755B73] font-medium">All Border Checkpoints</span>
        </Card>

        <Card className="border-[#DDE4FF] bg-[#EAF0FF] p-4 space-y-1 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#166534]">Genuine Passed</span>
            <CheckCircle2 className="w-4 h-4 text-[#16A34A]" />
          </div>
          <div className="text-2xl sm:text-3xl font-bold font-mono text-[#16A34A]">{counts.GENUINE}</div>
          <span className="text-[10px] text-[#166534]/80 font-medium">Clearance Issued</span>
        </Card>

        <Card className="border-[#F5E6A9] bg-[#FEF3C7] p-4 space-y-1 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#92400E]">Suspicious Flagged</span>
            <AlertTriangle className="w-4 h-4 text-[#D97706]" />
          </div>
          <div className="text-2xl sm:text-3xl font-bold font-mono text-[#D97706]">{counts.SUSPICIOUS}</div>
          <span className="text-[10px] text-[#92400E]/90 font-medium">Manual Secondary Review</span>
        </Card>

        <Card className="border-[#F7CFCF] bg-[#FEE2E2] p-4 space-y-1 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[#991B1B]">Fake / Rejected</span>
            <XCircle className="w-4 h-4 text-[#DC2626]" />
          </div>
          <div className="text-2xl sm:text-3xl font-bold font-mono text-[#DC2626]">{counts.FAKE + counts.REJECTED}</div>
          <span className="text-[10px] text-[#991B1B]/90 font-medium">Entry Denied / Apprehended</span>
        </Card>
      </div>

      {/* RECHARTS METRICS VISUALIZATION */}
      <AnalyticsCharts records={records} />

      {/* FILTERABLE AUDIT TABLE */}
      <Card className="border-[#DDE4FF] dark:border-[#1C345C] bg-[#FFFFFF] dark:bg-[#111C30] overflow-hidden">
        <CardHeader className="p-4 sm:p-5 border-b border-[#DDE4FF] dark:border-[#1C345C] bg-[#F3F6FF] dark:bg-[#0C162F] flex flex-col sm:flex-row sm:items-center justify-between gap-3 space-y-0">
          <div className="relative max-w-xs w-full">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#50589C] dark:text-[#AAB6C8]" />
            <Input
              type="text"
              placeholder="Search by name, case ID, officer..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 text-xs bg-[#FFFFFF] dark:bg-[#111C30] border-[#DDE4FF] dark:border-[#1C345C] text-[#1E2550] dark:text-[#DEF4F2]"
            />
          </div>

          {/* Filter Pills */}
          <div className="flex flex-wrap items-center gap-1.5 bg-[#FFFFFF] dark:bg-[#111C30] p-1 rounded-xl border border-[#DDE4FF] dark:border-[#1C345C]">
            {(['ALL', 'GENUINE', 'SUSPICIOUS', 'FAKE', 'REJECTED'] as const).map((filter) => (
              <Button
                key={filter}
                variant={verdictFilter === filter ? 'default' : 'ghost'}
                size="sm"
                onClick={() => {
                  soundFX.paperSlide()
                  setVerdictFilter(filter)
                }}
                className={`text-xs h-7 px-2.5 cursor-pointer ${
                  verdictFilter === filter
                    ? 'bg-[#3C467B] dark:bg-[#334FE0] text-white font-bold'
                    : 'text-[#50589C] dark:text-[#AAB6C8] hover:text-[#3C467B] dark:hover:text-white'
                }`}
              >
                {filter === 'ALL' ? 'All Cases' : filter}
              </Button>
            ))}
          </div>
        </CardHeader>

        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-[#3C467B] dark:text-[#AAB6C8]">Case Ref</TableHead>
                <TableHead className="text-[#3C467B] dark:text-[#AAB6C8]">Timestamp</TableHead>
                <TableHead className="text-[#3C467B] dark:text-[#AAB6C8]">Subject Name</TableHead>
                <TableHead className="text-[#3C467B] dark:text-[#AAB6C8]">Doc Type</TableHead>
                <TableHead className="text-[#3C467B] dark:text-[#AAB6C8]">Checkpoint Location</TableHead>
                <TableHead className="text-[#3C467B] dark:text-[#AAB6C8]">Verdict</TableHead>
                <TableHead className="text-center text-[#3C467B] dark:text-[#AAB6C8]">Risk Score</TableHead>
                <TableHead className="text-center text-[#3C467B] dark:text-[#AAB6C8]">Tamper</TableHead>
                <TableHead className="text-center text-[#3C467B] dark:text-[#AAB6C8]">Face Match</TableHead>
                <TableHead className="text-right text-[#3C467B] dark:text-[#AAB6C8]">Screened By</TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {filteredRecords.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={10} className="text-center py-8 text-[#755B73] text-xs font-mono">
                    No examination records match your filter criteria.
                  </TableCell>
                </TableRow>
              ) : (
                filteredRecords.map((r) => {
                  const isGenuine = r.verdict === 'GENUINE'
                  const isSuspicious = r.verdict === 'SUSPICIOUS'
                  const isFake = r.verdict === 'FAKE'

                  return (
                    <TableRow
                      key={r.id}
                      onClick={() => handleRowClick(r)}
                      className="cursor-pointer !bg-[#636CCB] hover:!bg-[#6E8CFB] dark:!bg-[#111C30] dark:hover:!bg-[#1C345C] text-xs text-white dark:text-[#DEF4F2]"
                    >
                      <TableCell className="font-mono font-bold !text-white dark:!text-[#DEF4F2] whitespace-nowrap">
                        {r.caseNumber}
                      </TableCell>
                      <TableCell className="!text-white/85 dark:!text-[#AAB6C8] whitespace-nowrap">
                        {new Date(r.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                      </TableCell>
                      <TableCell className="font-bold !text-white dark:!text-[#DEF4F2] text-sm whitespace-nowrap">
                        {r.subjectName}
                      </TableCell>
                      <TableCell className="font-mono text-[11px] !text-white/85 dark:!text-[#AAB6C8] whitespace-nowrap">
                        {r.documentType}
                      </TableCell>
                      <TableCell className="!text-white/85 dark:!text-[#AAB6C8] whitespace-nowrap">
                        {r.checkpointLocation || 'Attari-Wagah Border'}
                      </TableCell>
                      <TableCell className="whitespace-nowrap">
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
                          className="text-[10px]"
                        >
                          {r.verdict}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-center font-mono font-bold whitespace-nowrap">
                        <span className={r.riskScore > 65 ? 'text-[#DC2626]' : r.riskScore > 30 ? 'text-[#D97706]' : 'text-[#16A34A]'}>
                          {r.riskScore}/100
                        </span>
                      </TableCell>
                      <TableCell className="text-center font-mono !text-white/85 dark:!text-[#AAB6C8] whitespace-nowrap">
                        {r.tamperingScore}/100
                      </TableCell>
                      <TableCell className="text-center font-mono !text-white/85 dark:!text-[#AAB6C8] whitespace-nowrap">
                        {r.faceMatchScore !== undefined && r.faceMatchScore !== null ? `${r.faceMatchScore}%` : 'N/A'}
                      </TableCell>
                      <TableCell className="text-right font-mono font-semibold !text-white dark:!text-[#DEF4F2] whitespace-nowrap">
                        {r.officerEmail || r.examiner}
                      </TableCell>
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Row Deep Dive Dialog */}
      <CaseDetailDialog
        record={selectedRecord}
        open={isDialogChangeOpen}
        onOpenChange={setIsDialogChangeOpen}
      />
    </div>
  )
}
