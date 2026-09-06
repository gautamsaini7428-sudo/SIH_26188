import React, { useState } from 'react'
import { Eye, Layers, AlertTriangle } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import type { TamperingRegion } from '../../types'

interface TamperingHeatmapProps {
  score: number
  heatmapImageBase64?: string
  regions: TamperingRegion[]
  originalPreviewUrl: string
}

export const TamperingHeatmap: React.FC<TamperingHeatmapProps> = ({
  score,
  heatmapImageBase64,
  regions,
  originalPreviewUrl,
}) => {
  const [showHeatmapOverlay, setShowHeatmapOverlay] = useState(true)

  const isHighTampering = score > 70
  const isSuspiciousTampering = score > 30

  return (
    <Card className="border-[#E5DDD8] bg-[#FFFFFF]">
      <CardHeader className="pb-3 flex flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle className="text-sm font-semibold text-[#27212B] flex items-center gap-2">
            <Layers className="w-4 h-4 text-[#0B2925]" />
            <span>Forensic Tampering &amp; ELA Analysis</span>
          </CardTitle>
          <p className="text-xs text-[#755B73] mt-0.5">
            Error Level Analysis (ELA), JPEG compression noise grid, &amp; font splicing detector
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge
            variant={isHighTampering ? 'destructive' : isSuspiciousTampering ? 'warning' : 'success'}
            className="font-mono text-xs"
          >
            {score}/100 Tamper Score
          </Badge>

          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowHeatmapOverlay((prev) => !prev)}
            className="gap-1.5 text-xs border-[#E5DDD8] text-[#27212B] bg-[#FFFFFF] hover:bg-[#F8F5F3] cursor-pointer"
          >
            <Eye className="w-3.5 h-3.5" />
            <span>{showHeatmapOverlay ? 'Hide Heatmap Overlay' : 'Show Heatmap Overlay'}</span>
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Heatmap Preview Viewport */}
        <div className="relative aspect-[16/10] max-w-xl mx-auto rounded-xl border border-[#E5DDD8] bg-[#F8F5F3] overflow-hidden flex items-center justify-center">
          {/* Base Original Specimen */}
          <img
            src={originalPreviewUrl}
            alt="Original Specimen"
            className="w-full h-full object-contain"
          />

          {/* Base64 ELA Heatmap Overlay */}
          {showHeatmapOverlay && heatmapImageBase64 && (
            <img
              src={heatmapImageBase64}
              alt="ELA Heatmap Overlay"
              className="absolute inset-0 w-full h-full object-contain mix-blend-multiply opacity-80 pointer-events-none transition-opacity duration-300"
            />
          )}

          {/* Bounding Box Highlights for Altered Regions */}
          {regions.map((region, idx) => (
            <div
              key={idx}
              style={{
                left: `${(region.x / 600) * 100}%`,
                top: `${(region.y / 400) * 100}%`,
                width: `${(region.w / 600) * 100}%`,
                height: `${(region.h / 400) * 100}%`,
              }}
              className="absolute border-2 border-[#DC2626] bg-[#DC2626]/20 animate-pulse pointer-events-none rounded"
            >
              <span className="absolute -top-5 left-0 bg-[#DC2626] text-[#FFFFFF] text-[9px] font-mono px-1 rounded font-bold uppercase">
                {region.field || 'Altered Region'}
              </span>
            </div>
          ))}
        </div>

        {/* Regions Breakdown Table / List */}
        {regions && regions.length > 0 ? (
          <div className="space-y-2 pt-2 border-t border-[#E5DDD8]">
            <div className="text-xs font-semibold text-[#27212B] flex items-center gap-1.5 font-mono">
              <AlertTriangle className="w-3.5 h-3.5 text-[#755B73]" />
              <span>Flagged Spliced Regions ({regions.length}):</span>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
              {regions.map((r, i) => (
                <div key={i} className="p-2 rounded-lg bg-[#F8F5F3] border border-[#E5DDD8] flex items-center justify-between">
                  <span className="font-semibold text-[#27212B]">{r.field || `Region #${i + 1}`}</span>
                  <span className="text-[#8A2323] font-bold text-[11px]">
                    Coordinates: [{r.x}, {r.y}, {r.w}, {r.h}]
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="pt-2 border-t border-[#E5DDD8] text-center">
            <p className="text-xs text-[#0B2925] font-medium py-1">
              ✓ No tampering indicators detected. Compression and noise distribution are uniform.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
