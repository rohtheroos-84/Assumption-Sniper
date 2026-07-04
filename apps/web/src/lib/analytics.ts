const BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'
const SESSION_KEY = 'as_session_id'

function sessionId(): string {
  if (typeof window === 'undefined') return 'server'
  let id = localStorage.getItem(SESSION_KEY)
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem(SESSION_KEY, id)
  }
  return id
}

const queue: Array<Record<string, unknown>> = []

export function trackEvent(event_name: string, payload: Record<string, unknown> = {}) {
  if (typeof window === 'undefined') return
  queue.push({
    session_id: sessionId(),
    event_name,
    page: window.location.pathname,
    payload,
  })
  if (queue.length >= 5) flushEvents()
}

export async function flushEvents() {
  if (!queue.length || typeof window === 'undefined') return
  const events = queue.splice(0, queue.length)
  try {
    await fetch(`${BASE}/api/v1/analytics/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ events }),
    })
  } catch {
    queue.unshift(...events)
  }
}

if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    void flushEvents()
  })
}
