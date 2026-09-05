export type DocumentType = 'PASSPORT' | 'VISA' | 'NATIONAL_ID' | 'DRIVING_LICENSE' | 'PERMIT'
export type UserRole = 'OFFICER' | 'SUPERVISOR'

export interface UserAuth {
  email: string
  role: UserRole
  checkpointLocation: string
  token: string
}

export interface MRZResult {
  detected: boolean
  raw?: string | null
  valid?: boolean | null
  fields?: Record<string, any>
}

export interface ValidationResult {
  format_valid: boolean
  expiry_valid: boolean
  issues: string[]
  mrz_valid?: boolean | null
  mrz_details?: Record<string, any> | null
}

export interface TamperingRegion {
  x: number
  y: number
  w: number
  h: number
  field?: string
  confidence?: number
  reason?: string
}

export interface SecurityCheckItem {
  id: string
  name: string
  category: 'mrz' | 'tamper' | 'biometric' | 'crypto' | 'font'
  status: 'passed' | 'suspicious' | 'failed'
  score: number
  description: string
}

export interface QualityResult {
  status: 'GOOD' | 'LOW_QUALITY'
  score: number
  details?: string | null
}

export interface LivenessResult {
  status: 'PASS' | 'FAIL' | 'UNAVAILABLE'
  score: number
  details?: string | null
}

export interface PresentationAttackResult {
  detected: boolean
  score: number
  type?: 'SCREEN_REPLAY' | 'PRINT_ATTACK' | 'OBSTRUCTION' | string | null
  details?: string | null
}

export interface FaceMatchResult {
  status: 'MATCH' | 'NO_MATCH' | 'BORDERLINE' | 'SKIPPED'
  score?: number | null
  distance?: number | null
  threshold?: number
  details?: string | null
}

export interface BiometricResult {
  face_detected: boolean
  face_count: number
  quality: QualityResult
  liveness: LivenessResult
  presentation_attack: PresentationAttackResult
  face_match: FaceMatchResult
  status: 'VERIFIED' | 'REJECTED' | 'RETRY' | 'NEEDS_REVIEW' | 'NOT_APPLICABLE'
}

export interface IdentityLinkItem {
  historical_verification_id: number
  case_number: string
  historical_name?: string | null
  historical_document_number?: string | null
  similarity_score: number
  relationship_type: string
  recommendation: string
  details: string
}

export interface VerifyResponse {
  verification_id?: number
  document_type: DocumentType
  expected_document_type?: string
  detected_document_type?: string
  category_match?: boolean
  extracted_fields: Record<string, any>
  validation: ValidationResult
  tampering_score: number // 0 - 100
  tampering_regions: TamperingRegion[]
  heatmap_image_base64?: string
  heatmap_image_url?: string
  face_match_score?: number | null // 0 - 100
  biometric?: BiometricResult | null
  risk_score: number // 0 - 100 primary output
  risk_level?: string
  risk_factors?: string[]
  verdict: 'GENUINE' | 'SUSPICIOUS' | 'FAKE' | 'REJECTED'
  reason?: string
  security_checks?: SecurityCheckItem[]
  identity_links?: IdentityLinkItem[]
  processing_time_ms?: number
  case_number?: string
  checkpoint_location?: string
  officer_email?: string
  examiner_timestamp?: string
  mrz?: MRZResult | null
  raw_text?: string | null
}

export type ScreenMode = 'intake' | 'verifying' | 'results'
export type IntakeStep = 'step1_document' | 'step2_biometric'
export type AppView = 'dossier' | 'facematch' | 'alerts' | 'reporting'

export interface StepperStage {
  id: string
  label: string
  description: string
}

export interface DocumentFieldMarker {
  id: string
  field: string
  label: string
  value: string
  confidence: number
  box: { top: string; left: string; width: string; height: string }
  isFlagged?: boolean
}

export interface CaseAlert {
  id: string | number
  verification_id?: number
  verificationId?: number
  caseNumber: string
  subjectName: string
  verdict: 'GENUINE' | 'SUSPICIOUS' | 'FAKE' | 'REJECTED'
  reason: string
  timestamp: string
  severity: 'warning' | 'critical' | 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
  score: number
  read: boolean
  status?: 'UNREVIEWED' | 'REVIEWED' | 'RESOLVED' | 'ESCALATED'
  title?: string
  message?: string
  documentType?: string
  documentNumber?: string
  officerEmail?: string
  checkpoint?: string
  tamperingScore?: number
  faceScore?: number
  details?: string[]
  reviewedAt?: string
  reviewedBy?: string
  reviewNotes?: string
  resolvedAt?: string
}

export interface VerificationRecord {
  id: string
  caseNumber: string
  date: string
  subjectName: string
  documentType: string
  checkpointLocation?: string
  officerEmail?: string
  verdict: 'GENUINE' | 'SUSPICIOUS' | 'FAKE' | 'REJECTED'
  tamperingScore: number
  faceMatchScore?: number
  riskScore: number
  processingMs: number
  examiner: string
}

export interface AuditLogRecordData {
  document_id: string
  verdict: 'VERIFIED' | 'SUSPECTED' | 'REJECTED' | 'ERROR'
  tampering_score: number
  face_match_score: number
  timestamp: string
}

export interface AuditLogEntry {
  index: number
  timestamp: string
  record: AuditLogRecordData
  previous_hash: string
  hash: string
}

export interface AuditChainVerifyResult {
  valid: boolean
  entries_checked: number
  tampered_index: number | null
  reason: string
}

export interface FaceVerifyApiResponse {
  status: 'matched' | 'not_matched' | 'no_face_detected' | 'multiple_faces_detected' | 'error'
  score: number
  matched: boolean
  distance?: number | null
  threshold: number
  detail: string
}

export interface DailyVolumePoint {
  day: string
  count: number
  date?: string
}

export interface StatsResponse {
  genuine: number
  suspicious: number
  fake: number
  rejected: number
  total: number
  high_risk: number
  avg_processing_time_ms: number
  by_document_type: Record<string, number>
  by_checkpoint: Record<string, number>
  daily_volume: DailyVolumePoint[]
  alerts_total: number
  alerts_resolved: number
  period_from?: string | null
  period_to?: string | null
}

