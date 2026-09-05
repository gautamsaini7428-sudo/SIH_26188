import type { FC } from 'react'
import { motion } from 'framer-motion'
import { Zap } from 'lucide-react'

interface MatchConnectorProps {
  isScanning: boolean
}

export const MatchConnector: FC<MatchConnectorProps> = ({ isScanning }) => {
  return (
    <div className="relative flex flex-col items-center justify-center py-4 lg:py-0 w-full lg:w-28 select-none">
      {/* Horizontal / Vertical connecting track */}
      <div className="relative w-full h-12 flex items-center justify-center">
        {/* Static paper hairline track */}
        <div className="w-full h-0.5 bg-[#E3DCD6]" />

        {/* Animated scanning pulse line */}
        {isScanning && (
          <motion.div
            className="absolute h-1 bg-[#0B2925] rounded-full shadow-xs"
            initial={{ left: '0%', width: '20%' }}
            animate={{ left: ['0%', '80%', '0%'] }}
            transition={{ duration: 1.4, repeat: Infinity, ease: 'easeInOut' }}
          />
        )}

        {/* Center Node Icon */}
        <div
          className={`absolute w-9 h-9 rounded-full border flex items-center justify-center transition-all duration-300 ${
            isScanning
              ? 'bg-[#0B2925] border-[#0B2925] text-[#A7F3D0] shadow-sm scale-110'
              : 'bg-[#FFFFFF] border-[#E3DCD6] text-[#6E6571]'
          }`}
        >
          <Zap className={`w-4 h-4 ${isScanning ? 'animate-pulse' : ''}`} />
        </div>
      </div>

      {isScanning && (
        <motion.span
          initial={{ opacity: 0 }}
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ repeat: Infinity, duration: 1.2 }}
          className="text-[10px] font-mono text-[#0B2925] font-semibold mt-1 uppercase tracking-wider"
        >
          Comparing 128-d Vectors
        </motion.span>
      )}
    </div>
  )
}
