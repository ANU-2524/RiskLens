import { useRef, useMemo, useEffect, useState } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, Stars, Html } from '@react-three/drei'
import * as THREE from 'three'
import { useEntities } from '@/api/entities'
import { useUIStore } from '@/store/uiStore'
import type { EntitySummary } from '@/api/entities'

const tempObject = new THREE.Object3D()
const tempColor = new THREE.Color()

export function GalaxyMap() {
  const { data } = useEntities(1)
  const entities = data?.items ?? []

  return (
    <div className="w-full h-full bg-cosmic-bg relative">
      <Canvas camera={{ position: [0, 0, 80], fov: 60 }}>
        <color attach="background" args={['#050510']} />
        <ambientLight intensity={0.4} />
        <pointLight position={[10, 10, 10]} intensity={1.5} />
        <Stars radius={400} depth={60} count={5000} factor={6} saturation={0} fade speed={1} />
        
        {entities.length > 0 && <EntityInstancedMesh entities={entities} />}
        
        <OrbitControls
          enablePan
          enableZoom
          enableRotate
          autoRotate
          autoRotateSpeed={0.2}
          minDistance={10}
          maxDistance={200}
        />
      </Canvas>
      
      {/* Performance HUD */}
      <div className="absolute top-4 left-4 p-2 bg-black/50 rounded border border-white/10 text-xs font-mono text-cyan-400">
        RENDER MODE: INSTANCED_MESH<br/>
        ENTITIES: {entities.length}<br/>
        DRAW CALLS: 1
      </div>
    </div>
  )
}

function EntityInstancedMesh({ entities }: { entities: EntitySummary[] }) {
  const meshRef = useRef<THREE.InstancedMesh>(null)
  const selectEntity = useUIStore((s) => s.selectEntity)
  const { raycaster, mouse, camera, scene } = useThree()
  
  // Hover state
  const [hovered, setHovered] = useState<number | null>(null)

  const starsData = useMemo(() => {
    const sectorAngles: Record<string, number> = {}
    let angleOffset = 0

    return entities.map((entity, i) => {
      const sector = entity.sector ?? 'General'
      if (!(sector in sectorAngles)) {
        sectorAngles[sector] = angleOffset
        angleOffset += (Math.PI * 2) / 12 // Spread sectors more
      }

      // Procedural distribution - Fibonacci Spiral-ish
      const angle = sectorAngles[sector] + (i * 0.1)
      const distFromCenter = 20 + (i * 0.05) + Math.random() * 5
      const x = Math.cos(angle) * distFromCenter
      const z = Math.sin(angle) * distFromCenter
      const y = (Math.random() - 0.5) * 15

      const score = entity.current_risk_score ?? 0
      const size = 0.4 + (score / 100) * 1.2

      const color = {
        CRITICAL: '#FF3B30',
        HIGH: '#FFB800',
        MEDIUM: '#EAB308',
        LOW: '#00D4FF',
      }[entity.severity ?? 'LOW'] ?? '#00D4FF'

      return { id: entity.id, name: entity.name, position: [x, y, z], size, color, score }
    })
  }, [entities])

  // Initialize instances
  useEffect(() => {
    if (!meshRef.current) return
    
    starsData.forEach((star, i) => {
      tempObject.position.set(star.position[0], star.position[1], star.position[2])
      tempObject.scale.setScalar(star.size)
      tempObject.updateMatrix()
      meshRef.current!.setMatrixAt(i, tempObject.matrix)
      
      tempColor.set(star.color)
      meshRef.current!.setColorAt(i, tempColor)
    })
    
    meshRef.current.instanceMatrix.needsUpdate = true
    if (meshRef.current.instanceColor) meshRef.current.instanceColor.needsUpdate = true
  }, [starsData])

  // Animation & Interaction
  useFrame((state) => {
    if (!meshRef.current) return
    const t = state.clock.getElapsedTime()

    // Handle pulse for high-risk entities
    starsData.forEach((star, i) => {
      if (star.score > 60 || i === hovered) {
        const pulse = 1 + Math.sin(t * 4 + i) * 0.15
        tempObject.position.set(star.position[0], star.position[1], star.position[2])
        tempObject.scale.setScalar(star.size * pulse)
        tempObject.updateMatrix()
        meshRef.current!.setMatrixAt(i, tempObject.matrix)
      }
    })
    meshRef.current.instanceMatrix.needsUpdate = true
  })

  const handleClick = (e: any) => {
    e.stopPropagation()
    const { instanceId } = e
    const star = starsData[instanceId]
    if (star) {
      selectEntity({ id: star.id, name: star.name })
    }
  }

  return (
    <instancedMesh
      ref={meshRef}
      args={[undefined, undefined, entities.length]}
      onClick={handleClick}
      onPointerOver={(e) => setHovered(e.instanceId!)}
      onPointerOut={() => setHovered(null)}
    >
      <sphereGeometry args={[1, 32, 32]} />
      <meshStandardMaterial metalness={0.6} roughness={0.2} emissiveIntensity={0.5} />
      
      {/* Tooltip on hover */}
      {hovered !== null && (
        <Html position={[
          starsData[hovered].position[0],
          starsData[hovered].position[1] + 2,
          starsData[hovered].position[2]
        ]}>
          <div className="bg-black/80 border border-white/20 p-2 rounded whitespace-nowrap pointer-events-none">
            <div className="font-bold text-white text-xs">{starsData[hovered].name}</div>
            <div className="text-cyan-400 text-[10px]">RISK SCORE: {starsData[hovered].score}</div>
          </div>
        </Html>
      )}
    </instancedMesh>
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
