import { useEffect, useState } from 'react'
import Layout from '../components/Layout'
import Link from 'next/link'
import { fetchDemoPreview, fetchDemoSample } from '../lib/demo'
import { trackEvent } from '../lib/analytics'

export default function DemoPage() {
  const [sample, setSample] = useState<any>(null)
  const [preview, setPreview] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    trackEvent('demo_page_view')
    fetchDemoSample().then(setSample).catch(console.error)
  }, [])

  async function runPreview() {
    setLoading(true)
    trackEvent('demo_preview_click')
    try {
      const result = await fetchDemoPreview(sample?.input_text)
      setPreview(result)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout>
      <div className="h-container py-12 max-w-3xl">
        <h1 className="text-3xl font-bold mb-2">Interactive demo</h1>
        <p className="text-gray-400 mb-8">See how Assumption Sniper stress-tests an idea—no account required.</p>

        {sample && (
          <div className="border border-gray-800 rounded-lg p-6 bg-surface mb-6">
            <p className="text-sm text-primary mb-2">Sample idea</p>
            <p className="text-lg">{sample.input_text}</p>
            <button
              type="button"
              onClick={runPreview}
              disabled={loading}
              className="mt-4 bg-primary text-black font-semibold px-4 py-2 rounded disabled:opacity-50"
            >
              {loading ? 'Running preview…' : 'Run demo preview'}
            </button>
          </div>
        )}

        {preview?.preview && (
          <div className="space-y-6">
            <section>
              <h2 className="font-semibold mb-2">Assumptions</h2>
              <ul className="space-y-2 text-sm text-gray-300">
                {preview.preview.assumptions.map((a: any) => (
                  <li key={a.assumption_text} className="border-l-2 border-primary pl-3">{a.assumption_text}</li>
                ))}
              </ul>
            </section>
            <section>
              <h2 className="font-semibold mb-2">Top critiques</h2>
              <ul className="space-y-2 text-sm">
                {preview.preview.critiques.map((c: any) => (
                  <li key={c.critique_text} className="bg-black/30 p-3 rounded">
                    <span className="text-primary mr-2">[{c.severity}]</span>{c.critique_text}
                  </li>
                ))}
              </ul>
            </section>
            <p className="text-sm text-gray-400">Aggregate risk score: <strong className="text-white">{preview.preview.risk_score}</strong></p>
          </div>
        )}

        <div className="mt-10">
          <Link href="/beta" className="text-primary underline">Get beta access for full pipeline runs →</Link>
        </div>
      </div>
    </Layout>
  )
}
