import React from 'react'
import { Step1DocumentUpload } from './Step1DocumentUpload'
import { Step2WebcamCapture } from './Step2WebcamCapture'
import type { IntakeStep, DocumentType } from '../../types'
import { soundFX } from '../../utils/audio'
import { Check } from 'lucide-react'

interface IntakeContainerProps {
  intakeStep: IntakeStep
  onSetIntakeStep: (step: IntakeStep) => void
  selectedDocumentType: DocumentType
  onSelectDocumentType: (docType: DocumentType) => void
  uploadedFile: File | null
  filePreviewUrl: string | null
  capturedSelfieUrl: string | null
  onFileSelect: (file: File) => void
  onClearDocument: () => void
  onSelfieCaptured: (url: string) => void
  onClearSelfie: () => void
  onSubmitVerification: () => void
}

export const IntakeContainer: React.FC<IntakeContainerProps> = ({
  intakeStep,
  onSetIntakeStep,
  selectedDocumentType,
  onSelectDocumentType,
  uploadedFile,
  filePreviewUrl,
  capturedSelfieUrl,
  onFileSelect,
  onClearDocument,
  onSelfieCaptured,
  onClearSelfie,
  onSubmitVerification,
}) => {
  const isDocReady = Boolean(uploadedFile)
  const isBiometricReady = Boolean(capturedSelfieUrl)
  const isVisa = selectedDocumentType === 'VISA'

  const handleStep1Proceed = () => {
    if (isVisa) {
      // VISA auto-skips webcam capture and submits immediately
      onSubmitVerification()
    } else {
      onSetIntakeStep('step2_biometric')
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-6">
      {/* Folder Tab Intake Navigation */}
      <div className="flex border-b border-[#E3DCD6] space-x-2 select-none">
        {/* Tab 1 */}
        <button
          onClick={() => {
            soundFX.paperSlide()
            onSetIntakeStep('step1_document')
          }}
          className={`px-4 sm:px-6 py-2.5 rounded-t-md font-sans text-xs flex items-center gap-2 transition-all cursor-pointer ${
            intakeStep === 'step1_document'
              ? 'dossier-tab-active font-semibold text-[#3C467B]'
              : 'dossier-tab-inactive hover:text-[#3C467B]'
          }`}
        >
          <div
            className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-mono ${
              isDocReady
                ? 'bg-[#6E8CFB] text-[#ffffff] font-bold'
                : 'bg-[#E3DCD6] text-[#6E6571]'
            }`}
          >
            {isDocReady ? <Check className="w-2.5 h-2.5 stroke-[3]" /> : '1'}
          </div>
          <span>1. Document Intake</span>
        </button>

        {/* Tab 2 (Auto-disabled for VISA) */}
        {!isVisa && (
          <button
            onClick={() => {
              if (isDocReady) {
                soundFX.paperSlide()
                onSetIntakeStep('step2_biometric')
              }
            }}
            disabled={!isDocReady}
            className={`px-4 sm:px-6 py-2.5 rounded-t-md font-sans text-xs flex items-center gap-2 transition-all ${
              intakeStep === 'step2_biometric'
                ? 'dossier-tab-active font-semibold text-[#3C467B]'
                : isDocReady
                ? 'dossier-tab-inactive hover:text-[#3C467B] cursor-pointer'
                : 'bg-[#F8F5F3] border border-transparent text-[#C8BEB7] cursor-not-allowed'
            }`}
          >
            <div
              className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-mono ${
                isBiometricReady
                  ? 'bg-[#6E8CFB] text-[#ffffff] font-bold'
                  : 'bg-[#E3DCD6] text-[#6E6571]'
              }`}
            >
              {isBiometricReady ? <Check className="w-2.5 h-2.5 stroke-[3]" /> : '2'}
            </div>
            <span>2. Biometric Verification</span>
          </button>
        )}
      </div>

      {/* Main Dossier Content */}
      <div className="dossier-sheet rounded-b-lg rounded-tr-lg p-6 sm:p-8 bg-[#FFFFFF]">
        {intakeStep === 'step1_document' || isVisa ? (
          <Step1DocumentUpload
            uploadedFile={uploadedFile}
            filePreviewUrl={filePreviewUrl}
            selectedDocumentType={selectedDocumentType}
            onSelectDocumentType={onSelectDocumentType}
            onFileSelect={onFileSelect}
            onClearDocument={onClearDocument}
            onProceedToStep2={handleStep1Proceed}
          />
        ) : (
          <Step2WebcamCapture
            capturedSelfieUrl={capturedSelfieUrl}
            onSelfieCaptured={onSelfieCaptured}
            onClearSelfie={onClearSelfie}
            onBackToStep1={() => onSetIntakeStep('step1_document')}
            onSubmitForVerification={onSubmitVerification}
          />
        )}
      </div>
    </div>
  )
}
