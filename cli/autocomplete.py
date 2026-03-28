from __future__ import annotations

from typing import List

import click
from click.shell_completion import CompletionItem

from cli.compose_logic import ComposeEngine
from cli.registry import INSTALL_METHODS, RegistryManager, STAGE_DEFINITIONS


def _tools(ctx: click.Context) -> List[dict]:
    manager: RegistryManager = ctx.obj["manager"]
    payload, _ = manager.load_or_introspect()
    return payload.get("tools", [])


def complete_tool_names(ctx: click.Context, _param: click.Parameter, incomplete: str):
    names = [tool["name"] for tool in _tools(ctx)]
    return [CompletionItem(name) for name in names if name.startswith(incomplete)]


def complete_stage_values(_ctx: click.Context, _param: click.Parameter, incomplete: str):
    return [CompletionItem(stage) for stage in STAGE_DEFINITIONS if stage.startswith(incomplete.upper())]


def complete_categories(ctx: click.Context, _param: click.Parameter, incomplete: str):
    categories = sorted({tool.get("category", "") for tool in _tools(ctx)})
    return [CompletionItem(cat) for cat in categories if cat.startswith(incomplete)]


def complete_install_methods(_ctx: click.Context, _param: click.Parameter, incomplete: str):
    return [CompletionItem(item) for item in INSTALL_METHODS if item.startswith(incomplete)]


def complete_use_cases(ctx: click.Context, _param: click.Parameter, incomplete: str):
    engine = ComposeEngine()
    suggestions = engine.suggest_use_cases(_tools(ctx))
    return [CompletionItem(item) for item in suggestions if item.startswith(incomplete)]
