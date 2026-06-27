import axios, { AxiosInstance, AxiosError } from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

console.log('API Client initialized with URL:', API_URL)

class APIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      timeout: 30000,
      withCredentials: false, // Important for CORS
    })

    // Request interceptor for debugging
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`)
        return config
      },
      (error) => {
        console.error('Request Error:', error)
        return Promise.reject(error)
      }
    )

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => {
        console.log(`API Response: ${response.status} ${response.config.url}`)
        return response
      },
      (error: AxiosError) => {
        if (error.response) {
          // Server responded with error status
          console.error('API Error Response:', error.response.status, error.response.data)
        } else if (error.request) {
          // Request made but no response
          console.error('API No Response:', error.message)
        } else {
          // Error in request setup
          console.error('API Request Setup Error:', error.message)
        }
        return Promise.reject(error)
      }
    )
  }

  // Health Check
  async healthCheck() {
    try {
      const response = await this.client.get('/health')
      return response.data
    } catch (error) {
      console.error('Health check failed:', error)
      throw error
    }
  }

  // Store Metrics
  async getStoreMetrics(storeId: string, startTime?: string, endTime?: string) {
    try {
      const params: Record<string, string> = {}
      if (startTime) params.start_time = startTime
      if (endTime) params.end_time = endTime
      
      const response = await this.client.get(`/stores/${storeId}/metrics`, { params })
      return response.data
    } catch (error) {
      console.error('Get store metrics failed:', error)
      throw error
    }
  }

  // Conversion Funnel
  async getConversionFunnel(storeId: string, zoneId?: string) {
    try {
      const params: Record<string, string> = {}
      if (zoneId) params.zone_id = zoneId
      
      const response = await this.client.get(`/stores/${storeId}/funnel`, { params })
      return response.data
    } catch (error) {
      console.error('Get conversion funnel failed:', error)
      throw error
    }
  }

  // Heatmap
  async getHeatmap(storeId: string, resolution: number = 50) {
    try {
      const response = await this.client.get(`/stores/${storeId}/heatmap`, {
        params: { resolution }
      })
      return response.data
    } catch (error) {
      console.error('Get heatmap failed:', error)
      throw error
    }
  }

  // Anomalies
  async getAnomalies(storeId: string, timeWindow: number = 24) {
    try {
      const response = await this.client.get(`/stores/${storeId}/anomalies`, {
        params: { time_window: timeWindow }
      })
      return response.data
    } catch (error) {
      console.error('Get anomalies failed:', error)
      throw error
    }
  }

  // Event Ingestion
  async ingestEvents(events: any | any[]) {
    try {
      const response = await this.client.post('/events/ingest', events)
      return response.data
    } catch (error) {
      console.error('Ingest events failed:', error)
      throw error
    }
  }
}

export const apiClient = new APIClient()
