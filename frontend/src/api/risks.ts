import { useQuery } from '@tanstack/react-query'
import { apiClient } from './client'

export interface AlertRecord {
  id: number
  entity_id: number
  entity_name: string
  severity: string
  message: string
  triggered_at: string
  acknowledged: boolean
  current_score: number | null
  ai_summary: string | null
}

export interface SectorRisk {
  sector: string
  entity_count: number
  avg_risk_score: number
  max_risk_score: number
  top_entity: string | null
}

export interface DashboardStats {
  total_entities: number
  alerts_today: number
  critical_today: number
  avg_risk_score: number
  highest_risk_entity: {
    id: number
    name: string
    score: number
    severity: string
    sector: string | null
  } | null
  severity_distribution: Record<string, number>
  last_updated: string
}

export function useAlerts(hours = 24, severity?: string) {
  return useQuery({
    queryKey: ['alerts', hours, severity],
    queryFn: async () => {
      const params: Record<string, string | number> = { hours }
      if (severity) params.severity = severity
      const { data } = await apiClient.get<AlertRecord[]>('/risks/alerts', { params })
      return data
    },
    refetchInterval: 30_000,
  })
}

export function useSectorRisks() {
  return useQuery({
    queryKey: ['sector-risks'],
    queryFn: async () => {
      const { data } = await apiClient.get<SectorRisk[]>('/risks/sectors')
      return data
    },
    refetchInterval: 60_000,
  })
}

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const { data } = await apiClient.get<DashboardStats>('/dashboard/stats')
      return data
    },
    refetchInterval: 30_000,
  })
}
