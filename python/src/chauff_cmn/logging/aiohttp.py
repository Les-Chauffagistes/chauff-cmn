"""Middleware de log de requêtes pour aiohttp. Nécessite `aiohttp` (extra `aiohttp`)."""

import time
from typing import Awaitable, Callable

from aiohttp.web import HTTPException, Request, StreamResponse, middleware

from . import logger
from ._correlation import (
    REQUEST_ID_HEADER,
    bind_correlation_id,
    reset_correlation_id,
    resolve_correlation_id,
)

__all__ = ["request_logging_middleware"]


@middleware
async def request_logging_middleware(
    request: Request, handler: Callable[[Request], Awaitable[StreamResponse]]
) -> StreamResponse:
    correlation_id = resolve_correlation_id(request.headers)
    token = bind_correlation_id(correlation_id)
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
        if response is not None:
            response.headers.setdefault(REQUEST_ID_HEADER, correlation_id)
        # correlation_id est injecté automatiquement par le patcher loguru
        # (via le contextvar posé ci-dessus), pas besoin de le binder ici.
        logger.bind(
            method=request.method,
            path=request.path,
            status=status,
            duration_ms=duration_ms,
        ).info("requête traitée")
        reset_correlation_id(token)
