import { motion } from 'framer-motion'
import { useUIStore } from '@/store/uiStore'
import { useEntityDetail } from '@/api/entities'
import { useEntityTimeline } from '@/api/timeline'
import { SeverityBadge } from '@/components/SeverityBadge'
import { RiskGauge } from '@/components/Charts/RiskGauge'
import { RiskTimelineChart } from '@/components/Charts/RiskTimelineChart'
import { apiClient } from '@/api/client'
import { useState } from 'react'

export function EntityPanel() {
  const { selectedEntity, closeEntityPanel } = useUIStore()
  const { data: entity, isLoading } = useEntityDetail(selectedEntity?.id ?? null)
  const { data: timeline } = useEntityTimeline(selectedEntity?.id ?? null, 30)
  const [watchlistAdded, setWatchlistAdded] = useState(false)

  async function handleAddToWatchlist() {
    if (!entity) return
    try {
      await apiClient.post('/watchlist', { entity_id: entity.id })
      setWatchlistAdded(true)
    } catch {
      // Already in watchlist or not analyst
    }
  }

  return (
    <motion.div
      initial={{ x: 40, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 40, opacity: 0 }}
      transition={{ type: 'spring', bounce: 0.1, duration: 0.4 }}
      className="flex flex-col h-full"
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-cosmic-border flex items-center justify-between flex-shrink-0">
        <h2 className="text-sm font-semibold text-cosmic-text-primary">Entity Detail</h2>
        <button
          onClick={closeEntityPanel}
          className="text-cosmic-text-muted hover:text-cosmic-text-primary transition-colors p-1 rounded"
          aria-label="Close entity panel"
        >
          ✕
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isLoading && (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="card animate-pulse h-16" />
            ))}
          </div>
        )}

        {entity && (
          <>
            {/* Entity header */}
            <div className="card">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h3 className="text-lg font-semibold text-cosmic-text-primary">{entity.name}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs font-mono text-cosmic-text-muted uppercase">{entity.type}</span>
                    {entity.sector && (
                      <>
                        <span className="text-cosmic-text-muted">·</span>
                        <span className="text-xs text-cosmic-cyan">{entity.sector}</span>
                      </>
                    )}
                    {entity.ticker && (
                      <>
                        <span className="text-cosmic-text-muted">·</span>
                        <span className="text-xs font-mono text-cosmic-amber">{entity.ticker}</span>
                      </>
                    )}
                  </div>
                </div>
                {entity.severity && <SeverityBadge severity={entity.severity} />}
              </div>
              {entity.description && (
                <p className="text-xs text-cosmic-text-secondary">{entity.description}</p>
              )}
            </div>

            {/* Risk gauge */}
            {entity.current_risk_score !== null && (
              <div className="card flex flex-col items-center py-4">
                <p className="text-xs text-cosmic-text-muted mb-3 uppercase tracking-wider">Current Risk Score</p>
                <RiskGauge score={entity.current_risk_score} severity={entity.severity ?? 'LOW'} />
                <p className="text-3xl font-bold font-mono mt-2" style={{ color: getSeverityColor(entity.severity ?? 'LOW') }}>
                  {entity.current_risk_score.toFixed(1)}
                  <span className="text-sm text-cosmic-text-muted">/100</span>
                </p>
              </div>
            )}

            {/* Risk timeline */}
            {timeline && timeline.points.length > 0 && (
              <div className="card">
                <p className="text-xs text-cosmic-text-muted mb-3 uppercase tracking-wider">30-Day Risk History</p>
                <RiskTimelineChart points={timeline.points} />
              </div>
            )}

            {/* AI Summary */}
            {entity.latest_summary && (
              <div className="card border border-cosmic-cyan/20">
                <div className="flex items-center gap-2 mb-3">
                  <span className="w-2 h-2 rounded-full bg-cosmic-cyan animate-pulse" />
                  <p className="text-xs font-semibold text-cosmic-cyan uppercase tracking-wider">AI Risk Analysis</p>
                </div>
                <p className="text-sm text-cosmic-text-secondary leading-relaxed mb-3">
                  {entity.latest_summary.summary_text}
                </p>

                {entity.latest_summary.contributing_signals && (
                  <div className="space-y-2 mb-3">
                    <p className="text-xs text-cosmic-text-muted uppercase tracking-wider">Contributing Signals</p>
                    {entity.latest_summary.contributing_signals.map((sig, i) => (
                      <div key={i} className="bg-cosmic-bg-elevated rounded-lg p-2">
                        <p className="text-xs font-medium text-cosmic-text-primary">{sig.signal}</p>
                        <p className="text-xs text-cosmic-text-muted">{sig.evidence}</p>
                      </div>
                    ))}
                  </div>
                )}

                {entity.latest_summary.recommended_action && (
                  <div className="bg-cosmic-amber-glow border border-cosmic-amber/20 rounded-lg p-3">
                    <p className="text-xs font-semibold text-cosmic-amber mb-1">Recommended Action</p>
                    <p className="text-xs text-cosmic-text-secondary">{entity.latest_summary.recommended_action}</p>
                  </div>
                )}
              </div>
            )}

            {/* Stats */}
            <div className="grid grid-cols-2 gap-2">
              <div className="card text-center">
                <p className="text-xs text-cosmic-text-muted">Signals</p>
                <p className="text-xl font-bold font-mono text-cosmic-cyan">{entity.signal_count}</p>
              </div>
              <div className="card text-center">
                <p className="text-xs text-cosmic-text-muted">History Points</p>
                <p className="text-xl font-bold font-mono text-cosmic-cyan">{entity.recent_risk_scores.length}</p>
              </div>
            </div>

            {/* Watchlist button */}
            <button
              onClick={handleAddToWatchlist}
              disabled={watchlistAdded}
              className={`w-full py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                watchlistAdded
                  ? 'bg-cosmic-green/20 text-cosmic-green border border-cosmic-green/30 cursor-default'
                  : 'btn-primary'
              }`}
            >
              {watchlistAdded ? '✓ Added to Watchlist' : '+ Add to Watchlist'}
            </button>
          </>
        )}
      </div>
    </motion.div>
  )
}

function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    CRITICAL: '#FF3B30',
    HIGH: '#FFB800',
    MEDIUM: '#EAB308',
    LOW: '#00D4FF',
  }
  return colors[severity] ?? '#00D4FF'
}
