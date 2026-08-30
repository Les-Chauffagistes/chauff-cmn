"""Client HTTP sortant aiohttp qui crée un span OpenTelemetry CLIENT et
propage le contexte de trace courant (W3C Trace Context) sur chaque requête
via un header `traceparent`. Nécessite `aiohttp` (extra `aiohttp`).
"""

from typing import Any

import aiohttp
from aiohttp import TraceConfig, TraceRequestEndParams, TraceRequestExceptionParams, TraceRequestStartParams
from opentelemetry import trace
from opentelemetry.propagate import inject
from opentelemetry.trace import SpanKind, Status, StatusCode

__all__ = ["traced_trace_config", "create_traced_session"]

_tracer = trace.get_tracer(__name__)


async def _on_request_start(
    session: aiohttp.ClientSession,
    trace_config_ctx: Any,
    params: TraceRequestStartParams,
) -> None:
    # Un span CLIENT par appel sortant, enfant du span courant s'il y en a un
    # (posé par RequestLoggingMiddleware/request_logging_middleware), sinon
    # nouvelle trace racine — un appel sortant part toujours avec un
    # `traceparent`, y compris depuis un job de fond hors contexte de requête
    # entrante. Stocké sur `trace_config_ctx` pour être terminé dans
    # `_on_request_end`/`_on_request_exception` (callbacks séparés : pas de
    # bloc `with` possible ici).
    span = _tracer.start_span(f"{params.method} {params.url}", kind=SpanKind.CLIENT)
    trace_config_ctx.span = span
    inject(params.headers, context=trace.set_span_in_context(span))


async def _on_request_end(
    session: aiohttp.ClientSession,
    trace_config_ctx: Any,
    params: TraceRequestEndParams,
) -> None:
    span = trace_config_ctx.span
    span.set_attribute("http.status_code", params.response.status)
    if params.response.status >= 500:
        span.set_status(Status(StatusCode.ERROR))
    span.end()


async def _on_request_exception(
    session: aiohttp.ClientSession,
    trace_config_ctx: Any,
    params: TraceRequestExceptionParams,
) -> None:
    span = trace_config_ctx.span
    span.record_exception(params.exception)
    span.set_status(Status(StatusCode.ERROR))
    span.end()


def traced_trace_config() -> TraceConfig:
    """TraceConfig aiohttp qui crée un span CLIENT et pose `traceparent` sur
    chaque requête sortante.

    Usage: `aiohttp.ClientSession(trace_configs=[traced_trace_config()])`.
    """
    trace_config = TraceConfig()
    trace_config.on_request_start.append(_on_request_start)
    trace_config.on_request_end.append(_on_request_end)
    trace_config.on_request_exception.append(_on_request_exception)
    return trace_config


def create_traced_session(**kwargs: Any) -> aiohttp.ClientSession:
    """Raccourci équivalent à `aiohttp.ClientSession(trace_configs=[traced_trace_config()], **kwargs)`."""
    trace_configs = [traced_trace_config(), *kwargs.pop("trace_configs", [])]
    return aiohttp.ClientSession(trace_configs=trace_configs, **kwargs)
