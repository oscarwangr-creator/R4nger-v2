from __future__ import annotations

import click


@click.command("regen")
def regen_cmd():
    """Force live re-introspection and print metadata diff."""
    manager = click.get_current_context().obj["manager"]
    renderer = click.get_current_context().obj["renderer"]
    as_json = click.get_current_context().obj["json"]

    previous = manager.load_store(silent=True)
    payload = manager.introspect_live(previous=previous)
    manager.persist_store(payload)

    if as_json:
        renderer.emit(payload, as_json=True)
        return

    diff = payload.get("diff", {})
    renderer.emit(
        {
            "generated_at": payload.get("generated_at"),
            "tool_count": payload.get("tool_count"),
            "added": diff.get("added", []),
            "removed": diff.get("removed", []),
            "changed": diff.get("changed", []),
            "failures": payload.get("failures", []),
        }
    )
