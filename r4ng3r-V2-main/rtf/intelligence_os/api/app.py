from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException

from intelligence_os.analysis.validator import FrameworkValidator
from intelligence_os.architecture import ARCHITECTURE_LAYERS
from intelligence_os.automation.autonomous import AutonomousInvestigationEngine
from intelligence_os.graph.schema import GRAPH_SCHEMA
from intelligence_os.pipeline.engine import PipelineEngine
from intelligence_os.tooling.registry import registry
from intelligence_os.workflow.engine import WorkflowEngine



def create_app() -> FastAPI:
    app = FastAPI(title='Intelligence OS API', version='1.2.0')
    pipeline_engine = PipelineEngine()
    workflow_engine = WorkflowEngine(pipeline_engine=pipeline_engine)
    autonomous_engine = AutonomousInvestigationEngine(pipeline_engine=pipeline_engine)
    validator = FrameworkValidator()
    pipeline_dir = Path(__file__).resolve().parents[1] / 'pipelines'

    @app.get('/intelligence-os/health')
    def health():
        summary = registry.summary()
        validation = validator.validate()
        return {
            'status': 'ok',
            'pipelines': len(list(pipeline_dir.glob('*.yaml'))),
            'tools': summary['total_tools'],
            'module_packs': validation.metrics['module_packs'],
            'validation_status': validation.status,
        }

    @app.get('/intelligence-os/architecture')
    def architecture():
        return {k: {'name': v.name, 'responsibilities': v.responsibilities} for k, v in ARCHITECTURE_LAYERS.items()}

    @app.get('/intelligence-os/analysis')
    def analysis():
        return registry.framework_analysis()

    @app.get('/intelligence-os/validation')
    def validation():
        return validator.validate().to_dict()

    @app.get('/intelligence-os/tools')
    def tools():
        return {'summary': registry.summary(), 'sample': [t.__dict__ for t in registry.list_tools()[:50]]}

    @app.get('/intelligence-os/modules')
    def modules():
        return {'modules': registry.list_module_mappings()}

    @app.get('/intelligence-os/pipelines')
    def pipelines():
        return {'pipelines': registry.list_pipeline_mappings()}

    @app.get('/intelligence-os/workflows')
    def workflows():
        return {'workflows': workflow_engine.list_workflows()}

    @app.get('/intelligence-os/investigations/templates')
    def templates():
        return {
            'seed_types': ['username', 'email', 'phone', 'domain', 'organization', 'repository', 'location'],
            'workflow_families': sorted({wf['family'] for wf in workflow_engine.list_workflows()}),
            'report_formats': ['json', 'csv', 'xlsx', 'pdf', 'html', 'mtgl'],
        }

    @app.post('/intelligence-os/pipelines/{pipeline_name}/run')
    def run_pipeline(pipeline_name: str, seed: dict):
        pipeline_path = pipeline_dir / f'{pipeline_name}.yaml'
        if not pipeline_path.exists():
            raise HTTPException(status_code=404, detail='pipeline not found')
        definition = pipeline_engine.load_pipeline(pipeline_path)
        result = pipeline_engine.execute_pipeline(definition, seed)
        return {
            'pipeline': result.pipeline,
            'success': result.success,
            'modules': result.executed_modules,
            'graph_writes': result.graph_writes,
            'risk_score': result.context['risk_score'],
            'entity_summary': result.context['entity_summary'],
            'recommended_next_steps': result.context['recommended_next_steps'],
            'stage_results': result.context['stage_results'],
        }

    @app.post('/intelligence-os/workflows/{workflow_name}/run')
    def run_workflow(workflow_name: str, seed: dict):
        if workflow_name not in workflow_engine.workflows:
            raise HTTPException(status_code=404, detail='workflow not found')
        result = workflow_engine.run_workflow(workflow_name, seed)
        return {
            'workflow': workflow_name,
            'executions': [{'pipeline': r.pipeline, 'success': r.success, 'risk_score': r.context['risk_score']} for r in result['executions']],
            'families': result['families'],
        }

    @app.post('/intelligence-os/autonomous/run')
    def run_autonomous(seed: dict, max_depth: int = 2):
        result = autonomous_engine.investigate(seed, max_depth=max_depth)
        return {'visited': result['visited'], 'runs': len(result['runs'])}

    @app.get('/intelligence-os/graph/schema')
    def graph_schema():
        return GRAPH_SCHEMA

    return app
