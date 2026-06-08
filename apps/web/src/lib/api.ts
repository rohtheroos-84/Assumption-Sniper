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
