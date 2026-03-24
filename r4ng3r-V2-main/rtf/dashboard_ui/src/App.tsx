import { useEffect, useMemo, useState } from 'react';
import { GraphPanel } from './components/GraphPanel';

type MetricSummary = {
  modules: number;
  categories: number;
  findings_total: number;
  graph_nodes: number;
  graph_edges: number;
  scheduler_queue_depth: number;
  severity_counts?: Record<string, number>;
};

type DashboardSummary = {
  operation_id: string;
  operations: Array<{ id: string; name: string; summary: string; status: string; target?: string }>;
  metrics: MetricSummary;
  recent_jobs: Job[];
  recent_findings: Finding[];
  recent_events: EventItem[];
  module_categories: string[];
};

type ModuleOption = { name: string; required?: boolean; description?: string; default?: string | number | boolean | null };

type ModuleItem = {
  path: string;
  category: string;
  name: string;
  info?: { description?: string; author?: string; version?: string };
  options?: ModuleOption[];
};

type WorkflowStep = { name: string; module: string; required: boolean; retry_count: number };

type WorkflowItem = { name: string; description: string; steps: WorkflowStep[] };

type WorkflowRegistry = { workflows: Record<string, WorkflowItem>; module_registry: ModuleItem[] };

type GraphNode = { id: string; label?: string; value?: string; entity_type: string; source_module?: string; properties?: Record<string, unknown> };

type GraphEdge = { id: string; source_node_id: string; target_node_id: string; relationship: string };

type GraphData = { nodes: GraphNode[]; edges: GraphEdge[]; schema: { entity_types: string[]; relationship_types: string[] } };

type EventItem = { id: number; event_type: string; severity: string; source: string; message: string; job_id?: string; target?: string; created_at?: string };

type Job = { id: string; name: string; module_path: string; status: string; created_at?: string; completed_at?: string; result?: Record<string, unknown> };

type Finding = { id: number; title: string; target: string; severity: string; category: string; description?: string };

type ToolItem = { name: string; category: string; installed: boolean; description?: string; version?: string };

type ReportItem = { id?: string; title?: string; format?: string; path?: string; generated_at?: string };

type HealthData = {
  tool_summary: { installed: number; missing: number; total: number };
  worker_status: Record<string, unknown>;
  scheduler_jobs: Array<Record<string, unknown>>;
  api: { status: string; version: string };
  database: { path: string; status: string };
  system?: {
    cpu: { percent: number; load_avg: number[]; cores: number };
    memory: { percent: number; used: number; total: number };
    disk: { percent: number; used: number; total: number };
    services: Record<string, string>;
    tooling: Record<string, boolean>;
    hostname: string;
    platform: string;
  };
};

type VaultData = { findings: Finding[]; entities: GraphNode[]; artifacts: Array<Record<string, unknown>>; credentials: Array<Record<string, unknown>> };

type SectionProps = { title: string; subtitle?: string; action?: React.ReactNode; children: React.ReactNode };

const API = (import.meta.env.VITE_RTF_API as string | undefined) ?? 'http://127.0.0.1:8000';

const navItems = [
  ['dashboard', 'Dashboard'],
  ['investigation', 'Investigation Workspace'],
  ['pipelines', 'Pipeline Builder'],
  ['modules', 'Module Runner'],
  ['graph', 'Graph Explorer'],
  ['tools', 'Tool Manager'],
  ['automation', 'Automation Manager'],
  ['reports', 'Report Viewer'],
  ['monitor', 'System Monitor'],
] as const;

type NavKey = (typeof navItems)[number][0];

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, init);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Failed to load ${path}`);
  }
  return response.json() as Promise<T>;
}

function Section({ title, subtitle, action, children }: SectionProps) {



  return (
    <section className="panel section-panel">
      <div className="section-header">
        <div>
          <span className="eyebrow">Operations Interface</span>
          <h2>{title}</h2>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

function StatCard({ label, value, accent }: { label: string; value: string | number; accent: 'red' | 'blue' | 'green' | 'amber' }) {
  return (
    <div className={`stat-card accent-${accent}`}>
      <span className="eyebrow">{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatBytes(value?: number) {
  if (!value) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let size = value;
  let index = 0;
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024;
    index += 1;
  }
  return `${size.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

export default function App() {
  const [activeView, setActiveView] = useState<NavKey>('dashboard');
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [workflowData, setWorkflowData] = useState<WorkflowRegistry | null>(null);
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [health, setHealth] = useState<HealthData | null>(null);
  const [vault, setVault] = useState<VaultData | null>(null);
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [tools, setTools] = useState<ToolItem[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [graphQuery, setGraphQuery] = useState('');
  const [moduleFilter, setModuleFilter] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedModulePath, setSelectedModulePath] = useState('');
  const [selectedWorkflow, setSelectedWorkflow] = useState('');
  const [moduleTarget, setModuleTarget] = useState('example.com');
  const [pipelineSeed, setPipelineSeed] = useState('example.com');
  const [toolArgs, setToolArgs] = useState('--help');
  const [selectedTool, setSelectedTool] = useState('');
  const [terminalInput, setTerminalInput] = useState('help');
  const [terminalTranscript, setTerminalTranscript] = useState('');
  const [reportFormat, setReportFormat] = useState('html');
  const [investigationName, setInvestigationName] = useState('Global Asset Exposure Review');
  const [investigationSeed, setInvestigationSeed] = useState('example.com');
  const [automationTarget, setAutomationTarget] = useState('corp.example');
  const [flashMessage, setFlashMessage] = useState<string>('');

  const modules = useMemo(() => workflowData?.module_registry ?? [], [workflowData]);
  const workflows = useMemo(() => Object.values(workflowData?.workflows ?? {}), [workflowData]);

  useEffect(() => {
    void loadAll();
  }, []);

  useEffect(() => {
    const socket = new WebSocket(`${API.replace('http', 'ws')}/ws/events`);
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data) as { type: string; data?: EventItem; events?: EventItem[] };
      if (payload.type === 'snapshot' && payload.events) setEvents(payload.events);
      if (payload.type === 'event' && payload.data) setEvents((current) => [payload.data!, ...current].slice(0, 150));
    };
    return () => socket.close();
  }, []);

  useEffect(() => {
    if (!selectedModulePath && modules[0]) setSelectedModulePath(modules[0].path);
    if (!selectedWorkflow && workflows[0]) setSelectedWorkflow(workflows[0].name);
    if (!selectedTool && tools[0]) setSelectedTool(tools[0].name);
  }, [modules, workflows, tools, selectedModulePath, selectedWorkflow, selectedTool]);

  async function loadAll() {
    const [summaryData, workflowRegistry, graphData, healthData, vaultData, reportData, toolData, jobData, eventData] = await Promise.all([
      fetchJson<DashboardSummary>('/dashboard/summary'),
      fetchJson<WorkflowRegistry>('/dashboard/workflows'),
      fetchJson<GraphData>('/dashboard/graph'),
      fetchJson<HealthData>('/dashboard/health'),
      fetchJson<VaultData>('/dashboard/vault'),
      fetchJson<ReportItem[]>('/dashboard/reports'),
      fetchJson<ToolItem[]>('/tools'),
      fetchJson<{ items: Job[] }>('/jobs'),
      fetchJson<EventItem[]>('/dashboard/events'),
    ]);
    setSummary(summaryData);
    setWorkflowData(workflowRegistry);
    setGraph(graphData);
    setHealth(healthData);
    setVault(vaultData);
    setReports(reportData);
    setTools(toolData);
    setJobs(jobData.items);
    setEvents(eventData);
  }

  async function postAction(path: string, payload: unknown, success: string) {
    await fetchJson(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    setFlashMessage(success);
    await loadAll();
  }

  const filteredModules = useMemo(
    () =>
      modules.filter((module) => {
        const matchesCategory = selectedCategory === 'all' || module.category === selectedCategory;
        const matchesText = JSON.stringify(module).toLowerCase().includes(moduleFilter.toLowerCase());
        return matchesCategory && matchesText;
      }),
    [modules, moduleFilter, selectedCategory],
  );

  const selectedModule = modules.find((module) => module.path === selectedModulePath) ?? filteredModules[0];
  const selectedWorkflowItem = workflows.find((workflow) => workflow.name === selectedWorkflow) ?? workflows[0];
  const selectedToolItem = tools.find((tool) => tool.name === selectedTool) ?? tools[0];
  const graphNodes = useMemo(() => {
    if (!graph) return [];
    const q = graphQuery.trim().toLowerCase();
    if (!q) return graph.nodes;
    return graph.nodes.filter((node) => JSON.stringify(node).toLowerCase().includes(q));
  }, [graph, graphQuery]);
  const graphNodeIds = new Set(graphNodes.map((node) => node.id));
  const graphEdges = useMemo(
    () => (graph?.edges ?? []).filter((edge) => graphNodeIds.has(edge.source_node_id) || graphNodeIds.has(edge.target_node_id)),
    [graph?.edges, graphNodeIds],
  );
  const runningJobs = jobs.filter((job) => ['running', 'pending', 'scheduled'].includes(job.status));

  const investigationSection = (
    <Section
      title="Investigation Workspace"
      subtitle="Create a case, seed targets, run pipelines, pivot on entities, and preserve artifacts without leaving the dashboard."
      action={<button onClick={() => void postAction('/operations/start_investigation', { name: investigationName, operation_id: 'primary', summary: `Interactive workspace seeded with ${investigationSeed}`, seed: investigationSeed, tags: ['workspace', 'interactive'], targets: [{ value: investigationSeed, type: 'domain', tags: ['seed'] }] }, 'Investigation workspace created.')}>Start Investigation</button>}
    >
      <div className="form-grid">
        <label>
          Investigation Name
          <input value={investigationName} onChange={(event) => setInvestigationName(event.target.value)} />
        </label>
        <label>
          Seed Target
          <input value={investigationSeed} onChange={(event) => setInvestigationSeed(event.target.value)} />
        </label>
      </div>
      <div className="workspace-grid">
        <div className="panel-subtle">
          <h3>Target Board</h3>
          <div className="list-stack">
            {(vault?.entities ?? []).slice(0, 8).map((entity) => (
              <button key={entity.id} type="button" className="list-item interactive" onClick={() => { setSelectedNodeId(entity.id); setActiveView('graph'); }}>
                <div>
                  <strong>{entity.label || entity.value || entity.id}</strong>
                  <span>{entity.entity_type}</span>
                </div>
                <span className="pill pill-neutral">Pivot</span>
              </button>
            ))}
          </div>
        </div>
        <div className="panel-subtle">
          <h3>Findings & Artifacts</h3>
          <div className="list-stack scrollable">
            {(vault?.findings ?? []).slice(0, 8).map((finding) => (
              <div key={finding.id} className="list-item">
                <div>
                  <strong>{finding.title}</strong>
                  <span>{finding.target}</span>
                </div>
                <span className={`pill pill-${finding.severity}`}>{finding.severity}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Section>
  );

  const moduleRunnerSection = (
    <Section title="Module Runner" subtitle="Execute any registered module with async job dispatch, live queue visibility, JSON result retention, and graph ingestion.">
      <div className="toolbar">
        <select value={selectedCategory} onChange={(event) => setSelectedCategory(event.target.value)}>
          <option value="all">All Categories</option>
          {(summary?.module_categories ?? []).map((category) => (
            <option key={category} value={category}>{category}</option>
          ))}
        </select>
        <input placeholder="Search modules" value={moduleFilter} onChange={(event) => setModuleFilter(event.target.value)} />
      </div>
      <div className="workspace-grid">
        <div className="scrollable list-stack tall-pane">
          {filteredModules.map((module) => (
            <button key={module.path} type="button" className={`module-card ${selectedModule?.path === module.path ? 'selected' : ''}`} onClick={() => setSelectedModulePath(module.path)}>
              <div className="module-topline">
                <span className="pill pill-neutral">{module.category}</span>
                <span className="small-code">{module.path}</span>
              </div>
              <h3>{module.name}</h3>
              <p>{module.info?.description ?? 'Operational module exposed by the framework registry.'}</p>
            </button>
          ))}
        </div>
        <div className="panel-subtle">
          <h3>{selectedModule?.name ?? 'Select a module'}</h3>
          <p>{selectedModule?.info?.description ?? 'Choose a module from the registry to execute it interactively.'}</p>
          <label>
            Target / Seed
            <input value={moduleTarget} onChange={(event) => setModuleTarget(event.target.value)} />
          </label>
          <div className="option-stack">
            {(selectedModule?.options ?? []).slice(0, 8).map((option) => (
              <div key={option.name} className="option-chip">
                <strong>{option.name}</strong>
                <span>{option.description ?? (option.required ? 'required' : 'optional')}</span>
              </div>
            ))}
          </div>
          <div className="card-actions">
            <button onClick={() => selectedModule && void postAction('/operations/run_module', { module: selectedModule.path, operation_id: 'primary', target: moduleTarget, options: { target: moduleTarget } }, `Module queued: ${selectedModule.path}`)}>Run Module</button>
            <button className="secondary" onClick={() => setActiveView('monitor')}>View Jobs</button>
          </div>
        </div>
      </div>
    </Section>
  );

  const pipelineSection = (
    <Section title="Pipeline Builder & Execution" subtitle="Launch investigation workflows, monitor stage progress, and feed results directly into the graph and reporting surfaces.">
      <div className="workspace-grid">
        <div className="panel-subtle">
          <label>
            Pipeline
            <select value={selectedWorkflow} onChange={(event) => setSelectedWorkflow(event.target.value)}>
              {workflows.map((workflow) => (
                <option key={workflow.name} value={workflow.name}>{workflow.name}</option>
              ))}
            </select>
          </label>
          <label>
            Investigation Seed
            <input value={pipelineSeed} onChange={(event) => setPipelineSeed(event.target.value)} />
          </label>
          <div className="card-actions">
            <button onClick={() => selectedWorkflowItem && void postAction('/operations/run_pipeline', { pipeline: selectedWorkflowItem.name, seed: pipelineSeed, operation_id: 'primary', options: { target: pipelineSeed } }, `Pipeline queued: ${selectedWorkflowItem.name}`)}>Launch Pipeline</button>
          </div>
        </div>
        <div className="panel-subtle">
          <h3>{selectedWorkflowItem?.name ?? 'No pipeline selected'}</h3>
          <p>{selectedWorkflowItem?.description ?? 'Select a workflow to inspect its stage map.'}</p>
          <div className="timeline-strip">
            {(selectedWorkflowItem?.steps ?? []).map((step) => (
              <div key={step.name} className="timeline-item">
                <strong>{step.name}</strong>
                <span>{step.module}</span>
                <small>Retries: {step.retry_count}</small>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Section>
  );

  const graphSection = (
    <Section title="Graph Intelligence Explorer" subtitle="Search entities, expand relationships, pivot into investigations, and operate on intelligence data with an analyst-first graph workspace.">
      <div className="toolbar">
        <input value={graphQuery} onChange={(event) => setGraphQuery(event.target.value)} placeholder="Search person, email, domain, phone, IP, account…" />
        <button onClick={() => void loadAll()}>Refresh Graph</button>
      </div>
      <GraphPanel
        nodes={graphNodes}
        edges={graphEdges}
        highlightedNodeId={selectedNodeId}
        onNodeSelect={(node) => setSelectedNodeId(node.id)}
        onPivot={(node) => { setInvestigationSeed(node.label || node.value || node.id); setActiveView('investigation'); }}
      />
    </Section>
  );

  const toolSection = (
    <Section title="Tool Manager" subtitle="Inspect installed tooling, refresh state, queue installations, and dispatch direct tool launches from the UI.">
      <div className="workspace-grid">
        <div className="panel-subtle list-stack">
          {tools.map((tool) => (
            <button key={tool.name} type="button" className={`list-item interactive ${selectedToolItem?.name === tool.name ? 'selected' : ''}`} onClick={() => setSelectedTool(tool.name)}>
              <div>
                <strong>{tool.name}</strong>
                <span>{tool.category}</span>
              </div>
              <span className={`pill pill-${tool.installed ? 'completed' : 'pending'}`}>{tool.installed ? 'installed' : 'missing'}</span>
            </button>
          ))}
        </div>
        <div className="panel-subtle">
          <h3>{selectedToolItem?.name ?? 'Select a tool'}</h3>
          <p>{selectedToolItem?.description ?? 'Direct tool control exposed through the operations API.'}</p>
          <label>
            Arguments
            <input value={toolArgs} onChange={(event) => setToolArgs(event.target.value)} />
          </label>
          <div className="card-actions">
            <button onClick={() => selectedToolItem && void postAction(`/operations/run_tool?name=${encodeURIComponent(selectedToolItem.name)}`, { args: toolArgs.split(' ').filter(Boolean), operation_id: 'primary', target: investigationSeed }, `Tool run submitted: ${selectedToolItem.name}`)}>Run Tool</button>
            <button className="secondary" onClick={() => selectedToolItem && void postAction(`/tools/${encodeURIComponent(selectedToolItem.name)}/install`, {}, `Install queued: ${selectedToolItem.name}`)}>Install / Repair</button>
            <button className="secondary" onClick={() => void postAction('/tools/refresh', {}, 'Tool inventory refresh queued.')}>Refresh Inventory</button>
          </div>
        </div>
      </div>
    </Section>
  );

  const automationSection = (
    <Section title="Automation Manager" subtitle="Schedule recurring collection and breach monitoring workflows from the dashboard without dropping into the terminal.">
      <div className="workspace-grid">
        <div className="panel-subtle">
          <label>
            Monitor Target
            <input value={automationTarget} onChange={(event) => setAutomationTarget(event.target.value)} />
          </label>
          <p>Create a daily workflow rule to monitor a domain, run the selected pipeline, and surface an alert if new findings appear.</p>
          <button onClick={() => selectedModule && void postAction('/scheduler/interval', { path: selectedModule.path, interval_seconds: 86400, operation_id: 'primary', options: { target: automationTarget } }, `Automation rule scheduled for ${automationTarget}`)}>Schedule Daily Automation</button>
        </div>
        <div className="panel-subtle">
          <h3>Scheduled Jobs</h3>
          <div className="list-stack scrollable">
            {(health?.scheduler_jobs ?? []).map((job, index) => (
              <div key={`${job.id ?? index}`} className="list-item">
                <div>
                  <strong>{String(job.name ?? job.id ?? 'scheduled-job')}</strong>
                  <span>{String(job.status ?? 'pending')}</span>
                </div>
                <span className="pill pill-scheduled">automation</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Section>
  );

  const reportSection = (
    <Section title="Report Viewer" subtitle="Generate operational reports, inspect the export catalog, and keep delivery inside the workspace lifecycle.">
      <div className="toolbar">
        <select value={reportFormat} onChange={(event) => setReportFormat(event.target.value)}>
          <option value="html">HTML</option>
          <option value="json">JSON</option>
          <option value="md">Markdown</option>
        </select>
        <button onClick={() => void postAction('/dashboard/reports', { title: `RTF Ops Report ${new Date().toISOString().slice(0, 10)}`, format: reportFormat, operation_id: 'primary', metadata: { generator: 'dashboard-ui' } }, 'Report generated.')}>Generate Report</button>
      </div>
      <div className="report-list scrollable">
        {reports.map((report, index) => (
          <div key={`${report.path ?? report.title}-${index}`} className="list-item">
            <div>
              <strong>{report.title ?? 'Generated Report'}</strong>
              <span>{report.path ?? 'stored in data/reports'}</span>
            </div>
            <span className="pill pill-completed">{report.format ?? 'artifact'}</span>
          </div>
        ))}
      </div>
    </Section>
  );

  const monitorSection = (
    <Section title="System Monitor" subtitle="Track workers, queue pressure, resource utilization, service readiness, and raw terminal output in real time.">
      <div className="stats-grid compact">
        <StatCard label="CPU" value={`${health?.system?.cpu.percent ?? 0}%`} accent="amber" />
        <StatCard label="Memory" value={`${health?.system?.memory.percent ?? 0}%`} accent="red" />
        <StatCard label="Disk" value={`${health?.system?.disk.percent ?? 0}%`} accent="blue" />
        <StatCard label="Installed Tools" value={health?.tool_summary.installed ?? 0} accent="green" />
      </div>
      <div className="workspace-grid">
        <div className="panel-subtle">
          <h3>Services</h3>
          <div className="list-stack">
            {Object.entries(health?.system?.services ?? {}).map(([name, status]) => (
              <div key={name} className="list-item">
                <div>
                  <strong>{name}</strong>
                  <span>{status}</span>
                </div>
                <span className={`pill pill-${status === 'online' ? 'completed' : 'pending'}`}>{status}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="panel-subtle">
          <h3>Live Console</h3>
          <div className="toolbar compact-toolbar">
            <input value={terminalInput} onChange={(event) => setTerminalInput(event.target.value)} />
            <button onClick={async () => {
              const result = await fetchJson<{ transcript: string }>('/dashboard/terminal/command', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ command: terminalInput, workspace: 'operations' }) });
              setTerminalTranscript(result.transcript);
            }}>Run</button>
          </div>
          <div className="terminal-box"><pre>{terminalTranscript || 'rtf(operations)> help'}</pre></div>
          <p className="hint">Memory: {formatBytes(health?.system?.memory.used)} / {formatBytes(health?.system?.memory.total)} · Host: {health?.system?.hostname ?? 'unknown'}</p>
        </div>
      </div>
    </Section>
  );

  const overview = (
    <>
      <Section title="Command Dashboard" subtitle="Operate modules, pipelines, intelligence pivots, automation, and reporting from a single mission workspace.">
        <div className="stats-grid">
          <StatCard label="Modules" value={summary?.metrics.modules ?? 0} accent="blue" />
          <StatCard label="Pipelines" value={workflows.length} accent="green" />
          <StatCard label="Running Jobs" value={runningJobs.length} accent="amber" />
          <StatCard label="Findings" value={summary?.metrics.findings_total ?? 0} accent="red" />
          <StatCard label="Graph Nodes" value={summary?.metrics.graph_nodes ?? 0} accent="blue" />
          <StatCard label="Queue Depth" value={summary?.metrics.scheduler_queue_depth ?? 0} accent="red" />
        </div>
        <div className="three-column">
          <div className="panel-subtle">
            <h3>Operations</h3>
            <div className="list-stack">
              {(summary?.operations ?? []).map((operation) => (
                <button key={operation.id} type="button" className="list-item interactive" onClick={() => { setInvestigationName(operation.name); setInvestigationSeed(operation.target ?? ''); setActiveView('investigation'); }}>
                  <div>
                    <strong>{operation.name}</strong>
                    <span>{operation.summary}</span>
                  </div>
                  <span className={`pill pill-${operation.status || 'active'}`}>{operation.status || 'active'}</span>
                </button>
              ))}
            </div>
          </div>
          <div className="panel-subtle">
            <h3>Recent Jobs</h3>
            <div className="list-stack scrollable">
              {jobs.slice(0, 8).map((job) => (
                <div key={job.id} className="list-item">
                  <div>
                    <strong>{job.name}</strong>
                    <span>{job.module_path}</span>
                  </div>
                  <span className={`pill pill-${job.status}`}>{job.status}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="panel-subtle">
            <h3>Live Event Feed</h3>
            <div className="event-stream scrollable">
              {events.slice(0, 8).map((event) => (
                <div key={`${event.id}-${event.event_type}`} className={`event-row sev-${event.severity}`}>
                  <span className="mono">{event.event_type}</span>
                  <div>
                    <strong>{event.source}</strong>
                    <span>{event.message}</span>
                  </div>
                  <span>{event.target || 'n/a'}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Section>

      <div className="split-layout">
        {moduleRunnerSection}
        {pipelineSection}
      </div>
      <div className="split-layout">
        {graphSection}
        {monitorSection}
      </div>
    </>
  );
  return (
    <div className="app-shell">
      <aside className="sidebar panel">
        <div className="brand">
          <div className="brand-mark">RTF</div>
          <div>
            <strong>Operations Nexus</strong>
            <span>Interactive red-team command interface</span>
          </div>
        </div>
        <nav className="sidebar-section">
          <span className="sidebar-label">Workspaces</span>
          {navItems.map(([key, label]) => (
            <button key={key} type="button" className={activeView === key ? 'active' : ''} onClick={() => setActiveView(key)}>
              {label}
            </button>
          ))}
        </nav>
        <div className="sidebar-section intel-box">
          <span className="sidebar-label">Realtime Status</span>
          <p>WebSocket feed: <strong>{events.length ? 'connected' : 'waiting'}</strong></p>
          <p>API: <strong>{health?.api.status ?? 'unknown'}</strong></p>
          <p>Workers: <strong>{JSON.stringify(health?.worker_status ?? {})}</strong></p>
        </div>
        {flashMessage ? <div className="flash-message">{flashMessage}</div> : null}
      </aside>

      <main className="main-grid">
        {activeView === 'dashboard' && overview}
        {activeView === 'investigation' && investigationSection}
        {activeView === 'pipelines' && pipelineSection}
        {activeView === 'modules' && moduleRunnerSection}
        {activeView === 'graph' && graphSection}
        {activeView === 'tools' && toolSection}
        {activeView === 'automation' && automationSection}
        {activeView === 'reports' && reportSection}
        {activeView === 'monitor' && monitorSection}
      </main>
    </div>
  );
}
