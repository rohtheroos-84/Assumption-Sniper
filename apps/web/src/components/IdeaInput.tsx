import React, { useState } from 'react'
import { useRun } from '../context/RunContext'

export default function IdeaInput(){
  const [text, setText] = useState('')
  const { createRun } = useRun()
  const [loading, setLoading] = useState(false)

  async function submit(e: React.FormEvent){
    e.preventDefault()
    if(!text.trim()) return
    setLoading(true)
    try{
      await createRun(text.trim())
      setText('')
    }catch(err){
      console.error(err)
      alert('Failed to create run')
    }finally{ setLoading(false) }
  }

  return (
    <form onSubmit={submit} className="space-y-3">
      <label className="block text-sm text-gray-300">Idea / hypothesis</label>
      <textarea
        value={text}
        onChange={e=>setText(e.target.value)}
        rows={4}
        placeholder="e.g. On-demand hot food delivery to college dorms using gig drivers"
        className="w-full bg-black/30 border border-gray-800 rounded p-3 text-sm focus:border-primary focus:outline-none"
      />
      <p className="text-xs text-gray-500">Tip: include who pays, how you acquire users, and what must be true for unit economics to work.</p>
      <div>
        <button className="bg-primary text-black font-semibold px-4 py-2 rounded" disabled={loading}>{loading? 'Starting...': 'Start run'}</button>
      </div>
    </form>
  )
}
