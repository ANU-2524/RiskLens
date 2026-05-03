import { useNavigate } from 'react-router-dom'
import { useEffect, useRef } from 'react'
import Hls from 'hls.js'

export function LandingPage() {
  const navigate = useNavigate()
  const videoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    const videoSrc = 'https://stream.mux.com/Aa02T7oM1wH5Mk5EEVDYhbZ1ChcdhRsS2m1NYyx4Ua1g.m3u8'

    if (Hls.isSupported()) {
      const hls = new Hls()
      hls.loadSource(videoSrc)
      hls.attachMedia(video)
      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        video.play().catch(err => console.log('Autoplay prevented:', err))
      })
      return () => hls.destroy()
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      // Native HLS support (Safari)
      video.src = videoSrc
      video.play().catch(err => console.log('Autoplay prevented:', err))
    }
  }, [])

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-black">
      {/* Video Background */}
      <video
        ref={videoRef}
        className="absolute inset-0 w-full h-full object-cover"
        autoPlay
        loop
        muted
        playsInline
      />

      {/* Dark overlay for better text visibility */}
      <div className="absolute inset-0 bg-black/40" />

      {/* Content */}
      <div className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4">
        {/* Logo */}
        <div className="mb-8 animate-fade-in">
          <div className="w-24 h-24 rounded-full bg-cosmic-cyan/20 border-4 border-cosmic-cyan flex items-center justify-center shadow-cyan-glow">
            <span className="text-cosmic-cyan text-5xl font-bold">M</span>
          </div>
        </div>

        {/* Title */}
        <h1 className="text-6xl md:text-7xl font-bold text-white mb-4 text-center animate-fade-in-up glow-text-cyan">
          Mysterious
        </h1>
        
        <p className="text-xl md:text-2xl text-cosmic-cyan mb-12 text-center animate-fade-in-up-delay">
          AI-Powered Risk Intelligence Platform
        </p>

        {/* CTA Button */}
        <button
          onClick={() => navigate('/login')}
          className="group relative px-12 py-4 text-xl font-semibold text-white bg-cosmic-cyan rounded-full
                     hover:bg-cosmic-cyan-dim transition-all duration-300 transform hover:scale-105
                     shadow-cyan-glow hover:shadow-cyan-glow-lg animate-fade-in-up-delay-2"
        >
          <span className="relative z-10">Let's Go</span>
          <div className="absolute inset-0 rounded-full bg-cosmic-cyan opacity-0 group-hover:opacity-20 blur-xl transition-opacity duration-300" />
        </button>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
          <div className="w-6 h-10 border-2 border-cosmic-cyan/50 rounded-full flex items-start justify-center p-2">
            <div className="w-1 h-2 bg-cosmic-cyan rounded-full animate-pulse" />
          </div>
        </div>
      </div>
    </div>
  )
}
