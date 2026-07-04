import Layout from '../components/Layout'
import Link from 'next/link'

const FEATURES = [
  { title: 'Stress-test ideas fast', body: 'Decompose assumptions, run critiques, and simulate failure modes in minutes—not weeks.' },
  { title: 'Structured, not chatty', body: 'Every run produces scored assumptions, critiques, and a rebuilt idea—not an endless thread.' },
  { title: 'Built for founders & PMs', body: 'Private beta for early-stage teams validating product bets before they ship.' },
]

export default function LandingPage() {
  return (
    <Layout>
      <section className="h-container py-16 md:py-24">
        <p className="text-primary text-sm font-semibold tracking-wide uppercase mb-4">Assumption Sniper</p>
        <h1 className="text-4xl md:text-5xl font-bold leading-tight max-w-3xl">
          Find the hidden assumptions that will kill your idea—before you build.
        </h1>
        <p className="mt-6 text-lg text-gray-300 max-w-2xl">
          Upload a startup hypothesis. Get structured critiques, simulations, and a risk-scored rebuild. Not a chatbot—a critique engine.
        </p>
        <div className="mt-10 flex flex-wrap gap-4">
          <Link href="/demo" className="bg-primary text-black font-semibold px-6 py-3 rounded">
            Try the demo
          </Link>
          <Link href="/app" className="border border-gray-600 text-white px-6 py-3 rounded hover:border-primary">
            Open app
          </Link>
          <Link href="/beta" className="text-gray-300 underline underline-offset-4 hover:text-white">
            Request beta access
          </Link>
        </div>
      </section>

      <section className="h-container pb-20 grid md:grid-cols-3 gap-8">
        {FEATURES.map((f) => (
          <div key={f.title} className="border border-gray-800 rounded-lg p-6 bg-surface">
            <h2 className="font-semibold text-lg mb-2">{f.title}</h2>
            <p className="text-sm text-gray-400">{f.body}</p>
          </div>
        ))}
      </section>
    </Layout>
  )
}
