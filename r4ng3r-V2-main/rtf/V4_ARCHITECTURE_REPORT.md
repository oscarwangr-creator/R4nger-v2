# RTF Version 4.0 Architecture Report

## Executive Summary
- Version: 4.0.0
- CLI entrypoint: `rtf/rtf.py`
- Registered framework modules: 47
- Built-in workflows: 23
- TITAN services: 14

## Architecture Map

### Module System
- Base class: `framework/modules/base.py::BaseModule`
- Categories: {"active_directory": 3, "architecture": 13, "cloud": 3, "crypto": 1, "network": 1, "osint": 8, "post_exploitation": 4, "recon": 7, "web": 5, "wireless": 2}

### Module Loader
- Implementation: `framework/modules/loader.py`
- Discovery: framework.modules package scan, external filesystem module scan

### Pipelines
- Workflow engine: `framework/workflows/engine.py`
- Pipeline v2: `framework/automation/pipeline_v2.py`
- Legacy orchestrator: `core/pipeline_orchestrator.py`
- Workflow names: ad_attack, attack_surface_mapping, cloud_attack_pipeline, cloud_audit, continuous_attack_surface, credential_attack_chain, credential_intelligence, deep_osint, engine_mesh, external_pentest_full, full_ad_compromise, full_recon, identity_fusion, identity_fusion_extreme, infrastructure_correlation, nexus_identity_workflow, osint_person, physical_wireless_audit, social_engineering_intel, ssl_web_recon, threat_intelligence_pipeline, web_audit, web_deep_audit

### CLI Interface
- Main command router: `rtf/rtf.py`
- Interactive console: `framework/cli/console.py`
- Legacy-compatible module/workflow/tool/report commands retained

### Tool Wrappers
- Base wrapper: `framework/intelligence/tool_wrapper.py::ToolWrapper`
- Wrapper inventory: {"credential_attacks": 6, "exploitation_frameworks": 5, "modules": 1, "network_attacks": 7, "osint": 11, "post_exploitation": 4, "recon": 15, "reverse_engineering": 4, "scanning": 8, "threat_intelligence": 3, "web_exploitation": 11, "wrappers": 3}

### Database System
- Engine: SQLite
- Tables: jobs, findings, tool_registry, targets, schedules, operations, graph_nodes, graph_edges, intelligence_artifacts, credentials_vault, event_log, reports, console_sessions

### Reporting System
- Engine: `framework/reporting/engine.py`
- Formats: html, pdf, xlsx, markdown, json

### Installation Scripts
- Python installer: `framework/installer/installer.py`
- Shell installer: `tools/install_all_tools.sh`

### Workflow Logic
- Scheduler: `framework/scheduler/scheduler.py`
- AI orchestrator: `framework/ai/autonomous_agent.py`

## Sequential Upgrade Agents
### Architecture agent
- Status: completed
- Summary: Generated a repository-wide V4 architecture map and compatibility baseline.
- Outputs: `{"module_categories": {"active_directory": 3, "architecture": 13, "cloud": 3, "crypto": 1, "network": 1, "osint": 8, "post_exploitation": 4, "recon": 7, "web": 5, "wireless": 2}, "pipeline_count": 8, "service_count": 14, "version": "4.0.0"}`

### Module builder
- Status: completed
- Summary: Built a non-breaking extension inventory for legacy and TITAN modules.
- Outputs: `{"compatibility_contract": ["BaseModule.info()", "BaseModule._declare_options()", "BaseModule.run()", "ModuleResult serialization"], "module_count": 47}`

### OSINT pipeline builder
- Status: completed
- Summary: Mapped classical OSINT modules and external wrapper families into the V4 pipeline fabric.
- Outputs: `{"framework_osint_modules": 8, "wrapper_families": {"osint": 11}}`

### SOCMINT pipeline builder
- Status: completed
- Summary: Promoted the TITAN SOCMINT pipeline to the V4 orchestration layer with 15+ mapped stages.
- Outputs: `{"socmint_stage_count": 16, "socmint_stages": [{"code": "A", "name": "Seed normalization"}, {"code": "B", "name": "Username discovery"}, {"code": "B2", "name": "Deep account scraping"}, {"code": "B3", "name": "Search engine scraping"}, {"code": "B4", "name": "Social network analysis"}, {"code": "C", "name": "Email breach intelligence"}, {"code": "D", "name": "Social media deep analysis"}, {"code": "E", "name": "Domain intelligence"}, {"code": "F", "name": "Code intelligence"}, {"code": "G", "name": "Phone intelligence"}, {"code": "H", "name": "Dark web monitoring"}, {"code": "I", "name": "Metadata intelligence"}, {"code": "J", "name": "AI correlation engine"}, {"code": "K", "name": "Graph integration"}, {"code": "L", "name": "Recursive pivot engine"}, {"code": "M", "name": "Threat scoring"}]}`

### Dashboard builder
- Status: completed
- Summary: Composed dashboard data contracts for Flask and SPA surfaces without altering legacy routes.
- Outputs: `{"dashboard_surfaces": ["framework/dashboard/app.py", "dashboard_ui/src/App.tsx"], "workflow_count": 23}`

### Self-healing system builder
- Status: completed
- Summary: Defined health-checkable queues, services, and repairable extension points for V4 operations.
- Outputs: `{"heal_targets": ["tool_registry", "module_loader", "scheduler", "titan_message_bus", "database"], "health_snapshot": {"architecture": "RTF TITAN OMEGA", "queue_topics": {}, "queued_messages": 0, "service_count": 14, "services": [{"metadata": {"interfaces": ["queue:ai"]}, "name": "rtf-ai-engine", "queue_depth": 0, "status": "ready"}, {"metadata": {"interfaces": ["queue:automation"]}, "name": "rtf-automation-engine", "queue_depth": 0, "status": "ready"}, {"metadata": {"interfaces": ["queue:breach"]}, "name": "rtf-breach-engine", "queue_depth": 0, "status": "ready"}, {"metadata": {"interfaces": ["queue:casm"]}, "name": "rtf-casm-engine", "queue_depth": 0, "status": "ready"}, {"metadata": {"interfaces": ["cli", "api", "scheduler"]}, "name": "rtf-core", "queue_depth": 0, "status": "ready"}, {"metadata": {"interfaces": ["queue:credential"]}, "name": "rtf-credential-engine", "queue_depth": 0, "status": "ready"}, {"metadata": {"interfaces": ["queue:graph", "bolt"]}, "name": "rtf-graph-engine"`

### Final integration engine
- Status: completed
- Summary: Unified CLI, API, dashboard, workflows, data, and TITAN services into a single V4 manifest.
- Outputs: `{"entrypoints": ["rtf/rtf.py", "framework/api/server.py", "framework/dashboard/app.py"], "titan_manifest": {"architecture_map": {"data_plane": {"observability": ["Prometheus", "Grafana"], "queueing": ["RabbitMQ", "Redis"], "storage": ["Neo4j", "ElasticSearch", "MinIO"]}, "engine_mesh": {"distributed_workers": {"rtf-ai-engine": ["inference-worker", "ranking-worker"], "rtf-automation-engine": ["pipeline-worker", "template-worker"], "rtf-breach-engine": ["breach-worker", "dedupe-worker"], "rtf-casm-engine": ["surface-worker", "drift-worker"], "rtf-core": ["coordinator", "api-gateway"], "rtf-credential-engine": ["spray-worker", "cracker-worker"], "rtf-graph-engine": ["graph-writer", "query-worker"], "rtf-monitoring-engine": ["metrics-worker", "alert-worker"], "rtf-osint-engine": ["search-worker", "enrichment-worker"], "rtf-report-engine": ["report-worker", "render-worker"], "rtf-scraper-engine": ["fetch-worker", "parser-worker"], "rtf-socmint-engine": ["persona-worker", "timeline-worker"]}`
