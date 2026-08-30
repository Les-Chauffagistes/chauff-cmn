"""Middleware de log de requêtes pour aiohttp. Nécessite `aiohttp` (extra `aiohttp`)."""

import time
from typing import Awaitable, Callable

from aiohttp.web import HTTPException, Request, StreamResponse, middleware
from opentelemetry import trace
from opentelemetry.propagate import extract
from opentelemetry.trace import SpanKind, Status, StatusCode

from . import logger

__all__ = ["request_logging_middleware"]

_tracer = trace.get_tracer(__name__)


@middleware
async def request_logging_middleware(
    request: Request, handler: Callable[[Request], Awaitable[StreamResponse]]
) -> StreamResponse:
    # Continue le trace du `traceparent` entrant s'il est valide, sinon
    # `start_as_current_span` en démarre un nouveau — même politique que
    # Traefik en amont.
    parent_ctx = extract(request.headers)

    with _tracer.start_as_current_span(
        f"{request.method} {request.path}", context=parent_ctx, kind=SpanKind.SERVER
    ) as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.target", request.path)
        start = time.perf_counter()
        status = 500
        response: StreamResponse | None = None

        try:
            response = await handler(request)
            status = response.status
            return response
        except HTTPException as exc:
            status = exc.status_code
            raise
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            span.set_attribute("http.status_code", status)
            if status >= 500:
                span.set_status(Status(StatusCode.ERROR))
            # trace_id/span_id sont injectés automatiquement par le patcher
            # loguru (via le span OTel courant), pas besoin de les binder ici.
            # Émis à l'intérieur du `with` pour que le patcher lise bien ce
            # span, pas un contexte déjà détaché.
            logger.bind(
                method=request.method,
                path=request.path,
                status=status,
                duration_ms=duration_ms,
            ).info("requête traitée")
