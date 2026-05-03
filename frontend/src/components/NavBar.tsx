import { Link, useLocation, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuthStore } from '@/store/authStore'

const NAV_LINKS = [
  { path: '/app', label: 'Galaxy Map' },
  { path: '/app/dashboard', label: 'Dashboard' },
  { path: '/app/timeline', label: 'Timeline' },
  { path: '/app/reports', label: 'Reports' },
]

export function NavBar() {
  const location = useLocation()
  const navigate = useNavigate()
  const { email, role, clearAuth } = useAuthStore()

  function handleLogout() {
    clearAuth()
    navigate('/login')
  }

  return (
    <nav className="flex items-center justify-between px-6 py-3 border-b border-cosmic-border bg-cosmic-bg-secondary/80 backdrop-blur-sm z-50 flex-shrink-0">
      {/* Logo */}
      <Link to="/app" className="flex items-center gap-3 group">
        <div className="w-8 h-8 rounded-full bg-cosmic-cyan/20 border border-cosmic-cyan/40 flex items-center justify-center group-hover:shadow-cyan-glow transition-all duration-300">
          <span className="text-cosmic-cyan text-sm font-bold">M</span>
        </div>
        <span className="font-semibold text-cosmic-text-primary tracking-wide">
          <span className="text-gradient-cyan">Mysterious</span>
          <span className="text-cosmic-text-muted text-xs ml-2 font-mono">RISK INTELLIGENCE</span>
        </span>
      </Link>

      {/* Nav links */}
      <div className="hidden md:flex items-center gap-1">
        {NAV_LINKS.map((link) => {
          const isActive = location.pathname === link.path
          return (
            <Link
              key={link.path}
              to={link.path}
              className={`relative px-4 py-2 text-sm rounded-lg transition-all duration-200 ${
                isActive
                  ? 'text-cosmic-cyan'
                  : 'text-cosmic-text-secondary hover:text-cosmic-text-primary'
              }`}
            >
              {isActive && (
                <motion.div
                  layoutId="nav-indicator"
                  className="absolute inset-0 bg-cosmic-cyan-glow border border-cosmic-cyan/20 rounded-lg"
                  transition={{ type: 'spring', bounce: 0.2, duration: 0.4 }}
                />
              )}
              <span className="relative z-10">{link.label}</span>
            </Link>
          )
        })}
      </div>

      {/* User info */}
      <div className="flex items-center gap-3">
        <div className="hidden sm:flex flex-col items-end">
          <span className="text-xs text-cosmic-text-secondary">{email}</span>
          <span className="text-xs font-mono text-cosmic-cyan uppercase">{role}</span>
        </div>
        <button
          onClick={handleLogout}
          className="btn-ghost text-sm py-1.5"
          aria-label="Sign out"
        >
          Sign out
        </button>
      </div>
    </nav>
  )
}
