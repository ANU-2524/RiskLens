import { useState } from 'react'
import { useEntities, useEntityDetail } from '@/api/entities'
import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'

export function ReportsPage() {
  const { data: entitiesData } = useEntities(1)
  const [selectedEntityId, setSelectedEntityId] = useState<number | null>(null)
  const { data: entity } = useEntityDetail(selectedEntityId)
  const [isGenerating, setIsGenerating] = useState(false)

  const entities = entitiesData?.items ?? []

  async function generatePDF() {
    if (!entity) return
    setIsGenerating(true)

    try {
      const doc = new jsPDF()
      const pageWidth = doc.internal.pageSize.getWidth()

      // Header
      doc.setFontSize(20)
      doc.setTextColor(0, 212, 255)
      doc.text('Oracle Risk Intelligence Report', 14, 20)

      doc.setFontSize(10)
      doc.setTextColor(100, 100, 100)
      doc.text(`Generated: ${new Date().toLocaleString()}`, 14, 28)

      // Entity info
      doc.setFontSize(16)
      doc.setTextColor(0, 0, 0)
      doc.text(entity.name, 14, 40)

      doc.setFontSize(10)
      doc.setTextColor(100, 100, 100)
      doc.text(`${entity.type} | ${entity.sector ?? 'General'} | ${entity.ticker ?? 'N/A'}`, 14, 46)

      if (entity.description) {
        doc.setFontSize(9)
        doc.text(doc.splitTextToSize(entity.description, pageWidth - 28), 14, 52)
      }

      // Risk score
      doc.setFontSize(12)
      doc.setTextColor(0, 0, 0)
      doc.text('Current Risk Assessment', 14, 70)

      doc.setFontSize(24)
      const scoreColor = entity.current_risk_score && entity.current_risk_score >= 60 ? [255, 59, 48] : [0, 212, 255]
      doc.setTextColor(...scoreColor)
      doc.text(`${entity.current_risk_score?.toFixed(1) ?? 'N/A'}/100`, 14, 82)

      doc.setFontSize(10)
      doc.setTextColor(100, 100, 100)
      doc.text(`Severity: ${entity.severity ?? 'N/A'}`, 14, 90)

      // AI Summary
      if (entity.latest_summary) {
        doc.setFontSize(12)
        doc.setTextColor(0, 0, 0)
        doc.text('AI Risk Analysis', 14, 105)

        doc.setFontSize(9)
        doc.setTextColor(60, 60, 60)
        const summaryLines = doc.splitTextToSize(entity.latest_summary.summary_text, pageWidth - 28)
        doc.text(summaryLines, 14, 112)

        let yPos = 112 + summaryLines.length * 4 + 5

        if (entity.latest_summary.recommended_action) {
          doc.setFontSize(10)
          doc.setTextColor(255, 184, 0)
          doc.text('Recommended Action:', 14, yPos)
          yPos += 6

          doc.setFontSize(9)
          doc.setTextColor(60, 60, 60)
          const actionLines = doc.splitTextToSize(entity.latest_summary.recommended_action, pageWidth - 28)
          doc.text(actionLines, 14, yPos)
          yPos += actionLines.length * 4 + 10
        }

        // Contributing signals table
        if (entity.latest_summary.contributing_signals && yPos < 250) {
          autoTable(doc, {
            startY: yPos,
            head: [['Signal', 'Evidence']],
            body: entity.latest_summary.contributing_signals.map((s) => [s.signal, s.evidence]),
            theme: 'grid',
            headStyles: { fillColor: [0, 212, 255], textColor: [255, 255, 255] },
            styles: { fontSize: 8 },
          })
        }
      }

      // Risk history table
      if (entity.recent_risk_scores.length > 0) {
        const finalY = (doc as any).lastAutoTable?.finalY ?? 160
        autoTable(doc, {
          startY: finalY + 10,
          head: [['Date', 'Score', 'Severity']],
          body: entity.recent_risk_scores.slice(0, 10).map((rs) => [
            new Date(rs.computed_at).toLocaleDateString(),
            rs.score.toFixed(1),
            rs.severity,
          ]),
          theme: 'grid',
          headStyles: { fillColor: [0, 212, 255], textColor: [255, 255, 255] },
          styles: { fontSize: 8 },
        })
      }

      // Footer
      const pageCount = doc.getNumberOfPages()
      for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i)
        doc.setFontSize(8)
        doc.setTextColor(150, 150, 150)
        doc.text(
          `Oracle Risk Intelligence Platform | Page ${i} of ${pageCount}`,
          pageWidth / 2,
          doc.internal.pageSize.getHeight() - 10,
          { align: 'center' }
        )
      }

      doc.save(`oracle-report-${entity.name.replace(/\s+/g, '-')}-${Date.now()}.pdf`)
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-cosmic-text-primary mb-1">Risk Reports</h1>
        <p className="text-sm text-cosmic-text-secondary">Generate professional PDF risk reports for any entity</p>
      </div>

      <div className="card">
        <label className="block text-xs text-cosmic-text-muted uppercase tracking-wider mb-2">
          Select Entity
        </label>
        <select
          value={selectedEntityId ?? ''}
          onChange={(e) => setSelectedEntityId(Number(e.target.value) || null)}
          className="input-cosmic w-full max-w-md"
        >
          <option value="">— Choose an entity —</option>
          {entities.map((e) => (
            <option key={e.id} value={e.id}>
              {e.name} ({e.sector})
            </option>
          ))}
        </select>

        {entity && (
          <div className="mt-6 space-y-4">
            <div className="border-l-4 border-l-cosmic-cyan pl-4">
              <h3 className="text-lg font-semibold text-cosmic-text-primary">{entity.name}</h3>
              <p className="text-xs text-cosmic-text-muted mt-1">
                {entity.type} | {entity.sector} | {entity.ticker ?? 'N/A'}
              </p>
              {entity.description && (
                <p className="text-sm text-cosmic-text-secondary mt-2">{entity.description}</p>
              )}
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="card-elevated text-center">
                <p className="text-xs text-cosmic-text-muted">Risk Score</p>
                <p className="text-2xl font-bold font-mono text-cosmic-cyan mt-1">
                  {entity.current_risk_score?.toFixed(1) ?? 'N/A'}
                </p>
              </div>
              <div className="card-elevated text-center">
                <p className="text-xs text-cosmic-text-muted">Severity</p>
                <p className="text-lg font-semibold text-cosmic-amber mt-1">{entity.severity ?? 'N/A'}</p>
              </div>
              <div className="card-elevated text-center">
                <p className="text-xs text-cosmic-text-muted">Signals</p>
                <p className="text-2xl font-bold font-mono text-cosmic-cyan mt-1">{entity.signal_count}</p>
              </div>
            </div>

            <button
              onClick={generatePDF}
              disabled={isGenerating}
              className="btn-primary w-full py-3 text-base disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isGenerating ? 'Generating PDF...' : '📄 Generate PDF Report'}
            </button>

            <p className="text-xs text-cosmic-text-muted text-center">
              Report includes: risk score, AI summary, contributing signals, and historical data
            </p>
          </div>
        )}

        {!selectedEntityId && (
          <div className="mt-6 text-center py-8 text-cosmic-text-muted">
            Select an entity to generate a report
          </div>
        )}
      </div>
    </div>
  )
}
