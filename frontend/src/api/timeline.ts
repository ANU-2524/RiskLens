import { useQuery } from '@tanstack/react-query'
import { apiClient } from './client'

export interface TimelinePoint {
  timestamp: string
  score: number
  severity: string
  sentiment_delta: number | null
  volume_anomaly: number | null
  price_volatility: number | null
}

export interface TimelineResponse {
  entity_id: number
  entity_name: string
  sector: string | null
  points: TimelinePoint[]
}

export function useEntityTimeline(entityId: number | null, days = 30) {
  return useQuery({
    queryKey: ['timeline', entityId, days],
    queryFn: async () => {
      const { data } = await apiClient.get<TimelineResponse>(`/timeline/${entityId}`, {
        params: { days },
      })
      return data
    },
    enabled: entityId !== null,
  })
}
