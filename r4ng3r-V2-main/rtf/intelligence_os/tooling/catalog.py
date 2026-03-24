from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List


@lru_cache(maxsize=1)
def load_tool_catalog() -> List[Dict[str, Any]]:
    path = Path(__file__).with_name('tool_catalog.json')
    return json.loads(path.read_text())


@lru_cache(maxsize=1)
def load_framework_manifest() -> Dict[str, Any]:
    path = Path(__file__).resolve().parents[1] / 'manifests' / 'framework_manifest.json'
    return json.loads(path.read_text())


@lru_cache(maxsize=1)
def load_module_mappings() -> List[Dict[str, Any]]:
    return load_framework_manifest().get('modules', [])


@lru_cache(maxsize=1)
def load_pipeline_mappings() -> List[Dict[str, Any]]:
    return load_framework_manifest().get('pipelines', [])


@lru_cache(maxsize=1)
def load_workflow_mappings() -> List[Dict[str, Any]]:
    return load_framework_manifest().get('workflows', [])


@lru_cache(maxsize=1)
def load_framework_analysis() -> Dict[str, Any]:
    return load_framework_manifest().get('analysis', {})
