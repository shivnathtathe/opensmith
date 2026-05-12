from __future__ import annotations

import csv
import json
import socket
from pathlib import Path

from click.testing import CliRunner

from opensmith.cli import _find_free_port, cli
from opensmith.models import Step, Trace
from opensmith.storage import Storage


def test_find_free_port_returns_start_when_free() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        free_port = sock.getsockname()[1]

    assert _find_free_port(free_port) == free_port


def test_find_free_port_skips_used_port() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock1:
        sock1.bind(("127.0.0.1", 0))
        used_port = sock1.getsockname()[1]
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock2:
            sock2.bind(("127.0.0.1", used_port + 1))
            next_port = sock2.getsockname()[1]
        result = _find_free_port(used_port, max_attempts=3)
        assert result == next_port


def test_init_creates_opensmith_json(tmp_path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["init"])

        assert result.exit_code == 0
        assert "Created opensmith.json" in result.output

        payload = json.loads(Path("opensmith.json").read_text())
        assert payload == {
            "db_path": "~/.opensmith/traces.db",
            "console_mode": False,
            "autopatch": [],
        }


def test_init_does_not_overwrite_existing_config_by_default(tmp_path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path("opensmith.json").write_text('{"db_path": "./existing.db"}\n')

        result = runner.invoke(cli, ["init"], input="\n")

        assert result.exit_code == 0
        assert "opensmith.json already exists. Overwrite? [y/N]" in result.output
        assert json.loads(Path("opensmith.json").read_text()) == {
            "db_path": "./existing.db",
        }


def test_init_overwrites_existing_config_when_confirmed(tmp_path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path("opensmith.json").write_text('{"db_path": "./existing.db"}\n')

        result = runner.invoke(cli, ["init"], input="y\n")

        assert result.exit_code == 0
        assert "Created opensmith.json" in result.output

        payload = json.loads(Path("opensmith.json").read_text())
        assert payload == {
            "db_path": "~/.opensmith/traces.db",
            "console_mode": False,
            "autopatch": [],
        }


def test_export_json_default_filename(monkeypatch, tmp_path) -> None:
    storage = Storage(tmp_path / "traces.db")
    trace = Trace(name="pipeline", tags=["rag"])
    trace.steps.append(
        Step(
            trace_id=trace.id,
            name="llm",
            tokens_total=42,
            cost_usd=0.0001,
            model="gpt-4o-mini",
            step_type="llm",
        )
    )
    storage.save_trace(trace)
    monkeypatch.setattr("opensmith.cli.Storage", lambda: storage)

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["export"])

        assert result.exit_code == 0
        assert "Exported 1 traces to opensmith-export.json" in result.output

        payload = json.loads(Path("opensmith-export.json").read_text())
        assert payload[0]["name"] == "pipeline"
        assert payload[0]["tags"] == ["rag"]
        assert len(payload[0]["steps"]) == 1


def test_export_csv_format(monkeypatch, tmp_path) -> None:
    storage = Storage(tmp_path / "traces.db")
    storage.save_trace(Trace(name="pipeline", tags=["rag"]))
    monkeypatch.setattr("opensmith.cli.Storage", lambda: storage)

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["export", "--format", "csv"])

        assert result.exit_code == 0
        assert "Exported 1 traces to opensmith-export.csv" in result.output

        with Path("opensmith-export.csv").open(encoding="utf-8") as file:
            rows = list(csv.DictReader(file))

        assert rows[0]["name"] == "pipeline"
        assert rows[0]["tags"] == "rag"


def test_export_custom_output_filename(monkeypatch, tmp_path) -> None:
    storage = Storage(tmp_path / "traces.db")
    storage.save_trace(Trace(name="pipeline"))
    monkeypatch.setattr("opensmith.cli.Storage", lambda: storage)

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            cli,
            ["export", "--output", "traces.json"],
        )

        assert result.exit_code == 0
        assert "Exported 1 traces to traces.json" in result.output
        assert Path("traces.json").exists()


def test_export_respects_limit(monkeypatch, tmp_path) -> None:
    storage = Storage(tmp_path / "traces.db")
    storage.save_trace(Trace(name="one", start_time=1.0))
    storage.save_trace(Trace(name="two", start_time=2.0))
    monkeypatch.setattr("opensmith.cli.Storage", lambda: storage)

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["export", "--limit", "1"])

        assert result.exit_code == 0

        payload = json.loads(Path("opensmith-export.json").read_text())
        assert len(payload) == 1
        assert payload[0]["name"] == "two"


def test_traces_search_by_name(monkeypatch) -> None:
    calls = []

    class FakeStorage:
        def get_traces(self, **kwargs):
            calls.append(kwargs)
            return []

    monkeypatch.setattr("opensmith.cli.Storage", FakeStorage)

    runner = CliRunner()
    result = runner.invoke(cli, ["traces", "--q", "rag"])

    assert result.exit_code == 0
    assert calls == [
        {
            "limit": 20,
            "q": "rag",
            "status": None,
            "tags": None,
        }
    ]


def test_traces_filter_status_err(monkeypatch) -> None:
    calls = []

    class FakeStorage:
        def get_traces(self, **kwargs):
            calls.append(kwargs)
            return []

    monkeypatch.setattr("opensmith.cli.Storage", FakeStorage)

    runner = CliRunner()
    result = runner.invoke(cli, ["traces", "--status", "err"])

    assert result.exit_code == 0
    assert calls == [
        {
            "limit": 20,
            "q": None,
            "status": "err",
            "tags": None,
        }
    ]


def test_traces_filter_by_tag(monkeypatch) -> None:
    calls = []

    class FakeStorage:
        def get_traces(self, **kwargs):
            calls.append(kwargs)
            return []

    monkeypatch.setattr("opensmith.cli.Storage", FakeStorage)

    runner = CliRunner()
    result = runner.invoke(cli, ["traces", "--tags", "production,rag"])

    assert result.exit_code == 0
    assert calls == [
        {
            "limit": 20,
            "q": None,
            "status": None,
            "tags": ["production", "rag"],
        }
    ]
