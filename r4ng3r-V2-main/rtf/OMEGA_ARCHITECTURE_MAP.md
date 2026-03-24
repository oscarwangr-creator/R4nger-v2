# RTF v4.0 OMEGA Architecture Map

## Upgrade Strategy
RTF v4.0 OMEGA upgrades the existing framework in place. Legacy CLI flows, modules, workflows, and reporting remain available while the TITAN layer now exposes a fuller distributed intelligence topology.

## Entry Points
- CLI: `rtf console`, `rtf module`, `rtf workflow`, `rtf titan manifest|health|schema|investigate`
- API: `/health`, `/stats`, `/modules`, `/workflows`, `/graph/schema`, `/titan/manifest`, `/titan/health`
- Dashboard: investigation manager, graph explorer, module execution panel, SOCMINT coverage, queue health, report surfaces

## Distributed Service Topology
- `rtf-core`: shared configuration, compatibility, registry, scheduler bridge
- `rtf-osint-engine`: seed collection, normalization, search enrichment
- `rtf-socmint-engine`: 15-stage SOCMINT investigation pipeline
- `rtf-credential-engine`: breach intelligence and cracking coordination
- `rtf-casm-engine`: attack surface management and exposure monitoring
- `rtf-graph-engine`: Neo4j graph materialization and query support
- `rtf-ai-engine`: stylometry, clustering, identity resolution, risk scoring
- `rtf-scraper-engine`: social/search scraping collection plane
- `rtf-wireless-engine`: wireless and SDR orchestration
- `rtf-report-engine`: HTML/PDF/JSON/XLSX report generation
- `rtf-ingestion-engine`: evidence normalization and indexing
- `rtf-automation-engine`: workflow templates and recursive pivots
- `rtf-monitoring-engine`: Prometheus/Grafana observability plane
- `rtf-worker-cluster`: parallel distributed workers backed by queues/cache

## Infrastructure Stack
- Runtime: Docker, Kubernetes
- Queueing: RabbitMQ
- Cache/coordination: Redis
- Graph: Neo4j
- Search: ElasticSearch
- Artifact storage: MinIO
- Monitoring: Prometheus, Grafana

## SOCMINT 15-Stage Pipeline
1. A — Seed normalization
2. B — Username discovery
3. B2 — Deep account scraping
4. B3 — Search engine scraping
5. B4 — Social network analysis
6. C — Email breach intelligence
7. D — Social media deep analysis
8. E — Domain intelligence
9. F — Code intelligence
10. G — Phone intelligence
11. H — Dark web monitoring
12. I — Metadata intelligence
13. J — AI correlation engine
14. K — Graph integration
15. L — Recursive pivot engine
16. M — Threat scoring

## Intelligence Graph Schema
### Entities
Person, Username, Email, Phone, Domain, IP, Organization, Account, Repository, Location, Device, Website, Document, Media

### Relationships
REGISTERED_WITH, CONNECTED_TO, OWNS, POSTED_FROM, MENTIONED_IN, FOLLOWS, USES_EMAIL, USES_PHONE, USES_USERNAME, ASSOCIATED_WITH, HOSTED_ON, INTERACTED_WITH

## Legacy Compatibility Notes
- Existing workflows and wrappers remain intact.
- TITAN OMEGA operates as an additive architecture layer.
- Reporting remains multi-format and backward compatible.
- Existing REST and dashboard entry points remain active while exposing OMEGA extensions.
