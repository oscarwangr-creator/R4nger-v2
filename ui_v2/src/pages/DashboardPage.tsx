import { GraphView } from '../components/GraphView'
import { PipelineRunner } from '../components/PipelineRunner'
import { RiskChart } from '../components/RiskChart'
import { useRealtime } from '../hooks/useRealtime'

export function DashboardPage() {
  const wsStatus = useRealtime('ws://localhost:8000/ws/realtime')

  return (
    <main className="min-h-screen bg-slate-950 p-6 text-slate-100">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-cyan-300">Intelligence OS</h1>
          <p className="text-slate-400">Kibana-style analytics, graph intelligence, and autonomous workflows</p>
        </div>
        <div className="rounded border border-slate-700 px-3 py-2">WebSocket: {wsStatus}</div>
      </header>

      <section className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-slate-700 p-4">
          <h2 className="mb-3 text-xl font-semibold text-cyan-300">Entity Graph Explorer</h2>
          <GraphView />
        </div>
        <div className="rounded-xl border border-slate-700 p-4">
          <h2 className="mb-3 text-xl font-semibold text-cyan-300">Risk Dashboard</h2>
          <RiskChart />
        </div>
      </section>

      <section className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <PipelineRunner />
        <div className="rounded-xl border border-slate-700 p-4">
          <h3 className="text-lg font-semibold text-cyan-300">Workflow Builder</h3>
          <p className="text-slate-400">Create trigger-based workflows by selecting YAML pipelines and conditional paths.</p>
          <ul className="mt-2 list-disc pl-6 text-sm text-slate-300">
            <li>Trigger-based execution</li>
            <li>Conditional branching</li>
            <li>Real-time event updates</li>
          </ul>
        </div>
      </section>
    </main>
  )
}
