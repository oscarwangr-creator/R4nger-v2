from __future__ import annotations

import json
from typing import Any, Dict, List

import click

from discovery_v2.introspection import DiscoveryService

try:
    from rich.console import Console
    from rich.table import Table
except Exception:  # pragma: no cover - fallback mode
    Console = None
    Table = None


service = DiscoveryService()
console = Console() if Console else None


def _print_tools(tools: List[Dict[str, Any]]) -> None:
    if console and Table:
        table = Table(title="R4nger v3 Tool Catalog")
        table.add_column("name")
        table.add_column("category")
        table.add_column("stages")
        table.add_column("purpose")
        for item in tools:
            table.add_row(item["name"], item["category"], ",".join(item["pipeline_stage_labels"]), item["purpose"])
        console.print(table)
        return

    click.echo(json.dumps(tools, indent=2))


@click.group()
def cli() -> None:
    """Interactive tool discovery for R4nger v3."""


@cli.command("regen")
def regen() -> None:
    """Force registry re-introspection and rebuild metadata/docs."""
    payload = service.regenerate()
    click.echo(f"Regenerated {payload['tool_count']} tools")


@cli.command("list")
@click.option("--stage", "stage", default=None, help="Filter by stage label A-K/L")
@click.option("--keyword", "keyword", default=None, help="Filter by capability keyword")
def list_cmd(stage: str | None, keyword: str | None) -> None:
    """List discovered tools."""
    tools = service.load_store().get("tools", [])
    if stage:
        tools = [item for item in tools if stage.upper() in item.get("pipeline_stage_labels", [])]
    if keyword:
        lowered = keyword.lower()
        tools = [
            item for item in tools
            if lowered in item.get("purpose", "").lower()
            or lowered in item.get("name", "").lower()
            or lowered in item.get("category", "").lower()
        ]
    _print_tools(tools)


@cli.command("inspect")
@click.argument("tool_name")
def inspect_tool(tool_name: str) -> None:
    """Inspect tool metadata and YAML usage hints."""
    tools = service.load_store().get("tools", [])
    tool = next((item for item in tools if item["name"] == tool_name), None)
    if not tool:
        raise click.ClickException(f"Tool not found: {tool_name}")
    click.echo(json.dumps(tool, indent=2))


@cli.command("deps")
@click.argument("tool_name")
def deps(tool_name: str) -> None:
    """Show dependency graph + known conflicts for tool."""
    graph = json.loads(service.graph_path.read_text(encoding="utf-8")) if service.graph_path.exists() else service._build_graph([])
    edges = [edge for edge in graph.get("edges", []) if edge.get("from") == tool_name]
    click.echo(json.dumps(edges, indent=2))


@cli.command("recommend")
@click.argument("use_case")
def recommend(use_case: str) -> None:
    """Recommend compatible tool combinations for a use case."""
    payload = service.recommend(use_case)
    click.echo(json.dumps(payload, indent=2))


if __name__ == "__main__":
    cli()
