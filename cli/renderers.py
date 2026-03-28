from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List

try:
    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.tree import Tree
except Exception:  # pragma: no cover
    Console = None
    Table = None
    Panel = None
    Tree = None
    box = None

from cli.registry import STAGE_DEFINITIONS


class Renderer:
    def __init__(self):
        self.console = Console() if Console else None

    def emit(self, payload: Any, as_json: bool = False) -> None:
        if as_json or not self.console:
            print(json.dumps(payload, indent=2))
            return
        self.console.print(payload)

    def warning(self, message: str) -> None:
        if self.console:
            self.console.print(f"[bold yellow]⚠ {message}[/bold yellow]")
        else:
            print(f"WARNING: {message}")

    def error(self, message: str) -> None:
        if self.console:
            self.console.print(f"[bold red]✖ {message}[/bold red]")
        else:
            print(f"ERROR: {message}")

    def search_table(self, rows: List[Dict[str, Any]]) -> Any:
        if not self.console or not Table:
            return rows
        table = Table(title="R4nger Tool Search", box=box.SIMPLE_HEAVY)
        table.add_column("Rank", width=6)
        table.add_column("Tool", width=28)
        table.add_column("Stages", width=14)
        table.add_column("Category", width=18)
        table.add_column("Purpose", width=56, overflow="fold")
        for idx, row in enumerate(rows, start=1):
            stage_label = ", ".join([f"[cyan]{s}[/cyan]" for s in row.get("stages", [])])
            table.add_row(str(idx), row["name"], stage_label, row.get("category", ""), row.get("purpose", ""))
        return table

    def inspect_view(self, tool: Dict[str, Any]) -> Any:
        if not self.console or not Panel:
            return tool
        return [
            Panel(tool.get("purpose", "n/a"), title="Purpose", border_style="blue"),
            Panel(
                f"Stages: {', '.join(tool.get('stages', []))}\n"
                f"Category: {tool.get('category', 'n/a')}\n"
                f"Input: {', '.join(tool.get('input_types', []))}\n"
                f"Output: {', '.join(tool.get('output_types', []))}",
                title="Pipeline + I/O",
                border_style="cyan",
            ),
            Panel(
                f"Consumes: {', '.join(tool.get('consumes_variables', [])) or 'n/a'}\n"
                f"Produces: {', '.join(tool.get('produces_variables', [])) or 'n/a'}\n"
                f"Dataclasses: {', '.join(tool.get('dataclass_mappings', [])) or 'inferred'}",
                title="Variable Context + Mapping",
                border_style="magenta",
            ),
            Panel(
                f"Dependencies: {', '.join(tool.get('dependencies', [])) or 'none'}\n"
                f"Conflicts: {', '.join(tool.get('conflicts', [])) or 'none'}\n"
                f"Install: {tool.get('install_method', 'n/a')}\n"
                f"Reliability: {tool.get('reliability', 'unknown')}\n"
                f"Health score: {tool.get('health_score', 'n/a')}",
                title="Dependencies + Reliability",
                border_style="green",
            ),
            Panel(
                f"Celery queue: {tool.get('distributed_notes', {}).get('celery_queue', 'default')}\n"
                f"Redis namespace: {tool.get('distributed_notes', {}).get('redis_namespace', 'n/a')}\n"
                f"Distributed: {tool.get('distributed_notes', {}).get('distributed', False)}",
                title="Execution Notes",
                border_style="yellow",
            ),
            Panel(tool.get("yaml_snippet", ""), title="YAML Snippet", border_style="white"),
        ]

    def deps_tree(self, tool_name: str, dependencies: Iterable[str], conflicts: Iterable[str]) -> Any:
        if not self.console or not Tree:
            return {"tool": tool_name, "dependencies": list(dependencies), "conflicts": list(conflicts)}
        root = Tree(f"[bold]{tool_name}[/bold]")
        dep_node = root.add("[green]dependencies[/green]")
        for dep in dependencies:
            dep_node.add(dep)
        conflict_node = root.add("[yellow]conflicts[/yellow]")
        for conflict in conflicts:
            conflict_node.add(conflict)
        return root

    def stage_stats(self, tools: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        by_stage: Dict[str, Dict[str, Any]] = {stage: {"count": 0, "categories": {}} for stage in STAGE_DEFINITIONS}
        for tool in tools:
            for stage in tool.get("stages", ["L"]):
                if stage not in by_stage:
                    by_stage[stage] = {"count": 0, "categories": {}}
                by_stage[stage]["count"] += 1
                cat = tool.get("category", "unknown")
                by_stage[stage]["categories"][cat] = by_stage[stage]["categories"].get(cat, 0) + 1
        return by_stage

    def stage_table(self, tools: List[Dict[str, Any]]) -> Any:
        by_stage = self.stage_stats(tools)
        if not self.console or not Table:
            return by_stage
        table = Table(title="Pipeline Stage Overview", box=box.SIMPLE)
        table.add_column("Stage", width=8)
        table.add_column("Description", width=35)
        table.add_column("Tools", width=8)
        table.add_column("Category Distribution", width=55)
        for stage, desc in STAGE_DEFINITIONS.items():
            info = by_stage.get(stage, {"count": 0, "categories": {}})
            dist = ", ".join([f"{k}:{v}" for k, v in sorted(info["categories"].items())]) or "-"
            table.add_row(f"[cyan]{stage}[/cyan]", desc, str(info["count"]), dist)
        return table

    def category_stats(self, tools: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        index: Dict[str, Dict[str, Any]] = {}
        for tool in tools:
            cat = tool.get("category", "unknown")
            index.setdefault(cat, {"count": 0, "stages": set()})
            index[cat]["count"] += 1
            index[cat]["stages"].update(tool.get("stages", []))
        return {k: {"count": v["count"], "stages": sorted(v["stages"])} for k, v in index.items()}

    def category_table(self, tools: List[Dict[str, Any]]) -> Any:
        index = self.category_stats(tools)
        if not self.console or not Table:
            return index
        table = Table(title="Category Overview", box=box.SIMPLE)
        table.add_column("Category", width=26)
        table.add_column("Tool Count", width=12)
        table.add_column("Cross-Stage Presence", width=30)
        for cat, info in sorted(index.items()):
            table.add_row(cat, str(info["count"]), ", ".join(info["stages"]))
        return table
