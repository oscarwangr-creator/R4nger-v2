from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class EngineSpec:
    name: str
    category: str
    description: str
    module_path: str
    cli_alias: str
    queue: str
    dependencies: List[str] = field(default_factory=list)
    task_pipeline: List[str] = field(default_factory=list)
    worker_roles: List[str] = field(default_factory=list)
    graph_capabilities: List[str] = field(default_factory=list)
    tool_wrappers: List[str] = field(default_factory=list)
    scheduler_hooks: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EngineRegistry:
    def __init__(self) -> None:
        self._engines: Dict[str, EngineSpec] = {
            spec.name: spec for spec in [
                EngineSpec(
                    name="rtf-core",
                    category="architecture",
                    description="Shared orchestration plane for configuration, module dispatch, scheduler bridging, and CLI bootstrap.",
                    module_path="architecture/rtf_core_engine",
                    cli_alias="core",
                    queue="queue:core",
                    dependencies=["rtf-automation-engine", "rtf-monitoring-engine"],
                    task_pipeline=["config_load", "module_resolution", "queue_dispatch", "result_merge"],
                    worker_roles=["coordinator", "api-gateway"],
                    graph_capabilities=["operation_context", "engine_lineage"],
                    tool_wrappers=["module_loader", "tool_registry", "workflow_registry"],
                    scheduler_hooks=["job_submission", "priority_routing", "retry_policy"],
                ),
                EngineSpec(
                    name="rtf-osint-engine",
                    category="architecture",
                    description="OSINT collection mesh for search, enrichment, and normalization across passive sources.",
                    module_path="architecture/rtf_osint_engine",
                    cli_alias="osint",
                    queue="queue:osint",
                    dependencies=["rtf-core", "rtf-scraper-engine", "rtf-graph-engine"],
                    task_pipeline=["seed_normalization", "search_collection", "artifact_enrichment", "entity_normalization"],
                    worker_roles=["search-worker", "enrichment-worker"],
                    graph_capabilities=["identity_nodes", "evidence_edges"],
                    tool_wrappers=["web_search_scraper", "shodan_search", "username_enum"],
                    scheduler_hooks=["fanout_collection", "source_backoff"],
                ),
                EngineSpec(
                    name="rtf-socmint-engine",
                    category="architecture",
                    description="SOCMINT pipeline for persona fusion, recursive pivots, and timeline assembly.",
                    module_path="architecture/rtf_socmint_engine",
                    cli_alias="socmint",
                    queue="queue:socmint",
                    dependencies=["rtf-osint-engine", "rtf-ai-engine", "rtf-graph-engine"],
                    task_pipeline=["handle_expansion", "profile_correlation", "timeline_build", "relationship_scoring"],
                    worker_roles=["persona-worker", "timeline-worker"],
                    graph_capabilities=["social_graph", "timeline_edges"],
                    tool_wrappers=["identity_fusion", "identity_fusion_extreme", "nexus_identity_pipeline"],
                    scheduler_hooks=["recursive_pivots", "stage_barriers"],
                ),
                EngineSpec(
                    name="rtf-graph-engine",
                    category="architecture",
                    description="Graph intelligence storage and relationship query layer for distributed investigations.",
                    module_path="architecture/rtf_graph_engine",
                    cli_alias="graph",
                    queue="queue:graph",
                    dependencies=["rtf-core"],
                    task_pipeline=["entity_ingest", "edge_materialization", "query_projection", "subgraph_export"],
                    worker_roles=["graph-writer", "query-worker"],
                    graph_capabilities=["neo4j_sync", "sqlite_cache", "path_analysis"],
                    tool_wrappers=["graph_builder", "relationship_engine", "knowledge_graph"],
                    scheduler_hooks=["graph_flush", "query_batching"],
                ),
                EngineSpec(
                    name="rtf-ai-engine",
                    category="architecture",
                    description="AI correlation engine for identity resolution, prioritization, and summarization.",
                    module_path="architecture/rtf_ai_engine",
                    cli_alias="ai",
                    queue="queue:ai",
                    dependencies=["rtf-core", "rtf-graph-engine"],
                    task_pipeline=["feature_extraction", "identity_resolution", "risk_scoring", "brief_generation"],
                    worker_roles=["inference-worker", "ranking-worker"],
                    graph_capabilities=["entity_embeddings", "attack_path_summaries"],
                    tool_wrappers=["decision_engine", "goal_engine", "attack_path_generator"],
                    scheduler_hooks=["adaptive_priority", "feedback_loop"],
                ),
                EngineSpec(
                    name="rtf-breach-engine",
                    category="architecture",
                    description="Breach intelligence engine for leak ingestion, credential exposure scoring, and downstream pivots.",
                    module_path="architecture/rtf_breach_engine",
                    cli_alias="breach",
                    queue="queue:breach",
                    dependencies=["rtf-osint-engine", "rtf-credential-engine", "rtf-graph-engine"],
                    task_pipeline=["leak_ingestion", "record_deduplication", "credential_exposure_scoring", "pivot_generation"],
                    worker_roles=["breach-worker", "dedupe-worker"],
                    graph_capabilities=["breach_nodes", "exposure_relationships"],
                    tool_wrappers=["breach_correlation", "credential_intelligence"],
                    scheduler_hooks=["delta_sync", "severity_escalation"],
                ),
                EngineSpec(
                    name="rtf-scraper-engine",
                    category="architecture",
                    description="Proxy-aware scraping engine for search, websites, and social artifacts.",
                    module_path="architecture/rtf_scraper_engine",
                    cli_alias="scraper",
                    queue="queue:scrape",
                    dependencies=["rtf-core", "rtf-osint-engine"],
                    task_pipeline=["request_plan", "distributed_fetch", "artifact_parse", "cache_publish"],
                    worker_roles=["fetch-worker", "parser-worker"],
                    graph_capabilities=["artifact_provenance"],
                    tool_wrappers=["web_search_scraper", "email_harvest", "tech_stack_fingerprinter"],
                    scheduler_hooks=["rate_limit_budget", "proxy_rotation"],
                ),
                EngineSpec(
                    name="rtf-casm-engine",
                    category="architecture",
                    description="Continuous attack surface management engine with discovery and drift tracking.",
                    module_path="architecture/rtf_casm_engine",
                    cli_alias="casm",
                    queue="queue:casm",
                    dependencies=["rtf-core", "rtf-graph-engine", "rtf-monitoring-engine"],
                    task_pipeline=["asset_seed", "surface_discovery", "exposure_scoring", "drift_detection"],
                    worker_roles=["surface-worker", "drift-worker"],
                    graph_capabilities=["asset_inventory", "service_exposure_edges"],
                    tool_wrappers=["casm_pipeline", "subdomain_enum", "port_scan"],
                    scheduler_hooks=["continuous_scan", "snapshot_diff"],
                ),
                EngineSpec(
                    name="rtf-credential-engine",
                    category="architecture",
                    description="Credential attack coordination engine for sprays, cracking, and reuse analysis.",
                    module_path="architecture/rtf_credential_engine",
                    cli_alias="credential",
                    queue="queue:credential",
                    dependencies=["rtf-breach-engine", "rtf-core"],
                    task_pipeline=["candidate_generation", "reuse_analysis", "distributed_cracking", "result_enrichment"],
                    worker_roles=["spray-worker", "cracker-worker"],
                    graph_capabilities=["credential_nodes", "reuse_edges"],
                    tool_wrappers=["credential_intelligence", "credential_reuse_analyzer", "hash_crack"],
                    scheduler_hooks=["worker_sharding", "cooldown_windows"],
                ),
                EngineSpec(
                    name="rtf-automation-engine",
                    category="architecture",
                    description="Automation engine for reusable async task pipelines and workflow templates.",
                    module_path="architecture/rtf_automation_engine",
                    cli_alias="automation",
                    queue="queue:automation",
                    dependencies=["rtf-core", "rtf-monitoring-engine"],
                    task_pipeline=["template_expand", "pipeline_compile", "worker_dispatch", "result_reduce"],
                    worker_roles=["pipeline-worker", "template-worker"],
                    graph_capabilities=["workflow_lineage"],
                    tool_wrappers=["workflow_engine", "pipeline_v2", "advanced_pipeline"],
                    scheduler_hooks=["cron_bridge", "dependency_graph"],
                ),
                EngineSpec(
                    name="rtf-monitoring-engine",
                    category="architecture",
                    description="Observability engine for metrics, worker health, and execution telemetry.",
                    module_path="architecture/rtf_monitoring_engine",
                    cli_alias="monitoring",
                    queue="queue:metrics",
                    dependencies=["rtf-core", "rtf-automation-engine"],
                    task_pipeline=["telemetry_ingest", "health_aggregation", "slo_evaluation", "alert_projection"],
                    worker_roles=["metrics-worker", "alert-worker"],
                    graph_capabilities=["service_health_overlays"],
                    tool_wrappers=["scheduler", "tool_registry", "report_engine"],
                    scheduler_hooks=["heartbeat", "queue_depth_sampling"],
                ),
                EngineSpec(
                    name="rtf-report-engine",
                    category="architecture",
                    description="Reporting engine for graph-backed findings, executive summaries, and artifact bundles.",
                    module_path="architecture/rtf_report_engine",
                    cli_alias="report",
                    queue="queue:report",
                    dependencies=["rtf-graph-engine", "rtf-ai-engine", "rtf-monitoring-engine"],
                    task_pipeline=["finding_aggregation", "timeline_render", "graph_embed", "report_emit"],
                    worker_roles=["report-worker", "render-worker"],
                    graph_capabilities=["graph_export", "timeline_rendering"],
                    tool_wrappers=["report_engine", "json_reporter", "pdf_reporter"],
                    scheduler_hooks=["scheduled_exports", "artifact_retention"],
                ),
            ]
        }

    def list(self) -> List[EngineSpec]:
        return sorted(self._engines.values(), key=lambda item: item.name)

    def get(self, name_or_alias: str) -> EngineSpec:
        needle = name_or_alias.strip().lower()
        for spec in self._engines.values():
            if needle in {spec.name.lower(), spec.cli_alias.lower(), spec.module_path.split("/")[-1].lower()}:
                return spec
        raise KeyError(f"Unknown engine: {name_or_alias}")

    def architecture_map(self) -> Dict[str, Any]:
        return {
            "engines": [spec.to_dict() for spec in self.list()],
            "queues": {spec.name: spec.queue for spec in self.list()},
            "distributed_workers": {spec.name: list(spec.worker_roles) for spec in self.list()},
            "graph_intelligence": {spec.name: list(spec.graph_capabilities) for spec in self.list()},
            "tool_wrappers": {spec.name: list(spec.tool_wrappers) for spec in self.list()},
            "scheduler": {spec.name: list(spec.scheduler_hooks) for spec in self.list()},
        }


engine_registry = EngineRegistry()
