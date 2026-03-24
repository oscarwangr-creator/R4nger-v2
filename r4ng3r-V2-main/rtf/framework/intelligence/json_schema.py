from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional


def intelligence_envelope(
    module: str,
    stage: str,
    summary: Dict[str, Any],
    entities: Optional[Dict[str, List[Any]]] = None,
    evidence: Optional[List[Dict[str, Any]]] = None,
    analytics: Optional[Dict[str, Any]] = None,
    integrations: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "schema_version": "rtf-intel/1.0",
        "module": module,
        "stage": stage,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": summary,
        "entities": entities or {},
        "evidence": evidence or [],
        "analytics": analytics or {},
        "integrations": integrations or {},
    }
