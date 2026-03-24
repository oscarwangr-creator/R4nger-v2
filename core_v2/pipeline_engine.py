import yaml
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from core_v2.tool_registry import ToolRegistry

class PipelineStage:
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.tools = config.get('tools', [])
        self.transformations = config.get('transformations', [])
        self.outputs = config.get('outputs', [])
        self.parallel = config.get('parallel', False)
        self.timeout = config.get('timeout', 3600)
        self.fallback_tools = config.get('fallback_tools', [])

class PipelineEngine:
    def __init__(self, registry: ToolRegistry, pipelines_path: str = 'pipelines_v2'):
        self.registry = registry
        self.pipelines_path = Path(pipelines_path)
        self.logger = logging.getLogger(__name__)
        self.pipelines = {}
        self.execution_history = []

    def load_pipeline(self, pipeline_name: str) -> Optional[Dict[str, Any]]:
        pipeline_file = self.pipelines_path / f"{pipeline_name}.yaml"
        if not pipeline_file.exists():
            self.logger.error(f"Pipeline file not found: {pipeline_file}")
            return None
        try:
            with open(pipeline_file, 'r') as f:
                pipeline_config = yaml.safe_load(f)
                self.pipelines[pipeline_name] = pipeline_config
                self.logger.info(f"Loaded pipeline: {pipeline_name}")
                return pipeline_config
        except Exception as e:
            self.logger.error(f"Error loading pipeline: {str(e)}")
            return None

    def execute_pipeline(self, pipeline_name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            pipeline = self.load_pipeline(pipeline_name)
            if not pipeline:
                return {"status": "error", "message": f"Pipeline {pipeline_name} not found"}
            self.logger.info(f"Starting pipeline execution: {pipeline_name}")
            execution_result = { 
                'pipeline': pipeline_name,
                'start_time': datetime.now().isoformat(),
                'stages': [],
                'status': 'running',
                'errors': []
            }
            stages = pipeline.get('stages', [])
            current_data = input_data
            for stage_config in stages:
                stage_name = stage_config.get('name', 'unnamed')
                stage_result = self._execute_stage(stage_config, current_data)
                if stage_result.get('status') == 'error' and not stage_config.get('continue_on_error', True):
                    execution_result['status'] = 'failed'
                    execution_result['errors'].append(stage_result.get('error', 'Unknown error'))
                    break
                execution_result['stages'].append({'name': stage_name, 'result': stage_result})
                current_data = stage_result.get('output', current_data)
            execution_result['status'] = 'completed'
            execution_result['end_time'] = datetime.now().isoformat()
            execution_result['final_output'] = current_data
            self.execution_history.append(execution_result)
            return execution_result
        except Exception as e:
            self.logger.error(f"Pipeline execution error: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _execute_stage(self, stage_config: Dict[str, Any], input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            stage_name = stage_config.get('name', 'unnamed')
            tools = stage_config.get('tools', [])
            parallel = stage_config.get('parallel', False)
            results = []
            if parallel:
                results = self._execute_parallel(tools, input_data)
            else:
                results = self._execute_sequential(tools, input_data)
            return { 
                'status': 'completed', 
                'stage': stage_name,
                'tool_results': results,
                'output': {'results': results, 'input': input_data}
            }
        except Exception as e:
            self.logger.error(f"Stage execution error: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _execute_sequential(self, tools: List[str], input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        for tool_name in tools:
            try:
                tool_class = self.registry.get_tool(tool_name)
                if not tool_class:
                    self.logger.warning(f"Tool not found: {tool_name}")
                    continue
                tool = tool_class({'target': input_data.get('target', 'unknown')})
                result = tool.execute_with_timeout()
                results.append({'tool': tool_name, 'result': result})
            except Exception as e:
                self.logger.error(f"Tool {tool_name} execution error: {str(e)}")
                results.append({'tool': tool_name, 'error': str(e)})
        return results

    def _execute_parallel(self, tools: List[str], input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            for tool_name in tools:
                try:
                    tool_class = self.registry.get_tool(tool_name)
                    if tool_class:
                        tool = tool_class({'target': input_data.get('target', 'unknown')})
                        futures[executor.submit(tool.execute_with_timeout)] = tool_name
                except Exception as e:
                    self.logger.error(f"Error submitting tool {tool_name}: {str(e)}")
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append({'tool': futures[future], 'result': result})
            except Exception as e:
                self.logger.error(f"Parallel execution error: {str(e)}")
                results.append({'tool': futures[future], 'error': str(e)})
        return results

    def get_execution_history(self) -> List[Dict[str, Any]]:
        return self.execution_history