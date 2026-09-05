import type { VerificationRecord } from '../../types'

// ── DEMO DATA: Historical records for Supervisor Console reporting UI ──────────
// These are static/illustrative records displayed in the Supervisor Console.
// They are NOT connected to the real document upload or OCR pipeline.
// Real verifications are fetched from the backend /history endpoint.
export const HISTORICAL_RECORDS: VerificationRecord[] = [
  {
    id: 'rec-01',
    caseNumber: 'CASE-26188-01',
    date: '2026-09-02T10:45:00Z',
    subjectName: 'Rajesh Kumar',
    documentType: 'PASSPORT',
    checkpointLocation: 'Attari-Wagah Border',
    verdict: 'GENUINE',
    tamperingScore: 4,
    faceMatchScore: 97,
    riskScore: 3,
    processingMs: 1240,
    examiner: 'EX-941',
  },
  {
    id: 'rec-02',
    caseNumber: 'CASE-26188-02',
    date: '2026-09-02T10:30:00Z',
    subjectName: 'Priya Sharma',
    documentType: 'VISA',
    checkpointLocation: 'Petrapole-Benapole Crossing',
    verdict: 'GENUINE',
    tamperingScore: 8,
    faceMatchScore: undefined,
    riskScore: 6,
    processingMs: 980,
    examiner: 'EX-941',
  },
  {
    id: 'rec-03',
    caseNumber: 'CASE-26188-03',
    date: '2026-09-02T09:55:00Z',
    subjectName: 'David M. Vance',
    documentType: 'NATIONAL_ID',
    checkpointLocation: 'Moreh ICP',
    verdict: 'SUSPICIOUS',
    tamperingScore: 52,
    faceMatchScore: 58,
    riskScore: 43,
    processingMs: 1480,
    examiner: 'EX-802',
  },
  {
    id: 'rec-04',
    caseNumber: 'CASE-26188-04',
    date: '2026-09-02T09:12:00Z',
    subjectName: 'Alexander Reed',
    documentType: 'PERMIT',
    checkpointLocation: 'Raxaul Border Post',
    verdict: 'FAKE',
    tamperingScore: 89,
    faceMatchScore: 14,
    riskScore: 91,
    processingMs: 1890,
    examiner: 'EX-802',
  },
  {
    id: 'rec-05',
    caseNumber: 'CASE-26188-05',
    date: '2026-09-02T08:40:00Z',
    subjectName: 'Sarah L. Jenkins',
    documentType: 'DRIVING_LICENSE',
    checkpointLocation: 'Attari-Wagah Border',
    verdict: 'GENUINE',
    tamperingScore: 3,
    faceMatchScore: 98,
    riskScore: 2,
    processingMs: 1050,
    examiner: 'EX-419',
  },
  {
    id: 'rec-06',
    caseNumber: 'CASE-26188-06',
    date: '2026-09-02T08:15:00Z',
    subjectName: 'Sunita Devi',
    documentType: 'NATIONAL_ID',
    checkpointLocation: 'Dawki-Tamabil Gate',
    verdict: 'REJECTED',
    tamperingScore: 0,
    faceMatchScore: undefined,
    riskScore: 100,
    processingMs: 320,
    examiner: 'EX-802',
  },
]

export function exportRecordsToCSV(records: VerificationRecord[]) {
  const headers = [
    'Case Number',
    'Timestamp',
    'Subject Name',
    'Document Type',
    'Checkpoint Location',
    'Verdict',
    'Risk Score (0-100)',
    'Tampering Score (0-100)',
    'Face Match (%)',
    'Processing Time (ms)',
    'Examiner ID',
  ]

  const csvRows = records.map((r) => [
    `"${r.caseNumber}"`,
    `"${r.date}"`,
    `"${r.subjectName.replace(/"/g, '""')}"`,
    `"${r.documentType}"`,
    `"${r.checkpointLocation || 'N/A'}"`,
    `"${r.verdict}"`,
    r.riskScore,
    r.tamperingScore,
    r.faceMatchScore ?? 'N/A',
    r.processingMs,
    `"${r.examiner}"`,
  ])

  const csvContent = [headers.join(','), ...csvRows.map((row) => row.join(','))].join('\n')

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `border_identity_screening_log_${new Date().toISOString().split('T')[0]}.csv`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
