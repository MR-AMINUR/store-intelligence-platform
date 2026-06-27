'use client'

import { useEffect, useState } from 'react'
import { apiClient } from '@/lib/api'
import { StoreMetrics, ConversionFunnel, AnomaliesResponse, HealthStatus } from '@/lib/types'
import MetricsCards from './MetricsCards'
import ConversionFunnelChart from './ConversionFunnelChart'
import AnomaliesTable from './AnomaliesTable'
import HealthIndicator from './HealthIndicator'
import { RefreshCw } from 'lucide-react'

interface DashboardProps {
  storeId: string
}

export default function Dashboard({ storeId }: DashboardProps) {
  const [loading, setLoading] = useState(true)
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [metrics, setMetrics] = useState<StoreMetrics | null>(null)
  const [funnel, setFunnel] = useState<ConversionFunnel | null>(null)
  const [anomalies, setAnomalies] = useState<AnomaliesResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date())

  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)

      const [healthData, metricsData, funnelData, anomaliesData] = await Promise.all([
        apiClient.healthCheck(),
        apiClient.getStoreMetrics(storeId),
        apiClient.getConversionFunnel(storeId),
        apiClient.getAnomalies(storeId, 24),
      ])

      setHealth(healthData)
      setMetrics(metricsData)
      setFunnel(funnelData)
      setAnomalies(anomaliesData)
      setLastUpdated(new Date())
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to fetch data')
      console.error('Dashboard error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [storeId])

  if (loading && !metrics) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 text-primary-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Store Analytics</h1>
          <p className="text-gray-500 mt-1">
            Real-time insights for {storeId}
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <HealthIndicator health={health} />
          <button
            onClick={fetchData}
            disabled={loading}
            className="flex items-center space-x-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span className="text-sm font-medium">Refresh</span>
          </button>
        </div>
      </div>

      {/* Last Updated */}
      <div className="text-xs text-gray-400">
        Last updated: {lastUpdated.toLocaleTimeString()}
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          <p className="font-medium">Error loading data</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      )}

      {/* Metrics Cards */}
      {metrics && <MetricsCards metrics={metrics} />}

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Conversion Funnel */}
        {funnel && <ConversionFunnelChart funnel={funnel} />}

        {/* Anomalies */}
        {anomalies && <AnomaliesTable anomalies={anomalies.anomalies} />}
      </div>
    </div>
  )
}
