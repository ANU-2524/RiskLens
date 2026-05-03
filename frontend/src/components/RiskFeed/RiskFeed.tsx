import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useAlerts } from '@/api/risks'
import type { AlertRecord } from '@/api/risks'
import { useUIStore } from '@/store/uiStore'
import { SeverityBadge } from '@/components/SeverityBadge'
import { formatDistanceToNow } from '@/utils/time'

export function RiskFeed() {
  const { data: alerts, isLoading } = useAlerts(24)
  const [liveAlerts, setLiveAlerts] = useState<AlertRecord[]>([])
  const wsRef = useRef<WebSocket | null>(null)
  const selectEntity = useUIStore((s) => s.selectEntity)

  // Merge API alerts with live WebSocket alerts
  useEffect(() => {
    if (alerts) setLiveAlerts(alerts)
  }, [alerts])

  // WebSocket live feed
  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/risks/live`

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data as string) as Record<string, unknown>
          if (msg.type === 'alert') {
            setLiveAlerts((prev) => [msg as unknown as AlertRecord, ...prev.slice(0, 49)])
          }
        } catch {
          // ignore parse errors
        }
      }

      // Keep-alive ping
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) ws.send('ping')
      }, 30_000)

      return () => {
        clearInterval(pingInterval)
        ws.close()
      }
    } catch {
      return undefined
    }
  }, [])

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-cosmic-border flex items-center justify-between">
        <h2 className="text-sm font-semibold text-cosmic-text-primary">Live Risk Feed</h2>
        <div className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-cosmic-green animate-pulse" />
          <span className="text-xs text-cosmic-text-muted font-mono">LIVE</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {isLoading && (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="card animate-pulse h-20" />
            ))}
          </div>
        )}

        <AnimatePresence initial={false}>
          {liveAlerts.map((alert) => (
            <motion.div
              key={alert.id}
              initial={{ opacity: 0, x: -20, height: 0 }}
              animate={{ opacity: 1, x: 0, height: 'auto' }}
              exit={{ opacity: 0, x: -20, height: 0 }}
              transition={{ duration: 0.3 }}
            >
              <AlertCard
                alert={alert}
                onClick={() => selectEntity({ id: alert.entity_id, name: alert.entity_name })}
              />
            </motion.div>
          ))}
        </AnimatePresence>

        {!isLoading && liveAlerts.length === 0 && (
          <div className="text-center py-8 text-cosmic-text-muted text-sm">
            No alerts in the last 24 hours
          </div>
        )}
      </div>
    </div>
  )
}

function AlertCard({ alert, onClick }: { alert: AlertRecord; onClick: () => void }) {
  const borderColor = {
    CRITICAL: 'border-l-cosmic-red',
    HIGH: 'border-l-cosmic-amber',
    MEDIUM: 'border-l-yellow-500',
    LOW: 'border-l-cosmic-cyan',
  }[alert.severity] ?? 'border-l-cosmic-border'

  return (
    <button
      onClick={onClick}
      className={`w-full text-left card border-l-2 ${borderColor} hover:border-cosmic-cyan/40 transition-all duration-200 cursor-pointer`}
      aria-label={`View details for ${alert.entity_name}`}
    >
      <div className="flex items-start justify-between gap-2 mb-1">
        <span className="text-sm font-medium text-cosmic-text-primary truncate">
          {alert.entity_name}
        </span>
        <SeverityBadge severity={alert.severity} />
      </div>

      {alert.ai_summary && (
        <p className="text-xs text-cosmic-text-secondary line-clamp-2 mb-1">
          {alert.ai_summary}
        </p>
      )}

      <div className="flex items-center justify-between">
        {alert.current_score !== null && (
          <span className="text-xs font-mono text-cosmic-text-muted">
            Score: <span className="text-cosmic-cyan">{alert.current_score.toFixed(1)}</span>
          </span>
        )}
        <span className="text-xs text-cosmic-text-muted">
          {formatDistanceToNow(alert.triggered_at)}
        </span>
      </div>
    </button>
  )
}
