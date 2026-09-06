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
        <h2 className="text-2xl sm:text-3xl font-bold text-[#3C467B] dark:text-[#DEF4F2] tracking-tight font-editorial">
          Step 2 of 2: Live Facial Biometric Capture
        </h2>
        <p className="text-xs sm:text-sm text-[#50589C] dark:text-[#AAB6C8]">
          A live facial capture is required to compare physical biometric landmarks against Exhibit A.
        </p>
      </div>

      {/* Main Viewport */}
      {!capturedSelfieUrl ? (
        <Card className="p-6 space-y-4 border-[#DDE4FF] dark:border-[#1C345C] bg-[#FFFFFF] dark:bg-[#111C30]">
          <div className="relative aspect-[4/3] max-w-lg mx-auto rounded-xl border border-[#DDE4FF] dark:border-[#1C345C] bg-[#F3F6FF] dark:bg-[#0C162F] overflow-hidden flex items-center justify-center">
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
                <div className="w-12 h-12 mx-auto rounded-xl bg-[#EAF0FF] dark:bg-[#1C345C] border border-[#DDE4FF] dark:border-[#3D8FD8] flex items-center justify-center text-[#3C467B] dark:text-[#6AC7D4] shadow-xs">
                  <Camera className="w-6 h-6 text-[#3C467B] dark:text-[#6AC7D4]" />
                </div>
                <div>
                  <h4 className="text-base font-bold text-[#3C467B] dark:text-[#DEF4F2]">
                    {cameraError ? 'Camera Standby / Offline' : 'Initializing Webcam...'}
                  </h4>
                  <p className="text-xs text-[#50589C] dark:text-[#AAB6C8] mt-1">
                    {cameraError || 'Please allow browser camera permissions when prompted.'}
                  </p>
                </div>
                <Button variant="outline" size="sm" onClick={startWebcam} className="text-xs !text-[#3C467B] dark:!text-[#DEF4F2] border-[#DDE4FF] dark:border-[#1C345C] bg-[#FFFFFF] dark:bg-[#111C30] hover:bg-[#F3F6FF] dark:hover:bg-[#1C345C] cursor-pointer">
                  Retry Camera Connection
                </Button>
              </div>
            )}
          </div>

          {/* Trigger Button */}
          {isCameraActive && (
            <div className="flex justify-center pt-2">
              <Button onClick={handleCapture} className="gap-2 bg-[#3C467B] dark:bg-[#334FE0] hover:bg-[#50589C] dark:hover:bg-[#3D8FD8] text-white font-bold cursor-pointer">
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
            subtext="Timestamped and embedded for 128-dimensional facial vector correlation"
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
      <div className="pt-4 flex items-center justify-between border-t border-[#DDE4FF] dark:border-[#1C345C]">
        <Button variant="outline" onClick={onBackToStep1} className="gap-1.5 text-xs !text-[#3C467B] dark:!text-[#DEF4F2] border-[#DDE4FF] dark:border-[#1C345C] bg-[#FFFFFF] dark:bg-[#111C30] hover:bg-[#F3F6FF] dark:hover:bg-[#1C345C] cursor-pointer">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Step 1</span>
        </Button>

        <Button onClick={onSubmitForVerification} disabled={!capturedSelfieUrl} size="lg" className="gap-2 bg-[#3C467B] dark:bg-[#334FE0] hover:bg-[#50589C] dark:hover:bg-[#3D8FD8] text-white font-bold cursor-pointer">
          <span>Submit Case File for Verification</span>
          <ArrowRight className="w-4 h-4" />
        </Button>
      </div>
    </div>
  )
}
