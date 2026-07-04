import { useState } from 'react'
import Layout from '../components/Layout'
import { trackEvent } from '../lib/analytics'

const BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

export default function BetaPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [inviteCode, setInviteCode] = useState('')
  const [token, setToken] = useState<string | null>(null)
  const [error, setError] = useState('')

  async function register(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    trackEvent('beta_register_attempt')
    const res = await fetch(`${BASE}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, invite_code: inviteCode || undefined }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      setError(body.detail || 'Registration failed')
      return
    }
    const data = await res.json()
    localStorage.setItem('as_token', data.access_token)
    setToken(data.access_token)
    trackEvent('beta_register_success')
  }

  return (
    <Layout>
      <div className="h-container py-12 max-w-md">
        <h1 className="text-2xl font-bold mb-2">Private beta</h1>
        <p className="text-gray-400 text-sm mb-6">
          For founders and PMs. Use invite code <code className="text-primary">founder-beta</code> or <code className="text-primary">pm-beta</code> when beta mode is enabled.
        </p>
        {token ? (
          <div className="border border-primary/40 rounded p-4">
            <p className="text-primary font-semibold">You&apos;re in.</p>
            <a href="/app" className="underline text-sm mt-2 inline-block">Go to app →</a>
          </div>
        ) : (
          <form onSubmit={register} className="space-y-4">
            <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} className="w-full bg-black/30 border border-gray-800 rounded p-3 text-sm" required />
            <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full bg-black/30 border border-gray-800 rounded p-3 text-sm" required />
            <input type="text" placeholder="Invite code" value={inviteCode} onChange={(e) => setInviteCode(e.target.value)} className="w-full bg-black/30 border border-gray-800 rounded p-3 text-sm" />
            {error && <p className="text-red-400 text-sm">{error}</p>}
            <button type="submit" className="bg-primary text-black font-semibold px-4 py-2 rounded w-full">Create account</button>
          </form>
        )}
      </div>
    </Layout>
  )
}
