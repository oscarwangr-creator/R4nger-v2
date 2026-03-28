from __future__ import annotations

import click


@click.command("deps")
@click.argument("tool_name", shell_complete=lambda ctx, p, i: __import__("cli.autocomplete", fromlist=["complete_tool_names"]).complete_tool_names(ctx, p, i))
def deps_cmd(tool_name: str):
    """Show dependency/conflict graph and distributed notes for a tool."""
    manager = click.get_current_context().obj["manager"]
    renderer = click.get_current_context().obj["renderer"]
    as_json = click.get_current_context().obj["json"]

    payload, warnings = manager.load_or_introspect()
    for warning in warnings:
        renderer.warning(warning)

    tool = next((item for item in payload.get("tools", []) if item.get("name") == tool_name), None)
    if not tool:
        raise click.ClickException(f"Tool not found: {tool_name}")

    result = {
        "tool": tool_name,
        "dependencies": tool.get("dependencies", []),
        "optional_integrations": tool.get("optional_integrations", []),
        "conflicts": tool.get("conflicts", []),
        "distributed_notes": tool.get("distributed_notes", {}),
        "reliability": tool.get("reliability", "unknown"),
        "health_score": tool.get("health_score"),
    }
    if as_json:
        renderer.emit(result, as_json=True)
        return

    renderer.emit(renderer.deps_tree(tool_name, result["dependencies"], result["conflicts"]))
    renderer.emit(result)
