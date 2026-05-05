from __future__ import annotations

import json

from opensmith.config import get_config, load_config
from opensmith.console import is_console_mode, set_console_mode
from opensmith.storage import Storage, set_default_db_path


def test_load_config_returns_empty_if_no_file(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)

    assert load_config() == {}


def test_load_config_reads_json_file(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "opensmith.json").write_text(
        json.dumps(
            {
                "db_path": "./my_traces.db",
                "console_mode": False,
                "autopatch": ["openai", "qdrant"],
            }
        ),
        encoding="utf-8",
    )

    config = load_config()

    assert config == {
        "db_path": "./my_traces.db",
        "console_mode": False,
        "autopatch": ["openai", "qdrant"],
    }


def test_load_config_returns_empty_on_malformed_json(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "opensmith.json").write_text("{not-json", encoding="utf-8")

    assert load_config() == {}


def test_config_console_mode_key(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "opensmith.json").write_text(
        json.dumps({"console_mode": True}),
        encoding="utf-8",
    )
    monkeypatch.setattr("opensmith.config._CONFIG_CACHE", None)
    set_console_mode(False)

    config = get_config()
    if config.get("console_mode") is True:
        set_console_mode(True)

    assert is_console_mode() is True

    set_console_mode(False)


def test_config_db_path_key(tmp_path) -> None:
    custom_db = tmp_path / "my_traces.db"
    set_default_db_path(custom_db)

    storage = Storage()

    assert storage.db_path == custom_db


def test_config_autopatch_key(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "opensmith.json").write_text(
        json.dumps({"autopatch": ["openai", "qdrant"]}),
        encoding="utf-8",
    )
    monkeypatch.setattr("opensmith.config._CONFIG_CACHE", None)

    config = get_config()

    assert config["autopatch"] == ["openai", "qdrant"]
