import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiClient } from '@/api/client'
import { useAuthStore } from '@/store/authStore'

export function LoginPage() {
  const [isRegistering, setIsRegistering] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('ANALYST')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const setAuth = useAuthStore((s) => s.setAuth)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      const endpoint = isRegistering ? '/auth/register' : '/auth/login'
      const payload = isRegistering 
        ? { email, password, role } 
        : { email, password }

      const { data } = await apiClient.post<{ access_token: string }>(endpoint, payload)

      // Decode JWT to extract user info (simple base64 decode)
      const jwtPayload = JSON.parse(atob(data.access_token.split('.')[1]))
      setAuth(data.access_token, jwtPayload.email, jwtPayload.role)
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail ?? (isRegistering ? 'Registration failed' : 'Login failed'))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-cosmic-gradient">
      {/* Animated background particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {Array.from({ length: 50 }).map((_, i) => (
          <div
            key={i}
            className="absolute w-1 h-1 bg-cosmic-cyan/30 rounded-full animate-float"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 6}s`,
              animationDuration: `${6 + Math.random() * 4}s`,
            }}
          />
        ))}
      </div>

      <div className="card max-w-md w-full border border-cosmic-cyan/20 shadow-cyan-glow relative z-10">
        {/* Logo */}
        <div className="flex items-center justify-center mb-8">
          <div className="w-16 h-16 rounded-full bg-cosmic-cyan/20 border-2 border-cosmic-cyan flex items-center justify-center">
            <span className="text-cosmic-cyan text-3xl font-bold">M</span>
          </div>
        </div>

        <h1 className="text-2xl font-bold text-center text-gradient-cyan mb-2">RiskLens</h1>
        <p className="text-center text-cosmic-text-muted text-sm mb-8">
          {isRegistering ? 'Create your Analyst account' : 'AI-Powered Risk Intelligence Platform'}
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-cosmic-text-muted uppercase tracking-wider mb-2">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-cosmic w-full"
              required
              autoComplete="email"
            />
          </div>

          <div>
            <label className="block text-xs text-cosmic-text-muted uppercase tracking-wider mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-cosmic w-full"
              required
              autoComplete={isRegistering ? "new-password" : "current-password"}
            />
          </div>

          {isRegistering && (
            <div>
              <label className="block text-xs text-cosmic-text-muted uppercase tracking-wider mb-2">
                Role
              </label>
              <select 
                value={role} 
                onChange={(e) => setRole(e.target.value)}
                className="input-cosmic w-full bg-cosmic-bg"
              >
                <option value="ANALYST">Analyst</option>
                <option value="VIEWER">Viewer</option>
              </select>
            </div>
          )}

          {error && (
            <div className="bg-cosmic-red-glow border border-cosmic-red/30 rounded-lg p-3 text-sm text-cosmic-red">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary w-full py-3 text-base disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (isRegistering ? 'Registering...' : 'Signing in...') : (isRegistering ? 'Create Account' : 'Sign In')}
          </button>
        </form>

        <div className="mt-4 text-center">
          <button 
            onClick={() => setIsRegistering(!isRegistering)}
            className="text-xs text-cosmic-cyan hover:underline"
          >
            {isRegistering ? 'Already have an account? Sign in' : "Don't have an account? Register"}
          </button>
        </div>

        <div className="mt-6 pt-6 border-t border-cosmic-border">
          <p className="text-xs text-cosmic-text-muted text-center mb-2">Demo Credentials:</p>
          <div className="space-y-1 text-xs text-cosmic-text-secondary italic opacity-70">
            <p>demo@RiskLens.ai / RiskLens2024</p>
          </div>
        </div>
      </div>
    </div>
  )
}

