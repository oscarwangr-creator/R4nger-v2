from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class NexusService:
    name: str
    role: str
    transport: str
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role,
            "transport": self.transport,
            "enabled": self.enabled,
            "metadata": self.metadata,
        }


class NexusTopology:
    def __init__(self) -> None:
        self.services = [
            NexusService("osint-pipeline", "intelligence_collection", "redis"),
            NexusService("attack-surface-pipeline", "surface_monitoring", "rabbitmq"),
            NexusService("credential-pipeline", "credential_intelligence", "rabbitmq"),
            NexusService("exploitation-pipeline", "validation_execution", "redis"),
            NexusService("neo4j-correlation", "identity_resolution", "bolt", metadata={"database": "neo4j"}),
        ]

    def describe(self) -> Dict[str, Any]:
        services = [service.to_dict() for service in self.services]
        return {
            "architecture": "nexus",
            "orchestrators": ["docker", "kubernetes"],
            "message_brokers": ["redis", "rabbitmq"],
            "services": services,
            "data_flows": [
                {"from": "osint-pipeline", "to": "neo4j-correlation", "purpose": "identity enrichment"},
                {"from": "attack-surface-pipeline", "to": "credential-pipeline", "purpose": "exposed asset to credential pivot"},
                {"from": "credential-pipeline", "to": "exploitation-pipeline", "purpose": "validated credential handoff"},
            ],
        }
