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
      </div>

      {sectionCard(
        'Risk heatmap',
        'A compact matrix that combines critique severity, confidence, exposure, and risk score.',
        loading ? <div className="text-sm text-gray-400">Loading heatmap…</div> : <RiskHeatmapVisualization assumptions={assumptions} critiques={critiques} simulations={simulations} scores={scores} />,
      )}
    </div>
  )
}
