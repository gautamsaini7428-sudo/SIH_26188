import React from 'react'
import { CheckCircle2, XCircle, AlertTriangle, ShieldAlert, FileCode } from 'lucide-react'
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from '../ui/accordion'
import type { ValidationResult, DocumentType, MRZResult } from '../../types'

interface ValidationAccordionProps {
  validation: ValidationResult
  documentType: DocumentType
  mrz?: MRZResult | null
}

export const ValidationAccordion: React.FC<ValidationAccordionProps> = ({ validation, documentType, mrz }) => {
  const {
    format_valid = true,
    expiry_valid = true,
    issues = [],
    mrz_valid,
  } = validation || {}
  const hasIssues = issues.length > 0

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[#27212B] flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-[#0B2925]" />
          <span>Standalone Document Validation Report</span>
        </h3>
        {hasIssues ? (
          <span className="text-xs font-semibold text-[#8A2323] flex items-center gap-1">
            <XCircle className="w-3.5 h-3.5 text-[#8A2323]" />
            {issues.length} Anomaly Flagged
          </span>
        ) : (
          <span className="text-xs font-semibold text-[#0B2925] flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#0B2925]" />
            All Format Controls Passed
          </span>
        )}
      </div>

      <Accordion type="single" collapsible defaultValue="item-1" className="w-full border border-[#E5DDD8] rounded-xl bg-[#FFFFFF] overflow-hidden">
        {/* Item 1: Format & Layout Check */}
        <AccordionItem value="item-1">
          <AccordionTrigger className="px-4 hover:no-underline cursor-pointer">
            <div className="flex items-center gap-2 text-xs">
              {format_valid ? (
                <CheckCircle2 className="w-4 h-4 text-[#0B2925] shrink-0" />
              ) : (
                <XCircle className="w-4 h-4 text-[#8A2323] shrink-0" />
              )}
              <span className="font-semibold text-[#27212B]">Document Format &amp; Template Integrity</span>
            </div>
          </AccordionTrigger>
          <AccordionContent className="px-4 text-xs text-[#755B73] space-y-2">
            <p>
              {format_valid
                ? `Standard optical template layout verified for ${documentType}. Field coordinate geometry matches official specifications.`
                : `Format violation detected. Geometry or text baseline distribution does not match official ${documentType} templates.`}
            </p>
          </AccordionContent>
        </AccordionItem>

        {/* Item 2: Expiration Check */}
        <AccordionItem value="item-2">
          <AccordionTrigger className="px-4 hover:no-underline cursor-pointer">
            <div className="flex items-center gap-2 text-xs">
              {expiry_valid ? (
                <CheckCircle2 className="w-4 h-4 text-[#0B2925] shrink-0" />
              ) : (
                <XCircle className="w-4 h-4 text-[#8A2323] shrink-0" />
              )}
              <span className="font-semibold text-[#27212B]">Document Expiry &amp; Validity Date</span>
            </div>
          </AccordionTrigger>
          <AccordionContent className="px-4 text-xs text-[#755B73] space-y-2">
            <p>
              {expiry_valid
                ? 'Document issue and expiration dates parsed cleanly. Document is currently active and within valid border entry period.'
                : 'Document is expired or contains an invalid date format.'}
            </p>
          </AccordionContent>
        </AccordionItem>

        {/* Item 3: MRZ Checksum Math (Passport or MRZ-detected document) */}
        {(documentType === 'PASSPORT' || mrz?.detected) && (
          <AccordionItem value="item-3">
            <AccordionTrigger className="px-4 hover:no-underline cursor-pointer">
              <div className="flex items-center gap-2 text-xs">
                {mrz_valid === true || mrz?.valid === true ? (
                  <CheckCircle2 className="w-4 h-4 text-[#0B2925] shrink-0" />
                ) : mrz_valid === false || mrz?.valid === false ? (
                  <XCircle className="w-4 h-4 text-[#8A2323] shrink-0" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-[#755B73] shrink-0" />
                )}
                <span className="font-semibold text-[#27212B]">
                  ICAO 9303 MRZ Parsing &amp; Mathematical Checksums
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#F2ECE9] text-[#755B73] ml-auto">
                  {mrz?.detected ? 'MRZ Detected' : 'Not Detected'}
                </span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="px-4 text-xs text-[#755B73] space-y-3 font-sans">
              <p>
                {mrz_valid === true || mrz?.valid === true
                  ? 'All MRZ check digits (Document #, DOB, Expiry, Personal #, Composite) mathematically verified against ICAO 9303 standards.'
                  : mrz_valid === false || mrz?.valid === false
                  ? 'CRITICAL FAIL: MRZ check digit checksum mismatch detected. Line data indicates altered characters or forgery.'
                  : mrz?.detected
                  ? 'MRZ detected; validation in progress or inconclusive.'
                  : 'MRZ not detected on this specimen.'}
              </p>

              {mrz?.raw && (
                <div className="space-y-1">
                  <div className="text-[10px] font-mono font-bold uppercase text-[#0B2925] flex items-center gap-1">
                    <FileCode className="w-3.5 h-3.5" />
                    <span>Raw MRZ Optical Zone:</span>
                  </div>
                  <pre className="p-2.5 rounded bg-[#27212B] text-[#A7F3D0] font-mono text-[11px] leading-relaxed overflow-x-auto whitespace-pre">
                    {mrz.raw}
                  </pre>
                </div>
              )}

              {mrz?.fields && Object.keys(mrz.fields).length > 0 && (
                <div className="space-y-1">
                  <div className="text-[10px] font-mono font-bold uppercase text-[#0B2925]">
                    MRZ Decoded Payload:
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                    {Object.entries(mrz.fields).map(([k, v]) => (
                      <div key={k} className="p-1.5 rounded bg-[#F8F5F3] border border-[#E5DDD8] flex justify-between">
                        <span className="text-[#755B73]">{k}:</span>
                        <span className="font-bold text-[#27212B]">{String(v || 'N/A')}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </AccordionContent>
          </AccordionItem>
        )}

        {/* Item 4: Blacklist & Watchlist Flag Status */}
        <AccordionItem value="item-4">
          <AccordionTrigger className="px-4 hover:no-underline cursor-pointer">
            <div className="flex items-center gap-2 text-xs">
              {hasIssues ? (
                <XCircle className="w-4 h-4 text-[#8A2323] shrink-0" />
              ) : (
                <CheckCircle2 className="w-4 h-4 text-[#0B2925] shrink-0" />
              )}
              <span className="font-semibold text-[#27212B]">MHA Watchlist &amp; Blacklist Parity</span>
            </div>
          </AccordionTrigger>
          <AccordionContent className="px-4 text-xs text-[#755B73] space-y-2">
            {hasIssues ? (
              <div className="space-y-1.5">
                <p className="font-semibold text-[#8A2323]">Validation issues flagged:</p>
                <ul className="list-disc list-inside space-y-1 font-mono text-[11px]">
                  {issues.map((issue, idx) => (
                    <li key={idx} className="text-[#27212B]">{issue}</li>
                  ))}
                </ul>
              </div>
            ) : (
              <p>No active interpol, MHA blacklist, or stolen document registry matches found for this specimen.</p>
            )}
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    </div>
  )
}
