from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from intelligence_os.pipeline.engine import PipelineEngine
from intelligence_os.tooling.catalog import load_workflow_mappings


@dataclass
class WorkflowDefinition:
    name: str
    description: str
    pipelines: List[str]
    triggers: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    family: str = 'custom'


class WorkflowEngine:
    def __init__(self, pipeline_engine: PipelineEngine | None = None, pipeline_dir: str | Path | None = None) -> None:
        self.pipeline_engine = pipeline_engine or PipelineEngine()
        self.pipeline_dir = Path(pipeline_dir or Path(__file__).resolve().parents[1] / 'pipelines')
        generated = {
            entry['name']: WorkflowDefinition(
                name=entry['name'],
                description=entry['description'],
                pipelines=[f"{pipeline}.yaml" if not pipeline.endswith('.yaml') else pipeline for pipeline in entry['pipelines']],
                triggers=entry.get('triggers', ['manual', 'scheduled']),
                outputs=entry.get('outputs', ['graph', 'report', 'telemetry']),
                family=entry.get('family', 'generated'),
            )
            for entry in load_workflow_mappings()
        }
        builtin = {
            'target_profiling': WorkflowDefinition('target_profiling', 'Profile a target across identity, email, domain, and social pivots.', ['identity_intelligence_pipeline.yaml', 'email_intelligence_pipeline.yaml', 'domain_intelligence_pipeline.yaml'], ['new_person', 'new_username'], ['profile', 'graph', 'report'], 'identity'),
            'identity_investigation': WorkflowDefinition('identity_investigation', 'Pivot recursively from username to accounts, emails, domains, and breaches.', ['username_intelligence_pipeline.yaml', 'email_intelligence_pipeline.yaml', 'breach_intelligence_pipeline.yaml'], ['new_username'], ['identity_graph', 'risk_score'], 'identity'),
            'infrastructure_recon': WorkflowDefinition('infrastructure_recon', 'Map passive attack surface, services, and exposure.', ['domain_intelligence_pipeline.yaml', 'infrastructure_intelligence_pipeline.yaml', 'attack_surface_intelligence_pipeline.yaml'], ['new_domain'], ['service_map', 'exposure_report'], 'infrastructure'),
            'breach_monitoring': WorkflowDefinition('breach_monitoring', 'Continuously monitor breach, credential, and leak exposure.', ['breach_intelligence_pipeline.yaml', 'credential_intelligence_pipeline.yaml'], ['new_email', 'new_domain'], ['alerts', 'breach_summary'], 'exposure'),
            'social_network_mapping': WorkflowDefinition('social_network_mapping', 'Map social and identity signals for people and personas.', ['social_network_intelligence_pipeline.yaml', 'username_intelligence_pipeline.yaml'], ['new_person', 'new_username'], ['network_graph', 'accounts'], 'social'),
            'organization_due_diligence': WorkflowDefinition('organization_due_diligence', 'Chain organization, vendor, supply-chain, and infrastructure pipelines for analyst due diligence.', ['organization_profiling_pipeline.yaml', 'employee_enumeration_pipeline.yaml', 'vendor_attack_surface_pipeline.yaml', 'supply_chain_risk_pipeline.yaml'], ['new_organization', 'scheduled'], ['organization_profile', 'vendor_graph', 'risk_summary'], 'organization'),
            'threat_exposure_triage': WorkflowDefinition('threat_exposure_triage', 'Triages leaks, typosquats, and threat-actor references for a tracked target.', ['dark_web_exposure_pipeline.yaml', 'typosquat_monitoring_pipeline.yaml', 'threat_actor_profiling_pipeline.yaml'], ['new_keyword', 'new_domain'], ['alerts', 'actor_profile', 'report'], 'exposure'),
        }
        self.workflows: Dict[str, WorkflowDefinition] = {**builtin, **generated}

    def list_workflows(self) -> List[Dict[str, object]]:
        return [
            {
                'name': workflow.name,
                'description': workflow.description,
                'pipelines': workflow.pipelines,
                'triggers': workflow.triggers,
                'outputs': workflow.outputs,
                'family': workflow.family,
            }
            for workflow in self.workflows.values()
        ]

    def run_workflow(self, name: str, seed: Dict[str, str]) -> Dict[str, object]:
        workflow = self.workflows[name]
        executions = []
        for pipeline_file in workflow.pipelines:
            definition = self.pipeline_engine.load_pipeline(self.pipeline_dir / pipeline_file)
            executions.append(self.pipeline_engine.execute_pipeline(definition, seed))
        return {'workflow': workflow, 'executions': executions, 'families': sorted({workflow.family for workflow in self.workflows.values()})}
