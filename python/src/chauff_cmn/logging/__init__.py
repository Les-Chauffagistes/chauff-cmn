import json
import logging
import sys
import traceback
from typing import Any

from loguru import logger
from opentelemetry import trace

__all__ = ["logger", "configure"]


def configure(service: str, level: str = "INFO", intercept_stdlib: bool = False) -> None:
    # Existing `logger.info(...)` call sites keep working unchanged once the import switches to chauff_cmn.logging.
    logger.remove()
    logger.configure(patcher=_inject_trace_context)
    logger.add(_make_sink(service), level=level)
    if intercept_stdlib:
        _intercept_stdlib()


class _InterceptHandler(logging.Handler):
    # Redirige les records de la stdlib vers loguru, pour que le code en `logging.getLogger(__name__)`
    # (et les libs tierces : uvicorn, asyncpg, httpx...) sorte le même JSON que le reste.
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Remonte au-delà des frames du module logging pour que module/function/line
        # désignent l'appelant d'origine et non ce handler.
        frame, depth = sys._getframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def _intercept_stdlib() -> None:
    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)
    # uvicorn pose ses propres handlers et coupe la propagation : on les retire pour que tout
    # passe par le root logger (donc par loguru).
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        stdlib_logger = logging.getLogger(name)
        stdlib_logger.handlers.clear()
        stdlib_logger.propagate = True


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
            exc = record["exception"]
            payload["exception"] = "".join(traceback.format_exception(exc.type, exc.value, exc.traceback)).rstrip()
        sys.stdout.write(json.dumps(payload, default=str) + "\n")

    return sink
