# Codex Authorized Upgrade Brief

Use this brief as the single source of truth for additive upgrades to the existing `r4ng3r-V2` repository. Preserve current architecture, add new assets in-place, and avoid destructive refactors unless strictly required for runtime integrity.

## Operating Boundaries
- Authorized security research, defensive intelligence, exposure assessment, and public-data correlation only.
- Prefer public, consent-based, or operator-supplied data sources.
- Preserve existing repository behavior; add capabilities rather than removing them.
- Keep wrappers, manifests, pipelines, workflow mappings, reporting, and UI orchestration deterministic and testable.

## Current Inventory Snapshot
- Modules in manifest: 74
- Tools in manifest: 520
- Pipelines on disk: 75
- Workflows in manifest: 3

### Module Categories
- breach_darkweb_intelligence: 1 modules
- code_repository_intelligence: 1 modules
- domain_infrastructure_intelligence: 1 modules
- email_intelligence: 1 modules
- generated: 64 modules
- identity_intelligence: 1 modules
- infrastructure_attack_surface: 1 modules
- metadata_geolocation_intelligence: 1 modules
- organization_intelligence: 1 modules
- phone_intelligence: 1 modules
- social_media_intelligence: 1 modules

### Tool Categories
- breach_darkweb_intelligence: 52 tools
- code_repository_intelligence: 52 tools
- domain_infrastructure_intelligence: 52 tools
- email_intelligence: 52 tools
- identity_intelligence: 52 tools
- infrastructure_attack_surface: 52 tools
- metadata_geolocation_intelligence: 52 tools
- organization_intelligence: 52 tools
- phone_intelligence: 52 tools
- social_media_intelligence: 52 tools

## Required Delivery Goals
1. Maintain a standard module contract:
```text
modules/{module_name}/
├── module.py
├── config.yaml
├── requirements.txt
└── README.md
```
2. Keep all tools registry entries machine-readable with installation method, dependencies, wrapper mapping, supported inputs, and reporting compatibility.
3. Keep every pipeline at 8+ stages with explicit recursive pivoting, AI-assisted correlation flags, graph updates, reporting contracts, and next-step planning.
4. Ensure modules → pipelines → workflows → dashboard → reporting remain wired through the existing `rtf/intelligence_os` stack.
5. Generate example investigations for every pipeline so the UI and API can preload realistic demonstration jobs.

## Implementation Instructions for Codex
### 1. Preserve and enrich the existing architecture
- Treat `rtf/intelligence_os/manifests/framework_manifest.json` as the canonical manifest.
- Treat `rtf/intelligence_os/pipelines/*.yaml` as canonical pipeline definitions.
- Keep wrapper behavior additive: new wrappers should conform to the existing base wrapper and registry conventions.
- Extend workflow coverage so every pipeline is addressable through at least one workflow family.

### 2. Standardize module wrappers
For every module family, implement or retain:
- `module.py` with normalized `run()`, validation, parser selection, and result-shaping.
- `config.yaml` with tool command templates, environment variables, timeout, rate limits, and report flags.
- `requirements.txt` with Python-only dependencies for the wrapper layer.
- `README.md` with purpose, accepted seeds, output schema, and workflow usage.

### 3. Tool registry requirements
Every tool record must include:
- `name`
- `category`
- `install_method`
- `module`
- `dependencies`
- `mode`
- `input_types`
- `output_types`
- `pipeline_compatible`
- `validation`
- optional `docker_image`, `binary`, `api_required`, `auth_notes`

### 4. Pipeline contract
Each pipeline definition must include:
- `name`
- `purpose`
- `input.types`
- `recursive_pivoting`
- `ai_assisted`
- `stages[]` with `name`, `module`, `tool`, `input`, `required`
- `output.formats`
- `output.next_steps`

### 5. Workflow orchestration contract
Add or update workflow families so analysts can run:
- identity and persona investigations
- email and breach investigations
- phone and messaging investigations
- social and content investigations
- domain, infrastructure, and certificate investigations
- code, contributor, and package investigations
- organization, executive, and subsidiary investigations
- threat exposure, leak, and actor monitoring
- geolocation, imagery, and metadata investigations

### 6. Dashboard and API integration
- Surface module, pipeline, and workflow launch controls.
- Add live execution state, stage timing, status aggregation, and result download actions.
- Keep graph visualization connected to pipeline outputs and example investigations.
- Provide filters by seed type, intelligence domain, workflow family, and report format.

### 7. Reporting contract
All reports must support the existing multi-format reporters and emit:
- normalized evidence records
- extracted entities
- stage summaries
- graph edges
- confidence metadata
- analyst next steps

## Pipeline Inventory Reference
- academic_research_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- account_verification_pipeline: inputs=['username', 'email'], stages=7
- api_surface_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- asset_ownership_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- attack_surface_intelligence_pipeline: inputs=[], stages=3
- board_member_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- brand_impersonation_pipeline: inputs=['brand', 'domain'], stages=8
- breach_correlation_pipeline: inputs=['email', 'username', 'domain'], stages=7
- breach_intelligence_pipeline: inputs=[], stages=3
- campaign_tracking_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- certificate_transparency_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- chat_server_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- code_contributor_pipeline: inputs=['repository', 'username'], stages=7
- conference_exposure_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- credential_intelligence_pipeline: inputs=[], stages=2
- credential_reuse_pipeline: inputs=['email', 'domain'], stages=7
- crypto_wallet_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- dark_web_exposure_pipeline: inputs=['email', 'keyword', 'domain'], stages=8
- dark_web_intelligence_pipeline: inputs=[], stages=2
- dataset_leak_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- disinformation_monitoring_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- document_exploitation_pipeline: inputs=['file', 'domain'], stages=7
- document_intelligence_pipeline: inputs=[], stages=2
- domain_infrastructure_pipeline: inputs=['domain'], stages=8
- domain_intelligence_pipeline: inputs=[], stages=3
- email_intelligence_pipeline: inputs=['email'], stages=8
- employee_enumeration_pipeline: inputs=['organization', 'domain'], stages=8
- event_monitoring_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- executive_watch_pipeline: inputs=['real_name', 'username', 'email'], stages=8
- facility_mapping_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- forum_monitoring_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- fraud_investigation_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- geoint_intelligence_pipeline: inputs=[], stages=2
- geolocation_pivot_pipeline: inputs=['location', 'file', 'username'], stages=7
- github_intelligence_pipeline: inputs=[], stages=2
- github_secrets_pipeline: inputs=['username', 'organization'], stages=8
- identity_intelligence_pipeline: inputs=[], stages=3
- identity_mega_pipeline: inputs=['username', 'email', 'phone', 'real_name'], stages=11
- image_recon_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- influencer_mapping_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- infrastructure_exposure_pipeline: inputs=['domain', 'ip'], stages=8
- infrastructure_intelligence_pipeline: inputs=[], stages=3
- legal_exposure_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- malware_repo_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- marketing_asset_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- messaging_app_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- metadata_intelligence_pipeline: inputs=['file', 'image_url'], stages=8
- mobile_app_intelligence_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- newsletter_leak_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- ngo_network_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- ngo_partnership_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- organization_profiling_pipeline: inputs=['organization', 'domain'], stages=8
- package_registry_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- paste_monitoring_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- pastebin_identity_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- persona_correlation_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- phone_intelligence_pipeline: inputs=['phone'], stages=7
- press_correlation_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- public_records_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- ransomware_exposure_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- recruitment_signal_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- satellite_context_pipeline: inputs=['location', 'organization'], stages=7
- social_graph_pipeline: inputs=['username', 'keyword'], stages=8
- social_network_intelligence_pipeline: inputs=[], stages=2
- startup_due_diligence_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- subsidiary_domain_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- subsidiary_mapping_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- supply_chain_risk_pipeline: inputs=['organization', 'domain', 'repository'], stages=8
- threat_actor_profiling_pipeline: inputs=['alias', 'keyword', 'domain'], stages=8
- travel_pattern_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- typosquat_monitoring_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- username_intelligence_pipeline: inputs=['username'], stages=8
- vendor_attack_surface_pipeline: inputs=['organization', 'domain'], stages=8
- video_intelligence_pipeline: inputs=['keyword', 'domain', 'username'], stages=8
- vulnerability_trend_pipeline: inputs=['keyword', 'domain', 'username'], stages=8

## Expected Deliverables
- Updated wrappers and module metadata under `rtf/modules` and `rtf/intelligence_os/tooling`.
- Expanded workflow coverage and orchestration metadata.
- Dashboard/API support for launching, monitoring, and exporting investigations.
- Example investigation packs for every pipeline.
- Validation scripts/tests proving manifest integrity, pipeline loadability, and report generation.
