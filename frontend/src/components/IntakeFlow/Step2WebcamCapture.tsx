import { useRef, useState, useEffect } from 'react'
import { Camera, RotateCcw, ArrowLeft, ArrowRight } from 'lucide-react'
import { ExhibitCard } from './ExhibitCard'
import { soundFX } from '../../utils/audio'

interface Step2WebcamCaptureProps {
  capturedSelfieUrl: string | null
  onSelfieCaptured: (url: string) => void
  onClearSelfie: () => void
  onBackToStep1: () => void
  onSubmitForVerification: () => void
}

export const Step2WebcamCapture: React.FC<Step2WebcamCaptureProps> = ({
  capturedSelfieUrl,
  onSelfieCaptured,
  onClearSelfie,
  onBackToStep1,
  onSubmitForVerification,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [cameraError, setCameraError] = useState<string | null>(null)
  const [isCameraActive, setIsCameraActive] = useState(false)

  // Start webcam on mount if not already captured
  useEffect(() => {
    let activeStream: MediaStream | null = null

    if (!capturedSelfieUrl) {
      startWebcam().then((s) => {
        if (s) activeStream = s
      })
    }

    return () => {
      if (activeStream) {
        activeStream.getTracks().forEach((track) => track.stop())
      }
      if (stream) {
        stream.getTracks().forEach((track) => track.stop())
      }
    }
  }, [capturedSelfieUrl])

  const startWebcam = async (): Promise<MediaStream | null> => {
    setCameraError(null)
    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
          audio: false,
        })
        setStream(mediaStream)
        setIsCameraActive(true)
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream
          videoRef.current.play().catch(() => {})
        }
        return mediaStream
      } else {
        setCameraError('CAMERA_UNAVAILABLE: Webcam API is not supported in this browser environment.')
        return null
      }
    } catch (err) {
      console.warn('Unable to access webcam:', err)
      setCameraError('CAMERA_UNAVAILABLE: Live camera stream could not be established. Ensure camera hardware is connected and browser permission is granted.')
      setIsCameraActive(false)
      return null
    }
  }

  const handleCapture = () => {
    soundFX.cameraShutter()

    if (videoRef.current && isCameraActive) {
      const video = videoRef.current
      const canvas = document.createElement('canvas')
      canvas.width = video.videoWidth || 640
      canvas.height = video.videoHeight || 480
      const ctx = canvas.getContext('2d')
      if (ctx) {
        // Mirror horizontally for natural selfie view
        ctx.translate(canvas.width, 0)
        ctx.scale(-1, 1)
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
        const dataUrl = canvas.toDataURL('image/jpeg', 0.9)
        onSelfieCaptured(dataUrl)

        // Stop camera stream
        if (stream) {
          stream.getTracks().forEach((track) => track.stop())
          setStream(null)
          setIsCameraActive(false)
        }
        return
      }
    }
  }

  const handleRetake = () => {
    soundFX.paperSlide()
    onClearSelfie()
    startWebcam()
  }

  return (
    <div className="space-y-6">
      {/* Step Header */}
      <div className="space-y-1">
        <h2 className="font-editorial text-2xl sm:text-3xl font-bold text-[#3C467B]">
          Step 2 of 2: Verify It&apos;s You (Biometric Capture)
        </h2>
        <p className="text-xs sm:text-sm text-[#50589C] font-sans">
          A live facial capture is required to compare physical biometric landmarks against Exhibit A.
        </p>
      </div>

      {/* Main Viewport: Live Webcam Viewfinder OR Exhibit B Card */}
      {!capturedSelfieUrl ? (
        <div className="dossier-sheet rounded-lg p-5 sm:p-6 space-y-4">
          <div className="relative aspect-[4/3] max-w-lg mx-auto rounded border border-[#E3DCD6] bg-[#FCFAF8] overflow-hidden flex items-center justify-center">
            {/* Live Video Stream */}
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className={`w-full h-full object-cover transform -scale-x-100 ${
                isCameraActive ? 'block' : 'hidden'
              }`}
            />

            {/* Viewfinder Oval Outline Guide */}
            {isCameraActive && (
              <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                <div className="w-48 h-64 rounded-[50%] border-2 border-dashed border-[#EAF0FF]/80 shadow-[0_0_0_9999px_rgba(60,70,123,0.28)]" />
                <span className="absolute bottom-6 px-3 py-1 rounded bg-[#3C467B]/85 text-[#FFFFFF] text-[11px] font-sans">
                  Align face within the frame
                </span>
              </div>
            )}

            {/* Camera Loading or Error Fallback View */}
            {!isCameraActive && (
              <div className="text-center p-6 space-y-3 max-w-sm">
                <div className="w-12 h-12 mx-auto rounded bg-[#EEF3FF] border border-[#DDE4FF] flex items-center justify-center text-[#3C467B]">
                  <Camera className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-editorial text-base font-bold text-[#3C467B]">
                    {cameraError ? 'Camera Standby / Offline' : 'Initializing Webcam...'}
                  </h4>
                  <p className="text-xs text-[#50589C] font-sans mt-1">
                    {cameraError || 'Please allow browser camera permissions when prompted.'}
                  </p>
                </div>
                <button
                  onClick={startWebcam}
                  className="px-3.5 py-1.5 rounded border border-[#3C467B] bg-[#FFFFFF] hover:bg-[#EEF3FF] text-[#3C467B] text-xs font-sans font-medium transition-colors cursor-pointer"
                >
                  Retry Camera Connection
                </button>
              </div>
            )}
          </div>

          {/* Shutter Trigger Button */}
          {isCameraActive && (
            <div className="flex justify-center pt-2">
              <button
                onClick={handleCapture}
                className="flex items-center gap-2 px-6 py-2.5 rounded bg-[#3C467B] hover:bg-[#50589C] text-[#FFFFFF] text-xs font-sans font-medium shadow-sm transition-all"
              >
                <Camera className="w-4 h-4" />
                <span>Capture Live Biometric Photo</span>
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          <ExhibitCard
            label="Exhibit B: Live Biometric Capture"
            subtext="Timestamped and embedded for 128-dimensional facial vector correlation"
            previewUrl={capturedSelfieUrl}
            actionSlot={
              <button
                onClick={handleRetake}
                className="flex items-center gap-1 text-xs text-[#6E6571] hover:text-[#0B2925] transition-colors p-1"
                title="Retake capture"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Retake Photo</span>
              </button>
            }
          />
        </div>
      )}

      {/* Navigation Actions */}
      <div className="pt-4 flex items-center justify-between border-t border-[#E3DCD6]">
        <button
          onClick={() => {
            soundFX.paperSlide()
            onBackToStep1()
          }}
          className="flex items-center gap-1.5 px-4 py-2 rounded border border-[#DDE4FF] bg-[#FFFFFF] hover:bg-[#F3F6FF] text-[#3C467B] text-xs font-sans transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Step 1</span>
        </button>

        <button
          onClick={() => {
            soundFX.paperSlide()
            onSubmitForVerification()
          }}
          disabled={!capturedSelfieUrl}
          className={`flex items-center gap-2 px-6 py-2.5 rounded text-xs font-sans font-medium transition-all ${
            capturedSelfieUrl
              ? 'bg-[#3C467B] hover:bg-[#50589C] text-[#FFFFFF] shadow-sm cursor-pointer'
              : 'bg-[#E3DCD6] text-[#6E6571] cursor-not-allowed'
          }`}
        >
          <span>Submit Case File for Verification</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
