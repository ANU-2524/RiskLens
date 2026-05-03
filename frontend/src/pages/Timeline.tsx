import { useState } from 'react'
import { useEntities } from '@/api/entities'
import { useEntityTimeline } from '@/api/timeline'
import { RiskTimelineChart } from '@/components/Charts/RiskTimelineChart'

export function TimelinePage() {
  const { data: entitiesData } = useEntities(1)
  const [selectedEntityId, setSelectedEntityId] = useState<number | null>(null)
  const [days, setDays] = useState(30)
  const { data: timeline } = useEntityTimeline(selectedEntityId, days)

  const entities = entitiesData?.items ?? []

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-cosmic-text-primary mb-1">Risk Timeline Explorer</h1>
        <p className="text-sm text-cosmic-text-secondary">Historical risk score analysis for any entity</p>
      </div>

      {/* Entity selector */}
      <div className="card">
        <label className="block text-xs text-cosmic-text-muted uppercase tracking-wider mb-2">
          Select Entity
        </label>
        <select
          value={selectedEntityId ?? ''}
          onChange={(e) => setSelectedEntityId(Number(e.target.value) || null)}
          className="input-cosmic w-full max-w-md"
        >
          <option value="">— Choose an entity —</option>
          {entities.map((entity) => (
            <option key={entity.id} value={entity.id}>
              {entity.name} ({entity.sector})
            </option>
          ))}
        </select>

        <div className="mt-4 flex gap-2">
          {[7, 30, 90, 180].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-3 py-1.5 text-xs rounded-lg transition-all duration-200 ${
                days === d
                  ? 'bg-cosmic-cyan text-cosmic-bg font-semibold'
                  : 'border border-cosmic-border text-cosmic-text-secondary hover:border-cosmic-cyan hover:text-cosmic-cyan'
              }`}
            >
              {d} days
            </button>
          ))}
        </div>
      </div>

      {/* Timeline chart */}
      {timeline && timeline.points.length > 0 && (
        <div className="card">
          <div className="mb-4">
            <h2 className="text-lg font-semibold text-cosmic-text-primary">{timeline.entity_name}</h2>
            <p className="text-xs text-cosmic-text-muted">{timeline.sector}</p>
          </div>
          <div className="h-80">
            <RiskTimelineChart points={timeline.points} />
          </div>
          <div className="mt-4 grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-xs text-cosmic-text-muted">Data Points</p>
              <p className="text-xl font-bold font-mono text-cosmic-cyan">{timeline.points.length}</p>
            </div>
            <div>
              <p className="text-xs text-cosmic-text-muted">Current Score</p>
              <p className="text-xl font-bold font-mono text-cosmic-amber">
                {timeline.points[timeline.points.length - 1]?.score.toFixed(1) ?? '—'}
              </p>
            </div>
            <div>
              <p className="text-xs text-cosmic-text-muted">Peak Score</p>
              <p className="text-xl font-bold font-mono text-cosmic-red">
                {Math.max(...timeline.points.map((p) => p.score)).toFixed(1)}
              </p>
            </div>
          </div>
        </div>
      )}

      {selectedEntityId && (!timeline || timeline.points.length === 0) && (
        <div className="card text-center py-12">
          <p className="text-cosmic-text-muted">No timeline data available for this entity</p>
        </div>
      )}

      {!selectedEntityId && (
        <div className="card text-center py-12">
          <p className="text-cosmic-text-muted">Select an entity to view its risk timeline</p>
        </div>
      )}
    </div>
  )
}
