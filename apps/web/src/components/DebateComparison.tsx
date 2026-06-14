import React, { useMemo, useState } from 'react'
import * as api from '../lib/api'

const PERSONAS = [
  { key: 'red_team', label: 'Red Team', description: 'Find brittle logic and failure modes.' },
  { key: 'operator', label: 'Operator', description: 'Focus on deployability and observability.' },
  { key: 'customer', label: 'Customer Advocate', description: 'Challenge product fit and adoption risk.' },
  { key: 'adversary', label: 'Adversary', description: 'Surface abuse cases and malicious edge cases.' },
]

export default function DebateComparison({ run }: { run: any }) {
  const [selected, setSelected] = useState<string[]>(['red_team', 'operator', 'customer'])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  const selectedLabels = useMemo(
    () => PERSONAS.filter((persona) => selected.includes(persona.key)).map((persona) => persona.label),
    [selected],
  )

  function togglePersona(key: string) {
    setSelected((current) =>
      current.includes(key) ? current.filter((item) => item !== key) : [...current, key],
    )
  }

  async function launchDebate() {
    if (!run?.project_id && !run?.projectId) {
      setError('Missing project id for this run')
      return
    }
    if (!selected.length) {
      setError('Select at least one agent')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const response = await api.runDebate({
        input_text: run?.input_text || run?.project?.input_text || run?.title || '',
        run_id: run?.id,
        project_id: run?.project_id || run?.projectId,
        persona_keys: selected,
        max_agents: selected.length,
        timeout_seconds: 12,
        dry_run: false,
      })
      setResult(response)
    } catch (err: any) {
      setError(err?.message || 'debate failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-gray-800 bg-surface/80 p-4 shadow-lg shadow-black/30">
        <div className="mb-4">
          <h3 className="text-base font-semibold text-white">Agent toggles</h3>
          <p className="text-sm text-gray-400">Turn agents on or off per run, then compare the perspectives side by side.</p>
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {PERSONAS.map((persona) => {
            const active = selected.includes(persona.key)
            return (
              <button
                key={persona.key}
                type="button"
                onClick={() => togglePersona(persona.key)}
                className={`rounded-xl border p-3 text-left transition ${active ? 'border-primary bg-primary/10' : 'border-gray-800 bg-black/20 hover:bg-black/30'}`}
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-white">{persona.label}</div>
                    <div className="mt-1 text-xs text-gray-400">{persona.description}</div>
                  </div>
                  <div className={`h-3 w-3 rounded-full ${active ? 'bg-primary' : 'bg-gray-600'}`} />
                </div>
              </button>
            )
          })}
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={launchDebate}
            disabled={loading || selected.length === 0}
            className="rounded-lg border border-primary bg-primary/10 px-4 py-2 text-sm font-semibold text-primary hover:bg-primary/20 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading ? 'Running debate...' : 'Run debate'}
          </button>
          <div className="text-sm text-gray-400">
            Active: {selectedLabels.length ? selectedLabels.join(', ') : 'none'}
          </div>
        </div>
        {error ? <div className="mt-3 rounded-lg border border-red-800 bg-red-950/30 px-3 py-2 text-sm text-red-200">{error}</div> : null}
      </section>

      {result ? (
        <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          <section className="rounded-2xl border border-gray-800 bg-surface/80 p-4 shadow-lg shadow-black/30">
            <h3 className="text-base font-semibold text-white">Agent perspectives</h3>
            <div className="mt-4 space-y-3">
              {result.agents?.map((agent: any) => (
                <article key={agent.key} className="rounded-xl border border-gray-800 bg-black/20 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold text-white">{agent.name}</div>
                      <div className="text-xs text-gray-400">{agent.focus}</div>
                    </div>
                    <div className={`rounded-full px-2 py-1 text-xs ${agent.status === 'completed' ? 'bg-green-900/30 text-green-200' : 'bg-yellow-900/30 text-yellow-200'}`}>
                      {agent.status}
                    </div>
                  </div>
                  <div className="mt-3 space-y-2">
                    {agent.critiques?.length ? agent.critiques.map((critique: any, index: number) => (
                      <div key={`${agent.key}-${index}`} className="rounded-lg border border-gray-700 bg-black/30 p-3">
                        <div className="flex items-center justify-between gap-3">
                          <div className="text-sm text-gray-100">{critique.critique_text}</div>
                          <div className="rounded-full bg-red-900/30 px-2 py-0.5 text-xs text-red-200">{critique.severity}</div>
                        </div>
                        <div className="mt-2 text-xs text-gray-500">Attribution: {agent.name}</div>
                      </div>
                    )) : <div className="text-sm text-gray-500">No critiques returned by this agent.</div>}
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-gray-800 bg-surface/80 p-4 shadow-lg shadow-black/30">
            <h3 className="text-base font-semibold text-white">Merged critique stream</h3>
            <p className="mt-1 text-sm text-gray-400">Deduplicated across agents, with source roles preserved for traceability.</p>
            <div className="mt-4 space-y-3">
              {result.merged?.length ? result.merged.map((critique: any, index: number) => (
                <article key={`${critique.critique_text}-${index}`} className="rounded-xl border border-gray-800 bg-black/20 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold text-white">{critique.critique_text}</div>
                      <div className="mt-1 text-xs text-gray-400">Roles: {(critique.source_roles || critique.sources || []).join(', ')}</div>
                      <div className="mt-1 text-xs text-gray-500">Assumption: {critique.assumption_id || 'n/a'}</div>
                    </div>
                    <div className="rounded-full bg-red-900/30 px-2 py-1 text-xs text-red-200">{critique.severity}</div>
                  </div>
                </article>
              )) : <div className="text-sm text-gray-500">No merged critiques yet.</div>}
            </div>
          </section>
        </div>
      ) : (
        <section className="rounded-2xl border border-dashed border-gray-700 bg-black/20 p-6 text-sm text-gray-400">
          Run a debate to compare agent perspectives and inspect deduplicated critiques.
        </section>
      )}
    </div>
  )
}
