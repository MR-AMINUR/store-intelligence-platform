// API Response Types

export interface HealthStatus {
  status: 'healthy' | 'unhealthy'
  checks: {
    database: 'ok' | 'failed'
  }
  response_time_ms: number
  timestamp: string
}

export interface StoreMetrics {
  store_id: string
  total_entries: number
  total_exits: number
  current_occupancy: number
  avg_visit_duration_seconds: number
  time_range: {
    start_time: string
    end_time: string
  }
}

export interface FunnelStage {
  stage: string
  count: number
  conversion_rate: number
}

export interface ConversionFunnel {
  store_id: string
  stages: FunnelStage[]
  zone_id: string | null
}

export interface Heatmap {
  store_id: string
  grid_size: [number, number]
  density_map: number[][]
  max_density: number
}

export interface Anomaly {
  type: string
  timestamp: string
  severity: 'low' | 'medium' | 'high'
  description: string
  value?: number
  threshold?: number
}

export interface AnomaliesResponse {
  anomalies: Anomaly[]
}

export interface EventIngestion {
  event_id: string
  event_type: string
  timestamp: string
  store_id: string
  track_id: number
  metadata: Record<string, any>
}

export interface IngestResponse {
  success: boolean
  events_processed: number
  errors: string[]
}
