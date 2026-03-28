from __future__ import annotations

import click


@click.command("categories")
def categories_cmd():
    """Tool categories with counts and cross-stage coverage."""
    manager = click.get_current_context().obj["manager"]
    renderer = click.get_current_context().obj["renderer"]
    as_json = click.get_current_context().obj["json"]

    payload, warnings = manager.load_or_introspect()
    for warning in warnings:
        renderer.warning(warning)

    tools = payload.get("tools", [])
    if as_json:
        renderer.emit(renderer.category_stats(tools), as_json=True)
        return
    renderer.emit(renderer.category_table(tools))
