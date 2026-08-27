import json
import sys
from typing import Any

from loguru import logger

__all__ = ["logger", "configure"]


def configure(service: str, level: str = "INFO") -> None:
    # Existing `logger.info(...)` call sites keep working unchanged once the import switches to chauff_cmn.logging.
    logger.remove()
    logger.add(_make_sink(service), level=level)


def _make_sink(service: str):
    def sink(message: Any) -> None:
        record = message.record
        payload = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "service": service,
            "message": record["message"],
            # No distributed tracing yet: reserved so callers can start doing
            # logger.bind(correlation_id=...) later without a breaking change.
            "correlation_id": record["extra"].get("correlation_id"),
            "module": record["name"],
            "function": record["function"],
            "line": record["line"],
        }
        if record["exception"] is not None:
            payload["exception"] = str(record["exception"])
        sys.stdout.write(json.dumps(payload, default=str) + "\n")

    return sink
