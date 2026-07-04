import { useState } from 'react'
import { trackEvent } from '../lib/analytics'

const BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export default function FeedbackWidget() {
  const [open, setOpen] = useState(false)
  const [message, setMessage] = useState('')
  const [rating, setRating] = useState(0)
  const [sent, setSent] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    trackEvent('feedback_submit', { rating })
    const session_id = typeof window !== 'undefined' ? localStorage.getItem('as_session_id') : null
    await fetch(`${BASE}/api/v1/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        rating: rating || undefined,
        category: 'ux',
        page: typeof window !== 'undefined' ? window.location.pathname : undefined,
        session_id,
      }),
    })
    setSent(true)
    setMessage('')
    setRating(0)
  }

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {open && (
        <form onSubmit={submit} className="mb-3 w-72 border border-gray-700 bg-surface rounded-lg p-4 shadow-xl">
          <p className="text-sm font-semibold mb-2">Send feedback</p>
          {sent ? (
            <p className="text-sm text-primary">Thanks—we&apos;ll prioritize fixes monthly.</p>
          ) : (
            <>
              <textarea value={message} onChange={(e) => setMessage(e.target.value)} rows={3} className="w-full text-sm bg-black/40 border border-gray-800 rounded p-2 mb-2" placeholder="What should we improve?" required />
              <div className="flex gap-1 mb-2">
                {[1, 2, 3, 4, 5].map((n) => (
                  <button key={n} type="button" onClick={() => setRating(n)} className={`text-sm px-2 py-1 rounded ${rating >= n ? 'bg-primary text-black' : 'bg-gray-800'}`}>{n}</button>
                ))}
              </div>
              <button type="submit" className="w-full bg-primary text-black text-sm font-semibold py-2 rounded">Submit</button>
            </>
          )}
        </form>
      )}
      <button type="button" onClick={() => { setOpen(!open); trackEvent('feedback_widget_toggle') }} className="bg-primary text-black font-semibold px-4 py-2 rounded-full shadow-lg">
        Feedback
      </button>
    </div>
  )
}
