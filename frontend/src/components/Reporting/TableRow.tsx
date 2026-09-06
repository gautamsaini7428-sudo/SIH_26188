import type { FC } from 'react'
import { motion } from 'framer-motion'
import type { VerificationRecord } from '../../types'

interface TableRowProps {
  record: VerificationRecord
  index: number
}

export const TableRow: FC<TableRowProps> = ({ record, index }) => {
  const isGenuine = record.verdict === 'GENUINE'
  const isSuspicious = record.verdict === 'SUSPICIOUS'
  const isFake = record.verdict === 'FAKE'

  const formattedDate = new Date(record.date).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })

  return (
    <motion.tr
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: Math.min(index * 0.035, 0.5), duration: 0.25 }}
      className="bg-[#636CCB] hover:bg-[#6E8CFB] dark:bg-[#111C30] dark:hover:bg-[#1C345C] transition-colors border-b border-[#DDE4FF] dark:border-[#1C345C] text-xs font-sans text-white dark:text-[#DEF4F2]"
    >
      {/* 1. Case Number */}
      <td className="px-4 py-3 font-mono font-semibold text-white dark:text-[#DEF4F2] whitespace-nowrap">
        {record.caseNumber}
      </td>

      {/* 2. Timestamp */}
      <td className="px-4 py-3 text-white/85 dark:text-[#AAB6C8] whitespace-nowrap">
        {formattedDate}
      </td>

      {/* 3. Subject Legal Name */}
      <td className="px-4 py-3 font-editorial text-sm font-semibold text-white dark:text-[#DEF4F2] whitespace-nowrap">
        {record.subjectName}
      </td>

      {/* 4. Document Type */}
      <td className="px-4 py-3 text-white/85 dark:text-[#AAB6C8] whitespace-nowrap font-mono text-[11px]">
        {record.documentType}
      </td>

      {/* 5. Checkpoint Location */}
      <td className="px-4 py-3 text-white/85 dark:text-[#AAB6C8] whitespace-nowrap">
        {record.checkpointLocation || 'Attari-Wagah Border'}
      </td>

      {/* 6. Verdict Badge */}
      <td className="px-4 py-3 whitespace-nowrap">
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-sans font-semibold ${
            isGenuine
              ? 'bg-[#A7F3D0]/40 text-[#0B2925] border border-[#0B2925]/20'
              : isSuspicious
              ? 'bg-[#FDE68A] text-[#854D0E] border border-[#F59E0B]/40'
              : isFake
              ? 'bg-[#8B1E1E]/15 text-[#8B1E1E] border border-[#8B1E1E]/30'
              : 'bg-[#FDE68A] text-[#854D0E] border border-[#F59E0B]/40'
          }`}
        >
          {record.verdict}
        </span>
      </td>

      {/* 7. Risk Score */}
      <td className="px-4 py-3 font-mono text-center whitespace-nowrap">
        <span
          className={
            record.riskScore > 65
              ? 'text-[#8B1E1E] font-bold'
              : record.riskScore > 30
              ? 'text-[#FDE68A] font-medium'
              : 'text-[#A7F3D0] font-bold'
          }
        >
          {record.riskScore}/100
        </span>
      </td>

      {/* 8. Tampering Score */}
      <td className="px-4 py-3 font-mono text-center whitespace-nowrap">
        <span className="text-white/85 dark:text-[#AAB6C8]">{record.tamperingScore}/100</span>
      </td>

      {/* 9. Face Match Score */}
      <td className="px-4 py-3 font-mono text-center whitespace-nowrap text-white/85 dark:text-[#AAB6C8]">
        {record.faceMatchScore !== undefined && record.faceMatchScore !== null
          ? `${record.faceMatchScore}%`
          : 'N/A'}
      </td>

      {/* 10. Screened By (Officer Email / Examiner) */}
      <td className="px-4 py-3 font-mono text-right text-white dark:text-[#DEF4F2] font-medium whitespace-nowrap">
        {record.officerEmail || record.examiner}
      </td>
    </motion.tr>
  )
}
