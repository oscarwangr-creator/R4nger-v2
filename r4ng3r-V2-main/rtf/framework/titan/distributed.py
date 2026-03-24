from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from framework.automation.pipeline_v2 import PipelineEngineV2, PipelineStepV2
from framework.titan.architecture import build_titan_manifest
from framework.titan.socmint_pipeline import TitanSOCMINTPipeline


@dataclass
class QueueMessage:
    topic: str
    payload: Dict[str, Any]


@dataclass
class ServiceHealth:
    name: str
    status: str = "ready"
    queue_depth: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class TitanMessageBus:
    def __init__(self) -> None:
        self.messages: List[QueueMessage] = []

    async def publish(self, topic: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.messages.append(QueueMessage(topic, payload))
        return {"topic": topic, "queued": len(self.messages)}

    def drain(self, topic: Optional[str] = None) -> List[Dict[str, Any]]:
        selected = [m for m in self.messages if topic in (None, m.topic)]
        self.messages = [m for m in self.messages if m not in selected]
        return [{"topic": m.topic, "payload": m.payload} for m in selected]

    def snapshot(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for message in self.messages:
            counts[message.topic] = counts.get(message.topic, 0) + 1
        return counts


class TitanOrchestrator:
    def __init__(self) -> None:
        self.bus = TitanMessageBus()
        self.pipeline = TitanSOCMINTPipeline()

    def health(self) -> Dict[str, Any]:
        manifest = build_titan_manifest()
        queue_counts = self.bus.snapshot()
        services = []
        for service in manifest["services"]:
            suffix = service["name"].split("rtf-")[-1].replace("-engine", "")
            depth = sum(count for topic, count in queue_counts.items() if suffix in topic or topic.endswith(suffix))
            services.append(ServiceHealth(name=service["name"], queue_depth=depth, metadata={"interfaces": service.get("interfaces", [])}))
        return {
            "architecture": manifest["name"],
            "version": manifest["version"],
            "service_count": len(services),
            "services": [service.__dict__ for service in services],
            "queued_messages": len(self.bus.messages),
            "queue_topics": queue_counts,
        }

    async def run_investigation(self, seed: Dict[str, Any]) -> Dict[str, Any]:
        engine = PipelineEngineV2(concurrency=6)
        engine.add_step(PipelineStepV2("queue-seed", lambda ctx: self.bus.publish("ingestion", {"seed": seed})))
        engine.add_step(PipelineStepV2("queue-osint", lambda ctx: self.bus.publish("osint", {"seed_keys": sorted(seed.keys())})))
        engine.add_step(PipelineStepV2("socmint", lambda ctx: asyncio.to_thread(self.pipeline.run, seed)))
        engine.add_step(PipelineStepV2("queue-graph", lambda ctx: self.bus.publish("graph", {"nodes": len(ctx.get("graph", {}).get("nodes", []))})))
        engine.add_step(PipelineStepV2("queue-report", lambda ctx: self.bus.publish("report", {"risk": ctx.get("identity_resolution", {}).get("risk_score", 0)})))
        result = await engine.run()
        return {
            "success": result.success,
            "context": result.context,
            "history": result.history,
            "queues": self.bus.drain(),
            "health": self.health(),
        }
