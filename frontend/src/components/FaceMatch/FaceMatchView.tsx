import { useState, type FC } from 'react'
import { motion } from 'framer-motion'
import { FacePhotoPanel } from './FacePhotoPanel'
import { MatchConnector } from './MatchConnector'
import { SimilarityRing } from './SimilarityRing'
import { soundFX } from '../../utils/audio'
import { Play, RotateCcw, AlertTriangle } from 'lucide-react'
import { Card } from '../ui/card'
import { Button } from '../ui/button'
import { verifyFace } from '../../services/api'
import { toast } from 'sonner'

interface FaceMatchViewProps {
  initialDocumentPhoto?: string | null
  initialSelfiePhoto?: string | null
}

export const FaceMatchView: FC<FaceMatchViewProps> = ({
  initialDocumentPhoto = null,
  initialSelfiePhoto = null,
}) => {
  const [docPhoto, setDocPhoto] = useState<string | null>(initialDocumentPhoto)
  const [selfiePhoto, setSelfiePhoto] = useState<string | null>(initialSelfiePhoto)
  const [isScanning, setIsScanning] = useState(false)
  const [matchScore, setMatchScore] = useState<number | null>(null)
  const [matchDetails, setMatchDetails] = useState<{ status: string; distance?: number | null; detail: string; matched: boolean } | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const urlToBlob = async (url: string): Promise<Blob> => {
    const res = await fetch(url)
    return await res.blob()
  }

  const handleRunMatch = async () => {
    if (!docPhoto) {
      toast.error('Missing ID portrait', { description: 'Please provide Exhibit A: ID document portrait.' })
      return
    }
    if (!selfiePhoto) {
      toast.error('Missing live selfie', { description: 'Please capture or upload Exhibit B: Live Biometric selfie.' })
      return
    }

    soundFX.fieldInkLand()
    setIsScanning(true)
    setMatchScore(null)
    setMatchDetails(null)
    setErrorMessage(null)

    try {
      const [docBlob, selfieBlob] = await Promise.all([
        urlToBlob(docPhoto),
        urlToBlob(selfiePhoto),
      ])

      const result = await verifyFace(docBlob, selfieBlob)
      setIsScanning(false)
      setMatchScore(result.score)
      setMatchDetails({
        status: result.status,
        distance: result.distance,
        detail: result.detail,
        matched: result.matched,
      })

      if (result.matched) {
        soundFX.stampImpact(130)
      } else {
        soundFX.stampImpact(result.score >= 50 ? 110 : 85)
      }
    } catch (err: any) {
      setIsScanning(false)
      setErrorMessage(err.message || 'Face biometric verification failed.')
      soundFX.tamperAlert()
    }
  }

  const handleReset = () => {
    soundFX.paperSlide()
    setMatchScore(null)
    setMatchDetails(null)
    setErrorMessage(null)
    setIsScanning(false)
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-[#E5DDD8] dark:border-[#1C345C]">
        <div>
          <h2 className="font-editorial text-2xl sm:text-3xl font-bold text-[var(--page-heading)]">
            Biometric Face Verification
          </h2>
          <p className="text-xs sm:text-sm text-[var(--page-secondary)] font-sans mt-0.5">
            Compare facial landmarks between primary identification portrait and live webcam capture.
          </p>
        </div>

      </div>

      {/* Main Comparison Stage */}
      <div className="grid grid-cols-1 lg:grid-cols-7 gap-4 items-center">
        {/* Left: Document Photo (3 cols) */}
        <div className="lg:col-span-3">
          <FacePhotoPanel
            title="Exhibit A: ID Document Portrait"
            subtitle="Extracted from high-resolution scan"
            type="document"
            photoUrl={docPhoto}
            onPhotoUploaded={(file) => {
              const url = URL.createObjectURL(file)
              setDocPhoto(url)
              setMatchScore(null)
            }}
            isScanning={isScanning}
          />
        </div>

        {/* Center: Match Connector (1 col) */}
        <div className="lg:col-span-1 flex justify-center">
          <MatchConnector isScanning={isScanning} />
        </div>

        {/* Right: Live Webcam Capture (3 cols) */}
        <div className="lg:col-span-3">
          <FacePhotoPanel
            title="Exhibit B: Live Biometric Capture"
            subtitle="Webcam stream with landmark reticle"
            type="webcam"
            photoUrl={selfiePhoto}
            onPhotoCaptured={(url) => {
              setSelfiePhoto(url || null)
              setMatchScore(null)
            }}
            isScanning={isScanning}
          />
        </div>
      </div>

      {/* Action / Results Zone */}
      <Card className="rounded-2xl p-6 text-center space-y-4 border-[#E5DDD8] dark:border-[#1C345C] bg-[#FFFFFF] dark:bg-[#111C30]">
        {matchScore === null && !isScanning && (
          <div className="space-y-3 max-w-md mx-auto">
            <p className="text-xs text-[var(--page-secondary)]">
              Ensure both exhibits are acquired, then run the 128-dimensional facial embedding comparison.
            </p>
            <Button
              onClick={handleRunMatch}
              className="gap-2 bg-[#3C467B] hover:bg-[#50589C] dark:bg-[#334FE0] dark:hover:bg-[#3D8FD8] text-white font-bold cursor-pointer"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>Run Biometric Comparison</span>
            </Button>
          </div>
        )}

        {isScanning && (
          <div className="space-y-2 py-4">
            <div className="text-sm font-bold text-[var(--page-heading)]">
              Extracting ArcFace-R100 Embeddings…
            </div>
            <p className="text-xs text-[var(--page-secondary)]">
              Calculating cosine similarity distance across facial landmark vectors
            </p>
          </div>
        )}

        {/* Error Banner */}
        {errorMessage && !isScanning && (
          <div className="p-3.5 rounded-xl bg-[#DC2626]/10 border border-[#DC2626]/30 text-xs font-mono text-[#DC2626] flex items-start gap-2 max-w-md mx-auto text-left">
            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold block">Biometric Capture Error</span>
              <span>{errorMessage}</span>
            </div>
          </div>
        )}

        {matchScore !== null && !isScanning && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="space-y-4 py-2"
          >
            {/* Animated Circular Progress Ring + Count-up */}
            <SimilarityRing score={matchScore} />

            {matchDetails && (
              <div className="flex items-center justify-center gap-4 text-xs font-mono text-[#755B73]">
                <span>Status: <strong className={matchDetails.matched ? 'text-emerald-700 font-bold' : 'text-[#DC2626] font-bold'}>{matchDetails.status.toUpperCase()}</strong></span>
                {matchDetails.distance !== undefined && matchDetails.distance !== null && (
                  <span>Distance: <strong>{matchDetails.distance.toFixed(4)}</strong></span>
                )}
                <span>Threshold: <strong>0.68</strong></span>
              </div>
            )}

            <div className="max-w-md mx-auto text-xs text-[#755B73] pt-2 border-t border-[#E5DDD8]">
              {matchDetails?.detail || (
                matchScore >= 70
                  ? 'Facial structural correlation is within official verified tolerances.'
                  : matchScore >= 50
                  ? 'Borderline biometric variance detected. Secondary visual inspection recommended.'
                  : 'Significant biometric disparity. The live subject does not match the document portrait.'
              )}
            </div>

            <div className="pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleReset}
                className="gap-1.5 text-xs border-[#E5DDD8] text-[#27212B] bg-[#FFFFFF] hover:bg-[#F8F5F3] cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Re-evaluate Comparison</span>
              </Button>
            </div>
          </motion.div>
        )}
      </Card>
    </div>
  )
}
