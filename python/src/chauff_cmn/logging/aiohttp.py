"""Middleware de log de requêtes pour aiohttp. Nécessite `aiohttp` (extra `aiohttp`)."""

import time
from typing import Awaitable, Callable

from aiohttp.web import HTTPException, Request, StreamResponse, middleware

from . import logger
from ._trace import bind_trace_id, reset_trace_id, resolve_trace_id

__all__ = ["request_logging_middleware"]


@middleware
async def request_logging_middleware(
    request: Request, handler: Callable[[Request], Awaitable[StreamResponse]]
) -> StreamResponse:
    trace_id = resolve_trace_id(request.headers)
    token = bind_trace_id(trace_id)
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
        # trace_id est injecté automatiquement par le patcher loguru
        # (via le contextvar posé ci-dessus), pas besoin de le binder ici.
        logger.bind(
            method=request.method,
            path=request.path,
            status=status,
            duration_ms=duration_ms,
        ).info("requête traitée")
        reset_trace_id(token)
