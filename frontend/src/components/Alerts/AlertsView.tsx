import type { FC } from 'react'
import { AlertHistoryList } from './AlertHistoryList'
import type { CaseAlert, UserAuth } from '../../types'
import { soundFX } from '../../utils/audio'
import { ShieldAlert, AlertTriangle, Bell, RefreshCw, CheckCircle2 } from 'lucide-react'
import { Button } from '../ui/button'
import { Card } from '../ui/card'

interface AlertsViewProps {
  alerts: CaseAlert[]
  currentUser?: UserAuth | null
  onRefresh?: () => void
  onMarkAllRead: () => void
  onInspectAlert?: (alert: CaseAlert) => void
  onReviewAlert?: (alertId: number, status: 'REVIEWED' | 'RESOLVED' | 'ESCALATED', notes?: string) => Promise<void>
}

export const AlertsView: FC<AlertsViewProps> = ({
  alerts,
  currentUser,
  onRefresh,
  onMarkAllRead,
  onInspectAlert,
  onReviewAlert,
}) => {
  const criticalCount = alerts.filter((a) => (a.severity || '').toLowerCase() === 'critical').length
  const highWarningCount = alerts.filter(
    (a) => (a.severity || '').toLowerCase() === 'high' || (a.severity || '').toLowerCase() === 'warning' || (a.severity || '').toLowerCase() === 'medium'
  ).length
  const unreviewedCount = alerts.filter((a) => (a.status || 'UNREVIEWED') === 'UNREVIEWED').length
  const resolvedCount = alerts.filter((a) => a.status === 'RESOLVED').length

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-10 space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-4 border-b border-[#E5DDD8]">
        <div>
          <h2 className="font-editorial text-2xl sm:text-3xl font-bold text-[#27212B]">
            Security Alerts &amp; Flagged Queue
          </h2>
          <p className="text-xs sm:text-sm text-[#755B73] font-sans mt-0.5">
            Real-time notifications for identity specimens with tampering, facial mismatch, category failure, or blacklist flags.
          </p>
        </div>

        {onRefresh && (
          <Button
            onClick={() => {
              soundFX.paperSlide()
              onRefresh()
            }}
            variant="outline"
            className="gap-2 border-[#E5DDD8] text-[#0B2925] hover:bg-[#F8F5F3] font-semibold cursor-pointer self-start sm:self-auto text-xs"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh Feed</span>
          </Button>
        )}
      </div>

      {/* Summary KPI Ribbon */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Card className="rounded-xl p-4 bg-[#FFFFFF] border-[#E5DDD8] shadow-xs">
          <div className="flex items-center gap-2 text-[11px] text-[#8A2323] font-semibold">
            <ShieldAlert className="w-3.5 h-3.5 text-[#8A2323]" />
            <span>Critical Forgeries</span>
          </div>
          <div className="text-2xl font-bold text-[#8A2323] mt-1 font-mono">
            {criticalCount}
          </div>
          <div className="text-[10px] text-[#755B73] mt-0.5">Immediate void status</div>
        </Card>

        <Card className="rounded-xl p-4 bg-[#FFFFFF] border-[#E5DDD8] shadow-xs">
          <div className="flex items-center gap-2 text-[11px] text-[#755B73] font-semibold">
            <AlertTriangle className="w-3.5 h-3.5 text-[#755B73]" />
            <span>Suspicious Inquiries</span>
          </div>
          <div className="text-2xl font-bold text-[#755B73] mt-1 font-mono">
            {highWarningCount}
          </div>
          <div className="text-[10px] text-[#755B73] mt-0.5">Secondary screening queue</div>
        </Card>

        <Card className="rounded-xl p-4 bg-[#FFFFFF] border-[#E5DDD8] shadow-xs">
          <div className="flex items-center gap-2 text-[11px] text-[#0B2925] font-semibold">
            <Bell className="w-3.5 h-3.5 text-[#0B2925]" />
            <span>Pending Review</span>
          </div>
          <div className="text-2xl font-bold text-[#0B2925] mt-1 font-mono">
            {unreviewedCount}
          </div>
          <div className="text-[10px] text-[#755B73] mt-0.5">Awaiting supervisor action</div>
        </Card>

        <Card className="rounded-xl p-4 bg-[#FFFFFF] border-[#E5DDD8] shadow-xs">
          <div className="flex items-center gap-2 text-[11px] text-[#0B2925] font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#0B2925]" />
            <span>Resolved Cases</span>
          </div>
          <div className="text-2xl font-bold text-[#0B2925] mt-1 font-mono">
            {resolvedCount}
          </div>
          <div className="text-[10px] text-[#755B73] mt-0.5">Supervisor disposition logged</div>
        </Card>
      </div>

      {/* History List */}
      <AlertHistoryList
        alerts={alerts}
        currentUser={currentUser}
        onMarkAllRead={onMarkAllRead}
        onInspect={onInspectAlert}
        onReviewAlert={onReviewAlert}
      />
    </div>
  )
}
