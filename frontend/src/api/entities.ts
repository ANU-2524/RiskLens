import { useQuery } from '@tanstack/react-query'
import { apiClient } from './client'

export interface EntitySummary {
  id: number
  name: string
  type: string
  sector: string | null
  country: string | null
  ticker: string | null
  current_risk_score: number | null
  severity: string | null
  description: string | null
}

export interface RiskScoreRecord {
  id: number
  score: number
  severity: string
  computed_at: string
  sentiment_delta: number | null
  volume_anomaly: number | null
  price_volatility: number | null
}

export interface AISummaryRecord {
  id: number
  summary_text: string
  severity: string
  contributing_signals: Array<{ signal: string; evidence: string }> | null
  recommended_action: string | null
  generated_at: string
}

export interface EntityDetail extends EntitySummary {
  latest_summary: AISummaryRecord | null
  recent_risk_scores: RiskScoreRecord[]
  signal_count: number
}

export interface EntitiesResponse {
  total: number
  page: number
  page_size: number
  items: EntitySummary[]
}

export function useEntities(page = 1, sector?: string, severity?: string) {
  return useQuery({
    queryKey: ['entities', page, sector, severity],
    queryFn: async () => {
      const params: Record<string, string | number> = { page, page_size: 100 }
      if (sector) params.sector = sector
      if (severity) params.severity = severity
      const { data } = await apiClient.get<EntitiesResponse>('/entities', { params })
      return data
    },
  })
}

export function useEntityDetail(id: number | null) {
  return useQuery({
    queryKey: ['entity', id],
    queryFn: async () => {
      const { data } = await apiClient.get<EntityDetail>(`/entities/${id}`)
      return data
    },
    enabled: id !== null,
  })
}
