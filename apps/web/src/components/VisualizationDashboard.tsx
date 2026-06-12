import React, { useEffect, useMemo, useState } from 'react'
import * as api from '../lib/api'

type Assumption = {
  id: string
  parent_id?: string | null
  assumption_text?: string
  category?: string | null
  depth?: number | null
  confidence_score?: number | null
  impact_score?: number | null
}

type Critique = {
  id: string
  assumption_id?: string | null
  critique_text?: string
  severity?: number | null
}

type Simulation = {
  id: string
  scenario?: string
  impact?: number | null
  likelihood?: number | null
  affected_assumptions_json?: string[] | null
}

type Score = {
  id: string
  assumption_id?: string | null
  confidence_score?: number | null
  dependency_weight?: number | null
  impact_severity?: number | null
  evidence_strength?: number | null
  risk_score?: number | null
}

function clamp(value: number, min: number, max: number){
  return Math.max(min, Math.min(max, value))
}

function heatColor(risk: number){
  const normalized = clamp(risk / 100, 0, 1)
  const red = Math.round(220 * normalized + 20)
  const green = Math.round(180 * (1 - normalized) + 20)
  const blue = Math.round(40 * (1 - normalized))
  return `rgb(${red}, ${green}, ${blue})`
}

function normalizeArray<T>(value: any): T[] {
  if (Array.isArray(value)) return value
  if (Array.isArray(value?.items)) return value.items
  if (Array.isArray(value?.created)) return value.created
  if (Array.isArray(value?.data)) return value.data
  return []
}

function sectionCard(title: string, subtitle: string, body: React.ReactNode){
  return (
    <section className="rounded-2xl border border-gray-800 bg-surface/80 p-4 shadow-lg shadow-black/30">
      <div className="mb-4">
        <h3 className="text-base font-semibold text-white">{title}</h3>
        <p className="text-sm text-gray-400">{subtitle}</p>
      </div>
      {body}
    </section>
  )
}

function ConfidenceRadarVisualization({ scores, assumptions }: { scores: Score[]; assumptions: Assumption[] }){
  const size = 300
  const center = size / 2
  const maxRadius = size / 2.5

  const categories = Array.from(new Set(assumptions.map((a) => a.category || 'uncategorized'))).slice(0, 6)
  const categoryScores = categories.map((cat) => {
    const catAssumptions = assumptions.filter((a) => a.category === cat || (!a.category && cat === 'uncategorized'))
    const catScores = catAssumptions.flatMap((a) => scores.filter((s) => s.assumption_id === a.id))
    const avgConfidence = catScores.length > 0 ? Math.round(catScores.reduce((sum, s) => sum + (s.confidence_score ?? 0), 0) / catScores.length) : 0
    const avgEvidence = catScores.length > 0 ? Math.round(catScores.reduce((sum, s) => sum + (s.evidence_strength ?? 0), 0) / catScores.length) : 0
    return { category: cat, confidence: avgConfidence, evidence: avgEvidence, count: catAssumptions.length }
  })

  const angleSlice = (Math.PI * 2) / categories.length
  const radarPoints = categoryScores.map((item, idx) => {
    const angle = angleSlice * idx - Math.PI / 2
    const r1 = (item.confidence / 100) * maxRadius
    const x1 = center + r1 * Math.cos(angle)
    const y1 = center + r1 * Math.sin(angle)
    return { ...item, angle, x: x1, y: y1, r: r1 }
  })

  const pointsStr = radarPoints.map((p) => `${p.x},${p.y}`).join(' ')

  if (!assumptions.length) {
    return <div className="rounded-xl border border-dashed border-gray-700 bg-black/20 p-6 text-sm text-gray-400">No confidence data yet.</div>
  }

  return (
    <div className="flex flex-col items-center">
      <svg viewBox={`0 0 ${size} ${size}`} className="h-[300px] w-[300px]">
        {/* grid rings */}
        {[1, 2, 3, 4, 5].map((ring) => (
          <circle key={`ring-${ring}`} cx={center} cy={center} r={(maxRadius / 5) * ring} fill="none" stroke="rgba(0,255,127,0.1)" strokeWidth={1} />
        ))}
        {/* axes */}
        {radarPoints.map((p, idx) => (
          <line key={`axis-${idx}`} x1={center} y1={center} x2={p.x + (p.x - center) * 0.2} y2={p.y + (p.y - center) * 0.2} stroke="rgba(0,255,127,0.2)" strokeWidth={1} />
        ))}
        {/* confidence polygon */}
        <polygon points={pointsStr} fill="rgba(0,255,127,0.2)" stroke="#00FF7F" strokeWidth={2} />
        {/* points */}
        {radarPoints.map((p) => (
          <g key={`point-${p.category}`}>
            <circle cx={p.x} cy={p.y} r={5} fill="#00FF7F" stroke="#000" strokeWidth={1} />
            <text x={p.x + (p.x - center) * 0.3} y={p.y + (p.y - center) * 0.3 + 3} textAnchor="middle" className="fill-gray-300 text-[10px] font-semibold" style={{ pointerEvents: 'none' }}>
              {p.category.slice(0, 8)}
            </text>
          </g>
        ))}
      </svg>
      <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {radarPoints.map((item) => (
          <div key={item.category} className="rounded-lg border border-gray-800 bg-black/20 p-2 text-xs">
            <div className="font-medium text-white">{item.category}</div>
            <div className="text-gray-400">confidence: {item.confidence}%</div>
            <div className="text-gray-400">evidence: {item.evidence}%</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function ContradictionMapVisualization({ assumptions, critiques }: { assumptions: Assumption[]; critiques: Critique[] }){
  const contradictions = useMemo(() => {
    const result: { id: string; a1: Assumption; a2: Assumption; severity: number }[] = []
    for (let i = 0; i < assumptions.length; i++) {
      for (let j = i + 1; j < assumptions.length; j++) {
        const a1 = assumptions[i]!
        const a2 = assumptions[j]!
        if ((a1.category === a2.category && a1.assumption_text?.toLowerCase().includes('not') !== a2.assumption_text?.toLowerCase().includes('not')) ||
            (a1.assumption_text?.toLowerCase().localeCompare(a2.assumption_text?.toLowerCase() || '') || 0) > 0) {
          const a1Critiques = critiques.filter((c) => c.assumption_id === a1.id)
          const a2Critiques = critiques.filter((c) => c.assumption_id === a2.id)
          const severity = Math.max(0, ...[...a1Critiques, ...a2Critiques].map((c) => c.severity ?? 0))
          if (severity > 0) {
            result.push({ id: `${a1.id}-${a2.id}`, a1: a1, a2: a2, severity })
          }
        }
      }
    }
    return result
  }, [assumptions, critiques])

  if (!assumptions.length || !contradictions.length) {
    return <div className="rounded-xl border border-dashed border-gray-700 bg-black/20 p-6 text-sm text-gray-400">No contradictions detected. Run the pipeline for a full analysis.</div>
  }

  return (
    <div className="space-y-3">
      {contradictions.slice(0, 10).map((contra) => (
        <div key={contra.id} className="rounded-lg border border-gray-800 bg-black/20 p-3">
          <div className="mb-2 flex items-center justify-between">
            <div className="text-sm font-medium text-white">Potential contradiction</div>
            <div className="rounded-full bg-red-900/40 px-2 py-1 text-xs text-red-200">severity: {contra.severity}</div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-md border border-gray-700 bg-black/30 p-2">
              <div className="text-xs text-gray-400">{contra.a1?.category || 'uncategorized'}</div>
              <div className="mt-1 text-sm text-gray-200">{contra.a1?.assumption_text}</div>
            </div>
            <div className="rounded-md border border-gray-700 bg-black/30 p-2">
              <div className="text-xs text-gray-400">{contra.a2?.category || 'uncategorized'}</div>
              <div className="mt-1 text-sm text-gray-200">{contra.a2?.assumption_text}</div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

function InteractionControls({ onZoom, onFilter, onFocus, categoryOptions, selectedCategory }: { onZoom: (level: number) => void; onFilter: (cat: string) => void; onFocus: (mode: 'all' | 'high-risk' | 'low-confidence') => void; categoryOptions: string[]; selectedCategory: string }){
  return (
    <div className="flex flex-wrap gap-3">
      <div>
        <label className="block text-xs text-gray-400">Zoom</label>
        <div className="flex gap-1">
          <button onClick={() => onZoom(0.8)} className="rounded border border-gray-700 bg-black/30 px-2 py-1 text-xs hover:bg-black/50">−</button>
          <button onClick={() => onZoom(1)} className="rounded border border-gray-700 bg-black/30 px-2 py-1 text-xs hover:bg-black/50">1×</button>
          <button onClick={() => onZoom(1.2)} className="rounded border border-gray-700 bg-black/30 px-2 py-1 text-xs hover:bg-black/50">+</button>
        </div>
      </div>
      <div>
        <label className="block text-xs text-gray-400">Filter</label>
        <select value={selectedCategory} onChange={(e) => onFilter(e.target.value)} className="rounded border border-gray-700 bg-black/30 px-2 py-1 text-xs">
          <option value="">All categories</option>
          {categoryOptions.map((cat) => (
            <option key={cat} value={cat}>
              {cat}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="block text-xs text-gray-400">Focus</label>
        <div className="flex gap-1">
          <button onClick={() => onFocus('all')} className="rounded border border-gray-700 bg-black/30 px-2 py-1 text-xs hover:bg-black/50">All</button>
          <button onClick={() => onFocus('high-risk')} className="rounded border border-red-700/50 bg-red-900/20 px-2 py-1 text-xs text-red-200 hover:bg-red-900/40">High-risk</button>
          <button onClick={() => onFocus('low-confidence')} className="rounded border border-yellow-700/50 bg-yellow-900/20 px-2 py-1 text-xs text-yellow-200 hover:bg-yellow-900/40">Low-conf</button>
        </div>
      </div>
    </div>
  )
}

function GraphSnapshotExport({ runId }: { runId: string }){
  function downloadSvg(){
    const svg = document.querySelector('svg')
    if (!svg) {
      alert('No visualization found to export')
      return
    }
    const serializer = new XMLSerializer()
    const svgString = serializer.serializeToString(svg)
    const blob = new Blob([svgString], { type: 'image/svg+xml' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `visualization-${runId}-${Date.now()}.svg`
    a.click()
    URL.revokeObjectURL(url)
  }

  function downloadPng(){
    const canvas = document.createElement('canvas')
    const svg = document.querySelector('svg')
    if (!svg) {
      alert('No visualization found to export')
      return
    }
    const serializer = new XMLSerializer()
    const svgString = serializer.serializeToString(svg)
    const img = new Image()
    img.onload = () => {
      canvas.width = img.width
      canvas.height = img.height
      const ctx = canvas.getContext('2d')!
      ctx.fillStyle = '#000000'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      ctx.drawImage(img, 0, 0)
      const pngUrl = canvas.toDataURL('image/png')
      const a = document.createElement('a')
      a.href = pngUrl
      a.download = `visualization-${runId}-${Date.now()}.png`
      a.click()
    }
    img.src = 'data:image/svg+xml;base64,' + btoa(svgString)
  }

  return (
    <div className="flex gap-2">
      <button onClick={downloadSvg} className="rounded border border-primary bg-primary/10 px-3 py-2 text-sm text-primary hover:bg-primary/20">Export SVG</button>
      <button onClick={downloadPng} className="rounded border border-primary bg-primary/10 px-3 py-2 text-sm text-primary hover:bg-primary/20">Export PNG</button>
    </div>
  )
}

function AssumptionGraphVisualization({ assumptions }: { assumptions: Assumption[] }){
  const { nodes, edges, width, height } = useMemo(() => {
    const width = 920
    const height = 460
    const root = assumptions[0]

    const nodes = assumptions.map((assumption, index) => {
      const depth = assumption.depth ?? (assumption.parent_id ? 2 : 1)
      const layer = clamp(depth, 1, 4)
      const angle = assumptions.length > 1 ? (Math.PI * 2 * index) / assumptions.length : 0
      const radius = 70 + (layer - 1) * 95
      const cx = width / 2
      const cy = height / 2
      return {
        ...assumption,
        x: root && assumption.id === root.id ? cx : cx + Math.cos(angle) * radius,
        y: root && assumption.id === root.id ? cy : cy + Math.sin(angle) * radius,
        depth: layer,
      }
    })

    const lookup = new Map(nodes.map((node) => [node.id, node]))
    const edges = assumptions
      .filter((assumption) => assumption.parent_id && lookup.has(assumption.parent_id))
      .map((assumption) => ({
        from: lookup.get(assumption.parent_id as string)!,
        to: lookup.get(assumption.id)!,
      }))

    return { nodes, edges, width, height }
  }, [assumptions])

  if (!assumptions.length) {
    return <div className="rounded-xl border border-dashed border-gray-700 bg-black/20 p-6 text-sm text-gray-400">No assumption data yet. Run the pipeline to populate the graph.</div>
  }

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${height}`} className="h-[460px] w-full overflow-visible rounded-xl bg-black/20">
        {edges.map((edge, index) => (
          <line
            key={`${edge.from.id}-${edge.to.id}-${index}`}
            x1={edge.from.x}
            y1={edge.from.y}
            x2={edge.to.x}
            y2={edge.to.y}
            stroke="rgba(0,255,127,0.35)"
            strokeWidth={1.5}
          />
        ))}
        {nodes.map((node) => (
          <g key={node.id} transform={`translate(${node.x}, ${node.y})`}>
            <circle r={node.id === assumptions[0]?.id ? 24 : 18} fill={node.id === assumptions[0]?.id ? '#00FF7F' : '#0f1f16'} stroke="#00FF7F" strokeWidth={1.5} />
            <text textAnchor="middle" y={4} className="fill-black text-[10px] font-semibold" style={{ pointerEvents: 'none' }}>
              {node.id === assumptions[0]?.id ? 'root' : node.category?.slice(0, 1)?.toUpperCase() || 'A'}
            </text>
            <title>{node.assumption_text || node.category || node.id}</title>
          </g>
        ))}
      </svg>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {nodes.slice(0, 6).map((node) => (
          <div key={node.id} className="rounded-xl border border-gray-800 bg-black/20 p-3 text-sm text-gray-200">
            <div className="mb-1 font-medium text-white">{node.category || 'uncategorized'}</div>
            <div className="text-gray-400">{node.assumption_text || node.id}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

function DependencyTreeVisualization({ assumptions }: { assumptions: Assumption[] }){
  const tree = useMemo(() => {
    const childrenByParent = new Map<string | null, Assumption[]>()
    for (const assumption of assumptions) {
      const parentKey = assumption.parent_id ?? null
      const current = childrenByParent.get(parentKey) ?? []
      current.push(assumption)
      childrenByParent.set(parentKey, current)
    }
    return childrenByParent
  }, [assumptions])

  function renderBranch(parentId: string | null, depth: number): React.ReactNode {
    const children = tree.get(parentId) ?? []
    if (!children.length) {
      return null
    }

    return (
      <ul className="space-y-2 border-l border-gray-700 pl-4">
        {children.map((child) => (
          <li key={child.id}>
            <div className="rounded-lg border border-gray-800 bg-black/20 p-3">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="text-sm font-medium text-white">{child.assumption_text || child.id}</div>
                  <div className="text-xs text-gray-400">{child.category || 'uncategorized'} • depth {depth + 1}</div>
                </div>
                <div className="text-right text-xs text-gray-500">
                  <div>confidence {child.confidence_score ?? '—'}</div>
                  <div>impact {child.impact_score ?? '—'}</div>
                </div>
              </div>
            </div>
            {renderBranch(child.id, depth + 1)}
          </li>
        ))}
      </ul>
    )
  }

  const roots = assumptions.filter((assumption) => !assumption.parent_id)

  if (!assumptions.length) {
    return <div className="rounded-xl border border-dashed border-gray-700 bg-black/20 p-6 text-sm text-gray-400">No assumption tree available yet.</div>
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
      <div>{renderBranch(null, 0)}</div>
      <div className="rounded-xl border border-gray-800 bg-black/20 p-4">
        <h4 className="text-sm font-semibold text-white">Tree summary</h4>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <div className="rounded-lg bg-surface/60 p-3">
            <div className="text-xs uppercase tracking-[0.2em] text-gray-500">Roots</div>
            <div className="text-2xl font-semibold text-white">{roots.length}</div>
          </div>
          <div className="rounded-lg bg-surface/60 p-3">
            <div className="text-xs uppercase tracking-[0.2em] text-gray-500">Nodes</div>
            <div className="text-2xl font-semibold text-white">{assumptions.length}</div>
          </div>
        </div>
        <div className="mt-4 space-y-2 text-sm text-gray-300">
          {roots.slice(0, 4).map((root) => (
            <div key={root.id} className="rounded-lg border border-gray-800 bg-black/20 p-3">
              <div className="font-medium text-white">{root.assumption_text || root.id}</div>
              <div className="text-xs text-gray-400">{root.category || 'uncategorized'}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function RiskHeatmapVisualization({ assumptions, critiques, simulations, scores }: { assumptions: Assumption[]; critiques: Critique[]; simulations: Simulation[]; scores: Score[] }){
  const rows = assumptions.slice(0, 12).map((assumption) => {
    const assumptionCritiques = critiques.filter((critique) => critique.assumption_id === assumption.id)
    const assumptionScores = scores.filter((score) => score.assumption_id === assumption.id)
    const maxRisk = Math.max(0, ...assumptionScores.map((score) => score.risk_score ?? 0))
    const maxSeverity = Math.max(0, ...assumptionCritiques.map((critique) => critique.severity ?? 0))
    const exposure = Math.max(0, ...simulations.map((simulation) => {
      const affected = simulation.affected_assumptions_json ?? []
      return affected.includes(assumption.id) ? (simulation.impact ?? 0) * (simulation.likelihood ?? 0) : 0
    }))

    return {
      id: assumption.id,
      label: assumption.assumption_text || assumption.id,
      category: assumption.category || 'uncategorized',
      risk: maxRisk || Math.round((maxSeverity * 14 + exposure) / 3),
      confidence: assumption.confidence_score ?? assumptionScores[0]?.confidence_score ?? 0,
      severity: maxSeverity,
      exposure,
    }
  })

  if (!assumptions.length) {
    return <div className="rounded-xl border border-dashed border-gray-700 bg-black/20 p-6 text-sm text-gray-400">No risk data yet. The heatmap will populate after assumptions, critiques, and scores exist.</div>
  }

  return (
    <div className="overflow-hidden rounded-xl border border-gray-800 bg-black/20">
      <div className="grid grid-cols-[minmax(14rem,1.4fr)_repeat(4,minmax(5rem,0.7fr))] border-b border-gray-800 bg-surface/60 text-xs uppercase tracking-[0.2em] text-gray-500">
        <div className="px-4 py-3">Assumption</div>
        <div className="px-4 py-3">Risk</div>
        <div className="px-4 py-3">Confidence</div>
        <div className="px-4 py-3">Severity</div>
        <div className="px-4 py-3">Exposure</div>
      </div>
      {rows.map((row) => (
        <div key={row.id} className="grid grid-cols-[minmax(14rem,1.4fr)_repeat(4,minmax(5rem,0.7fr))] border-b border-gray-900 last:border-b-0">
          <div className="px-4 py-3">
            <div className="text-sm font-medium text-white">{row.label}</div>
            <div className="text-xs text-gray-500">{row.category}</div>
          </div>
          <div className="px-4 py-3">
            <div className="flex h-10 items-center justify-center rounded-md text-sm font-semibold text-black" style={{ backgroundColor: heatColor(row.risk) }}>
              {row.risk || '—'}
            </div>
          </div>
          <div className="px-4 py-3">
            <div className="flex h-10 items-center justify-center rounded-md bg-surface/80 text-sm text-gray-200">
              {row.confidence || '—'}
            </div>
          </div>
          <div className="px-4 py-3">
            <div className="flex h-10 items-center justify-center rounded-md bg-surface/80 text-sm text-gray-200">
              {row.severity || '—'}
            </div>
          </div>
          <div className="px-4 py-3">
            <div className="flex h-10 items-center justify-center rounded-md bg-surface/80 text-sm text-gray-200">
              {row.exposure || '—'}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default function VisualizationDashboard({ runId }: { runId: string }){
  const [assumptions, setAssumptions] = useState<Assumption[]>([])
  const [critiques, setCritiques] = useState<Critique[]>([])
  const [simulations, setSimulations] = useState<Simulation[]>([])
  const [scores, setScores] = useState<Score[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState('')
  const [focusMode, setFocusMode] = useState<'all' | 'high-risk' | 'low-confidence'>('all')
  const [zoomLevel, setZoomLevel] = useState(1)

  useEffect(() => {
    let active = true
    async function load() {
      setLoading(true)
      try {
        const [assumptionData, critiqueData, simulationData, scoreData] = await Promise.all([
          api.fetchAssumptions(runId).catch(() => []),
          api.fetchCritiques(runId).catch(() => []),
          api.fetchSimulations(runId).catch(() => []),
          api.fetchScores(runId).catch(() => []),
        ])

        if (!active) return
        setAssumptions(normalizeArray<Assumption>(assumptionData))
        setCritiques(normalizeArray<Critique>(critiqueData))
        setSimulations(normalizeArray<Simulation>(simulationData))
        setScores(normalizeArray<Score>(scoreData))
      } finally {
        if (active) setLoading(false)
      }
    }

    load().catch(() => {
      if (active) setLoading(false)
    })

    return () => {
      active = false
    }
  }, [runId])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3 rounded-lg border border-gray-800 bg-surface/60 p-3">
        <div>
          <InteractionControls onZoom={setZoomLevel} onFilter={setSelectedCategory} onFocus={setFocusMode} categoryOptions={Array.from(new Set(assumptions.map((a) => a.category || 'uncategorized')))} selectedCategory={selectedCategory} />
        </div>
        <div>
          <GraphSnapshotExport runId={runId} />
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {sectionCard(
          'Assumption graph',
          'A node-link view of the assumption chain and parent-child relationships.',
          loading ? <div className="text-sm text-gray-400">Loading graph…</div> : <AssumptionGraphVisualization assumptions={assumptions} />,
        )}
        {sectionCard(
          'Dependency tree',
          'Indented tree layout for spotting branches, roots, and deep dependency paths.',
          loading ? <div className="text-sm text-gray-400">Loading tree…</div> : <DependencyTreeVisualization assumptions={assumptions} />,
        )}
        {sectionCard(
          'Confidence radar',
          'Polar chart showing average confidence and evidence strength by category.',
          loading ? <div className="text-sm text-gray-400">Loading radar…</div> : <ConfidenceRadarVisualization scores={scores} assumptions={assumptions} />,
        )}
        {sectionCard(
          'Contradiction map',
          'Detected potential contradictions between assumptions with severity indicators.',
          loading ? <div className="text-sm text-gray-400">Loading map…</div> : <ContradictionMapVisualization assumptions={assumptions} critiques={critiques} />,
        )}
      </div>

      {sectionCard(
        'Risk heatmap',
        'A compact matrix that combines critique severity, confidence, exposure, and risk score.',
        loading ? <div className="text-sm text-gray-400">Loading heatmap…</div> : <RiskHeatmapVisualization assumptions={assumptions} critiques={critiques} simulations={simulations} scores={scores} />,
      )}
    </div>
  )
}
