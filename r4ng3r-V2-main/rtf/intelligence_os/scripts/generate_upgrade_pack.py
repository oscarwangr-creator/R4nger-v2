from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "manifests" / "framework_manifest.json"
PIPELINES_DIR = ROOT / "pipelines"
PLANNING_DIR = ROOT / "planning"
PROMPT_PATH = PLANNING_DIR / "CODEX_AUTHORIZED_UPGRADE_BRIEF.md"
WORKFLOW_MAP_PATH = PLANNING_DIR / "workflow_mappings.yaml"
EXAMPLES_PATH = PLANNING_DIR / "example_investigations.yaml"

SAMPLE_INPUTS = {
    "username": "analyst_seed",
    "email": "contact@example.org",
    "phone": "+1-202-555-0199",
    "real_name": "Jordan Example",
    "domain": "example.org",
    "organization": "Example Org",
    "company": "Example Org",
    "keyword": "example initiative",
    "keywords": ["example initiative", "executive update"],
    "ip": "203.0.113.10",
    "ip_range": "203.0.113.0/24",
    "repo": "https://github.com/example/project",
    "repository": "https://github.com/example/project",
    "profile_url": "https://social.example/analyst_seed",
    "platform": "mastodon",
    "location": "Washington, DC",
    "document": "example-brief.pdf",
    "wallet": "bc1qexamplewalletaddress000",
    "package": "example-package",
    "image": "example-photo.jpg",
    "video": "example-video.mp4",
    "facility": "Example Campus",
    "event": "Example Summit",
    "certificate": "example.org",
}

MODULE_STRUCTURE = """modules/{module_name}/\n├── module.py\n├── config.yaml\n├── requirements.txt\n└── README.md"""


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text())


def load_pipelines() -> list[dict[str, Any]]:
    pipelines: list[dict[str, Any]] = []
    for path in sorted(PIPELINES_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text())
        data["__path__"] = path
        pipelines.append(data)
    return pipelines


def pipeline_example_input(input_types: list[str]) -> dict[str, Any]:
    example: dict[str, Any] = {}
    for item in input_types:
        example[item] = SAMPLE_INPUTS.get(item, f"sample_{item}")
    return example


def build_workflow_map(manifest: dict[str, Any], pipelines: list[dict[str, Any]]) -> dict[str, Any]:
    module_lookup = {module["name"]: module for module in manifest.get("modules", [])}
    tools_by_pipeline: dict[str, list[str]] = defaultdict(list)
    modules_by_pipeline: dict[str, list[str]] = defaultdict(list)

    for pipeline in pipelines:
        name = pipeline["name"]
        for stage in pipeline.get("stages", []):
            module_name = stage.get("module")
            tool_name = stage.get("tool")
            if module_name and module_name not in modules_by_pipeline[name]:
                modules_by_pipeline[name].append(module_name)
            if tool_name and tool_name not in tools_by_pipeline[name]:
                tools_by_pipeline[name].append(tool_name)

    workflows = []
    for workflow in manifest.get("workflows", []):
        linked_pipelines = workflow.get("pipelines", [])
        linked_modules: list[str] = []
        linked_tools: list[str] = []
        for pipeline_name in linked_pipelines:
            for module_name in modules_by_pipeline.get(pipeline_name, []):
                if module_name not in linked_modules:
                    linked_modules.append(module_name)
            for tool_name in tools_by_pipeline.get(pipeline_name, []):
                if tool_name not in linked_tools:
                    linked_tools.append(tool_name)
        workflows.append(
            {
                "name": workflow["name"],
                "description": workflow.get("description", ""),
                "pipelines": linked_pipelines,
                "modules": linked_modules,
                "tools": linked_tools,
            }
        )

    orphan_pipelines = []
    for pipeline in pipelines:
        name = pipeline["name"]
        if not any(name in workflow.get("pipelines", []) for workflow in manifest.get("workflows", [])):
            orphan_pipelines.append(
                {
                    "name": name,
                    "modules": modules_by_pipeline.get(name, []),
                    "tools": tools_by_pipeline.get(name, []),
                    "suggested_workflow": f"{name}_workflow",
                }
            )

    return {
        "summary": {
            "modules": len(manifest.get("modules", [])),
            "tools": len(manifest.get("tools", [])),
            "pipelines": len(pipelines),
            "workflows": len(manifest.get("workflows", [])),
        },
        "workflows": workflows,
        "pipeline_index": [
            {
                "name": pipeline["name"],
                "path": str(pipeline["__path__"].relative_to(ROOT)),
                "input_types": pipeline.get("input", {}).get("types", []),
                "modules": modules_by_pipeline.get(pipeline["name"], []),
                "tools": tools_by_pipeline.get(pipeline["name"], []),
                "recursive_pivoting": pipeline.get("recursive_pivoting", False),
                "ai_assisted": pipeline.get("ai_assisted", False),
            }
            for pipeline in pipelines
        ],
        "orphan_pipelines": orphan_pipelines,
        "module_index": [
            {
                "name": name,
                "category": module.get("category"),
                "pipelines": module.get("pipelines", []),
                "tools": module.get("tools", []),
            }
            for name, module in sorted(module_lookup.items())
        ],
    }


def build_examples(pipelines: list[dict[str, Any]]) -> dict[str, Any]:
    examples = []
    for pipeline in pipelines:
        input_types = pipeline.get("input", {}).get("types", [])
        example_input = pipeline_example_input(input_types)
        outputs = pipeline.get("output", {}).get("formats", ["json"])
        examples.append(
            {
                "pipeline": pipeline["name"],
                "path": str(pipeline["__path__"].relative_to(ROOT)),
                "sample_input": example_input,
                "expected_artifacts": [
                    f"reports/{pipeline['name']}.{fmt}" for fmt in outputs
                ],
                "entity_graph_nodes": [
                    {"type": input_type, "value": value}
                    for input_type, value in example_input.items()
                ],
                "analyst_summary": (
                    f"{pipeline['name']} starts from {', '.join(input_types) or 'seed data'} and "
                    "produces pivot-ready evidence, graph updates, and multi-format reports."
                ),
                "next_steps": pipeline.get("output", {}).get(
                    "next_steps",
                    ["review correlations", "queue follow-on pivots", "publish report"],
                ),
            }
        )
    return {"example_investigations": examples}


def build_prompt(manifest: dict[str, Any], pipelines: list[dict[str, Any]]) -> str:
    categories = defaultdict(int)
    for module in manifest.get("modules", []):
        categories[module.get("category", "uncategorized")] += 1

    tool_categories = defaultdict(int)
    for tool in manifest.get("tools", []):
        tool_categories[tool.get("category", "uncategorized")] += 1

    category_lines = "\n".join(
        f"- {category}: {count} modules" for category, count in sorted(categories.items())
    )
    tool_category_lines = "\n".join(
        f"- {category}: {count} tools" for category, count in sorted(tool_categories.items())
    )
    pipeline_lines = "\n".join(
        f"- {pipeline['name']}: inputs={pipeline.get('input', {}).get('types', [])}, stages={len(pipeline.get('stages', []))}"
        for pipeline in pipelines
    )

    return f"""# Codex Authorized Upgrade Brief

Use this brief as the single source of truth for additive upgrades to the existing `r4ng3r-V2` repository. Preserve current architecture, add new assets in-place, and avoid destructive refactors unless strictly required for runtime integrity.

## Operating Boundaries
- Authorized security research, defensive intelligence, exposure assessment, and public-data correlation only.
- Prefer public, consent-based, or operator-supplied data sources.
- Preserve existing repository behavior; add capabilities rather than removing them.
- Keep wrappers, manifests, pipelines, workflow mappings, reporting, and UI orchestration deterministic and testable.

## Current Inventory Snapshot
- Modules in manifest: {len(manifest.get('modules', []))}
- Tools in manifest: {len(manifest.get('tools', []))}
- Pipelines on disk: {len(pipelines)}
- Workflows in manifest: {len(manifest.get('workflows', []))}

### Module Categories
{category_lines}

### Tool Categories
{tool_category_lines}

## Required Delivery Goals
1. Maintain a standard module contract:
```text
{MODULE_STRUCTURE}
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
{pipeline_lines}

## Expected Deliverables
- Updated wrappers and module metadata under `rtf/modules` and `rtf/intelligence_os/tooling`.
- Expanded workflow coverage and orchestration metadata.
- Dashboard/API support for launching, monitoring, and exporting investigations.
- Example investigation packs for every pipeline.
- Validation scripts/tests proving manifest integrity, pipeline loadability, and report generation.
"""


def main() -> None:
    PLANNING_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    pipelines = load_pipelines()
    workflow_map = build_workflow_map(manifest, pipelines)
    examples = build_examples(pipelines)

    WORKFLOW_MAP_PATH.write_text(yaml.safe_dump(workflow_map, sort_keys=False))
    EXAMPLES_PATH.write_text(yaml.safe_dump(examples, sort_keys=False))
    PROMPT_PATH.write_text(build_prompt(manifest, pipelines))

    print(f"Wrote {PROMPT_PATH.relative_to(ROOT)}")
    print(f"Wrote {WORKFLOW_MAP_PATH.relative_to(ROOT)}")
    print(f"Wrote {EXAMPLES_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
