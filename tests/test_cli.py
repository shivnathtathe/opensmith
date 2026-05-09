from __future__ import annotations

import csv
import json
from pathlib import Path

from click.testing import CliRunner

from opensmith.cli import cli
from opensmith.models import Step, Trace
from opensmith.storage import Storage


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
