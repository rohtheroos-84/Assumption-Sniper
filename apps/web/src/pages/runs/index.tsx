import Layout from '../../components/Layout'
import { useEffect, useState } from 'react'
import * as api from '../../lib/api'
import Link from 'next/link'

export default function RunsList(){
  const [runs, setRuns] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(()=>{
    api.fetchRuns().then(data=>{ setRuns(data || []) }).catch(()=>{}).finally(()=>setLoading(false))
  }, [])

  return (
    <Layout>
      <div className="h-container py-12">
        <h2 className="text-2xl font-semibold mb-4">Run history</h2>
        {loading ? (<div className="text-gray-400">Loading…</div>) : (
          <ul className="space-y-3">
            {runs.length===0 && <li className="text-gray-500">No runs yet</li>}
            {runs.map(r=> (
              <li key={r.id} className="bg-surface border border-gray-800 rounded p-3 flex items-center justify-between">
                <div>
                  <div className="font-medium">{r.title || r.id}</div>
                  <div className="text-sm text-gray-400">{r.created_at}</div>
                </div>
                <div>
                  <Link href={`/runs/${r.id}`} className="text-primary">View</Link>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Layout>
  )
}
