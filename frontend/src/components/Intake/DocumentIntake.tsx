import React, { useRef, useState } from 'react'
import { Upload, ArrowRight, AlertCircle, Trash2, FileCheck } from 'lucide-react'
import { Tabs, TabsList, TabsTrigger } from '../ui/tabs'
import { Card } from '../ui/card'
import { Button } from '../ui/button'
import { ExhibitCard } from '../IntakeFlow/ExhibitCard'
import type { DocumentType } from '../../types'
import { soundFX } from '../../utils/audio'

interface DocumentIntakeProps {
  uploadedFile: File | null
  filePreviewUrl: string | null
  selectedDocumentType: DocumentType
  onSelectDocumentType: (docType: DocumentType) => void
  onFileSelect: (file: File) => void
  onClearDocument: () => void
  onProceedToNextStep: () => void
}

const DOCUMENT_TYPES: { type: DocumentType; label: string; sub: string }[] = [
  { type: 'PASSPORT', label: 'Passport', sub: 'ICAO 9303 TD3' },
  { type: 'VISA', label: 'Visa', sub: 'Entry Permit (No Face)' },
  { type: 'NATIONAL_ID', label: 'National ID', sub: 'Aadhaar / Voter ID' },
  { type: 'DRIVING_LICENSE', label: 'Driving License', sub: 'State DMV' },
  { type: 'PERMIT', label: 'Permit', sub: 'Border / Transit' },
]

export const DocumentIntake: React.FC<DocumentIntakeProps> = ({
  uploadedFile,
  filePreviewUrl,
  selectedDocumentType,
  onSelectDocumentType,
  onFileSelect,
  onClearDocument,
  onProceedToNextStep,
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
      {/* Page Header */}
      <div className="space-y-1">
        <h2 className="text-2xl sm:text-3xl font-bold text-[#3C467B] tracking-tight font-editorial">
          Step 1: Document Classification &amp; Specimen Deposit
        </h2>
        <p className="text-xs sm:text-sm text-[#50589C]">
          Select the document category, then deposit the physical or scanned specimen into the border case file.
        </p>
      </div>

      {/* Clean Sentence-Case Section Heading */}
      <div className="space-y-2">
        <label className="text-xs font-semibold text-[#3C467B] block">
          Document Category
        </label>
        <Tabs
          value={selectedDocumentType}
          onValueChange={(val) => {
            soundFX.paperSlide()
            onSelectDocumentType(val as DocumentType)
          }}
          className="w-full"
        >
          <TabsList className="w-full grid grid-cols-2 sm:grid-cols-5 h-auto p-1.5 gap-1.5 bg-[#FFFFFF] border border-[#DDE4FF] rounded-xl shadow-xs">
            {DOCUMENT_TYPES.map((t) => (
              <TabsTrigger
                key={t.type}
                value={t.type}
                className="flex-col items-start py-2.5 px-3 text-left text-[#50589C] bg-transparent data-[state=active]:bg-[#EAF0FF] data-[state=active]:text-[#3C467B] data-[state=active]:shadow-2xs transition-all rounded-lg"
              >
                <div className="flex items-center justify-between w-full font-semibold text-xs">
                  <span>{t.label}</span>
                  {selectedDocumentType === t.type && <FileCheck className="w-3.5 h-3.5 text-[#3C467B]" />}
                </div>
                <span className="text-[10px] text-[#50589C] mt-0.5 font-normal">{t.sub}</span>
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </div>

      {/* DOCUMENT DROPZONE CARD */}
      {!documentReady ? (
        <Card
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`cursor-pointer border-dashed p-8 sm:p-12 text-center transition-all bg-[#FFFFFF] border-[#DDE4FF] ${
            isDragOver ? 'border-[#3C467B] bg-[#F3F6FF]' : 'hover:border-[#636CCB]/60 hover:bg-[#F3F6FF]'
          }`}
        >
          <div className="max-w-md mx-auto space-y-4">
            <div className="w-12 h-12 mx-auto rounded-xl bg-[#EEF3FF] border border-[#DDE4FF] flex items-center justify-center text-[#3C467B] shadow-xs">
              <Upload className="w-6 h-6 text-[#3C467B]" />
            </div>

            <div>
              <h3 className="text-lg font-bold text-[#3C467B]">
                Deposit {selectedDocumentType.replace('_', ' ')} Specimen
              </h3>
              <p className="text-xs text-[#50589C] mt-1">
                Drag and drop a physical or scanned document file here, or{' '}
                <span className="text-[#3C467B] font-semibold underline underline-offset-2">
                  browse local archives
                </span>
              </p>
            </div>

            <div className="text-[11px] text-[#50589C] font-mono">
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
        </Card>
      ) : (
        <div className="space-y-4">
          <ExhibitCard
            label={`Exhibit A: ${selectedDocumentType.replace('_', ' ')} Specimen`}
            subtext={`Filed as ${currentFileName} • Optical resolution verified`}
            previewUrl={currentPreview}
            isPdf={isPdf}
            actionSlot={
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  soundFX.paperSlide()
                  onClearDocument()
                }}
                className="gap-1 text-xs text-[#755B73] hover:text-[#DC2626]"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Replace Specimen</span>
              </Button>
            }
          />
        </div>
      )}

      {errorMessage && (
        <div className="p-3 rounded-xl bg-[#FBDADA] border border-[#DC2626]/30 text-[#8A2323] text-xs font-medium flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* STEP 1 NEXT CTA */}
      <div className="pt-2 flex justify-end">
        <Button
          onClick={() => {
            soundFX.paperSlide()
            onProceedToNextStep()
          }}
          disabled={!documentReady}
          size="lg"
          className="gap-2 bg-[#3C467B] hover:bg-[#50589C] text-[#ffffff] font-bold cursor-pointer"
        >
          <span>
            {selectedDocumentType === 'VISA'
              ? 'Run Document Verification (Selfie Auto-Skipped)'
              : 'Continue to Step 2: Live Biometric Capture'}
          </span>
          <ArrowRight className="w-4 h-4" />
        </Button>
      </div>
    </div>
  )
}
