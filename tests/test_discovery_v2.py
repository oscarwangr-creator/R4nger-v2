from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from click.testing import CliRunner

from discovery_v2.cli import cli
from discovery_v2.introspection import DiscoveryService


def test_discovery_regenerate_creates_store_and_graph(tmp_path: Path):
    service = DiscoveryService(
        store_path=str(tmp_path / "store.json"),
        graph_path=str(tmp_path / "graph.json"),
        docs_path=str(tmp_path / "docs"),
        audit_log_path=str(tmp_path / "audit.log"),
    )

    payload = service.regenerate()

    assert payload["tool_count"] >= 1
    assert (tmp_path / "store.json").exists()
    assert (tmp_path / "graph.json").exists()
    assert (tmp_path / "docs").exists()


def test_dependency_and_conflict_metadata_is_present(tmp_path: Path):
    service = DiscoveryService(
        store_path=str(tmp_path / "store.json"),
        graph_path=str(tmp_path / "graph.json"),
        docs_path=str(tmp_path / "docs"),
        audit_log_path=str(tmp_path / "audit.log"),
    )
    payload = service.regenerate()
    tools = payload["tools"]

    assert all("dependencies" in item for item in tools)
    assert all("conflicts" in item for item in tools)


def test_cli_list_and_inspect_commands(tmp_path: Path):
    service = DiscoveryService(
        store_path=str(tmp_path / "store.json"),
        graph_path=str(tmp_path / "graph.json"),
        docs_path=str(tmp_path / "docs"),
        audit_log_path=str(tmp_path / "audit.log"),
    )
    service.regenerate()

    from discovery_v2 import cli as cli_module

    cli_module.service = service
    runner = CliRunner()

    result_list = runner.invoke(cli, ["list", "--stage", "B"])
    assert result_list.exit_code == 0

    data = json.loads((tmp_path / "store.json").read_text(encoding="utf-8"))
    first_tool = data["tools"][0]["name"]
    result_inspect = runner.invoke(cli, ["inspect", first_tool])
    assert result_inspect.exit_code == 0
    assert first_tool in result_inspect.output


def test_recommendation_handoffs_shape(tmp_path: Path):
    service = DiscoveryService(
        store_path=str(tmp_path / "store.json"),
        graph_path=str(tmp_path / "graph.json"),
        docs_path=str(tmp_path / "docs"),
        audit_log_path=str(tmp_path / "audit.log"),
    )
    service.regenerate()
    recommendation = service.recommend("username-to-breach")

    assert recommendation["tools"]
    assert isinstance(recommendation["handoffs"], list)
