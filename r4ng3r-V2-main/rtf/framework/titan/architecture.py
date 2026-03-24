from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

from framework.engines import engine_registry


@dataclass
class TitanService:
    name: str
    purpose: str
    dependencies: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    pipelines: List[str] = field(default_factory=list)
    storage: List[str] = field(default_factory=list)
    scalability: str = "horizontal"


@dataclass
class TitanInfrastructure:
    message_bus: str = "RabbitMQ"
    cache: str = "Redis"
    graph_db: str = "Neo4j"
    search: str = "ElasticSearch"
    object_store: str = "MinIO"
    api: str = "FastAPI"
    metrics: List[str] = field(default_factory=lambda: ["Prometheus", "Grafana"])
    orchestrators: List[str] = field(default_factory=lambda: ["Docker", "Kubernetes"])


class TitanArchitecture:
    def __init__(self) -> None:
        self.infrastructure = TitanInfrastructure()
        self.services: List[TitanService] = self._build_services()

    def _build_services(self) -> List[TitanService]:
        service_interfaces = {
            "rtf-core": ["cli", "api", "scheduler"],
            "rtf-graph-engine": ["queue:graph", "bolt"],
            "rtf-monitoring-engine": ["queue:metrics", "prometheus"],
            "rtf-report-engine": ["queue:report", "http"],
        }
        storage_overrides = {
            "rtf-core": ["Redis"],
            "rtf-osint-engine": ["ElasticSearch", "MinIO"],
            "rtf-socmint-engine": ["Neo4j", "ElasticSearch"],
            "rtf-graph-engine": ["Neo4j"],
            "rtf-ai-engine": ["Redis", "MinIO"],
            "rtf-breach-engine": ["ElasticSearch", "MinIO", "Neo4j"],
            "rtf-scraper-engine": ["MinIO"],
            "rtf-casm-engine": ["ElasticSearch", "Neo4j"],
            "rtf-credential-engine": ["MinIO", "ElasticSearch"],
            "rtf-automation-engine": ["Redis"],
            "rtf-monitoring-engine": ["ElasticSearch"],
            "rtf-report-engine": ["MinIO"],
        }
        services = []
        for spec in engine_registry.list():
            services.append(
                TitanService(
                    name=spec.name,
                    purpose=spec.description,
                    dependencies=list(spec.dependencies),
                    interfaces=service_interfaces.get(spec.name, [spec.queue]),
                    pipelines=list(spec.task_pipeline),
                    storage=storage_overrides.get(spec.name, [self.infrastructure.object_store]),
                )
            )
        services.append(
            TitanService(
                "rtf-worker-cluster",
                "Distributed worker execution for compute-heavy jobs",
                [self.infrastructure.message_bus, self.infrastructure.cache],
                ["queue:worker"],
                ["parallel_jobs", "fanout_execution"],
                [self.infrastructure.cache, self.infrastructure.object_store],
            )
        )
        services.append(
            TitanService(
                "rtf-ingestion-engine",
                "Normalizes evidence into events, entities, and artifacts",
                [self.infrastructure.object_store, self.infrastructure.search, self.infrastructure.graph_db],
                ["queue:ingestion"],
                ["normalization", "evidence_tagging", "artifact_indexing"],
                [self.infrastructure.search, self.infrastructure.object_store, self.infrastructure.graph_db],
            )
        )
        return services

    def dependency_map(self) -> Dict[str, List[str]]:
        return {service.name: list(service.dependencies) for service in self.services}

    def service_catalog(self) -> Dict[str, Dict[str, Any]]:
        return {
            service.name: {
                "purpose": service.purpose,
                "interfaces": list(service.interfaces),
                "pipelines": list(service.pipelines),
                "storage": list(service.storage),
                "scalability": service.scalability,
            }
            for service in self.services
        }

    def extension_points(self) -> Dict[str, List[str]]:
        return {
            "cli": ["Add titan and engine subcommands without impacting legacy commands"],
            "api": ["Expose distributed service topology and queue status endpoints"],
            "dashboard": ["Add graph explorer, workflow monitor, live logs, and service health cards"],
            "workflow_engine": ["Register engine-driven pipelines through the existing workflow registry"],
            "module_system": ["Wrap architecture engines as BaseModule-compatible modules"],
            "reporting": ["Feed graph, AI, and evidence timelines into existing reporting engine"],
            "scheduler": ["Bridge local async jobs to queue-backed worker execution"],
            "configuration": ["Layer service topology and queue settings over current YAML/env config"],
        }

    def architecture_map(self) -> Dict[str, Any]:
        return {
            "entrypoints": {
                "cli": ["rtf console", "rtf module", "rtf workflow", "rtf titan", "rtf engine"],
                "api": ["/health", "/stats", "/modules", "/workflows", "/graph/schema", "/titan/manifest"],
                "dashboard": ["investigation_manager", "graph_explorer", "module_execution_panel", "report_viewer"],
            },
            "pipelines": {
                "legacy": ["full_recon", "identity_fusion", "cloud_audit", "web_audit"],
                "omega": [
                    "socmint_15_stage",
                    "identity_resolution",
                    "global_intelligence_graph",
                    "recursive_pivot_engine",
                    "distributed_reporting",
                    "engine_mesh_orchestration",
                ],
            },
            "data_plane": {
                "queueing": [self.infrastructure.message_bus, self.infrastructure.cache],
                "storage": [self.infrastructure.graph_db, self.infrastructure.search, self.infrastructure.object_store],
                "observability": list(self.infrastructure.metrics),
            },
            "services": self.service_catalog(),
            "engine_mesh": engine_registry.architecture_map(),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": "RTF TITAN OMEGA",
            "version": "4.0.0-omega",
            "infrastructure": asdict(self.infrastructure),
            "services": [asdict(service) for service in self.services],
            "dependency_map": self.dependency_map(),
            "service_catalog": self.service_catalog(),
            "architecture_map": self.architecture_map(),
            "extension_points": self.extension_points(),
        }


def build_titan_manifest() -> Dict[str, Any]:
    return TitanArchitecture().to_dict()
