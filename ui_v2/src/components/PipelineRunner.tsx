import { useState } from 'react'
import axios from 'axios'

export function PipelineRunner() {
  const [pipeline, setPipeline] = useState('identity_pipeline')
  const [value, setValue] = useState('alice@example.com')
  const [output, setOutput] = useState('')

  const run = async () => {
    const res = await axios.post('/api/pipeline/run', {
      pipeline,
      payload: { input_type: 'email', value },
    })
    setOutput(JSON.stringify(res.data, null, 2))
  }

  return (
    <div className="space-y-3 rounded-xl border border-slate-700 p-4">
      <h3 className="text-lg font-semibold text-cyan-300">Pipeline Execution</h3>
      <input className="w-full rounded bg-slate-800 p-2" value={pipeline} onChange={(e) => setPipeline(e.target.value)} />
      <input className="w-full rounded bg-slate-800 p-2" value={value} onChange={(e) => setValue(e.target.value)} />
      <button className="rounded bg-cyan-600 px-3 py-2" onClick={run}>Run</button>
      <pre className="max-h-64 overflow-auto rounded bg-black/40 p-2 text-xs">{output}</pre>
    </div>
  )
}
