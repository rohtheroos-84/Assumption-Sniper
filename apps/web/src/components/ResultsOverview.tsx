import React from 'react'

export default function ResultsOverview({run}:{run:any}){
  return (
    <div className="bg-surface border border-gray-800 rounded p-4">
      <h3 className="font-semibold mb-2">Overview</h3>
      <div className="text-sm text-gray-300">Title: {run?.title || '—'}</div>
      <div className="mt-3">
        <div className="text-sm text-gray-400">Decomposition</div>
        <pre className="text-xs bg-black/20 p-3 rounded mt-2 whitespace-pre-wrap">{JSON.stringify(run?.decomposition, null, 2) || 'No decomposition yet'}</pre>
      </div>
    </div>
  )
}
