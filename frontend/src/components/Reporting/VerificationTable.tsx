import { useState, useMemo, type FC } from 'react'
import { TableRow } from './TableRow'
import { exportRecordsToCSV } from './reportingData'
import type { VerificationRecord } from '../../types'
import { soundFX } from '../../utils/audio'
import { Search, Download, ArrowUpDown } from 'lucide-react'

interface VerificationTableProps {
  records: VerificationRecord[]
}

type SortField = 'date' | 'riskScore' | 'tamperingScore' | 'subjectName'
type SortOrder = 'asc' | 'desc'

export const VerificationTable: FC<VerificationTableProps> = ({ records }) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [verdictFilter, setVerdictFilter] = useState<'ALL' | 'GENUINE' | 'SUSPICIOUS' | 'FAKE' | 'REJECTED'>('ALL')
  const [sortField, setSortField] = useState<SortField>('date')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')

  const handleSort = (field: SortField) => {
    soundFX.paperSlide()
    if (sortField === field) {
      setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortField(field)
      setSortOrder('desc')
    }
  }

  const filteredAndSortedRecords = useMemo(() => {
    return records
      .filter((r) => {
        if (verdictFilter !== 'ALL' && r.verdict !== verdictFilter) return false

        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase()
          return (
            r.subjectName.toLowerCase().includes(q) ||
            r.caseNumber.toLowerCase().includes(q) ||
            r.documentType.toLowerCase().includes(q) ||
            (r.checkpointLocation && r.checkpointLocation.toLowerCase().includes(q)) ||
            (r.officerEmail && r.officerEmail.toLowerCase().includes(q)) ||
            r.examiner.toLowerCase().includes(q)
          )
        }
        return true
      })
      .sort((a, b) => {
        let cmp = 0
        if (sortField === 'date') {
          cmp = new Date(a.date).getTime() - new Date(b.date).getTime()
        } else if (sortField === 'riskScore') {
          cmp = a.riskScore - b.riskScore
        } else if (sortField === 'tamperingScore') {
          cmp = a.tamperingScore - b.tamperingScore
        } else if (sortField === 'subjectName') {
          cmp = a.subjectName.localeCompare(b.subjectName)
        }
        return sortOrder === 'asc' ? cmp : -cmp
      })
  }, [records, verdictFilter, searchQuery, sortField, sortOrder])

  const handleExport = () => {
    soundFX.paperSlide()
    exportRecordsToCSV(filteredAndSortedRecords)
  }

  return (
    <div className="dossier-sheet rounded-lg overflow-hidden space-y-0">
      {/* Table Toolbar */}
      <div className="p-4 sm:p-5 border-b border-[#E3DCD6] bg-[#FCFAF8] flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="relative max-w-xs w-full">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 transform -translate-y-1/2 text-[#6E6571]" />
          <input
            type="text"
            placeholder="Search by name, case ID, officer email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 rounded border border-[#E3DCD6] bg-[#FFFFFF] text-xs font-sans text-[#27212B] placeholder-[#6E6571] focus:outline-none focus:border-[#0B2925]"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center bg-[#FFFFFF] p-0.5 rounded border border-[#E3DCD6] text-xs font-sans">
            {(['ALL', 'GENUINE', 'SUSPICIOUS', 'FAKE', 'REJECTED'] as const).map((filter) => (
              <button
                key={filter}
                onClick={() => {
                  soundFX.paperSlide()
                  setVerdictFilter(filter)
                }}
                className={`px-2.5 py-1 rounded transition-colors cursor-pointer ${
                  verdictFilter === filter
                    ? 'bg-[#0B2925] text-[#FFFFFF] font-medium'
                    : 'text-[#6E6571] hover:text-[#0B2925]'
                }`}
              >
                {filter === 'ALL' ? 'All Records' : filter}
              </button>
            ))}
          </div>

          <button
            onClick={handleExport}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#0B2925] hover:bg-[#16433C] text-[#FFFFFF] text-xs font-sans font-medium transition-colors shadow-xs cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-[#F8F5F3] border-b border-[#E3DCD6] text-[11px] font-sans font-semibold text-[#6E6571] select-none">
              <th className="px-4 py-2.5">Case Reference</th>
              <th
                onClick={() => handleSort('date')}
                className="px-4 py-2.5 cursor-pointer hover:text-[#0B2925]"
              >
                <div className="flex items-center gap-1">
                  <span>Timestamp</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th
                onClick={() => handleSort('subjectName')}
                className="px-4 py-2.5 cursor-pointer hover:text-[#0B2925]"
              >
                <div className="flex items-center gap-1">
                  <span>Subject Legal Name</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="px-4 py-2.5">Type</th>
              <th className="px-4 py-2.5">Checkpoint</th>
              <th className="px-4 py-2.5">Verdict</th>
              <th
                onClick={() => handleSort('riskScore')}
                className="px-4 py-2.5 text-center cursor-pointer hover:text-[#0B2925]"
              >
                <div className="flex items-center justify-center gap-1">
                  <span>Risk Score</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th
                onClick={() => handleSort('tamperingScore')}
                className="px-4 py-2.5 text-center cursor-pointer hover:text-[#0B2925]"
              >
                <div className="flex items-center justify-center gap-1">
                  <span>Tamper</span>
                  <ArrowUpDown className="w-3 h-3" />
                </div>
              </th>
              <th className="px-4 py-2.5 text-center">Face Match</th>
              <th className="px-4 py-2.5 text-right">Screened By</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#F2ECE9] bg-[#FFFFFF]">
            {filteredAndSortedRecords.length === 0 ? (
              <tr>
                <td colSpan={10} className="px-4 py-8 text-center text-xs text-[#6E6571] font-sans">
                  No examination records match your filter criteria.
                </td>
              </tr>
            ) : (
              filteredAndSortedRecords.map((record, index) => (
                <TableRow key={record.id} record={record} index={index} />
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Table Footer */}
      <div className="px-4 py-3 bg-[#FCFAF8] border-t border-[#E3DCD6] flex items-center justify-between text-xs text-[#6E6571] font-sans">
        <div>
          Showing {filteredAndSortedRecords.length} of {records.length} total verification records
        </div>
        <div className="text-[11px] font-mono text-[#6E6571]">
          Border Audit Registry • Ministry of Home Affairs
        </div>
      </div>
    </div>
  )
}
