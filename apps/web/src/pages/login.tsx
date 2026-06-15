import { useState } from 'react'
import { useRouter } from 'next/router'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const router = useRouter()

  async function handleSubmit(e: any) {
    e.preventDefault()
    setErr('')
    try {
      const res = await fetch((process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000') + '/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      if (!res.ok) {
        const payload = await res.json().catch(() => ({}))
        setErr(payload.detail || 'login failed')
        return
      }
      const data = await res.json()
      localStorage.setItem('as_token', data.access_token)
      router.push('/')
    } catch (e) {
      setErr('network error')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <form onSubmit={handleSubmit} className="w-full max-w-md p-6 bg-white/5 rounded">
        <h2 className="text-xl mb-4">Sign in</h2>
        {err && <div className="text-red-400 mb-2">{err}</div>}
        <label className="block mb-2">Email
          <input className="w-full mt-1 p-2 rounded bg-white/5" value={email} onChange={e=>setEmail(e.target.value)} />
        </label>
        <label className="block mb-4">Password
          <input type="password" className="w-full mt-1 p-2 rounded bg-white/5" value={password} onChange={e=>setPassword(e.target.value)} />
        </label>
        <button className="px-4 py-2 bg-green-600 rounded" type="submit">Sign in</button>
      </form>
    </div>
  )
}
