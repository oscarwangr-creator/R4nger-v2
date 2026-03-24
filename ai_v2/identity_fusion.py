from __future__ import annotations

from hashlib import sha1
from typing import Any, Dict, List


class IdentityFusion:
    def fuse(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        clusters: Dict[str, Dict[str, Any]] = {}
        for e in entities:
            key_material = f"{e.get('type')}::{e.get('value')}".lower().encode()
            key = sha1(key_material).hexdigest()[:16]
            cluster = clusters.setdefault(key, {"cluster_id": key, "members": [], "score": 0.0})
            cluster["members"].append(e)
            cluster["score"] = min(1.0, cluster["score"] + (e.get("confidence", 0.5) / 5))
        return list(clusters.values())
