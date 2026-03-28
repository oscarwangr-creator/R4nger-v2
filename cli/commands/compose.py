from __future__ import annotations

import click

from cli.compose_logic import ComposeEngine


@click.command("compose")
@click.argument("use_case", shell_complete=lambda ctx, p, i: __import__("cli.autocomplete", fromlist=["complete_use_cases"]).complete_use_cases(ctx, p, i))
@click.option("--output-dir", default="generated", show_default=True)
def compose_cmd(use_case: str, output_dir: str):
    """Compose compatible tool chains and generate runnable artifacts."""
    manager = click.get_current_context().obj["manager"]
    renderer = click.get_current_context().obj["renderer"]
    as_json = click.get_current_context().obj["json"]

    payload, warnings = manager.load_or_introspect()
    for warning in warnings:
        renderer.warning(warning)

    engine = ComposeEngine()
    artifact = engine.compose(use_case, payload.get("tools", []), output_dir=output_dir)
    response = {
        "use_case": artifact.use_case,
        "stages": artifact.stages,
        "tools": artifact.tools,
        "ordering_warnings": artifact.ordering_warnings,
        "contention_warnings": artifact.contention_warnings,
        "variable_flow": artifact.variable_flow,
        "yaml_file": artifact.yaml_file,
        "python_stub_file": artifact.python_stub_file,
    }
    renderer.emit(response, as_json=as_json)
