import json
import sys
from typing import Any

from loguru import logger
from opentelemetry import trace

__all__ = ["logger", "configure"]


def configure(service: str, level: str = "INFO") -> None:
    # Existing `logger.info(...)` call sites keep working unchanged once the import switches to chauff_cmn.logging.
    logger.remove()
    logger.configure(patcher=_inject_trace_context)
    logger.add(_make_sink(service), level=level)


def _inject_trace_context(record: Any) -> None:
    # Rend trace_id/span_id disponibles sur CHAQUE ligne de log émise pendant
    # une requête (pas seulement celle du middleware), tant qu'un span OTel
    # est actif (posé par RequestLoggingMiddleware/request_logging_middleware
    # via `start_as_current_span`). `setdefault` laisse un
    # `logger.bind(trace_id=...)` explicite gagner.
    span_context = trace.get_current_span().get_span_context()
    if span_context.is_valid:
        record["extra"].setdefault("trace_id", format(span_context.trace_id, "032x"))
        record["extra"].setdefault("span_id", format(span_context.span_id, "016x"))
    else:
        record["extra"].setdefault("trace_id", None)
        record["extra"].setdefault("span_id", None)


def _make_sink(service: str):
    def sink(message: Any) -> None:
        record = message.record
        payload = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "service": service,
            "message": record["message"],
            "trace_id": record["extra"].get("trace_id"),
            "span_id": record["extra"].get("span_id"),
            "module": record["name"],
            "function": record["function"],
            "line": record["line"],
        }
        # Tout champ bindé en plus (logger.bind(method=..., status=...)) devient
        # une clé JSON top-level plutôt que de rester coincé dans "message".
        payload.update({k: v for k, v in record["extra"].items() if k not in ("trace_id", "span_id")})
        if record["exception"] is not None:
            payload["exception"] = str(record["exception"])
        sys.stdout.write(json.dumps(payload, default=str) + "\n")

    return sink
