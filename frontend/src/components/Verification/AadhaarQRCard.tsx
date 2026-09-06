import React from 'react'
import {
  ShieldCheck,
  ShieldAlert,
  QrCode,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  HelpCircle,
  Lock,
  UserCheck,
} from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card'
import { Badge } from '../ui/badge'
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../ui/table'
import type { AadhaarQRResult } from '../../types'

interface AadhaarQRCardProps {
  aadhaarQr?: AadhaarQRResult | null
  extractedFields?: Record<string, any>
}

export const AadhaarQRCard: React.FC<AadhaarQRCardProps> = ({
  aadhaarQr,
  extractedFields = {},
}) => {
  if (!aadhaarQr) {
    return (
      <Card className="border-[#E5DDD8] bg-[#FFFFFF] p-6 space-y-3">
        <div className="flex items-center justify-between border-b border-[#E5DDD8] pb-3">
          <div className="flex items-center gap-2">
            <QrCode className="w-5 h-5 text-[#0B2925]" />
            <h3 className="text-sm font-semibold text-[#27212B]">
              Aadhaar Secure QR Cryptographic Verification
            </h3>
          </div>
          <Badge variant="outline" className="font-mono text-xs text-[#755B73]">
            NOT EVALUATED
          </Badge>
        </div>
        <p className="text-xs text-[#755B73]">
          No QR verification data available for this document.
        </p>
      </Card>
    )
  }

  const {
    detected,
    decoded,
    signature_valid,
    verification_status,
    signed_fields = {},
    field_matches = {},
    mismatches = [],
    photo_available,
    message,
  } = aadhaarQr

  const isVerified = signature_valid === true && mismatches.length === 0
  const isCriticalMismatch = signature_valid === true && mismatches.length > 0
  const isSignatureInvalid = signature_valid === false
  const isCryptoUnavailable = signature_valid === null && detected
  const isNotDetected = !detected

  // Status Badge formatting
  let statusBadgeVariant: 'success' | 'destructive' | 'warning' | 'outline' = 'outline'
  let statusBadgeText = verification_status

  if (isVerified) {
    statusBadgeVariant = 'success'
    statusBadgeText = 'VERIFIED (AUTHENTIC)'
  } else if (isCriticalMismatch) {
    statusBadgeVariant = 'destructive'
    statusBadgeText = 'CRITICAL INTEGRITY MISMATCH'
  } else if (isSignatureInvalid) {
    statusBadgeVariant = 'destructive'
    statusBadgeText = 'SIGNATURE INVALID (TAMPERED)'
  } else if (isCryptoUnavailable) {
    statusBadgeVariant = 'warning'
    statusBadgeText = 'UNVERIFIED / INCONCLUSIVE'
  } else if (isNotDetected) {
    statusBadgeVariant = 'outline'
    statusBadgeText = 'QR NOT DETECTED'
  }

  return (
    <Card className="border-[#E5DDD8] bg-[#FFFFFF] overflow-hidden">
      {/* Header */}
      <CardHeader className="pb-3 border-b border-[#E5DDD8] bg-[#FCFAF8]">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <CardTitle className="text-sm font-semibold text-[#27212B] flex items-center gap-2">
            <QrCode className="w-4 h-4 text-[#0B2925]" />
            <span>Aadhaar Secure QR Cryptographic Verification</span>
          </CardTitle>

          <div className="flex items-center gap-2">
            <Badge
              variant={statusBadgeVariant}
              className="font-mono text-xs px-2.5 py-1 uppercase font-bold"
            >
              {statusBadgeText}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-4 sm:p-6 space-y-5">
        {/* Stage Status Indicators */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
          {/* 1. QR Detection */}
          <div className="p-3 rounded-lg border border-[#E5DDD8] bg-[#FCFAF8] flex items-center justify-between">
            <span className="text-[#755B73]">QR Code:</span>
            <span className="font-bold flex items-center gap-1">
              {detected ? (
                <span className="text-[#0B2925] flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4 text-[#0B2925]" /> DETECTED
                </span>
              ) : (
                <span className="text-[#755B73] flex items-center gap-1">
                  <XCircle className="w-4 h-4 text-[#755B73]" /> NOT DETECTED
                </span>
              )}
            </span>
          </div>

          {/* 2. QR Decoding */}
          <div className="p-3 rounded-lg border border-[#E5DDD8] bg-[#FCFAF8] flex items-center justify-between">
            <span className="text-[#755B73]">QR Payload:</span>
            <span className="font-bold flex items-center gap-1">
              {decoded ? (
                <span className="text-[#0B2925] flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4 text-[#0B2925]" /> DECODED
                </span>
              ) : detected ? (
                <span className="text-[#DC2626] flex items-center gap-1">
                  <XCircle className="w-4 h-4 text-[#DC2626]" /> DECODE FAILED
                </span>
              ) : (
                <span className="text-[#755B73]">N/A</span>
              )}
            </span>
          </div>

          {/* 3. Digital Signature */}
          <div className="p-3 rounded-lg border border-[#E5DDD8] bg-[#FCFAF8] flex items-center justify-between">
            <span className="text-[#755B73]">Digital Signature:</span>
            <span className="font-bold flex items-center gap-1">
              {signature_valid === true ? (
                <span className="text-[#0B2925] flex items-center gap-1">
                  <Lock className="w-4 h-4 text-[#0B2925]" /> VALID (RSA 2048)
                </span>
              ) : signature_valid === false ? (
                <span className="text-[#DC2626] flex items-center gap-1">
                  <XCircle className="w-4 h-4 text-[#DC2626]" /> INVALID
                </span>
              ) : (
                <span className="text-amber-700 flex items-center gap-1">
                  <HelpCircle className="w-4 h-4 text-amber-600" /> NOT VERIFIED
                </span>
              )}
            </span>
          </div>
        </div>

        {/* Informative Alerts based on verification outcome */}
        {isCriticalMismatch && (
          <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-xs text-red-900 space-y-2">
            <div className="flex items-center gap-2 font-bold text-red-800 text-sm">
              <ShieldAlert className="w-5 h-5 text-red-600" />
              <span>CRITICAL INTEGRITY ALERT</span>
            </div>
            <p className="font-medium">
              The cryptographic digital signature on the QR code is authentic, but the printed demographic information on the physical card does NOT match the digitally signed data embedded in the QR code.
            </p>
            <ul className="list-disc list-inside space-y-1 text-red-800 font-mono text-[11px] pt-1">
              {mismatches.map((m, idx) => (
                <li key={idx}>{m}</li>
              ))}
            </ul>
          </div>
        )}

        {isSignatureInvalid && (
          <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-xs text-red-900 space-y-2">
            <div className="flex items-center gap-2 font-bold text-red-800 text-sm">
              <ShieldAlert className="w-5 h-5 text-red-600" />
              <span>CRYPTOGRAPHIC SIGNATURE VERIFICATION FAILED</span>
            </div>
            <p className="font-medium">
              The digital signature embedded in the Secure QR code is invalid or does not match official UIDAI public verification keys. The QR code has likely been generated by an unauthorized party or modified post-issuance.
            </p>
          </div>
        )}

        {isCryptoUnavailable && (
          <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900 space-y-2">
            <div className="flex items-center gap-2 font-bold text-amber-800 text-sm">
              <AlertTriangle className="w-5 h-5 text-amber-600" />
              <span>DIGITAL SIGNATURE NOT VERIFIED (INCONCLUSIVE)</span>
            </div>
            <p className="font-medium">
              {message || 'Trusted verification material or supported cryptographic certificate is unavailable. Document authenticity must be evaluated manually or through secondary screening.'}
            </p>
          </div>
        )}

        {isVerified && (
          <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-900 flex items-start gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold block text-sm text-emerald-800">
                Cryptographic Integrity Verified
              </span>
              <span className="font-medium">
                The UIDAI 2048-bit RSA digital signature is valid, and all extracted demographic fields are perfectly consistent with the printed document data.
              </span>
            </div>
          </div>
        )}

        {/* Demographic Field Consistency Comparison Table */}
        {decoded && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-[#27212B] uppercase tracking-wider font-mono">
                Field Consistency Cross-Check (Signed QR vs Printed OCR)
              </span>
              {photo_available && (
                <Badge variant="outline" className="font-mono text-[11px] text-[#0B2925] border-[#0B2925]/30">
                  <UserCheck className="w-3.5 h-3.5 mr-1 text-[#0B2925]" /> Signed Photo Available
                </Badge>
              )}
            </div>

            <div className="rounded-lg border border-[#E5DDD8] overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-[#FCFAF8]">
                    <TableHead className="text-[#755B73] font-mono text-xs">Field</TableHead>
                    <TableHead className="text-[#755B73] font-mono text-xs">Digitally Signed QR Data</TableHead>
                    <TableHead className="text-[#755B73] font-mono text-xs">Printed OCR Data</TableHead>
                    <TableHead className="text-right text-[#755B73] font-mono text-xs">Consistency</TableHead>
                  </TableRow>
                </TableHeader>

                <TableBody>
                  {/* Name */}
                  <TableRow>
                    <TableCell className="font-mono text-xs font-bold text-[#755B73]">NAME</TableCell>
                    <TableCell className="font-bold text-xs text-[#27212B]">
                      {signed_fields.name || <span className="text-[#755B73] italic">Not present</span>}
                    </TableCell>
                    <TableCell className="text-xs text-[#27212B]">
                      {extractedFields.name || <span className="text-[#755B73] italic">Not detected</span>}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs font-bold">
                      {field_matches.name === true ? (
                        <span className="inline-flex items-center gap-1 text-[#0B2925]">
                          <CheckCircle2 className="w-3.5 h-3.5 text-[#0B2925]" /> MATCH
                        </span>
                      ) : field_matches.name === false ? (
                        <span className="inline-flex items-center gap-1 text-[#DC2626]">
                          <XCircle className="w-3.5 h-3.5 text-[#DC2626]" /> MISMATCH
                        </span>
                      ) : (
                        <span className="text-[#755B73]">N/A</span>
                      )}
                    </TableCell>
                  </TableRow>

                  {/* DOB */}
                  <TableRow>
                    <TableCell className="font-mono text-xs font-bold text-[#755B73]">DATE OF BIRTH</TableCell>
                    <TableCell className="font-mono font-bold text-xs text-[#27212B]">
                      {signed_fields.dob || <span className="text-[#755B73] italic">Not present</span>}
                    </TableCell>
                    <TableCell className="font-mono text-xs text-[#27212B]">
                      {extractedFields.dob || extractedFields.date_of_birth || <span className="text-[#755B73] italic">Not detected</span>}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs font-bold">
                      {field_matches.dob === true ? (
                        <span className="inline-flex items-center gap-1 text-[#0B2925]">
                          <CheckCircle2 className="w-3.5 h-3.5 text-[#0B2925]" /> MATCH
                        </span>
                      ) : field_matches.dob === false ? (
                        <span className="inline-flex items-center gap-1 text-[#DC2626]">
                          <XCircle className="w-3.5 h-3.5 text-[#DC2626]" /> MISMATCH
                        </span>
                      ) : (
                        <span className="text-[#755B73]">N/A</span>
                      )}
                    </TableCell>
                  </TableRow>

                  {/* Gender */}
                  <TableRow>
                    <TableCell className="font-mono text-xs font-bold text-[#755B73]">GENDER</TableCell>
                    <TableCell className="font-mono font-bold text-xs text-[#27212B]">
                      {signed_fields.gender || <span className="text-[#755B73] italic">Not present</span>}
                    </TableCell>
                    <TableCell className="font-mono text-xs text-[#27212B]">
                      {extractedFields.gender || <span className="text-[#755B73] italic">Not detected</span>}
                    </TableCell>
                    <TableCell className="text-right font-mono text-xs font-bold">
                      {field_matches.gender === true ? (
                        <span className="inline-flex items-center gap-1 text-[#0B2925]">
                          <CheckCircle2 className="w-3.5 h-3.5 text-[#0B2925]" /> MATCH
                        </span>
                      ) : field_matches.gender === false ? (
                        <span className="inline-flex items-center gap-1 text-[#DC2626]">
                          <XCircle className="w-3.5 h-3.5 text-[#DC2626]" /> MISMATCH
                        </span>
                      ) : (
                        <span className="text-[#755B73]">N/A</span>
                      )}
                    </TableCell>
                  </TableRow>

                  {/* Address */}
                  {(signed_fields.address || extractedFields.address) && (
                    <TableRow>
                      <TableCell className="font-mono text-xs font-bold text-[#755B73]">ADDRESS</TableCell>
                      <TableCell className="text-xs text-[#27212B]">
                        {signed_fields.address || <span className="text-[#755B73] italic">Not present</span>}
                      </TableCell>
                      <TableCell className="text-xs text-[#27212B]">
                        {extractedFields.address || <span className="text-[#755B73] italic">Not detected</span>}
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs font-bold">
                        {field_matches.address === true ? (
                          <span className="inline-flex items-center gap-1 text-[#0B2925]">
                            <CheckCircle2 className="w-3.5 h-3.5 text-[#0B2925]" /> MATCH
                          </span>
                        ) : field_matches.address === false ? (
                          <span className="inline-flex items-center gap-1 text-[#DC2626]">
                            <XCircle className="w-3.5 h-3.5 text-[#DC2626]" /> MISMATCH
                          </span>
                        ) : (
                          <span className="text-[#755B73]">N/A</span>
                        )}
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
