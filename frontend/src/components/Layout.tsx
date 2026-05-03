import { Outlet } from 'react-router-dom'
import { NavBar } from './NavBar'
import { RiskFeed } from './RiskFeed/RiskFeed'
import { EntityPanel } from './EntityPanel/EntityPanel'
import { QueryBar } from './QueryBar/QueryBar'
import { useUIStore } from '@/store/uiStore'

export function Layout() {
  const isEntityPanelOpen = useUIStore((s) => s.isEntityPanelOpen)

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-cosmic-bg">
      <NavBar />
      <QueryBar />

      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar — live risk feed */}
        <aside className="w-80 flex-shrink-0 border-r border-cosmic-border overflow-y-auto hidden lg:block">
          <RiskFeed />
        </aside>

        {/* Main content */}
        <main className="flex-1 overflow-auto relative">
          <Outlet />
        </main>

        {/* Right sidebar — entity detail panel */}
        {isEntityPanelOpen && (
          <aside className="w-96 flex-shrink-0 border-l border-cosmic-border overflow-y-auto">
            <EntityPanel />
          </aside>
        )}
      </div>
    </div>
  )
}
