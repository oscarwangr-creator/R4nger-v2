from __future__ import annotations

import click


@click.command("inspect")
@click.argument("tool_name", shell_complete=lambda ctx, p, i: __import__("cli.autocomplete", fromlist=["complete_tool_names"]).complete_tool_names(ctx, p, i))
def inspect_cmd(tool_name: str):
    """Detailed tool metadata inspection."""
    manager = click.get_current_context().obj["manager"]
    renderer = click.get_current_context().obj["renderer"]
    as_json = click.get_current_context().obj["json"]

    payload, warnings = manager.load_or_introspect()
    for warning in warnings:
        renderer.warning(warning)

    tool = next((item for item in payload.get("tools", []) if item.get("name") == tool_name), None)
    if not tool:
        raise click.ClickException(f"Tool not found: {tool_name}")

    yaml_vars = tool.get("consumes_variables", []) or ["value"]
    tool["yaml_snippet"] = (
        "stages:\n"
        f"  - name: stage_{(tool.get('stages') or ['L'])[0].lower()}\n"
        "    tools:\n"
        f"      - {tool['name']}\n"
        "    input:\n"
        + "\n".join([f"      {var}: {{{{{var}}}}}" for var in yaml_vars])
    )

    if as_json:
        renderer.emit(tool, as_json=True)
        return
    renderer.emit(renderer.inspect_view(tool))
