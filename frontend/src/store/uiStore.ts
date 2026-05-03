import { create } from 'zustand'

interface SelectedEntity {
  id: number
  name: string
}

interface UIState {
  selectedEntity: SelectedEntity | null
  isEntityPanelOpen: boolean
  queryHistory: string[]
  selectEntity: (entity: SelectedEntity) => void
  closeEntityPanel: () => void
  addQueryToHistory: (query: string) => void
}

export const useUIStore = create<UIState>((set) => ({
  selectedEntity: null,
  isEntityPanelOpen: false,
  queryHistory: [],
  selectEntity: (entity) => set({ selectedEntity: entity, isEntityPanelOpen: true }),
  closeEntityPanel: () => set({ isEntityPanelOpen: false, selectedEntity: null }),
  addQueryToHistory: (query) =>
    set((state) => ({
      queryHistory: [query, ...state.queryHistory.slice(0, 9)],
    })),
}))
