import React, { useEffect, useState } from 'react'
import * as api from '../lib/api'

export default function EdgeCaseList({runId}:{runId:string}){
  const [items, setItems] = useState<any[]>([])

  useEffect(()=>{
    api.fetchSimulations(runId).then((d:any)=> setItems(d || [])).catch(()=>{})
  }, [runId])

  return (
    <div>
      <ul className="space-y-3">
        {items.map(s=> (
          <li key={s.id} className="bg-black/20 p-3 rounded">
            <div className="font-medium">{s.title || s.scenario?.slice(0,80)}</div>
            <div className="text-xs text-gray-400">impact: {s.impact_score || s.impact || 'n/a'}</div>
            <div className="mt-2 text-sm text-gray-200">{s.scenario}</div>
          </li>
        ))}
      </ul>
    </div>
  )
}
