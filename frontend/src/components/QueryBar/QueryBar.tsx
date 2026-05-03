import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { submitQuery } from '@/api/search'
import { useUIStore } from '@/store/uiStore'
import type { QueryResponse } from '@/api/search'

const EXAMPLE_QUERIES = [
  'What companies in Asia are at high risk right now?',
  'Which energy sector entities show critical signals?',
  'Are there any crypto exchange risks I should know about?',
  'What is the current state of supply chain risk?',
]

export function QueryBar() {
  const [query, setQuery] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<QueryResponse | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const { queryHistory, addQueryToHistory } = useUIStore()

  async function handleSubmit(q: string) {
    if (!q.trim()) return
    setIsLoading(true)
    setIsModalOpen(true)
    addQueryToHistory(q)
    try {
      const response = await submitQuery(q)
      setResult(response)
    } catch {
      setResult({
        question: q,
        answer: 'Unable to process query. Please check your connection and try again.',
        context_entities: [],
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <>
      <div className="px-4 py-2 border-b border-cosmic-border bg-cosmic-bg-secondary/60 backdrop-blur-sm">
        <div className="max-w-2xl mx-auto">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-cosmic-text-muted text-sm">⌖</span>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSubmit(query)}
                placeholder="Ask Oracle anything... e.g. 'What companies are at critical risk?'"
                className="input-cosmic w-full pl-8 text-sm"
                aria-label="Natural language risk query"
              />
            </div>
            <button
              onClick={() => handleSubmit(query)}
              disabled={isLoading || !query.trim()}
              className="btn-primary text-sm px-4 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? '...' : 'Ask'}
            </button>
          </div>

          {/* Example query chips */}
          <div className="flex gap-2 mt-1.5 overflow-x-auto pb-1 scrollbar-hide">
            {EXAMPLE_QUERIES.map((q) => (
              <button
                key={q}
                onClick={() => { setQuery(q); handleSubmit(q) }}
                className="flex-shrink-0 text-xs px-2.5 py-1 rounded-full border border-cosmic-border text-cosmic-text-muted hover:border-cosmic-cyan hover:text-cosmic-cyan transition-all duration-200"
              >
                {q.length > 40 ? q.slice(0, 40) + '…' : q}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Result modal */}
      <AnimatePresence>
        {isModalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
            onClick={() => setIsModalOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              transition={{ type: 'spring', bounce: 0.2 }}
              className="card max-w-2xl w-full border border-cosmic-cyan/20 shadow-cyan-glow"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-cosmic-cyan animate-pulse" />
                  <span className="text-xs font-mono text-cosmic-cyan uppercase tracking-wider">Oracle AI Response</span>
                </div>
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="text-cosmic-text-muted hover:text-cosmic-text-primary transition-colors"
                  aria-label="Close query result"
                >
                  ✕
                </button>
              </div>

              <p className="text-sm text-cosmic-text-muted mb-3 italic">"{result?.question}"</p>

              {isLoading ? (
                <div className="space-y-2">
                  <div className="h-4 bg-cosmic-bg-elevated rounded animate-pulse" />
                  <div className="h-4 bg-cosmic-bg-elevated rounded animate-pulse w-4/5" />
                  <div className="h-4 bg-cosmic-bg-elevated rounded animate-pulse w-3/5" />
                </div>
              ) : (
                <>
                  <p className="text-sm text-cosmic-text-primary leading-relaxed mb-4">
                    {result?.answer}
                  </p>

                  {result?.context_entities && result.context_entities.length > 0 && (
                    <div>
                      <p className="text-xs text-cosmic-text-muted mb-2">Context entities:</p>
                      <div className="flex flex-wrap gap-1.5">
                        {result.context_entities.map((entity) => (
                          <span
                            key={entity}
                            className="text-xs px-2 py-0.5 rounded-full bg-cosmic-cyan-glow text-cosmic-cyan border border-cosmic-cyan/20"
                          >
                            {entity}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
