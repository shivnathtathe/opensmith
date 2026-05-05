from opensmith.tracer import TraceCallable, trace
from opensmith.patcher import autopatch, unpatch
from opensmith.storage import Storage, set_default_db_path
from opensmith.models import Trace, Step, Run
from opensmith.console import set_console_mode
from opensmith.config import get_config


def _apply_config() -> None:
    config = get_config()

    db_path = config.get("db_path")
    if isinstance(db_path, str) and db_path:
        set_default_db_path(db_path)

    if config.get("console_mode") is True:
        set_console_mode(True)

    autopatch_backends = config.get("autopatch")
    if isinstance(autopatch_backends, list) and all(
        isinstance(item, str) for item in autopatch_backends
    ):
        autopatch(only=autopatch_backends)


_apply_config()

__all__ = [
    "trace",
    "autopatch",
    "unpatch",
    "Storage",
    "Trace",
    "Step",
    "Run",
    "set_console_mode",
    "set_default_db_path",
]
