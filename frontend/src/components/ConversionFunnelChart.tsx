'use client'

import { ConversionFunnel } from '@/lib/types'
import { formatNumber, formatPercentage } from '@/lib/utils'
import { TrendingUp } from 'lucide-react'

interface ConversionFunnelChartProps {
  funnel: ConversionFunnel
}

export default function ConversionFunnelChart({ funnel }: ConversionFunnelChartProps) {
  // Map stage names to display names
  const stageNameMap: Record<string, string> = {
    'entries': 'Store Entries',
    'zone_visits': 'Zone Visits',
    'billing_queue_joins': 'Queue Joins',
    'completed_purchases': 'Purchases',
  }

  // Map stage names to colors
  const stageColorMap: Record<string, string> = {
    'entries': 'bg-blue-500',
    'zone_visits': 'bg-green-500',
    'billing_queue_joins': 'bg-yellow-500',
    'completed_purchases': 'bg-purple-500',
  }

  const stages = funnel.stages.map((stage, index) => {
    // Calculate percentage relative to first stage (entries)
    const entriesCount = funnel.stages[0]?.count || 1
    const percentage = (stage.count / entriesCount) * 100

    return {
      name: stageNameMap[stage.stage] || stage.stage,
      value: stage.count,
      percentage: percentage,
      color: stageColorMap[stage.stage] || 'bg-gray-500',
      conversionRate: stage.conversion_rate,
    }
  })

  // Calculate overall conversion (last stage / first stage)
  const overallConversion = funnel.stages.length > 0
    ? (funnel.stages[funnel.stages.length - 1].count / (funnel.stages[0]?.count || 1)) * 100
    : 0

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Conversion Funnel</h3>
          <p className="text-sm text-gray-500 mt-1">Customer journey stages</p>
        </div>
        <TrendingUp className="w-5 h-5 text-gray-400" />
      </div>

      <div className="space-y-4">
        {stages.map((stage, index) => (
          <div key={stage.name}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-3">
                <div className="flex items-center justify-center w-8 h-8 bg-gray-100 rounded-full text-sm font-semibold text-gray-700">
                  {index + 1}
                </div>
                <div>
                  <p className="font-medium text-gray-900">{stage.name}</p>
                  <p className="text-sm text-gray-500">
                    {formatNumber(stage.value)} customers
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-lg font-bold text-gray-900">
                  {stage.percentage.toFixed(1)}%
                </p>
                {stage.conversionRate !== undefined && (
                  <p className="text-xs text-gray-500">
                    {formatPercentage(stage.conversionRate)} conversion
                  </p>
                )}
              </div>
            </div>

            {/* Progress Bar */}
            <div className="relative h-3 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full ${stage.color} transition-all duration-500`}
                style={{ width: `${stage.percentage}%` }}
              />
            </div>

            {/* Conversion Rate Arrow */}
            {stage.conversionRate !== undefined && index < stages.length - 1 && (
              <div className="flex items-center justify-center my-2">
                <div className="text-xs text-gray-400">↓</div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Summary */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">Overall Conversion Rate</span>
          <span className="font-semibold text-gray-900">
            {overallConversion.toFixed(1)}%
          </span>
        </div>
      </div>
    </div>
  )
}
