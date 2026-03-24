#!/usr/bin/env python3
"""R4nger V3 single entrypoint CLI."""
from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from api.app import create_app
from core.pipeline_engine import PipelineEngine
from core.workflow_engine import WorkflowEngine
from modules import build_discovered_module_registry


def _build_runtime() -> tuple[Dict[str, Any], PipelineEngine, WorkflowEngine]:
    module_registry = build_discovered_module_registry()
    pipeline_engine = PipelineEngine(module_registry=module_registry)
    workflow_engine = WorkflowEngine(pipeline_engine=pipeline_engine)
    return module_registry, pipeline_engine, workflow_engine


def _print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def cmd_modules(args: argparse.Namespace) -> int:
    module_registry, _, _ = _build_runtime()
    if args.action == "list":
        _print_json([
            {
                "name": module.metadata.name,
                "category": module.metadata.category,
                "description": module.metadata.description,
            }
            for module in module_registry.values()
        ])
        return 0

    module = module_registry.get(args.name)
    if not module:
        print(f"Module not found: {args.name}")
        return 1

    payload = {"target": args.target}
    if args.payload:
        payload.update(json.loads(args.payload))

    _print_json(module.run(payload))
    return 0


def cmd_pipelines(args: argparse.Namespace) -> int:
    _, pipeline_engine, _ = _build_runtime()
    if args.action == "list":
        _print_json(pipeline_engine.list_pipelines())
        return 0

    payload = {"target": args.target}
    if args.payload:
        payload.update(json.loads(args.payload))

    _print_json(
        pipeline_engine.execute(
            name=args.name,
            payload=payload,
            parallel=args.parallel,
            max_workers=args.max_workers,
        )
    )
    return 0



def cmd_workflows(args: argparse.Namespace) -> int:
    _, _, workflow_engine = _build_runtime()
    if args.action == "list":
        _print_json(workflow_engine.list_workflows())
        return 0

    payload = {"target": args.target}
    if args.payload:
        payload.update(json.loads(args.payload))

    _print_json(workflow_engine.execute(name=args.name, payload=payload))
    return 0

def cmd_api(args: argparse.Namespace) -> int:
    app = create_app()
    app.run(host=args.host, port=args.port, debug=False)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="r4ng3r", description="R4nger V3 framework entrypoint")
    subparsers = parser.add_subparsers(dest="command", required=True)

    api = subparsers.add_parser("api", help="Start API and dashboard")
    api.add_argument("--host", default="0.0.0.0")
    api.add_argument("--port", default=5000, type=int)
    api.set_defaults(func=cmd_api)

    modules = subparsers.add_parser("modules", help="List or execute modules")
    modules_sub = modules.add_subparsers(dest="action", required=True)

    modules_sub.add_parser("list", help="List modules")

    module_run = modules_sub.add_parser("run", help="Run a module")
    module_run.add_argument("name")
    module_run.add_argument("--target", required=True)
    module_run.add_argument("--payload", help="JSON object with additional payload")
    modules.set_defaults(func=cmd_modules)

    pipelines = subparsers.add_parser("pipelines", help="List or execute pipelines")
    pipelines_sub = pipelines.add_subparsers(dest="action", required=True)

    pipelines_sub.add_parser("list", help="List pipelines")

    pipeline_run = pipelines_sub.add_parser("run", help="Run a pipeline")
    pipeline_run.add_argument("name")
    pipeline_run.add_argument("--target", required=True)
    pipeline_run.add_argument("--parallel", action="store_true")
    pipeline_run.add_argument("--max-workers", type=int, default=4)
    pipeline_run.add_argument("--payload", help="JSON object with additional payload")
    pipelines.set_defaults(func=cmd_pipelines)

    workflows = subparsers.add_parser("workflows", help="List or execute workflows")
    workflows_sub = workflows.add_subparsers(dest="action", required=True)

    workflows_sub.add_parser("list", help="List workflows")

    workflow_run = workflows_sub.add_parser("run", help="Run a workflow")
    workflow_run.add_argument("name")
    workflow_run.add_argument("--target", required=True)
    workflow_run.add_argument("--payload", help="JSON object with additional payload")
    workflows.set_defaults(func=cmd_workflows)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
