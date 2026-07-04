const BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export async function fetchDemoSample() {
  const res = await fetch(`${BASE}/api/v1/demo/sample`)
  if (!res.ok) throw new Error('demo sample failed')
  return res.json()
}

export async function fetchDemoPreview(input_text?: string) {
  const res = await fetch(`${BASE}/api/v1/demo/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ input_text }),
  })
  if (!res.ok) throw new Error('demo preview failed')
  return res.json()
}

export async function fetchBetaStatus() {
  const res = await fetch(`${BASE}/api/v1/beta/status`)
  if (!res.ok) throw new Error('beta status failed')
  return res.json()
}
