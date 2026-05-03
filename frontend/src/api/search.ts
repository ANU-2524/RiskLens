import { apiClient } from './client'

export interface SearchResult {
  id: number
  name: string
  type: string
  sector: string | null
  current_risk_score: number | null
  severity: string | null
  match_context: string | null
}

export interface QueryResponse {
  question: string
  answer: string
  context_entities: string[]
}

export async function searchEntities(q: string): Promise<SearchResult[]> {
  const { data } = await apiClient.get<SearchResult[]>('/search', { params: { q } })
  return data
}

export async function submitQuery(question: string): Promise<QueryResponse> {
  const { data } = await apiClient.post<QueryResponse>('/query', { question })
  return data
}
