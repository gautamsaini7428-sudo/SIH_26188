import { useState, useCallback, useEffect } from 'react'
import { Switch, Route, Redirect, useLocation } from 'wouter'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster, toast } from 'sonner'
import { ThemeProvider } from './context/ThemeContext'
import { Header } from './components/Common/Header'
import { DocumentIntake } from './components/Intake/DocumentIntake'
import { WebcamCapture } from './components/Intake/WebcamCapture'
import { VerificationProgress } from './components/Verification/VerificationProgress'
import { ResultsView } from './components/Verification/ResultsView'
import { FaceMatchView } from './components/FaceMatch/FaceMatchView'
import { AlertsView } from './components/Alerts/AlertsView'
import { SupervisorConsole } from './components/Reporting/SupervisorConsole'
import { LoginScreen } from './components/Auth/LoginScreen'
import { HomePage } from './pages/HomePage'
import { VidyutAssistant, type VidyutScreen } from './components/VidyutAI/VidyutAssistant'
import type { VerifyResponse, DocumentType, UserAuth, CaseAlert } from './types'
import {
  verifyDocument,
  getVerificationById,
  setAuthToken,
  fetchAlerts,
  reviewAlert,
  markAllAlertsRead,
} from './services/api'
import { soundFX } from './utils/audio'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function MainApp() {
  const [location, setLocation] = useLocation()

  // Auth State
  const [currentUser, setCurrentUser] = useState<UserAuth | null>(() => {
    try {
      const saved = localStorage.getItem('sih_user_auth')
      if (saved) {
        const parsed: UserAuth = JSON.parse(saved)
        setAuthToken(parsed.token)
        return parsed
      }
    } catch {
      localStorage.removeItem('sih_user_auth')
    }
    return null
  })

  // Intake State
  const [intakeStep, setIntakeStep] = useState<'step1' | 'step2'>('step1')
  const [selectedDocumentType, setSelectedDocumentType] = useState<DocumentType>('DRIVING_LICENSE')
  const [uploadedFile, setUploadedFile] = useState<File | null>(null)
  const [filePreviewUrl, setFilePreviewUrl] = useState<string | null>(null)
  const [capturedSelfieUrl, setCapturedSelfieUrl] = useState<string | null>(null)
  const [documentName, setDocumentName] = useState(() => {
    return sessionStorage.getItem('sih_document_name') || 'document.jpg'
  })

  // Verification Results State - Persisted in sessionStorage across refreshes
  const [isVerifying, setIsVerifying] = useState(false)
  const [verifyResult, setVerifyResult] = useState<VerifyResponse | null>(() => {
    try {
      const saved = sessionStorage.getItem('sih_latest_verification')
      return saved ? JSON.parse(saved) : null
    } catch {
      return null
    }
  })

  // Alerts State
  const [alerts, setAlerts] = useState<CaseAlert[]>([])

  const loadAlerts = useCallback(async () => {
    try {
      const res = await fetchAlerts({ limit: 100 })
      if (res && res.items) {
        const mapped: CaseAlert[] = res.items.map((item) => ({
          id: item.id,
          verification_id: item.verification_id || undefined,
          verificationId: item.verification_id || undefined,
          caseNumber: item.case_number,
          subjectName: item.person_name || item.title || 'Security Anomaly',
          verdict: (item.verdict as any) || 'FAKE',
          reason: item.message,
          timestamp: new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          severity: item.severity.toLowerCase() as any,
          score: item.risk_score || 0,
          read: item.status !== 'UNREVIEWED',
          status: item.status as any,
          title: item.title,
          message: item.message,
          documentType: item.document_type || undefined,
          documentNumber: item.document_number || undefined,
          officerEmail: item.officer_email || undefined,
          checkpoint: item.checkpoint || undefined,
          tamperingScore: item.tampering_score || undefined,
          faceScore: item.face_score || undefined,
          details: item.details,
          reviewedAt: item.reviewed_at ? new Date(item.reviewed_at).toLocaleString() : undefined,
          reviewedBy: item.reviewed_by || undefined,
          reviewNotes: item.review_notes || undefined,
          resolvedAt: item.resolved_at ? new Date(item.resolved_at).toLocaleString() : undefined,
        }))
        setAlerts(mapped)
      }
    } catch {
      // Offline / unauthenticated fallback
    }
  }, [])

  useEffect(() => {
    if (currentUser) {
      loadAlerts()
    }
  }, [currentUser, loadAlerts])

  // Sync verifyResult to sessionStorage
  useEffect(() => {
    if (verifyResult) {
      sessionStorage.setItem('sih_latest_verification', JSON.stringify(verifyResult))
    }
  }, [verifyResult])

  // Support direct URL /results?id=... loading
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const idParam = params.get('id')
    if (idParam && !verifyResult) {
      const idNum = parseInt(idParam, 10)
      if (!isNaN(idNum)) {
        getVerificationById(idNum)
          .then((res) => {
            if (res) {
              setVerifyResult(res)
              setLocation('/results')
            }
          })
          .catch(() => {
            // Ignore if not found
          })
      }
    }
  }, [verifyResult, setLocation])

  // Sync Auth Token
  useEffect(() => {
    if (currentUser) {
      setAuthToken(currentUser.token)
    }
  }, [currentUser])

  // Login Success Handler
  const handleLoginSuccess = (user: UserAuth) => {
    setCurrentUser(user)
    setAuthToken(user.token)
    localStorage.setItem('sih_user_auth', JSON.stringify(user))

    if (user.role === 'SUPERVISOR') {
      setLocation('/audit')
    } else {
      setLocation('/intake')
    }
  }

  const handleLogout = () => {
    setCurrentUser(null)
    setAuthToken(null)
    localStorage.removeItem('sih_user_auth')
    sessionStorage.removeItem('sih_latest_verification')
    sessionStorage.removeItem('sih_document_name')
    setLocation('/login')
    toast.info('Logged out of system.')
  }

  // File Handlers
  const handleFileSelect = useCallback((file: File) => {
    setUploadedFile(file)
    setDocumentName(file.name)
    sessionStorage.setItem('sih_document_name', file.name)
    const url = URL.createObjectURL(file)
    setFilePreviewUrl(url)
  }, [])

  const handleClearDocument = useCallback(() => {
    setUploadedFile(null)
    if (filePreviewUrl) URL.revokeObjectURL(filePreviewUrl)
    setFilePreviewUrl(null)
    setDocumentName('document.jpg')
    sessionStorage.removeItem('sih_document_name')
  }, [filePreviewUrl])

  // Biometric Handlers
  const handleSelfieCaptured = useCallback((url: string) => {
    setCapturedSelfieUrl(url)
  }, [])

  const handleClearSelfie = useCallback(() => {
    setCapturedSelfieUrl(null)
  }, [])

  // Helper to convert base64/dataURL or object URL to a File object
  const getSelfieFile = async (url: string | null): Promise<File | null> => {
    if (!url) return null
    try {
      const res = await fetch(url)
      const blob = await res.blob()
      return new File([blob], 'selfie_capture.jpg', { type: 'image/jpeg' })
    } catch {
      return null
    }
  }

  // Verification Submit
  const handleSubmitVerification = useCallback(async () => {
    setIsVerifying(true)
    soundFX.paperSlide()

    try {
      const selfieFile = await getSelfieFile(capturedSelfieUrl)
      const res = await verifyDocument(uploadedFile, selfieFile, selectedDocumentType)
      if (currentUser && res) {
        res.officer_email = currentUser.email
      }
      setVerifyResult(res)

      if (res.verdict === 'SUSPICIOUS' || res.verdict === 'FAKE' || res.verdict === 'REJECTED') {
        toast.error(`Security Alert: ${res.verdict} Document Flagged`, {
          description: res.reason || 'Anomalies detected in specimen verification.',
        })
      }
      // Refresh live alerts feed from backend
      loadAlerts()
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Verification failed'
      toast.error('Verification Error', { description: msg })
      setIsVerifying(false)
    }
  }, [uploadedFile, capturedSelfieUrl, selectedDocumentType, currentUser, loadAlerts])

  const handleVerificationSequenceComplete = useCallback(() => {
    setIsVerifying(false)
    setLocation('/results')
  }, [setLocation])

  // Reset
  const handleReset = useCallback(() => {
    soundFX.paperSlide()
    setIsVerifying(false)
    setVerifyResult(null)
    setIntakeStep('step1')
    setUploadedFile(null)
    if (filePreviewUrl) URL.revokeObjectURL(filePreviewUrl)
    setFilePreviewUrl(null)
    setDocumentName('document.jpg')
    setCapturedSelfieUrl(null)
    setLocation('/intake')
  }, [filePreviewUrl, setLocation])

  const currentDocumentPreview = filePreviewUrl || ''
  const unreadAlertsCount = alerts.filter((a) => !a.read).length

  // Unauthenticated Guard
  if (!currentUser) {
    if (location === '/') {
      return <HomePage />
    }
    return <LoginScreen onLoginSuccess={handleLoginSuccess} />
  }

  // Derive Vidyut screen context from location
  const vidyutScreen: VidyutScreen = (() => {
    if (location.startsWith('/results')) return 'RESULTS'
    if (location.startsWith('/facematch')) return 'FACEMATCH'
    if (location.startsWith('/alerts')) return 'ALERTS'
    if (location.startsWith('/audit')) return 'AUDIT'
    if (location.startsWith('/intake')) return 'INTAKE'
    return 'GENERAL'
  })()

  const vidyutCaseContext = verifyResult
    ? {
        case_number: verifyResult.case_number,
        document_type: verifyResult.document_type,
        verdict: verifyResult.verdict,
        risk_score: verifyResult.risk_score,
        tampering_score: verifyResult.tampering_score,
        face_match_confidence: verifyResult.face_match_score ?? undefined,
        validation_issues: verifyResult.validation?.issues ?? [],
        reason: verifyResult.reason,
        checkpoint_location: verifyResult.checkpoint_location,
      }
    : undefined

  return (
    <div className="min-h-screen bg-background text-foreground transition-colors font-sans">
      <Header currentUser={currentUser} onLogout={handleLogout} unreadAlertsCount={unreadAlertsCount} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        <Switch>
          {/* Default Route */}
          <Route path="/">
            <Redirect to={currentUser.role === 'SUPERVISOR' ? '/audit' : '/intake'} />
          </Route>

          {/* Login Route */}
          <Route path="/login">
            <LoginScreen onLoginSuccess={handleLoginSuccess} />
          </Route>

          {/* Document Intake Route */}
          <Route path="/intake">
            {currentUser.role === 'SUPERVISOR' ? (
              <Redirect to="/audit" />
            ) : isVerifying ? (
              <VerificationProgress
                documentPreviewUrl={currentDocumentPreview}
                selfiePreviewUrl={capturedSelfieUrl}
                isDone={!!verifyResult}
                onComplete={handleVerificationSequenceComplete}
              />
            ) : intakeStep === 'step1' ? (
              <DocumentIntake
                uploadedFile={uploadedFile}
                filePreviewUrl={filePreviewUrl}
                selectedDocumentType={selectedDocumentType}
                onSelectDocumentType={setSelectedDocumentType}
                onFileSelect={handleFileSelect}
                onClearDocument={handleClearDocument}
                onRunStage1Only={handleSubmitVerification}
                onProceedToNextStep={() => {
                  if (selectedDocumentType === 'VISA') {
                    handleSubmitVerification()
                  } else {
                    setIntakeStep('step2')
                  }
                }}
              />
            ) : (
              <WebcamCapture
                capturedSelfieUrl={capturedSelfieUrl}
                onSelfieCaptured={handleSelfieCaptured}
                onClearSelfie={handleClearSelfie}
                onBackToStep1={() => setIntakeStep('step1')}
                onSubmitForVerification={handleSubmitVerification}
              />
            )}
          </Route>

          {/* Verification Results Route */}
          <Route path="/results">
            {verifyResult ? (
              <ResultsView
                result={verifyResult}
                documentPreviewUrl={currentDocumentPreview}
                selfiePreviewUrl={capturedSelfieUrl}
                documentName={documentName}
                onReset={handleReset}
                onProceedToBiometrics={() => {
                  setIntakeStep('step2')
                  setLocation('/intake')
                }}
              />
            ) : isVerifying ? (
              <VerificationProgress
                documentPreviewUrl={currentDocumentPreview}
                selfiePreviewUrl={capturedSelfieUrl}
                isDone={false}
                onComplete={handleVerificationSequenceComplete}
              />
            ) : (
              <Redirect to={currentUser.role === 'SUPERVISOR' ? '/audit' : '/intake'} />
            )}
          </Route>

          {/* Face Biometrics Route */}
          <Route path="/facematch">
            {currentUser.role === 'SUPERVISOR' ? (
              <Redirect to="/audit" />
            ) : (
              <FaceMatchView
                initialDocumentPhoto={currentDocumentPreview}
                initialSelfiePhoto={capturedSelfieUrl}
              />
            )}
          </Route>

          {/* Alerts Route */}
          <Route path="/alerts">
            <AlertsView
              alerts={alerts}
              currentUser={currentUser}
              onRefresh={loadAlerts}
              onReviewAlert={async (alertId, status, notes) => {
                try {
                  await reviewAlert(alertId, status, notes)
                  await loadAlerts()
                  toast.success(`Alert #${alertId} disposition recorded as ${status}`)
                } catch (err: unknown) {
                  const msg = err instanceof Error ? err.message : 'Failed to update alert'
                  toast.error('Review Error', { description: msg })
                }
              }}
              onMarkAllRead={async () => {
                try {
                  await markAllAlertsRead()
                  await loadAlerts()
                  toast.success('All alerts marked as acknowledged')
                } catch (err: unknown) {
                  const msg = err instanceof Error ? err.message : 'Failed to mark alerts'
                  toast.error('Error', { description: msg })
                }
              }}
              onInspectAlert={async (alert) => {
                const verId = alert.verification_id || alert.verificationId
                if (verId) {
                  try {
                    const rec = await getVerificationById(verId)
                    if (rec) {
                      setVerifyResult(rec)
                      setLocation('/results')
                      return
                    }
                  } catch {
                    // Fall back
                  }
                }
                toast.error('Record details unavailable for this alert.')
              }}
            />
          </Route>

          {/* Supervisor Console Route */}
          <Route path="/audit">
            <SupervisorConsole />
          </Route>

          {/* Fallback */}
          <Route>
            <Redirect to={currentUser.role === 'SUPERVISOR' ? '/audit' : '/intake'} />
          </Route>
        </Switch>
      </main>

      {/* Vidyut AI — persistent on all authenticated screens */}
      <VidyutAssistant
        screen={vidyutScreen}
        caseContext={vidyutCaseContext}
        hasNewInsight={verifyResult?.verdict === 'FAKE' || verifyResult?.verdict === 'SUSPICIOUS'}
      />
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <MainApp />
        <Toaster position="top-right" richColors />
      </ThemeProvider>
    </QueryClientProvider>
  )
}
