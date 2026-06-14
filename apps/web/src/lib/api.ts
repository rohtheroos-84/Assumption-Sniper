const BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export async function createProjectAndRun(title: string){
  // Minimal: POST /api/v1/projects -> create project, POST /api/v1/runs -> create run
  const res = await fetch(`${BASE}/api/v1/runs`, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({title})
  })
  if(!res.ok) throw new Error('create run failed')
  return res.json()
}

export async function startRun(run_id: string){
  const res = await fetch(`${BASE}/api/v1/runs/${run_id}/start`, { method: 'POST' })
  if(!res.ok) throw new Error('start run failed')
  return res.json()
}

export function subscribeRunEvents(run_id: string, onEvent: (ev:any)=>void){
  const url = `${BASE}/api/v1/runs/${run_id}/events`
  const es = new EventSource(url)
  es.onmessage = (e)=>{
    try{ const data = JSON.parse(e.data); onEvent(data) }catch(err){ console.warn('non-json event', e.data) }
  }
  es.onerror = (err)=>{ console.warn('es error', err); es.close() }
  return () => es.close()
}

export async function fetchRun(run_id:string){
  const res = await fetch(`${BASE}/api/v1/runs/${run_id}`)
  if(!res.ok) throw new Error('fetch run failed')
  return res.json()
}

export async function fetchRuns(){
  const res = await fetch(`${BASE}/api/v1/runs`)
  if(!res.ok) throw new Error('fetch runs failed')
  return res.json()
}

export async function fetchAssumptions(run_id:string){
  const res = await fetch(`${BASE}/api/v1/runs/${run_id}/assumptions`)
  if(!res.ok) throw new Error('fetch assumptions failed')
  return res.json()
}

export async function fetchCritiques(run_id:string){
  const res = await fetch(`${BASE}/api/v1/runs/${run_id}/critiques`)
  if(!res.ok) throw new Error('fetch critiques failed')
  return res.json()
}

export async function fetchSimulations(run_id:string){
  const res = await fetch(`${BASE}/api/v1/runs/${run_id}/simulations`)
  if(!res.ok) throw new Error('fetch simulations failed')
  return res.json()
}

export async function fetchReconstructions(run_id:string){
  const res = await fetch(`${BASE}/api/v1/runs/${run_id}/reconstructions`)
  if(!res.ok) throw new Error('fetch reconstructions failed')
  return res.json()
}

export async function fetchScores(run_id:string){
  const res = await fetch(`${BASE}/api/v1/runs/${run_id}/scores`)
  if(!res.ok) throw new Error('fetch scores failed')
  return res.json()
}

export async function runDebate(input: { input_text: string; run_id?: string; project_id?: string; persona_keys?: string[]; max_agents?: number; timeout_seconds?: number; dry_run?: boolean }){
  const res = await fetch(`${BASE}/api/v1/ai/debate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if(!res.ok) throw new Error('run debate failed')
  return res.json()
}
