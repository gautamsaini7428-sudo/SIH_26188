import React, { useRef, useState, useEffect } from 'react'
import { Camera, RotateCcw, ArrowLeft, ArrowRight } from 'lucide-react'
import { Card } from '../ui/card'
import { Button } from '../ui/button'
import { ExhibitCard } from '../IntakeFlow/ExhibitCard'
import { soundFX } from '../../utils/audio'

interface WebcamCaptureProps {
  capturedSelfieUrl: string | null
  onSelfieCaptured: (url: string) => void
  onClearSelfie: () => void
  onBackToStep1: () => void
  onSubmitForVerification: () => void
}

export const WebcamCapture: React.FC<WebcamCaptureProps> = ({
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
        ctx.translate(canvas.width, 0)
        ctx.scale(-1, 1)
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
        const dataUrl = canvas.toDataURL('image/jpeg', 0.9)
        onSelfieCaptured(dataUrl)

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
      {/* Header */}
      <div className="space-y-1">
        <h2 className="text-2xl sm:text-3xl font-bold text-[#27212B] tracking-tight font-editorial">
          Step 2 of 2: Live Facial Biometric Capture
        </h2>
        <p className="text-xs sm:text-sm text-[#755B73]">
          A live facial capture is required to compare physical biometric landmarks against Exhibit A.
        </p>
      </div>

      {/* Main Viewport */}
      {!capturedSelfieUrl ? (
        <Card className="p-6 space-y-4 border-[#E5DDD8] bg-[#FFFFFF]">
          <div className="relative aspect-[4/3] max-w-lg mx-auto rounded-xl border border-[#E5DDD8] bg-[#F8F5F3] overflow-hidden flex items-center justify-center">
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

            {/* Viewfinder Guide */}
            {isCameraActive && (
              <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                <div className="w-48 h-64 rounded-[50%] border-2 border-dashed border-[#A7F3D0] shadow-[0_0_0_9999px_rgba(11,41,37,0.35)]" />
                <span className="absolute bottom-6 px-3 py-1 rounded-lg bg-[#0B2925] text-[#F8F5F3] text-xs font-semibold">
                  Align face within the frame
                </span>
              </div>
            )}

            {/* Camera Offline Fallback */}
            {!isCameraActive && (
              <div className="text-center p-6 space-y-3 max-w-sm">
                <div className="w-12 h-12 mx-auto rounded-xl bg-[#FFFFFF] border border-[#E5DDD8] flex items-center justify-center text-[#0B2925] shadow-xs">
                  <Camera className="w-6 h-6 text-[#0B2925]" />
                </div>
                <div>
                  <h4 className="text-base font-bold text-[#27212B]">
                    {cameraError ? 'Camera Standby / Offline' : 'Initializing Webcam...'}
                  </h4>
                  <p className="text-xs text-[#755B73] mt-1">
                    {cameraError || 'Please allow browser camera permissions when prompted.'}
                  </p>
                </div>
                <Button variant="outline" size="sm" onClick={startWebcam} className="text-xs border-[#E5DDD8] text-[#27212B] bg-[#FFFFFF] hover:bg-[#F8F5F3] cursor-pointer">
                  Retry Camera Connection
                </Button>
              </div>
            )}
          </div>

          {/* Trigger Button */}
          {isCameraActive && (
            <div className="flex justify-center pt-2">
              <Button onClick={handleCapture} className="gap-2 bg-[#0B2925] hover:bg-[#133D37] text-[#F8F5F3] font-bold cursor-pointer">
                <Camera className="w-4 h-4" />
                <span>Capture Live Biometric Photo</span>
              </Button>
            </div>
          )}
        </Card>
      ) : (
        <div className="space-y-4">
          <ExhibitCard
            label="Exhibit B: Live Biometric Capture"
            subtext="Timestamped and embedded for 512-dimensional facial vector correlation"
            previewUrl={capturedSelfieUrl}
            actionSlot={
              <Button variant="ghost" size="sm" onClick={handleRetake} className="gap-1 text-xs text-[#755B73] hover:text-[#27212B]">
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Retake Photo</span>
              </Button>
            }
          />
        </div>
      )}

      {/* Navigation Actions */}
      <div className="pt-4 flex items-center justify-between border-t border-[#E5DDD8]">
        <Button variant="outline" onClick={onBackToStep1} className="gap-1.5 text-xs border-[#E5DDD8] text-[#27212B] bg-[#FFFFFF] hover:bg-[#F8F5F3] cursor-pointer">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Step 1</span>
        </Button>

        <Button onClick={onSubmitForVerification} disabled={!capturedSelfieUrl} size="lg" className="gap-2 bg-[#0B2925] hover:bg-[#133D37] text-[#F8F5F3] font-bold cursor-pointer">
          <span>Submit Case File for Verification</span>
          <ArrowRight className="w-4 h-4" />
        </Button>
      </div>
    </div>
  )
}
