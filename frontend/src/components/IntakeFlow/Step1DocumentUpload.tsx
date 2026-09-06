import { useRef, useState } from 'react'
import { Upload, ArrowRight, AlertCircle, Trash2, FileCheck } from 'lucide-react'
import { ExhibitCard } from './ExhibitCard'
import type { DocumentType } from '../../types'
import { soundFX } from '../../utils/audio'

interface Step1DocumentUploadProps {
  uploadedFile: File | null
  filePreviewUrl: string | null
  selectedDocumentType: DocumentType
  onSelectDocumentType: (docType: DocumentType) => void
  onFileSelect: (file: File) => void
  onClearDocument: () => void
  onProceedToStep2: () => void
}

const DOCUMENT_TYPE_TABS: { type: DocumentType; label: string; sub: string }[] = [
  { type: 'PASSPORT', label: 'Passport', sub: 'ICAO 9303 TD3' },
  { type: 'VISA', label: 'Visa', sub: 'Entry Permit (No Face)' },
  { type: 'NATIONAL_ID', label: 'National ID', sub: 'Aadhaar / Voter ID' },
  { type: 'DRIVING_LICENSE', label: 'Driving License', sub: 'State DMV' },
  { type: 'PERMIT', label: 'Permit', sub: 'Border / Transit' },
]

export const Step1DocumentUpload: React.FC<Step1DocumentUploadProps> = ({
  uploadedFile,
  filePreviewUrl,
  selectedDocumentType,
  onSelectDocumentType,
  onFileSelect,
  onClearDocument,
  onProceedToStep2,
}) => {
  const [isDragOver, setIsDragOver] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const documentReady = Boolean(uploadedFile)
  const currentPreview = filePreviewUrl || ''
  const currentFileName = uploadedFile ? uploadedFile.name : ''
  const isPdf = uploadedFile
    ? uploadedFile.type === 'application/pdf' || uploadedFile.name.endsWith('.pdf')
    : false

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
    const files = e.dataTransfer.files
    if (files && files.length > 0) {
      processFile(files[0])
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      processFile(files[0])
    }
  }

  const processFile = (file: File) => {
    setErrorMessage(null)
    const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf']
    if (!validTypes.includes(file.type) && !file.name.match(/\.(jpg|jpeg|png|webp|pdf)$/i)) {
      setErrorMessage('Unsupported file format. Please upload JPG, PNG, WEBP or PDF.')
      return
    }
    soundFX.paperSlide()
    onFileSelect(file)
  }

  return (
    <div className="space-y-6">
      {/* Folder Tab Case Intake Header */}
      <div className="space-y-1">
        <h2 className="font-editorial text-2xl sm:text-3xl font-bold text-[#3C467B]">
          Step 1: Document Type &amp; Intake Specimen
        </h2>
        <p className="text-xs sm:text-sm text-[#50589C] font-sans">
          Select the document category, then deposit the physical or scanned specimen into the border case file.
        </p>
      </div>

      {/* ─── DOCUMENT TYPE SELECTOR TABS ─── */}
      <div className="space-y-2">
        <label className="text-xs font-mono font-semibold text-[#0B2925] uppercase tracking-wider">
          CLASSIFICATION TYPE
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
          {DOCUMENT_TYPE_TABS.map((tab) => {
            const isSelected = selectedDocumentType === tab.type
            return (
              <button
                key={tab.type}
                type="button"
                onClick={() => {
                  soundFX.paperSlide()
                  onSelectDocumentType(tab.type)
                }}
                className={`p-3 rounded-lg border text-left transition-all cursor-pointer ${
                  isSelected
                    ? 'border-[#3C467B] bg-[#3C467B] text-[#FFFFFF] shadow-sm'
                    : 'border-[#DDE4FF] bg-[#FFFFFF] hover:border-[#636CCB] text-[#3C467B] hover:bg-[#F3F6FF]'
                }`}
              >
                <div className="text-xs font-bold font-sans flex items-center justify-between">
                  <span>{tab.label}</span>
                  {isSelected && <FileCheck className="w-3.5 h-3.5 text-[#EAF0FF]" />}
                </div>
                <div
                  className={`text-[10px] font-sans mt-0.5 ${
                    isSelected ? 'text-[#EAF0FF]/90' : 'text-[#50589C]'
                  }`}
                >
                  {tab.sub}
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {/* Main Folder Document Drop Zone / Exhibit A Preview */}
      {!documentReady ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`relative cursor-pointer rounded-lg border transition-all duration-200 p-8 sm:p-12 text-center bg-[#FFFFFF] ${
            isDragOver
              ? 'border-[#3C467B] bg-[#F3F6FF] ring-1 ring-[#636CCB]'
              : 'border-[#DDE4FF] hover:border-[#636CCB] hover:bg-[#F3F6FF]'
          }`}
        >
          {/* Folder Tab Notch at top */}
          <div className="absolute -top-3.5 left-6 bg-[#EEF3FF] border-t border-l border-r border-[#DDE4FF] px-3.5 py-0.5 rounded-t text-[10px] font-sans font-medium text-[#50589C] flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#6E8CFB] border border-[#3C467B]/30" />
            <span>Folder Tab // {selectedDocumentType} Intake</span>
          </div>

          <div className="max-w-md mx-auto space-y-3">
            <div className="w-12 h-12 mx-auto rounded-lg bg-[#EEF3FF] border border-[#DDE4FF] flex items-center justify-center text-[#3C467B]">
              <Upload className="w-5 h-5" />
            </div>

            <div>
              <h3 className="font-editorial text-lg font-bold text-[#3C467B]">
                Deposit {selectedDocumentType.replace('_', ' ')} Specimen
              </h3>
              <p className="text-xs text-[#50589C] font-sans mt-1">
                Drag and drop a physical or scanned document file here, or{' '}
                <span className="text-[#3C467B] font-semibold underline underline-offset-2">
                  browse local archives
                </span>
              </p>
            </div>

            <div className="text-[11px] text-[#50589C] font-sans pt-1">
              Accepted archival formats: High-Resolution JPG, PNG, WEBP, or PDF
            </div>
          </div>

          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp,application/pdf"
            onChange={handleInputChange}
            className="hidden"
          />
        </div>
      ) : (
        <div className="space-y-4">
          <ExhibitCard
            label={`Exhibit A: ${selectedDocumentType.replace('_', ' ')} Specimen`}
            subtext={`Filed as ${currentFileName} • Optical resolution verified`}
            previewUrl={currentPreview}
            isPdf={isPdf}
            actionSlot={
              <button
                onClick={() => {
                  soundFX.paperSlide()
                  onClearDocument()
                }}
                className="flex items-center gap-1 text-xs text-[#6E6571] hover:text-[#755B73] transition-colors p-1"
                title="Remove exhibit"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Replace Specimen</span>
              </button>
            }
          />
        </div>
      )}

      {errorMessage && (
        <div className="p-3 rounded bg-[#755B73]/10 border border-[#755B73]/30 text-[#755B73] text-xs font-sans flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Step 1 CTA */}
      <div className="pt-4 flex justify-end">
        <button
          onClick={() => {
            soundFX.paperSlide()
            onProceedToStep2()
          }}
          disabled={!documentReady}
          className={`flex items-center gap-2 px-6 py-2.5 rounded text-xs font-sans font-medium transition-all ${
            documentReady
              ? 'bg-[#3C467B] hover:bg-[#50589C] text-[#FFFFFF] shadow-sm cursor-pointer'
              : 'bg-[#E3DCD6] text-[#6E6571] cursor-not-allowed'
          }`}
        >
          <span>
            {selectedDocumentType === 'VISA'
              ? 'Run Document Verification (Selfie Auto-Skipped)'
              : 'Continue to Step 2: Live Biometric Capture'}
          </span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
