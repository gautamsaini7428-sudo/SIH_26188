import { useRef, useState, useEffect, type FC } from 'react'
import { Camera, RotateCcw, Upload, Check } from 'lucide-react'
import { soundFX } from '../../utils/audio'

interface FacePhotoPanelProps {
  title: string
  subtitle: string
  type: 'document' | 'webcam'
  photoUrl: string | null
  onPhotoCaptured?: (url: string) => void
  onPhotoUploaded?: (file: File) => void
  isScanning: boolean
}

export const FacePhotoPanel: FC<FacePhotoPanelProps> = ({
  title,
  subtitle,
  type,
  photoUrl,
  onPhotoCaptured,
  onPhotoUploaded,
  isScanning,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [isCameraActive, setIsCameraActive] = useState(false)
  const [cameraError, setCameraError] = useState<string | null>(null)

  // Start webcam for webcam type if photo not captured yet
  useEffect(() => {
    let activeStream: MediaStream | null = null

    if (type === 'webcam' && !photoUrl) {
      startCamera().then((s) => {
        if (s) activeStream = s
      })
    }

    return () => {
      if (activeStream) activeStream.getTracks().forEach((t) => t.stop())
      if (stream) stream.getTracks().forEach((t) => t.stop())
    }
  }, [type, photoUrl])

  const startCamera = async () => {
    setCameraError(null)
    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        const s = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
        })
        setStream(s)
        setIsCameraActive(true)
        if (videoRef.current) {
          videoRef.current.srcObject = s
          videoRef.current.play().catch(() => {})
        }
        return s
      } else {
        setCameraError('Camera not supported')
        return null
      }
    } catch {
      setCameraError('Webcam unavailable')
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
        if (onPhotoCaptured) onPhotoCaptured(dataUrl)

        if (stream) {
          stream.getTracks().forEach((t) => t.stop())
          setStream(null)
          setIsCameraActive(false)
        }
        return
      }
    }

    // Fallback sample capture
    const sampleSVG = `data:image/svg+xml;utf8,${encodeURIComponent(`
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 360" width="100%" height="100%" style="background:#F2ECE9;">
  <rect width="300" height="360" fill="#EAE2DC"/>
  <circle cx="150" cy="140" r="65" fill="#BDB0A6"/>
  <ellipse cx="150" cy="300" rx="100" ry="75" fill="#BDB0A6"/>
  <path d="M 120 135 Q 135 125 150 135 Q 165 125 180 135" stroke="#7A7068" stroke-width="3" fill="none"/>
  <text x="150" y="340" fill="#0B2925" font-family="Georgia, serif" font-size="12" font-weight="600" text-anchor="middle">LIVE BIOMETRIC FEED</text>
</svg>`)}`
    if (onPhotoCaptured) onPhotoCaptured(sampleSVG)
  }

  const handleRetake = () => {
    soundFX.paperSlide()
    if (onPhotoCaptured) onPhotoCaptured('')
    startCamera()
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files[0] && onPhotoUploaded) {
      soundFX.paperSlide()
      onPhotoUploaded(files[0])
    }
  }

  return (
    <div className="dossier-sheet rounded-lg p-4 sm:p-5 flex flex-col justify-between h-full space-y-3 dark:bg-[#111C30] dark:border-[#1C345C]">
      {/* Header */}
      <div className="flex items-center justify-between pb-2.5 border-b border-[#E3DCD6] dark:border-[#1C345C]">
        <div>
          <h4 className="font-editorial text-sm sm:text-base font-bold text-[#0B2925] dark:text-[#DEF4F2]">
            {title}
          </h4>
          <p className="text-[11px] text-[#6E6571] dark:text-[#AAB6C8] font-sans">{subtitle}</p>
        </div>
        {photoUrl && (
          <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-[#A7F3D0]/30 dark:bg-[#20B9A7]/20 text-[#0B2925] dark:text-[#DEF4F2] border border-[#0B2925]/20 dark:border-[#20B9A7]/40 flex items-center gap-1">
            <Check className="w-2.5 h-2.5 stroke-[3]" />
            Acquired
          </span>
        )}
      </div>

      {/* Main Viewport */}
      <div className="relative aspect-[4/3] w-full rounded border border-[#E3DCD6] dark:border-[#1C345C] bg-[#FCFAF8] dark:bg-[#0C162F] overflow-hidden flex items-center justify-center">
        {photoUrl ? (
          <img
            src={photoUrl}
            alt={title}
            className="w-full h-full object-cover select-none"
          />
        ) : type === 'webcam' ? (
          <>
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className={`w-full h-full object-cover transform -scale-x-100 ${
                isCameraActive ? 'block' : 'hidden'
              }`}
            />
            {isCameraActive && (
              <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                <div className="w-36 h-48 rounded-[50%] border-2 border-dashed border-[#FFFFFF]/80 shadow-[0_0_0_9999px_rgba(39,33,43,0.3)]" />
              </div>
            )}
            {!isCameraActive && (
              <div className="text-center p-4 space-y-2">
                <div className="w-10 h-10 mx-auto rounded bg-[#F2ECE9] dark:bg-[#1C345C] border border-[#E3DCD6] dark:border-[#1C345C] flex items-center justify-center text-[#0B2925] dark:text-[#6AC7D4]">
                  <Camera className="w-4 h-4" />
                </div>
                <div className="text-xs text-[#6E6571] dark:text-[#AAB6C8] font-sans">
                  {cameraError || 'Webcam Standby'}
                </div>
                <button
                  onClick={handleCapture}
                  className="px-3 py-1 rounded border border-[#0B2925] dark:border-[#3D8FD8] bg-[#FFFFFF] dark:bg-[#334FE0] text-[11px] font-sans text-[#0B2925] dark:text-white hover:bg-[#F2ECE9] dark:hover:bg-[#3D8FD8]"
                >
                  Use Sample Biometric Feed
                </button>
              </div>
            )}
          </>
        ) : (
          <div
            onClick={() => fileInputRef.current?.click()}
            className="text-center p-6 cursor-pointer hover:bg-[#F2ECE9]/50 dark:hover:bg-[#1C345C] transition-colors w-full h-full flex flex-col items-center justify-center space-y-2"
          >
            <div className="w-10 h-10 rounded bg-[#F2ECE9] dark:bg-[#1C345C] border border-[#E3DCD6] dark:border-[#1C345C] flex items-center justify-center text-[#0B2925] dark:text-[#6AC7D4]">
              <Upload className="w-4 h-4" />
            </div>
            <div className="text-xs font-sans text-[#27212B] dark:text-[#DEF4F2] font-medium">
              Upload ID Photo
            </div>
            <div className="text-[11px] text-[#6E6571] dark:text-[#AAB6C8] font-sans">
              Click to select photo image
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileUpload}
              className="hidden"
            />
          </div>
        )}

        {/* Scanning Reticle Overlay */}
        {isScanning && photoUrl && (
          <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
            <div className="w-36 h-48 rounded-[50%] border-2 border-[#0B2925] animate-pulse shadow-[0_0_0_9999px_rgba(11,41,37,0.15)]" />
            {/* Corner brackets */}
            <div className="absolute top-4 left-4 w-4 h-4 border-t-2 border-l-2 border-[#0B2925]" />
            <div className="absolute top-4 right-4 w-4 h-4 border-t-2 border-r-2 border-[#0B2925]" />
            <div className="absolute bottom-4 left-4 w-4 h-4 border-b-2 border-l-2 border-[#0B2925]" />
            <div className="absolute bottom-4 right-4 w-4 h-4 border-b-2 border-r-2 border-[#0B2925]" />
          </div>
        )}
      </div>

      {/* Footer Controls */}
      <div className="flex items-center justify-between pt-1">
        {type === 'webcam' ? (
          photoUrl ? (
            <button
              onClick={handleRetake}
              disabled={isScanning}
              className="flex items-center gap-1.5 text-xs text-[#6E6571] hover:text-[#0B2925] transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Retake Photo</span>
            </button>
          ) : (
            isCameraActive && (
              <button
                onClick={handleCapture}
                className="w-full flex items-center justify-center gap-1.5 py-1.5 rounded bg-[#0B2925] text-[#FFFFFF] text-xs font-sans font-medium hover:bg-[#16433C] transition-colors shadow-xs"
              >
                <Camera className="w-3.5 h-3.5" />
                <span>Capture Live Frame</span>
              </button>
            )
          )
        ) : (
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isScanning}
            className="flex items-center gap-1.5 text-xs text-[#6E6571] hover:text-[#0B2925] transition-colors"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>{photoUrl ? 'Replace Photo' : 'Choose Photo'}</span>
          </button>
        )}
      </div>
    </div>
  )
}
