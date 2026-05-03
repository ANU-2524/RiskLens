import { GalaxyMap } from '@/components/GalaxyMap/GalaxyMap'

export function GalaxyMapPage() {
  return (
    <div className="w-full h-full relative">
      <GalaxyMap />
      <div className="absolute top-4 left-4 card max-w-xs">
        <h2 className="text-sm font-semibold text-cosmic-cyan mb-1">Galaxy Map</h2>
        <p className="text-xs text-cosmic-text-secondary leading-relaxed">
          Each star represents a tracked entity. Size and brightness indicate risk level.
          Click any star to view details.
        </p>
        <div className="mt-3 space-y-1 text-xs">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cosmic-cyan" />
            <span className="text-cosmic-text-muted">Low Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cosmic-amber" />
            <span className="text-cosmic-text-muted">High Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-cosmic-red animate-pulse" />
            <span className="text-cosmic-text-muted">Critical Risk</span>
          </div>
        </div>
      </div>
    </div>
  )
}
