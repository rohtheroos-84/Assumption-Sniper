import React, { createContext, useContext, useState } from 'react'
import * as api from '../lib/api'

const RunContext = createContext<any>(null)

export const RunProvider: React.FC<{children: React.ReactNode}> = ({children})=>{
  const [currentRun, setCurrentRun] = useState<any>(null)

  async function createRun(title: string){
    const run = await api.createProjectAndRun(title)
    setCurrentRun({...run, events: []})
    // auto-start the run
    await api.startRun(run.id)
  }

  function subscribeToRunEvents(run_id: string){
    const stop = api.subscribeRunEvents(run_id, (ev)=>{
      // append to current run events
      setCurrentRun((prev:any)=>{
        if(!prev || prev.id !== run_id) return prev
        const next = {...prev, events: [...(prev.events||[]), ev]}
        if(ev.type === 'run_status') next.status = ev.status
        return next
      })
    })
    return stop
  }

  return (
    <RunContext.Provider value={{ currentRun, createRun, subscribeToRunEvents }}>
      {children}
    </RunContext.Provider>
  )
}

export function useRun(){
  return useContext(RunContext)
}
