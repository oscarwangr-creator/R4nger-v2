# RTF TITAN Architecture

## Current framework analysis

RTF already exposes stable extension points across the module loader, CLI, workflow engine, API server, dashboard, tool registry, installer, scheduler, and reporting engine. TITAN expands those layers instead of replacing them.

### Dependency map

- `rtf.py` bootstraps config, DB, CLI, API, dashboard, installer, module, workflow, and reporting commands.
- `framework/modules/base.py` defines the module contract used by module implementations and workflows.
- `framework/workflows/engine.py` orchestrates built-in workflows and remains the backward-compatible registration point for TITAN pipelines.
- `framework/api/server.py` is the API entrypoint and now also exposes TITAN topology/investigation endpoints.
- `framework/dashboard/app.py` is the visual entrypoint and now surfaces TITAN health and queue telemetry.
- `framework/intelligence/tool_wrapper.py` remains the compatibility wrapper while `framework/titan/wrappers.py` adds the universal TITAN wrapper contract.

### TITAN distributed services

- `rtf-core`
- `rtf-osint-engine`
- `rtf-socmint-engine`
- `rtf-casm-engine`
- `rtf-credential-engine`
- `rtf-graph-engine`
- `rtf-ai-engine`
- `rtf-scraper-engine`
- `rtf-wireless-engine`
- `rtf-worker-cluster`
- `rtf-report-engine`
- `rtf-ingestion-engine`
- `rtf-automation-engine`
- `rtf-monitoring-engine`

### Message-queue orchestration

TITAN uses a queue-backed orchestration model aligned to RabbitMQ/Redis. The in-repo implementation ships an in-memory message bus for local validation, while deployment manifests model the production shape for Docker and Kubernetes.

### Intelligence layers

- Knowledge graph ingestion for `Person`, `Username`, `Email`, `Phone`, `Domain`, `Organization`, `Account`, `Repository`, `IP`, `Location`, `Device`, `Website`, `Document`, and `Media`.
- Relationship support for `REGISTERED_WITH`, `CONNECTED_TO`, `OWNS`, `POSTED_FROM`, `MENTIONED_IN`, `FOLLOWS`, `USES_EMAIL`, `USES_PHONE`, `USES_USERNAME`, `ASSOCIATED_WITH`, `HOSTED_ON`, and `INTERACTED_WITH`.
- AI identity resolution with stylometry, behavior fingerprinting, posting-time clustering, linguistic similarity, username similarity, avatar perceptual hashing, and timeline alignment.
- A 15-stage SOCMINT pipeline from seed normalization through investigation reporting.

### Extension points

1. CLI: add `titan` subcommands without disturbing legacy operators.
2. API: publish service topology, health, and distributed investigation controls.
3. Dashboard: add service health, graph explorer, and queue telemetry cards.
4. Workflow engine: register TITAN pipelines in the existing workflow registry.
5. Reporting engine: consume TITAN graph and AI outputs for multi-format reports.
6. Scheduler: bridge local async jobs to queue-backed workers.
