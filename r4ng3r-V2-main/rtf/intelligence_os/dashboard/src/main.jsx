import React, { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './styles.css'

const API_BASE = import.meta.env.VITE_INTELLIGENCE_API_BASE || 'http://127.0.0.1:8080/intelligence-os'

function StatCard({ label, value, helper }) {
  return (
    <article className="card stat-card">
      <span className="eyebrow">{label}</span>
      <strong>{value}</strong>
      {helper ? <small>{helper}</small> : null}
    </article>
  )
}

function App() {
  const [health, setHealth] = useState(null)
  const [validation, setValidation] = useState(null)
  const [workflows, setWorkflows] = useState([])
  const [templates, setTemplates] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/health`).then((r) => r.json()),
      fetch(`${API_BASE}/validation`).then((r) => r.json()),
      fetch(`${API_BASE}/workflows`).then((r) => r.json()),
      fetch(`${API_BASE}/investigations/templates`).then((r) => r.json()),
    ])
      .then(([healthResp, validationResp, workflowResp, templateResp]) => {
        setHealth(healthResp)
        setValidation(validationResp)
        setWorkflows(workflowResp.workflows || [])
        setTemplates(templateResp)
      })
      .catch((err) => setError(err.message))
  }, [])

  const validationIssues = useMemo(() => validation?.issues?.slice(0, 6) || [], [validation])

  return (
    <div className="app-shell">
      <header className="hero card">
        <div>
          <span className="eyebrow">Intelligence OS</span>
          <h1>Analyst Control Plane</h1>
          <p>
            Run modular intelligence pipelines, validate orchestration integrity, inspect workflow families,
            and drive graph-ready investigations from a single dashboard.
          </p>
        </div>
        <div className="hero-actions">
          <button>Launch Pipeline</button>
          <button className="secondary">Open Workflow</button>
        </div>
      </header>

      {error ? <section className="banner error">API unavailable: {error}</section> : null}

      <section className="stats-grid">
        <StatCard label="Pipelines" value={health?.pipelines ?? '—'} helper="Canonical YAML definitions" />
        <StatCard label="Tools" value={health?.tools ?? '—'} helper="Registry-backed integrations" />
        <StatCard label="Module Packs" value={health?.module_packs ?? '—'} helper="Generated wrapper packs" />
        <StatCard label="Validation" value={validation?.status ?? '—'} helper="Framework integrity status" />
      </section>

      <section className="content-grid">
        <article className="card panel">
          <h2>Workflow Families</h2>
          <div className="chip-row">
            {(templates?.workflow_families || []).map((family) => (
              <span key={family} className="chip">{family}</span>
            ))}
          </div>
          <ul className="workflow-list">
            {workflows.slice(0, 8).map((workflow) => (
              <li key={workflow.name}>
                <div>
                  <strong>{workflow.name}</strong>
                  <p>{workflow.description}</p>
                </div>
                <span>{workflow.pipelines.length} pipelines</span>
              </li>
            ))}
          </ul>
        </article>

        <article className="card panel">
          <h2>Validation Snapshot</h2>
          <p>Continuous checks confirm stage depth, manifest alignment, and generated module pack completeness.</p>
          <ul className="issue-list">
            {validationIssues.length ? validationIssues.map((issue, idx) => (
              <li key={`${issue.location}-${idx}`} className={issue.severity}>
                <strong>{issue.severity.toUpperCase()}</strong> {issue.message}
              </li>
            )) : <li className="ok"><strong>OK</strong> No validation issues detected.</li>}
          </ul>
        </article>

        <article className="card panel">
          <h2>Investigation Templates</h2>
          <p>Seed types and report outputs available to the orchestration layer.</p>
          <div className="template-grid">
            <div>
              <span className="eyebrow">Seed Types</span>
              <ul>{(templates?.seed_types || []).map((seed) => <li key={seed}>{seed}</li>)}</ul>
            </div>
            <div>
              <span className="eyebrow">Report Formats</span>
              <ul>{(templates?.report_formats || []).map((fmt) => <li key={fmt}>{fmt}</li>)}</ul>
            </div>
          </div>
        </article>
      </section>
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App />)
