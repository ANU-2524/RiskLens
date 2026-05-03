interface RiskGaugeProps {
  score: number
  severity: string
}

export function RiskGauge({ score, severity }: RiskGaugeProps) {
  const percentage = Math.min(score, 100)
  const rotation = (percentage / 100) * 180 - 90

  const color = {
    CRITICAL: '#FF3B30',
    HIGH: '#FFB800',
    MEDIUM: '#EAB308',
    LOW: '#00D4FF',
  }[severity] ?? '#00D4FF'

  return (
    <div className="relative w-32 h-16">
      <svg viewBox="0 0 100 50" className="w-full h-full">
        {/* Background arc */}
        <path
          d="M 10 45 A 40 40 0 0 1 90 45"
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth="8"
          strokeLinecap="round"
        />
        {/* Colored arc */}
        <path
          d="M 10 45 A 40 40 0 0 1 90 45"
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={`${(percentage / 100) * 126} 126`}
          style={{ filter: `drop-shadow(0 0 8px ${color}80)` }}
        />
        {/* Needle */}
        <line
          x1="50"
          y1="45"
          x2="50"
          y2="15"
          stroke={color}
          strokeWidth="2"
          strokeLinecap="round"
          style={{ transformOrigin: '50px 45px', transform: `rotate(${rotation}deg)` }}
        />
        <circle cx="50" cy="45" r="3" fill={color} />
      </svg>
    </div>
  )
}
