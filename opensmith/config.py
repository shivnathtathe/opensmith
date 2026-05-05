from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rich.console import Console


_CONFIG_CACHE: dict[str, Any] | None = None
_console = Console()


def load_config() -> dict[str, Any]:
    config_path = Path.cwd() / "opensmith.json"
    if not config_path.exists():
        return {}

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _console.print(
            f"[yellow]opensmith warning:[/yellow] invalid opensmith.json: {exc}",
        )
        return {}

    if not isinstance(data, dict):
        _console.print(
            "[yellow]opensmith warning:[/yellow] opensmith.json must contain a JSON object",
        )
        return {}

    return data


def get_config() -> dict[str, Any]:
    global _CONFIG_CACHE

    if _CONFIG_CACHE is None:
        _CONFIG_CACHE = load_config()

    return _CONFIG_CACHE
