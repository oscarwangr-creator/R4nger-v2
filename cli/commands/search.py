from __future__ import annotations

from typing import Any, Dict, List

import click


def _score(tool: Dict[str, Any], query: str, capability: str | None) -> int:
    haystacks = [tool.get("name", ""), tool.get("purpose", ""), tool.get("category", ""), " ".join(tool.get("capabilities", []))]
    score = 0
    q = query.lower()
    for hay in haystacks:
        text = hay.lower()
        if q in text:
            score += 3
        if text.startswith(q):
            score += 2
    if capability and capability.lower() in " ".join(tool.get("capabilities", [])).lower():
        score += 2
    return score


@click.command("search")
@click.argument("query")
@click.option("--stage", shell_complete=lambda ctx, p, i: __import__("cli.autocomplete", fromlist=["complete_stage_values"]).complete_stage_values(ctx, p, i))
@click.option("--category", shell_complete=lambda ctx, p, i: __import__("cli.autocomplete", fromlist=["complete_categories"]).complete_categories(ctx, p, i))
@click.option("--input-type")
@click.option("--output-type")
@click.option("--capability")
@click.option("--install-method", shell_complete=lambda ctx, p, i: __import__("cli.autocomplete", fromlist=["complete_install_methods"]).complete_install_methods(ctx, p, i))
def search_cmd(query: str, stage: str | None, category: str | None, input_type: str | None, output_type: str | None, capability: str | None, install_method: str | None):
    """Full-text search across tool metadata."""
    manager = click.get_current_context().obj["manager"]
    renderer = click.get_current_context().obj["renderer"]
    as_json = click.get_current_context().obj["json"]

    payload, warnings = manager.load_or_introspect()
    for warning in warnings:
        renderer.warning(warning)

    tools: List[Dict[str, Any]] = payload.get("tools", [])
    filtered: List[Dict[str, Any]] = []
    for tool in tools:
        if stage and stage.upper() not in tool.get("stages", []):
            continue
        if category and category.lower() != str(tool.get("category", "")).lower():
            continue
        if input_type and input_type not in tool.get("input_types", []):
            continue
        if output_type and output_type not in tool.get("output_types", []):
            continue
        if install_method and install_method.lower() != str(tool.get("install_method", "")).lower():
            continue

        rank = _score(tool, query, capability)
        if rank > 0:
            row = dict(tool)
            row["rank"] = rank
            filtered.append(row)

    filtered.sort(key=lambda t: (-t["rank"], t["name"]))
    if as_json:
        renderer.emit(filtered, as_json=True)
        return
    renderer.emit(renderer.search_table(filtered))
