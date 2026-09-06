import type {
  VerifyResponse,
  DocumentType,
  UserAuth,
  AuditLogEntry,
  AuditChainVerifyResult,
  FaceVerifyApiResponse,
  StatsResponse,
} from '../types'

const API_BASE_URL = (import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '')

let currentAuthToken: string | null = null

export function setAuthToken(token: string | null) {
  currentAuthToken = token
}

export function getAuthToken(): string | null {
  return currentAuthToken
}

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 5000)
    const res = await fetch(`${API_BASE_URL}/health`, { signal: controller.signal })
    clearTimeout(timeoutId)
    if (res.ok) {
      const data = await res.json()
      return data.status === 'ok'
    }
    return false
  } catch {
    return false
  }
}

export async function loginUser(email: string, password_str: string): Promise<UserAuth> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password: password_str }),
  })

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}))
    throw new Error(errData.detail || errData.message || 'Invalid email or password credentials')
  }

  const data = await response.json()
  const user = data.user
  const token = data.access_token

  setAuthToken(token)

  return {
    email: user.email,
    role: user.role,
    checkpointLocation: user.checkpoint_location || 'Attari-Wagah Border',
    token,
  }
}

export async function verifyDocument(
  file: File | null,
  selfie: File | null = null,
  documentType: DocumentType = 'DRIVING_LICENSE'
): Promise<VerifyResponse> {
  if (!file) {
    throw new Error('No document file uploaded. Please upload a document to proceed.')
  }

  const formData = new FormData()
  formData.append('file', file)
  formData.append('document_type', documentType)
  if (selfie && documentType !== 'VISA') {
    formData.append('selfie', selfie)
  }

  const headers: Record<string, string> = {}
  if (currentAuthToken) {
    headers['Authorization'] = `Bearer ${currentAuthToken}`
  }

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}/verify-document`, {
      method: 'POST',
      headers,
      body: formData,
    })
  } catch {
    throw new Error('Verification backend is unavailable.')
  }

  if (response.ok) {
    const data: VerifyResponse = await response.json()
    return data
  }

  if (response.status === 401) {
    throw new Error('Authentication required. Please log in again.')
  }

  if (response.status === 403) {
    throw new Error('Access denied: Officer role required for document verification.')
  }

  if (response.status === 502 || response.status === 503 || response.status === 504) {
    throw new Error('Verification backend is unavailable.')
  }

  if (response.status >= 500) {
    throw new Error('Verification failed due to a server error.')
  }

  const errData = await response.json().catch(() => ({}))
  const detailMsg = String(errData.detail || errData.message || errData.error || '').toLowerCase()

  if (detailMsg.includes('ocr') || detailMsg.includes('extract') || detailMsg.includes('text')) {
    throw new Error('Unable to extract document information.')
  }
  if (detailMsg.includes('mismatch') || detailMsg.includes('category') || detailMsg.includes('document type')) {
    throw new Error('Selected document category does not match detected document.')
  }
  if (detailMsg.includes('invalid') || response.status === 422 || response.status === 400) {
    throw new Error(errData.detail || 'Invalid document request.')
  }

  throw new Error('Verification failed due to a server error.')
}

export async function getVerificationById(verificationId: number): Promise<VerifyResponse> {
  const headers: Record<string, string> = {}
  if (currentAuthToken) {
    headers['Authorization'] = `Bearer ${currentAuthToken}`
  }

  const response = await fetch(`${API_BASE_URL}/verification/${verificationId}`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}))
    throw new Error(errData.detail || `Failed to fetch verification #${verificationId}`)
  }

  return await response.json()
}

// ─── Vidyut AI Assistant ────────────────────────────────────────────────────

export interface VidyutCaseContext {
  case_number?: string
  document_type?: string
  verdict?: string
  risk_score?: number
  tampering_score?: number
  face_match_confidence?: number
  face_match_verdict?: string
  validation_issues?: string[]
  extracted_fields?: Record<string, unknown>
  reason?: string
  checkpoint_location?: string
}

export interface VidyutChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export interface VidyutAssistResponse {
  answer: string
  suggested_followups: string[]
  context_badge: string | null
}

export async function askVidyutAssistant(
  question: string,
  screen: string,
  caseData?: VidyutCaseContext,
  history?: VidyutChatMessage[],
): Promise<VidyutAssistResponse> {
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 12000)

    const res = await fetch(`${API_BASE_URL}/vidyut-assist`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(currentAuthToken ? { Authorization: `Bearer ${currentAuthToken}` } : {}),
      },
      body: JSON.stringify({
        question,
        screen,
        case_data: caseData ?? null,
        history: history ?? [],
      }),
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    if (!res.ok) {
      throw new Error(`Assistant API returned ${res.status}`)
    }

    return await res.json()
  } catch {
    // Graceful fallback
    return {
      answer:
        "I'm temporarily offline but will be back shortly. In the meantime:\n\n" +
        '• For **FAKE** verdicts: hold document and escalate to Supervisor via the Alerts tab.\n' +
        '• For **MRZ errors**: request the physical document and inspect tactile microprinting.\n' +
        '• For **intake issues**: ensure the document is fully in-frame with diffuse lighting.',
      suggested_followups: [
        'Explain Risk Score & Verdicts',
        'What MRZ checksum error means',
        'How to escalate to supervisor',
      ],
      context_badge: `Screen: ${screen}`,
    }
  }
}

// ─── Tamper-Evident SHA-256 Audit Log ──────────────────────────────────────

export async function fetchAuditLog(): Promise<AuditLogEntry[]> {
  const headers: Record<string, string> = {}
  if (currentAuthToken) {
    headers['Authorization'] = `Bearer ${currentAuthToken}`
  }

  const response = await fetch(`${API_BASE_URL}/audit-log`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to fetch audit log')
  }

  return await response.json()
}

export async function verifyAuditChainIntegrity(): Promise<AuditChainVerifyResult> {
  const headers: Record<string, string> = {}
  if (currentAuthToken) {
    headers['Authorization'] = `Bearer ${currentAuthToken}`
  }

  const response = await fetch(`${API_BASE_URL}/audit-log/verify`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to verify audit chain integrity')
  }

  return await response.json()
}

// ─── Real Security Alerts API ──────────────────────────────────────────────

export interface AlertApiItem {
  id: number
  verification_id: number | null
  case_number: string
  severity: string
  status: string
  title: string
  message: string
  document_number: string | null
  person_name: string | null
  document_type: string | null
  officer_email: string | null
  checkpoint: string | null
  risk_score: number | null
  verdict: string | null
  face_score: number | null
  tampering_score: number | null
  details: string[]
  created_at: string
  reviewed_at: string | null
  reviewed_by: string | null
  review_notes: string | null
  resolved_at: string | null
}

export interface AlertApiResponse {
  items: AlertApiItem[]
  total: number
  unreviewed_count: number
  critical_count: number
  high_count: number
  resolved_count: number
}

export async function fetchAlerts(params?: {
  status?: string
  severity?: string
  checkpoint?: string
  verification_id?: number
  page?: number
  limit?: number
}): Promise<AlertApiResponse> {
  const query = new URLSearchParams()
  if (params?.status) query.set('status', params.status)
  if (params?.severity) query.set('severity', params.severity)
  if (params?.checkpoint) query.set('checkpoint', params.checkpoint)
  if (params?.verification_id) query.set('verification_id', String(params.verification_id))
  if (params?.page) query.set('page', String(params.page))
  if (params?.limit) query.set('limit', String(params.limit))

  const headers: Record<string, string> = {}
  if (currentAuthToken) {
    headers['Authorization'] = `Bearer ${currentAuthToken}`
  }

  const response = await fetch(`${API_BASE_URL}/alerts?${query.toString()}`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to fetch alerts')
  }

  return await response.json()
}

export async function fetchAlertDetail(alertId: number): Promise<AlertApiItem> {
  const headers: Record<string, string> = {}
  if (currentAuthToken) {
    headers['Authorization'] = `Bearer ${currentAuthToken}`
  }

  const response = await fetch(`${API_BASE_URL}/alerts/${alertId}`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to fetch alert #${alertId}`)
  }

  return await response.json()
}

export async function reviewAlert(
  alertId: number,
  status: 'REVIEWED' | 'RESOLVED' | 'ESCALATED' | 'UNREVIEWED',
  notes?: string
): Promise<AlertApiItem> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (currentAuthToken) {
    headers['Authorization'] = `Bearer ${currentAuthToken}`
  }

  const response = await fetch(`${API_BASE_URL}/alerts/${alertId}/review`, {
    method: 'PATCH',
    headers,
    body: JSON.stringify({ status, notes: notes || null }),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || `Failed to update review for alert #${alertId}`)
  }

  return await response.json()
}

export async function markAllAlertsRead(): Promise<void> {
  const headers: Record<string, string> = {}
  if (currentAuthToken) {
    headers['Authorization'] = `Bearer ${currentAuthToken}`
  }

  const response = await fetch(`${API_BASE_URL}/alerts/mark-all-read`, {
    method: 'POST',
    headers,
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to mark alerts as read')
  }
}

export async function verifyFace(
  idFile: File | Blob,
  selfieFile: File | Blob
): Promise<FaceVerifyApiResponse> {
  const formData = new FormData()
  if (idFile instanceof File) {
    formData.append('id_file', idFile)
  } else {
    formData.append('id_file', idFile, 'id_document.jpg')
  }

  if (selfieFile instanceof File) {
    formData.append('selfie_file', selfieFile)
  } else {
    formData.append('selfie_file', selfieFile, 'selfie_capture.jpg')
  }

  const headers: Record<string, string> = {}
  if (currentAuthToken) {
    headers['Authorization'] = `Bearer ${currentAuthToken}`
  }

  const response = await fetch(`${API_BASE_URL}/verify/face`, {
    method: 'POST',
    headers,
    body: formData,
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || 'Face verification analysis failed')
  }

  return await response.json()
}

export async function fetchStats(params?: {
  date_from?: string
  date_to?: string
}): Promise<StatsResponse> {
  const query = new URLSearchParams()
  if (params?.date_from) query.set('date_from', params.date_from)
  if (params?.date_to) query.set('date_to', params.date_to)

  const headers: Record<string, string> = {}
  if (currentAuthToken) {
    headers['Authorization'] = `Bearer ${currentAuthToken}`
  }

  const response = await fetch(`${API_BASE_URL}/stats?${query.toString()}`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to fetch operational stats')
  }

  return await response.json()
}

export async function fetchVerificationHistory(params?: {
  verdict?: string
  document_type?: string
  checkpoint_location?: string
  officer_email?: string
  q?: string
  date_from?: string
  date_to?: string
  page?: number
  limit?: number
}): Promise<{ items: any[]; total: number; page: number; limit: number; total_pages: number }> {
  const query = new URLSearchParams()
  if (params?.verdict && params.verdict !== 'ALL') query.set('verdict', params.verdict)
  if (params?.document_type && params.document_type !== 'ALL') query.set('document_type', params.document_type)
  if (params?.checkpoint_location) query.set('checkpoint_location', params.checkpoint_location)
  if (params?.officer_email) query.set('officer_email', params.officer_email)
  if (params?.q) query.set('q', params.q)
  if (params?.date_from) query.set('date_from', params.date_from)
  if (params?.date_to) query.set('date_to', params.date_to)
  if (params?.page) query.set('page', String(params.page))
  if (params?.limit) query.set('limit', String(params.limit))

  const headers: Record<string, string> = {}
  if (currentAuthToken) {
    headers['Authorization'] = `Bearer ${currentAuthToken}`
  }

  const response = await fetch(`${API_BASE_URL}/history?${query.toString()}`, {
    method: 'GET',
    headers,
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to fetch verification history')
  }

  return await response.json()
}



