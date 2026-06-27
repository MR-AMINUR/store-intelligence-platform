'use client'

import { StoreMetrics } from '@/lib/types'
import { Users, LogIn, LogOut, Clock } from 'lucide-react'
import { formatNumber, formatDuration } from '@/lib/utils'

interface MetricsCardsProps {
  metrics: StoreMetrics
}

export default function MetricsCards({ metrics }: MetricsCardsProps) {
  const cards = [
    {
      title: 'Total Entries',
      value: formatNumber(metrics.total_entries),
      icon: LogIn,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
    },
    {
      title: 'Total Exits',
      value: formatNumber(metrics.total_exits),
      icon: LogOut,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
    },
    {
      title: 'Current Occupancy',
      value: formatNumber(metrics.current_occupancy),
      icon: Users,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      title: 'Avg Visit Duration',
      value: formatDuration(metrics.avg_visit_duration_seconds),
      icon: Clock,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card) => (
        <div
          key={card.title}
          className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">{card.title}</p>
              <p className="text-3xl font-bold text-gray-900 mt-2">{card.value}</p>
            </div>
            <div className={`p-3 rounded-lg ${card.bgColor}`}>
              <card.icon className={`w-6 h-6 ${card.color}`} />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
