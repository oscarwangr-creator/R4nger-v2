from __future__ import annotations

import click

from cli.commands import categories_cmd, compose_cmd, deps_cmd, inspect_cmd, regen_cmd, search_cmd, stages_cmd
from cli.registry import RegistryManager
from cli.renderers import Renderer


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--json", "json_out", is_flag=True, default=False, help="Emit JSON output for automation use cases.")
@click.option("--store-path", default="discovery_v2/tool_metadata_store.json", show_default=True)
@click.pass_context
def cli(ctx: click.Context, json_out: bool, store_path: str):
    """R4nger BaseTool registry discovery CLI."""
    ctx.ensure_object(dict)
    ctx.obj["json"] = json_out
    ctx.obj["manager"] = RegistryManager(store_path=store_path)
    ctx.obj["renderer"] = Renderer()


@cli.command("install-completion")
@click.option("--shell", type=click.Choice(["bash", "zsh"]), required=True)
def install_completion(shell: str):
    """Print shell completion hook command for manual installation."""
    click.echo(f"eval \"$(_R4NGER_COMPLETE={shell}_source r4nger)\"")


cli.add_command(search_cmd)
cli.add_command(inspect_cmd)
cli.add_command(compose_cmd)
cli.add_command(deps_cmd)
cli.add_command(stages_cmd)
cli.add_command(categories_cmd)
cli.add_command(regen_cmd)


if __name__ == "__main__":
    cli()
