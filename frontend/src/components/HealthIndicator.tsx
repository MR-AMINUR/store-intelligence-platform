'use client'

import { HealthStatus } from '@/lib/types'
import { CheckCircle, XCircle, Loader2 } from 'lucide-react'

interface HealthIndicatorProps {
  health: HealthStatus | null
}

export default function HealthIndicator({ health }: HealthIndicatorProps) {
  if (!health) {
    return (
      <div className="flex items-center space-x-2 px-3 py-2 bg-gray-100 rounded-lg">
        <Loader2 className="w-4 h-4 text-gray-600 animate-spin" />
        <span className="text-sm font-medium text-gray-700">Checking...</span>
      </div>
    )
  }

  const isHealthy = health.status === 'healthy'

  return (
    <div
      className={`flex items-center space-x-2 px-3 py-2 rounded-lg ${
        isHealthy ? 'bg-green-50' : 'bg-red-50'
      }`}
    >
      {isHealthy ? (
        <CheckCircle className="w-4 h-4 text-green-600" />
      ) : (
        <XCircle className="w-4 h-4 text-red-600" />
      )}
      <div className="text-sm">
        <span
          className={`font-medium ${
            isHealthy ? 'text-green-700' : 'text-red-700'
          }`}
        >
          {isHealthy ? 'Healthy' : 'Unhealthy'}
        </span>
        <span className="text-gray-500 ml-2">
          {health.response_time_ms.toFixed(0)}ms
        </span>
      </div>
    </div>
  )
}
