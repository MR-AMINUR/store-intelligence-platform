'use client'

import { Anomaly } from '@/lib/types'
import { formatDateTime } from '@/lib/utils'
import { AlertTriangle, AlertCircle, Info } from 'lucide-react'

interface AnomaliesTableProps {
  anomalies: Anomaly[]
}

export default function AnomaliesTable({ anomalies }: AnomaliesTableProps) {
  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high':
        return <AlertTriangle className="w-5 h-5 text-red-500" />
      case 'medium':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />
      default:
        return <Info className="w-5 h-5 text-blue-500" />
    }
  }

  const getSeverityBadge = (severity: string) => {
    const styles = {
      high: 'bg-red-100 text-red-700 border-red-200',
      medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
      low: 'bg-blue-100 text-blue-700 border-blue-200',
    }
    return styles[severity as keyof typeof styles] || styles.low
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Anomaly Detection</h3>
          <p className="text-sm text-gray-500 mt-1">Last 24 hours</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="px-3 py-1 bg-gray-100 rounded-full text-xs font-medium text-gray-700">
            {anomalies.length} detected
          </div>
        </div>
      </div>

      {anomalies.length === 0 ? (
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-green-600" />
          </div>
          <p className="text-gray-600 font-medium">No anomalies detected</p>
          <p className="text-sm text-gray-500 mt-1">All metrics are within normal range</p>
        </div>
      ) : (
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {anomalies.map((anomaly, index) => (
            <div
              key={index}
              className="flex items-start space-x-4 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="flex-shrink-0 mt-1">
                {getSeverityIcon(anomaly.severity)}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-2">
                  <p className="font-medium text-gray-900">{anomaly.type}</p>
                  <span
                    className={`px-2 py-1 text-xs font-medium border rounded-full ${getSeverityBadge(
                      anomaly.severity
                    )}`}
                  >
                    {anomaly.severity.toUpperCase()}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mb-2">{anomaly.description}</p>
                <div className="flex items-center space-x-4 text-xs text-gray-500">
                  <span>{formatDateTime(anomaly.timestamp)}</span>
                  {anomaly.value !== undefined && (
                    <span>Value: {anomaly.value.toFixed(2)}</span>
                  )}
                  {anomaly.threshold !== undefined && (
                    <span>Threshold: {anomaly.threshold.toFixed(2)}</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
