import React, { useEffect, useState } from 'react'
import * as api from '../lib/api'

export default function CritiqueList({runId}:{runId:string}){
  const [items, setItems] = useState<any[]>([])
  const [severity, setSeverity] = useState<string>('all')

  useEffect(()=>{
    api.fetchCritiques(runId).then((d:any)=> setItems(d || [])).catch(()=>{})
  }, [runId])

  const filtered = items.filter(i=> severity==='all' ? true : (i.severity===severity))

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <div className="text-sm text-gray-300">Critiques</div>
        <select value={severity} onChange={e=>setSeverity(e.target.value)} className="bg-black/20 text-sm p-1 rounded">
          <option value="all">All severities</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
      </div>
      <ul className="space-y-2">
        {filtered.map(c=> (
          <li key={c.id} className="bg-black/20 p-3 rounded">
            <div className="font-medium">{c.summary || c.text?.slice(0,80)}</div>
            <div className="text-xs text-gray-400">severity: {c.severity || 'unknown'}</div>
          </li>
        ))}
      </ul>
    </div>
  )
}
