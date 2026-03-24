def require_target(payload: dict) -> None:
    if not payload.get("target"):
        raise ValueError("target is required")
