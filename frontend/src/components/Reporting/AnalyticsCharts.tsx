import React from 'react'
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts'
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card'
import type { VerificationRecord, DailyVolumePoint } from '../../types'

interface AnalyticsChartsProps {
  records: VerificationRecord[]
  dailyVolume?: DailyVolumePoint[]
}

export const AnalyticsCharts: React.FC<AnalyticsChartsProps> = ({ records, dailyVolume }) => {
  // Compute verdict distribution for PieChart
  const verdictCounts = records.reduce(
    (acc, r) => {
      acc[r.verdict] = (acc[r.verdict] || 0) + 1
      return acc
    },
    { GENUINE: 0, SUSPICIOUS: 0, FAKE: 0, REJECTED: 0 } as Record<string, number>
  )

  const pieData = [
    { name: 'Genuine', value: verdictCounts.GENUINE, color: '#A7F3D0' },
    { name: 'Suspicious', value: verdictCounts.SUSPICIOUS, color: '#755B73' },
    { name: 'Fraudulent', value: verdictCounts.FAKE, color: '#DC2626' },
    { name: 'Rejected', value: verdictCounts.REJECTED, color: '#8A2323' },
  ].filter((d) => d.value > 0)

  // Compute daily volume dynamically from real records if dailyVolume prop not supplied
  const barData = React.useMemo(() => {
    if (dailyVolume && dailyVolume.length > 0) {
      return dailyVolume
    }
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    const dayCounts: Record<string, number> = { Mon: 0, Tue: 0, Wed: 0, Thu: 0, Fri: 0, Sat: 0, Sun: 0 }
    
    records.forEach((r) => {
      try {
        const d = new Date(r.date)
        const dayName = days[d.getDay()]
        if (dayCounts[dayName] !== undefined) {
          dayCounts[dayName] += 1
        }
      } catch {}
    })

    return ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => ({
      day,
      count: dayCounts[day] || 0,
    }))
  }, [dailyVolume, records])

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Pie Chart: Verdict Distribution */}
      <Card className="border-[#E5DDD8] bg-[#FFFFFF] shadow-xs">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-semibold text-[#27212B]">
            Verdict Distribution Overview
          </CardTitle>
        </CardHeader>
        <CardContent className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={45}
                outerRadius={75}
                paddingAngle={4}
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} stroke="#E5DDD8" />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#FFFFFF',
                  borderColor: '#E5DDD8',
                  color: '#27212B',
                  borderRadius: '0.75rem',
                  fontSize: '12px',
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Bar Chart: Case Volume Trend */}
      <Card className="border-[#E5DDD8] bg-[#FFFFFF] shadow-xs">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-semibold text-[#27212B]">
            Weekly Border Screening Volume
          </CardTitle>
        </CardHeader>
        <CardContent className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.2} stroke="#E5DDD8" />
              <XAxis dataKey="day" stroke="#755B73" fontSize={11} />
              <YAxis stroke="#755B73" fontSize={11} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#FFFFFF',
                  borderColor: '#E5DDD8',
                  color: '#27212B',
                  borderRadius: '0.75rem',
                  fontSize: '12px',
                }}
              />
              <Bar dataKey="count" fill="#0B2925" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  )
}
