import { useState, useEffect, type FC } from 'react'
import { StatsHeader } from './StatsHeader'
import { VerificationTable } from './VerificationTable'
import type { VerificationRecord, StatsResponse } from '../../types'
import { fetchVerificationHistory, fetchStats } from '../../services/api'

interface ReportingViewProps {
  records?: VerificationRecord[]
}

export const ReportingView: FC<ReportingViewProps> = ({ records: initialRecords }) => {
  const [records, setRecords] = useState<VerificationRecord[]>(initialRecords || [])
  const [stats, setStats] = useState<StatsResponse | null>(null)

  useEffect(() => {
    if (!initialRecords || initialRecords.length === 0) {
      Promise.all([
        fetchVerificationHistory({ limit: 50 }),
        fetchStats(),
      ])
        .then(([histData, statsData]) => {
          if (histData && histData.items) {
            const mapped: VerificationRecord[] = histData.items.map((item: any) => ({
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
            setRecords(mapped)
          }
          if (statsData) {
            setStats(statsData)
          }
        })
        .catch((err) => console.error('Error loading reporting data:', err))
    }
  }, [initialRecords])

  const totalCount = stats ? stats.total : records.length
  const genuineCount = stats ? stats.genuine : records.filter((r) => r.verdict === 'GENUINE').length
  const suspiciousCount = stats ? stats.suspicious : records.filter((r) => r.verdict === 'SUSPICIOUS').length
  const fakeCount = stats ? stats.fake + stats.rejected : records.filter((r) => r.verdict === 'FAKE' || r.verdict === 'REJECTED').length

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-6">
      {/* Page Header */}
      <div className="space-y-1 pb-4 border-b border-[#E3DCD6]">
        <h2 className="font-editorial text-2xl sm:text-3xl font-bold text-[#0B2925]">
          Verification Registry &amp; Audit Log
        </h2>
        <p className="text-xs sm:text-sm text-[#6E6571] font-sans">
          Centralized administrative record of all document screenings, tampering metrics, and biometric decisions.
        </p>
      </div>

      {/* 1. Animated Stats KPI Header */}
      <StatsHeader
        totalCount={totalCount}
        genuineCount={genuineCount}
        suspiciousCount={suspiciousCount}
        fakeCount={fakeCount}
      />

      {/* 2. Searchable, Filterable Table with CSV Export */}
      <VerificationTable records={records} />
    </div>
  )
}

