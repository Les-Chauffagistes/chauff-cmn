import json
import sys
from typing import Any

from loguru import logger

from ._trace import trace_id_var

__all__ = ["logger", "configure"]


def configure(service: str, level: str = "INFO") -> None:
    # Existing `logger.info(...)` call sites keep working unchanged once the import switches to chauff_cmn.logging.
    logger.remove()
    logger.configure(patcher=_inject_trace_id)
    logger.add(_make_sink(service), level=level)


def _inject_trace_id(record: Any) -> None:
    # Rend trace_id disponible sur CHAQUE ligne de log émise pendant une
    # requête (pas seulement celle du middleware), tant qu'un middleware a posé
    # le contextvar. `setdefault` laisse un `logger.bind(trace_id=...)`
    # explicite gagner.
    record["extra"].setdefault("trace_id", trace_id_var.get())


def _make_sink(service: str):
    def sink(message: Any) -> None:
        record = message.record
        payload = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "service": service,
            "message": record["message"],
            "trace_id": record["extra"].get("trace_id"),
            "module": record["name"],
            "function": record["function"],
            "line": record["line"],
        }
        # Tout champ bindé en plus (logger.bind(method=..., status=...)) devient
        # une clé JSON top-level plutôt que de rester coincé dans "message".
        payload.update({k: v for k, v in record["extra"].items() if k != "trace_id"})
        if record["exception"] is not None:
            payload["exception"] = str(record["exception"])
        sys.stdout.write(json.dumps(payload, default=str) + "\n")

    return sink
