"""Security primitives: RBAC, TLS policy metadata, and audit logging."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Callable, Dict, Iterable

from flask import Request, jsonify, request


ROLE_MATRIX: Dict[str, set[str]] = {
    "admin": {"read", "execute", "manage", "audit"},
    "operator": {"read", "execute"},
    "viewer": {"read"},
}


@dataclass(slots=True)
class SecurityManager:
    tls_min_version: str = "TLSv1.3"
    audit_log_path: str = "logs/audit.log"

    def __post_init__(self) -> None:
        Path(self.audit_log_path).parent.mkdir(parents=True, exist_ok=True)

    def has_permission(self, role: str, permission: str) -> bool:
        return permission in ROLE_MATRIX.get(role, set())

    def audit(self, req: Request, action: str, status: str, details: str = "") -> None:
        line = (
            f"{datetime.now(timezone.utc).isoformat()} "
            f"ip={req.remote_addr} method={req.method} path={req.path} "
            f"role={req.headers.get('X-Role', 'viewer')} action={action} status={status} details={details}\n"
        )
        Path(self.audit_log_path).write_text(
            Path(self.audit_log_path).read_text() + line if Path(self.audit_log_path).exists() else line
        )


def require_permission(security: SecurityManager, permission: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            role = request.headers.get("X-Role", "viewer")
            if not security.has_permission(role, permission):
                security.audit(request, action=func.__name__, status="denied", details=permission)
                return jsonify({"error": "forbidden", "required_permission": permission}), 403
            return func(*args, **kwargs)

        return wrapper

    return decorator
