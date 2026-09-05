import { useState, useEffect, type FC } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { AlertTriangle, XCircle, X, ChevronDown, ChevronUp, ArrowRight } from 'lucide-react'
import type { CaseAlert } from '../../types'
import { soundFX } from '../../utils/audio'

interface AlertToastProps {
  alert: CaseAlert
  onDismiss: (id: string | number) => void
  onInspect?: (alert: CaseAlert) => void
  autoDismissMs?: number
}

export const AlertToast: FC<AlertToastProps> = ({
  alert,
  onDismiss,
  onInspect,
  autoDismissMs = 7000,
}) => {
  const [isExpanded, setIsExpanded] = useState(false)
  const isCritical = alert.severity === 'critical'

  useEffect(() => {
    const timer = setTimeout(() => {
      onDismiss(alert.id)
    }, autoDismissMs)
    return () => clearTimeout(timer)
  }, [alert.id, autoDismissMs, onDismiss])

  const toggleExpand = () => {
    soundFX.paperSlide()
    setIsExpanded((v) => !v)
  }

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: 300, scale: 0.9 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 260, scale: 0.9, transition: { duration: 0.2 } }}
      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
      className={`w-88 rounded-lg shadow-lg border overflow-hidden select-none bg-[#FFFFFF] ${
        isCritical
          ? 'border-[#8B1E1E]/40 shadow-[#8B1E1E]/10'
          : 'border-[#755B73]/40 shadow-[#755B73]/10'
      }`}
    >
      {/* Top Banner */}
      <div
        onClick={toggleExpand}
        className={`px-3.5 py-2.5 flex items-start gap-2.5 cursor-pointer transition-colors ${
          isCritical ? 'bg-[#8B1E1E]/10 hover:bg-[#8B1E1E]/15' : 'bg-[#755B73]/10 hover:bg-[#755B73]/15'
        }`}
      >
        <div className="mt-0.5 shrink-0">
          {isCritical ? (
            <XCircle className="w-4 h-4 text-[#8B1E1E]" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-[#755B73]" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono font-bold tracking-wider uppercase text-[#6E6571]">
              {alert.caseNumber}
            </span>
            <span className="text-[9.5px] font-sans text-[#6E6571]">
              {alert.timestamp}
            </span>
          </div>
          <div className="font-editorial text-sm font-bold text-[#0B2925] truncate">
            {alert.subjectName}
          </div>
          <div className="flex items-center gap-1.5 mt-0.5">
            <span
              className={`text-[9px] font-sans font-semibold px-1.5 py-0.2 rounded ${
                isCritical
                  ? 'bg-[#8B1E1E] text-[#FFFFFF]'
                  : 'bg-[#755B73] text-[#FFFFFF]'
              }`}
            >
              {alert.verdict === 'FAKE' ? 'FRAUDULENT' : 'SUSPICIOUS'}
            </span>
            <span className="text-[10px] text-[#6E6571] font-sans">
              Score: {alert.score}/100
            </span>
          </div>
        </div>

        <div className="flex items-center gap-1 shrink-0 ml-1">
          <button
            onClick={(e) => {
              e.stopPropagation()
              toggleExpand()
            }}
            className="p-1 rounded text-[#6E6571] hover:text-[#0B2925] transition-colors"
          >
            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              onDismiss(alert.id)
            }}
            className="p-1 rounded text-[#6E6571] hover:text-[#27212B] transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Expandable Inline Detail */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden bg-[#FFFFFF] border-t border-[#E3DCD6]"
          >
            <div className="p-3 text-xs font-sans space-y-2">
              <div>
                <span className="text-[10px] text-[#6E6571] uppercase font-semibold block">
                  Flagged Anomaly Reason:
                </span>
                <p className="text-[#27212B] leading-relaxed mt-0.5">
                  {alert.reason}
                </p>
              </div>

              {onInspect && (
                <div className="pt-1 flex justify-end">
                  <button
                    onClick={() => {
                      soundFX.paperSlide()
                      onInspect(alert)
                    }}
                    className="flex items-center gap-1 text-[11px] font-medium text-[#0B2925] hover:underline"
                  >
                    <span>Inspect Case Dossier</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Auto-dismiss countdown bar */}
      <motion.div
        className={`h-0.5 ${isCritical ? 'bg-[#8B1E1E]' : 'bg-[#755B73]'}`}
        initial={{ width: '100%' }}
        animate={{ width: '0%' }}
        transition={{ duration: autoDismissMs / 1000, ease: 'linear' }}
      />
    </motion.div>
  )
}
