import React, { useEffect, useState } from 'react'
import * as api from '../lib/api'

export default function ReconstructionComparison({runId}:{runId:string}){
  const [items, setItems] = useState<any[]>([])

  useEffect(()=>{
    api.fetchReconstructions(runId).then((d:any)=> setItems(d || [])).catch(()=>{})
  }, [runId])

  return (
    <div>
      {items.length===0 ? <div className="text-gray-500">No reconstructions yet</div> : (
        <div className="space-y-4">
          {items.map(r=> (
            <div key={r.id} className="bg-black/20 p-3 rounded">
              <div className="font-medium">{r.title || 'Reconstruction'}</div>
              <div className="mt-2 text-sm text-gray-200">{r.reconstructed_text || r.text}</div>
              <div className="mt-2 text-xs text-gray-400">rationale: {r.rationale || '—'}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
