import React, { useEffect } from 'react'
import useSWR from 'swr'
import { useRun } from '../context/RunContext'

export default function RunProgress(){
  const { currentRun, subscribeToRunEvents } = useRun()

  useEffect(()=>{
    if(!currentRun) return
    const stop = subscribeToRunEvents(currentRun.id)
    return () => stop()
  }, [currentRun])

  if(!currentRun) return <div className="text-sm text-gray-400">No active run</div>

  return (
    <div className="bg-surface border border-gray-800 rounded p-4">
      <div className="flex items-center justify-between">
        <div className="font-medium">Run: {currentRun.id}</div>
        <div className="text-sm text-gray-400">status: {currentRun.status}</div>
      </div>
      <div className="mt-3">
        {currentRun.events && currentRun.events.length>0 ? (
          <ul className="text-sm text-gray-300 space-y-2">
            {currentRun.events.map((ev:any, idx:number)=> (
              <li key={idx} className="border-l-2 border-gray-700 pl-3">{ev.message}</li>
            ))}
          </ul>
        ) : (
          <div className="text-sm text-gray-500">Waiting for events...</div>
        )}
      </div>
    </div>
  )
}
