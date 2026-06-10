import React, { useEffect, useState } from 'react'
import * as api from '../lib/api'

export default function AssumptionList({runId}:{runId:string}){
  const [items, setItems] = useState<any[]>([])
  const [selected, setSelected] = useState<any|null>(null)

  useEffect(()=>{
    api.fetchAssumptions(runId).then((d:any)=> setItems(d || [])).catch(()=>{})
  }, [runId])

  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="col-span-1">
        <ul className="space-y-2">
          {items.map(a=> (
            <li key={a.id} className="bg-black/20 p-3 rounded cursor-pointer" onClick={()=>setSelected(a)}>
              <div className="font-medium">{a.summary || a.text?.slice(0,60)}</div>
              <div className="text-xs text-gray-400">category: {a.category || 'uncategorized'}</div>
            </li>
          ))}
        </ul>
      </div>
      <div className="col-span-2 bg-surface border border-gray-800 rounded p-4">
        {selected ? (
          <div>
            <h4 className="font-semibold">Assumption</h4>
            <div className="mt-2 text-sm text-gray-200">{selected.text}</div>
            <div className="mt-3 text-sm text-gray-400">Parent: {selected.parent_id || 'none'}</div>
            <div className="mt-3 text-sm text-gray-400">Metadata: {JSON.stringify(selected.meta || {})}</div>
          </div>
        ) : (
          <div className="text-gray-500">Select an assumption to view details</div>
        )}
      </div>
    </div>
  )
}
