import React from 'react'
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RotateCcw,
  FileText,
  ShieldCheck,
  Fingerprint,
  Activity,
  Check,
  Info,
  ShieldAlert,
  Download,
  Link2,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card'
import { Badge } from '../ui/badge'
import { Button } from '../ui/button'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../ui/table'
import { RiskGauge } from './RiskGauge'
import { ValidationAccordion } from './ValidationAccordion'
import { TamperingHeatmap } from './TamperingHeatmap'
import type { VerifyResponse } from '../../types'
import { soundFX } from '../../utils/audio'

interface ResultsViewProps {
  result: VerifyResponse
  documentPreviewUrl: string
  selfiePreviewUrl?: string | null
  documentName: string
  onReset: () => void
}

export const ResultsView: React.FC<ResultsViewProps> = ({
  result,
  documentPreviewUrl,
  selfiePreviewUrl,
  onReset,
}) => {
  const {
    document_type,
    expected_document_type,
    detected_document_type,
    category_match,
    extracted_fields = {},
    validation,
    tampering_score,
    tampering_regions = [],
    heatmap_image_base64,
    face_match_score,
    biometric,
    risk_score,
    risk_level,
    risk_factors = [],
    verdict,
    reason,
    case_number,
    checkpoint_location,
    officer_email,
    mrz,
    identity_links = [],
  } = result

  const isRejected = verdict === 'REJECTED'
  const isFake = verdict === 'FAKE'
  const isSuspicious = verdict === 'SUSPICIOUS'
  const isGenuine = verdict === 'GENUINE'

  // Standardized document field mapping (Real data only)
  const docNumber =
    extracted_fields.id_number ||
    extracted_fields.passport_number ||
    extracted_fields.visa_number ||
    extracted_fields.document_number ||
    extracted_fields.license_number ||
    'Not detected'

  const subjectName = extracted_fields.name || 'Not detected'
  const dateOfBirth = extracted_fields.dob || extracted_fields.date_of_birth || 'Not detected'
  const nationality = extracted_fields.nationality || (document_type === 'PASSPORT' && extracted_fields.nationality ? extracted_fields.nationality : 'Not detected')
  const expiryDate = extracted_fields.expiry_date || extracted_fields.date_of_expiry || 'Not detected'
  const gender = extracted_fields.gender || 'Not detected'
  const address = extracted_fields.address || 'Not detected'

  // Tampering Status
  const tamperingStatus =
    tampering_score > 70
      ? 'CRITICAL TAMPERING DETECTED'
      : tampering_score > 30
      ? 'SUSPICIOUS ANOMALIES FLAGGED'
      : 'AUTHENTIC SPECIMEN'

  const effectiveRiskLevel = risk_level || (risk_score >= 65 ? 'HIGH RISK' : risk_score >= 30 ? 'MEDIUM RISK' : 'LOW RISK')
  const riskVariant = effectiveRiskLevel.includes('HIGH') ? 'destructive' : effectiveRiskLevel.includes('MEDIUM') ? 'warning' : 'success'

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* ── 1. FINAL VERIFICATION / HERO HEADER ── */}
      <Card className="border-[#E5DDD8] bg-[#FFFFFF] shadow-sm overflow-hidden">
        <div className="p-6 sm:p-8 flex flex-col md:flex-row items-center justify-between gap-6">
          {/* Radial Risk Gauge */}
          <div className="shrink-0">
            <RiskGauge score={risk_score} verdict={verdict} />
          </div>

          {/* Verdict Seal & Details */}
          <div className="flex-1 space-y-3 text-center md:text-left">
            <div className="flex flex-wrap items-center justify-center md:justify-start gap-2">
              <span className="text-xs font-mono font-semibold text-[#755B73]">
                {case_number || 'CASE-26188'} • {checkpoint_location || 'Attari-Wagah Border'}
              </span>

              {officer_email && (
                <span className="text-xs font-mono bg-[#EBE5E2] px-2 py-0.5 rounded text-[#27212B] font-semibold">
                  Officer: {officer_email}
                </span>
              )}
            </div>

            {/* Verdict Stamp */}
            <div className="flex flex-wrap items-center justify-center md:justify-start gap-3">
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
                className="text-lg px-4 py-1 animate-stamp-impact uppercase tracking-widest font-mono font-bold shadow-xs"
              >
                {isGenuine && <CheckCircle2 className="w-5 h-5 mr-2 inline" />}
                {isSuspicious && <AlertTriangle className="w-5 h-5 mr-2 inline text-[#755B73]" />}
                {(isFake || isRejected) && <XCircle className="w-5 h-5 mr-2 inline text-[#DC2626]" />}
                <span>OVERALL STATUS: {verdict}</span>
              </Badge>

              <Badge variant={riskVariant} className="font-mono text-xs px-2.5 py-1">
                {effectiveRiskLevel} ({risk_score}/100)
              </Badge>
            </div>

            {/* Verdict Explanation Reason */}
            {reason && (
              <p className="text-sm font-medium text-[#27212B] bg-[#F8F5F3] p-3 rounded-xl border border-[#E5DDD8]">
                {reason}
              </p>
            )}
          </div>

          {/* Actions */}
          <div className="shrink-0 flex flex-wrap gap-2 items-center">
            {result.verification_id && (
              <Button
                onClick={() => {
                  soundFX.stampImpact()
                  window.open(`/verification/${result.verification_id}/export?format=json`, '_blank')
                }}
                variant="outline"
                size="lg"
                className="gap-2 border-[#0B2925] text-[#0B2925] hover:bg-[#0B2925]/10 font-bold cursor-pointer"
                title="Download official forensic screening dossier"
              >
                <Download className="w-4 h-4" />
                <span>Export Dossier</span>
              </Button>
            )}

            <Button
              onClick={() => {
                soundFX.paperSlide()
                onReset()
              }}
              size="lg"
              className="gap-2 bg-[#0B2925] hover:bg-[#133D37] text-[#F8F5F3] font-bold cursor-pointer"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Start New Examination</span>
            </Button>
          </div>
        </div>
      </Card>

      {/* If REJECTED -> Fast fail notice */}
      {isRejected ? (
        <Card className="p-6 border-[#DC2626]/40 bg-[#DC2626]/10 text-[#DC2626] space-y-2">
          <div className="flex items-center gap-2 text-base font-bold">
            <XCircle className="w-5 h-5 shrink-0" />
            <span>Fast-Fail Intake Rejection Triggered</span>
          </div>
          <p className="text-xs text-[#27212B] font-medium">
            Forensic analysis skipped because the specimen failed basic identity document validation (no extractable text or facial landmarks detected).
          </p>
        </Card>
      ) : (
        <>
          {/* ── 2. DOCUMENT INFORMATION CARD ── */}
          <Card className="border-[#E5DDD8] bg-[#FFFFFF]">
            <CardHeader className="pb-3 border-b border-[#E5DDD8] bg-[#FCFAF8]">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <CardTitle className="text-sm font-semibold text-[#27212B] flex items-center gap-2">
                  <FileText className="w-4 h-4 text-[#0B2925]" />
                  <span>Document Information</span>
                </CardTitle>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline" className="font-mono text-xs text-[#0B2925] border-[#0B2925]/30">
                    Expected Category: {expected_document_type || document_type}
                  </Badge>
                  {detected_document_type && (
                    <Badge variant="outline" className="font-mono text-xs text-[#755B73]">
                      Detected Type: {detected_document_type.toUpperCase()}
                    </Badge>
                  )}
                  {category_match !== undefined && (
                    <Badge
                      variant={category_match ? 'success' : 'destructive'}
                      className="font-mono text-[10px]"
                    >
                      {category_match ? 'Category Match' : 'Category Mismatch'}
                    </Badge>
                  )}
                </div>
              </div>
            </CardHeader>

            <CardContent className="p-4 sm:p-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
                <div className="p-3 rounded-lg border border-[#E5DDD8] bg-[#FCFAF8] space-y-1">
                  <span className="text-[#755B73] font-mono text-[11px] block uppercase">Document Number</span>
                  <span className="font-mono font-bold text-sm text-[#0B2925]">{docNumber}</span>
                </div>

                <div className="p-3 rounded-lg border border-[#E5DDD8] bg-[#FCFAF8] space-y-1">
                  <span className="text-[#755B73] font-mono text-[11px] block uppercase">Subject Full Name</span>
                  <span className="font-bold text-sm text-[#27212B]">{subjectName}</span>
                </div>

                <div className="p-3 rounded-lg border border-[#E5DDD8] bg-[#FCFAF8] space-y-1">
                  <span className="text-[#755B73] font-mono text-[11px] block uppercase">Date of Birth</span>
                  <span className="font-mono font-bold text-sm text-[#27212B]">{dateOfBirth}</span>
                </div>

                <div className="p-3 rounded-lg border border-[#E5DDD8] bg-[#FCFAF8] space-y-1">
                  <span className="text-[#755B73] font-mono text-[11px] block uppercase">Nationality / Issuing State</span>
                  <span className="font-mono font-bold text-sm text-[#27212B]">{nationality}</span>
                </div>

                <div className="p-3 rounded-lg border border-[#E5DDD8] bg-[#FCFAF8] space-y-1">
                  <span className="text-[#755B73] font-mono text-[11px] block uppercase">Expiration Date</span>
                  <span className="font-mono font-bold text-sm text-[#27212B]">{expiryDate}</span>
                </div>

                <div className="p-3 rounded-lg border border-[#E5DDD8] bg-[#FCFAF8] space-y-1">
                  <span className="text-[#755B73] font-mono text-[11px] block uppercase">Gender</span>
                  <span className="font-mono font-bold text-sm text-[#27212B]">{gender}</span>
                </div>
              </div>

              {address !== 'Not detected' && (
                <div className="mt-3 p-3 rounded-lg border border-[#E5DDD8] bg-[#FCFAF8] space-y-1 text-xs">
                  <span className="text-[#755B73] font-mono text-[11px] block uppercase">Extracted Address</span>
                  <span className="font-medium text-[#27212B]">{address}</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* ── 3. OCR ANALYSIS & CONFIDENCE ── */}
          <Card className="border-[#E5DDD8] bg-[#FFFFFF]">
            <CardHeader className="pb-3 border-b border-[#E5DDD8] bg-[#FCFAF8]">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-semibold text-[#27212B] flex items-center gap-2">
                  <Activity className="w-4 h-4 text-[#0B2925]" />
                  <span>Optical Character Recognition (OCR) Analysis</span>
                </CardTitle>
                <Badge variant="outline" className="font-mono text-xs bg-[#A7F3D0]/20 text-[#0B2925] border-[#A7F3D0]">
                  OCR Status: {Object.keys(extracted_fields).length > 0 ? 'Extracted & Parsed' : 'No fields detected'}
                </Badge>
              </div>
            </CardHeader>

            <CardContent className="p-0">
              {Object.keys(extracted_fields).length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-[#755B73]">Field Attribute</TableHead>
                      <TableHead className="text-[#755B73]">Extracted Value</TableHead>
                      <TableHead className="text-right text-[#755B73]">Attribute Status</TableHead>
                    </TableRow>
                  </TableHeader>

                  <TableBody>
                    {Object.entries(extracted_fields).map(([key, val]) => (
                      <TableRow key={key}>
                        <TableCell className="font-mono text-xs font-bold text-[#755B73] uppercase">
                          {key.replace('_', ' ')}
                        </TableCell>
                        <TableCell className="font-semibold text-[#27212B] text-sm">
                          {val !== null && val !== undefined && String(val).trim() !== ''
                            ? String(val)
                            : 'Not detected'}
                        </TableCell>
                        <TableCell className="text-right font-mono text-xs font-bold text-[#0B2925]">
                          {val !== null && val !== undefined && String(val).trim() !== '' ? (
                            <span className="inline-flex items-center gap-1">
                              <Check className="w-3.5 h-3.5 text-[#0B2925]" />
                              Extracted
                            </span>
                          ) : (
                            <span className="text-[#755B73] font-normal">Null</span>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="p-4 text-center text-xs text-[#755B73]">
                  No structured text fields detected in the uploaded specimen.
                </div>
              )}
            </CardContent>
          </Card>

          {/* ── 4. MRZ ANALYSIS SECTION ── */}
          <ValidationAccordion validation={validation} documentType={document_type} mrz={mrz} />

          {/* ── 5. TAMPERING ANALYSIS (SCORE, STATUS, INDICATORS & ELA HEATMAP) ── */}
          <TamperingHeatmap
            score={tampering_score}
            heatmapImageBase64={heatmap_image_base64}
            regions={tampering_regions}
            originalPreviewUrl={documentPreviewUrl}
          />

          {/* ── 6. MULTI-FACTOR BIOMETRIC ANALYSIS (QUALITY, LIVENESS, PRESENTATION ATTACK & MATCH) ── */}
          {document_type !== 'VISA' && (
            <Card className="border-[#E5DDD8] bg-[#FFFFFF] p-6 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#E5DDD8] pb-3">
                <div>
                  <h3 className="text-sm font-semibold text-[#27212B] flex items-center gap-2">
                    <Fingerprint className="w-4 h-4 text-[#0B2925]" />
                    <span>Multi-Factor Biometric &amp; Liveness Verification</span>
                  </h3>
                  <p className="text-xs text-[#755B73] mt-0.5">
                    Face detection, image quality, anti-spoof liveness, presentation attack analysis &amp; ArcFace vector match.
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <Badge
                    variant={
                      biometric?.status === 'VERIFIED'
                        ? 'success'
                        : biometric?.status === 'REJECTED'
                        ? 'destructive'
                        : biometric?.status === 'NEEDS_REVIEW' || biometric?.status === 'RETRY'
                        ? 'warning'
                        : 'outline'
                    }
                    className="text-sm px-3 py-1 font-mono font-bold"
                  >
                    Status: {biometric?.status || (face_match_score !== null && face_match_score !== undefined ? (face_match_score >= 80 ? 'VERIFIED' : 'NEEDS_REVIEW') : 'NOT APPLICABLE')}
                  </Badge>
                </div>
              </div>

              {/* Sub-checks: Face Detection, Quality, Liveness, Spoof */}
              {biometric && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
                  <div className="p-3 rounded-lg border border-[#E5DDD8] bg-[#FCFAF8] space-y-1">
                    <span className="text-[#755B73] block text-[10px] uppercase">Face Detection</span>
                    <span className="font-bold text-sm text-[#27212B]">
                      {biometric.face_detected ? `Detected (${biometric.face_count})` : 'No face found'}
                    </span>
                  </div>

                  <div className="p-3 rounded-lg border border-[#E5DDD8] bg-[#FCFAF8] space-y-1">
                    <span className="text-[#755B73] block text-[10px] uppercase">Image Quality</span>
                    <span className={`font-bold text-sm ${biometric.quality.status === 'GOOD' ? 'text-[#0B2925]' : 'text-amber-600'}`}>
                      {biometric.quality.status} ({biometric.quality.score}/100)
                    </span>
                  </div>

                  <div className="p-3 rounded-lg border border-[#E5DDD8] bg-[#FCFAF8] space-y-1">
                    <span className="text-[#755B73] block text-[10px] uppercase">Liveness Engine</span>
                    <span className={`font-bold text-sm ${biometric.liveness.status === 'PASS' ? 'text-[#0B2925]' : biometric.liveness.status === 'FAIL' ? 'text-[#DC2626]' : 'text-[#755B73]'}`}>
                      {biometric.liveness.status} ({biometric.liveness.score}/100)
                    </span>
                  </div>

                  <div className="p-3 rounded-lg border border-[#E5DDD8] bg-[#FCFAF8] space-y-1">
                    <span className="text-[#755B73] block text-[10px] uppercase">Spoof / Replay</span>
                    <span className={`font-bold text-sm ${biometric.presentation_attack.detected ? 'text-[#DC2626]' : 'text-[#0B2925]'}`}>
                      {biometric.presentation_attack.detected ? `ATTACK: ${biometric.presentation_attack.type}` : 'NONE DETECTED'}
                    </span>
                  </div>
                </div>
              )}

              {/* Side-by-side Photo Comparison */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div className="space-y-1.5 text-center">
                  <div className="aspect-[4/3] rounded-xl border border-[#E5DDD8] bg-[#F8F5F3] overflow-hidden flex items-center justify-center">
                    <img src={documentPreviewUrl} alt="Exhibit A Document Portrait" className="w-full h-full object-contain" />
                  </div>
                  <span className="text-xs font-mono font-semibold text-[#755B73]">Exhibit A Document Portrait</span>
                </div>

                <div className="space-y-1.5 text-center">
                  <div className="aspect-[4/3] rounded-xl border border-[#E5DDD8] bg-[#F8F5F3] overflow-hidden flex items-center justify-center">
                    {selfiePreviewUrl ? (
                      <img src={selfiePreviewUrl} alt="Exhibit B Live Selfie" className="w-full h-full object-contain" />
                    ) : (
                      <span className="text-xs text-[#755B73]">No selfie submitted</span>
                    )}
                  </div>
                  <span className="text-xs font-mono font-semibold text-[#755B73]">Exhibit B Live Selfie</span>
                </div>
              </div>

              {/* Face Match Vector Score */}
              <div className="p-3 rounded-lg border border-[#E5DDD8] bg-[#FCFAF8] flex items-center justify-between text-xs font-mono">
                <span className="text-[#755B73]">ArcFace 128-D Correlation Score:</span>
                <span className="font-bold text-sm text-[#0B2925]">
                  {face_match_score !== null && face_match_score !== undefined ? `${face_match_score}%` : 'Not evaluated'}
                </span>
              </div>
            </Card>
          )}

          {/* ── 7. RISK ANALYSIS & DISCRETE FACTORS ── */}
          <Card className="border-[#E5DDD8] bg-[#FFFFFF] p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-[#E5DDD8] pb-3">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-[#0B2925]" />
                <h3 className="text-sm font-semibold text-[#27212B]">Risk Engine &amp; Identified Factors</h3>
              </div>
              <Badge variant={riskVariant} className="font-mono text-xs">
                {effectiveRiskLevel} ({risk_score}/100)
              </Badge>
            </div>

            {risk_factors && risk_factors.length > 0 ? (
              <div className="space-y-2">
                <span className="text-xs font-mono text-[#755B73] uppercase block">Triggered Risk Factors:</span>
                <div className="flex flex-wrap gap-2">
                  {risk_factors.map((factor, idx) => (
                    <Badge
                      key={idx}
                      variant="destructive"
                      className="font-mono text-xs px-2.5 py-1"
                    >
                      {factor.replace(/_/g, ' ')}
                    </Badge>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-xs text-[#0B2925] font-semibold">
                <CheckCircle2 className="w-4 h-4" />
                <span>No anomalous risk factors triggered. Specimen matches baseline authenticity profiles.</span>
              </div>
            )}
          </Card>

          {/* ── 7.5. IDENTITY LINK ANALYSIS (INVESTIGATIVE CORRELATION) ── */}
          <Card className="border-[#E5DDD8] bg-[#FFFFFF] p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-[#E5DDD8] pb-3">
              <div className="flex items-center gap-2">
                <Link2 className="w-4 h-4 text-[#0B2925]" />
                <h3 className="text-sm font-semibold text-[#27212B]">Identity Link Analysis (Investigative Correlation)</h3>
              </div>
              <Badge variant="outline" className="font-mono text-xs text-[#0B2925] border-[#0B2925]/30">
                {identity_links && identity_links.length > 0 ? `${identity_links.length} Link(s) Detected` : 'No Prior Linkages'}
              </Badge>
            </div>

            {identity_links && identity_links.length > 0 ? (
              <div className="space-y-3">
                <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-800 flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                  <span>
                    <strong>Investigative Correlation:</strong> Prior records match key attributes. This is an investigative signal for officer review, not a definitive conclusion of identity.
                  </span>
                </div>

                <div className="space-y-2">
                  {identity_links.map((link, idx) => (
                    <div key={idx} className="p-3 rounded-xl border border-[#E5DDD8] bg-[#FCFAF8] space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge variant="destructive" className="font-mono text-[10px] uppercase">
                            {link.relationship_type.replace(/_/g, ' ')}
                          </Badge>
                          <span className="font-mono text-xs font-bold text-[#27212B]">{link.case_number}</span>
                        </div>
                        <Badge variant="outline" className="font-mono text-[10px] text-amber-800 bg-amber-100 border-amber-300">
                          {link.recommendation}
                        </Badge>
                      </div>

                      <p className="text-xs text-[#59535E]">{link.details}</p>

                      <div className="flex items-center gap-4 text-[11px] font-mono text-[#755B73] pt-1 border-t border-[#E5DDD8]/60">
                        {link.historical_name && <span>Prior Name: <strong>{link.historical_name}</strong></span>}
                        {link.historical_document_number && <span>Prior Doc: <strong>{link.historical_document_number}</strong></span>}
                        <span>Correlation Confidence: <strong>{link.similarity_score}%</strong></span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-xs text-[#0B2925] font-semibold">
                <CheckCircle2 className="w-4 h-4" />
                <span>No historical correlations or duplicate credential linkages detected in database.</span>
              </div>
            )}
          </Card>

          {/* ── 8. COMPREHENSIVE VERIFICATION SUMMARY ── */}
          <Card className="border-[#E5DDD8] bg-[#FCFAF8] p-6 space-y-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-[#0B2925]" />
              <h4 className="text-sm font-bold text-[#0B2925]">Comprehensive Verification Summary</h4>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs font-mono">
              <div className="p-2.5 rounded bg-[#FFFFFF] border border-[#E5DDD8]">
                <span className="text-[#755B73] block text-[10px] uppercase">Final Verdict</span>
                <span className="font-bold text-sm text-[#0B2925]">{verdict}</span>
              </div>

              <div className="p-2.5 rounded bg-[#FFFFFF] border border-[#E5DDD8]">
                <span className="text-[#755B73] block text-[10px] uppercase">Composite Risk Score</span>
                <span className="font-bold text-sm text-[#0B2925]">{risk_score}/100 ({effectiveRiskLevel})</span>
              </div>

              <div className="p-2.5 rounded bg-[#FFFFFF] border border-[#E5DDD8]">
                <span className="text-[#755B73] block text-[10px] uppercase">Tampering Analysis</span>
                <span className="font-bold text-sm text-[#0B2925]">{tampering_score}/100</span>
                <span className="text-[10px] text-[#755B73] block truncate">{tamperingStatus}</span>
              </div>

              <div className="p-2.5 rounded bg-[#FFFFFF] border border-[#E5DDD8]">
                <span className="text-[#755B73] block text-[10px] uppercase">Facial Biometric Match</span>
                <span className="font-bold text-sm text-[#0B2925]">
                  {face_match_score !== null && face_match_score !== undefined ? `${face_match_score}%` : 'N/A'}
                </span>
              </div>
            </div>

            {reason && (
              <div className="p-3 rounded bg-[#FFFFFF] border border-[#E5DDD8] text-xs text-[#27212B] font-sans flex items-start gap-2">
                <Info className="w-4 h-4 text-[#755B73] shrink-0 mt-0.5" />
                <span>{reason}</span>
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  )
}

