import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Stars } from '@react-three/drei'
import * as THREE from 'three'
import { useEntities } from '@/api/entities'
import { useUIStore } from '@/store/uiStore'
import type { EntitySummary } from '@/api/entities'

export function GalaxyMap() {
  const { data } = useEntities(1)
  const entities = data?.items ?? []

  return (
    <div className="w-full h-full bg-cosmic-bg">
      <Canvas camera={{ position: [0, 0, 50], fov: 60 }}>
        <color attach="background" args={['#050510']} />
        <ambientLight intensity={0.3} />
        <Stars radius={300} depth={60} count={3000} factor={4} saturation={0} fade speed={0.5} />
        <EntityStars entities={entities} />
        <OrbitControls
          enablePan
          enableZoom
          enableRotate
          autoRotate
          autoRotateSpeed={0.3}
          minDistance={20}
          maxDistance={100}
        />
      </Canvas>
    </div>
  )
}

function EntityStars({ entities }: { entities: EntitySummary[] }) {
  const selectEntity = useUIStore((s) => s.selectEntity)

  const stars = useMemo(() => {
    const sectorAngles: Record<string, number> = {}
    let angleOffset = 0

    return entities.map((entity, i) => {
      const sector = entity.sector ?? 'General'
      if (!(sector in sectorAngles)) {
        sectorAngles[sector] = angleOffset
        angleOffset += (Math.PI * 2) / 8
      }

      const angle = sectorAngles[sector] + (i * 0.3)
      const radius = 15 + Math.random() * 20
      const x = Math.cos(angle) * radius
      const z = Math.sin(angle) * radius
      const y = (Math.random() - 0.5) * 10

      const score = entity.current_risk_score ?? 0
      const size = 0.3 + (score / 100) * 0.7

      const color = {
        CRITICAL: '#FF3B30',
        HIGH: '#FFB800',
        MEDIUM: '#EAB308',
        LOW: '#00D4FF',
      }[entity.severity ?? 'LOW'] ?? '#00D4FF'

      return { entity, position: [x, y, z] as [number, number, number], size, color, score }
    })
  }, [entities])

  return (
    <group>
      {stars.map(({ entity, position, size, color, score }) => (
        <EntityStar
          key={entity.id}
          position={position}
          size={size}
          color={color}
          score={score}
          onClick={() => selectEntity({ id: entity.id, name: entity.name })}
        />
      ))}
    </group>
  )
}

interface EntityStarProps {
  position: [number, number, number]
  size: number
  color: string
  score: number
  onClick: () => void
}

function EntityStar({ position, size, color, score, onClick }: EntityStarProps) {
  const meshRef = useRef<THREE.Mesh>(null)
  const glowRef = useRef<THREE.Mesh>(null)

  useFrame((state) => {
    if (!meshRef.current || !glowRef.current) return
    const t = state.clock.getElapsedTime()
    const pulse = score > 60 ? 1 + Math.sin(t * 3) * 0.2 : 1
    meshRef.current.scale.setScalar(pulse)
    glowRef.current.scale.setScalar(pulse * 1.5)
  })

  return (
    <group position={position}>
      {/* Glow */}
      <mesh ref={glowRef}>
        <sphereGeometry args={[size * 1.2, 16, 16]} />
        <meshBasicMaterial color={color} transparent opacity={0.2} />
      </mesh>
      {/* Core */}
      <mesh ref={meshRef} onClick={onClick}>
        <sphereGeometry args={[size, 16, 16]} />
        <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.8} />
      </mesh>
    </group>
  )
}
