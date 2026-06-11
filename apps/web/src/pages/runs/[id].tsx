import Layout from '../../components/Layout'
import { useRouter } from 'next/router'
import { useEffect, useState } from 'react'
import * as api from '../../lib/api'
import ResultsOverview from '../../components/ResultsOverview'
import AssumptionList from '../../components/AssumptionList'
import CritiqueList from '../../components/CritiqueList'
import EdgeCaseList from '../../components/EdgeCaseList'
import ReconstructionComparison from '../../components/ReconstructionComparison'
import ShareExport from '../../components/ShareExport'
import VisualizationDashboard from '../../components/VisualizationDashboard'

export default function RunDetail(){
  const router = useRouter()
  const { id } = router.query as { id?: string }
  const [run, setRun] = useState<any>(null)
  const [tab, setTab] = useState('results')

  useEffect(()=>{
    if(!id) return
    api.fetchRun(id).then(setRun).catch(()=>{})
  }, [id])

  return (
    <Layout>
      <div className="h-container py-12">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold">Run {id}</h2>
          <div className="text-sm text-gray-400">status: {run?.status || 'unknown'}</div>
        </div>
        <div className="mb-6">
          <nav className="flex space-x-3">
            <button onClick={()=>setTab('results')} className={`px-3 py-1 rounded ${tab==='results'? 'bg-primary text-black':'text-gray-300'}`}>Results</button>
            <button onClick={()=>setTab('assumptions')} className={`px-3 py-1 rounded ${tab==='assumptions'? 'bg-primary text-black':'text-gray-300'}`}>Assumptions</button>
            <button onClick={()=>setTab('critiques')} className={`px-3 py-1 rounded ${tab==='critiques'? 'bg-primary text-black':'text-gray-300'}`}>Critiques</button>
            <button onClick={()=>setTab('simulations')} className={`px-3 py-1 rounded ${tab==='simulations'? 'bg-primary text-black':'text-gray-300'}`}>Edge cases</button>
            <button onClick={()=>setTab('reconstructions')} className={`px-3 py-1 rounded ${tab==='reconstructions'? 'bg-primary text-black':'text-gray-300'}`}>Reconstructions</button>
            <button onClick={()=>setTab('visualizations')} className={`px-3 py-1 rounded ${tab==='visualizations'? 'bg-primary text-black':'text-gray-300'}`}>Visualizations</button>
          </nav>
        </div>

        <div>
          {tab==='results' && <>
            <ResultsOverview run={run} />
            <ShareExport run={run} />
          </>}
          {tab==='assumptions' && <AssumptionList runId={id as string} />}
          {tab==='critiques' && <CritiqueList runId={id as string} />}
          {tab==='simulations' && <EdgeCaseList runId={id as string} />}
          {tab==='reconstructions' && <ReconstructionComparison runId={id as string} />}
          {tab==='visualizations' && <VisualizationDashboard runId={id as string} />}
        </div>
      </div>
    </Layout>
  )
}
