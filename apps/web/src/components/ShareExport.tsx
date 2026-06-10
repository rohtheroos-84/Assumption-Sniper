import React from 'react'

export default function ShareExport({run}:{run:any}){
  function exportJson(){
    const data = JSON.stringify(run, null, 2)
    const blob = new Blob([data], {type: 'application/json'})
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `run-${run?.id || 'export'}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="mt-4">
      <button onClick={exportJson} className="bg-primary text-black px-3 py-1 rounded">Export run JSON</button>
    </div>
  )
}
