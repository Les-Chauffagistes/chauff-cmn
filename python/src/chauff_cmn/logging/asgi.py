"""Middleware ASGI pur (FastAPI, Starlette, ou tout serveur ASGI) qui loggue chaque
requête en JSON. Aucune dépendance supplémentaire : ne parle qu'au protocole ASGI.
"""

import time
from typing import Any, Awaitable, Callable, MutableMapping

from . import logger
from ._correlation import (
    REQUEST_ID_HEADER,
    bind_correlation_id,
    reset_correlation_id,
    resolve_correlation_id,
)

__all__ = ["RequestLoggingMiddleware"]

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
App = Callable[[Scope, Receive, Send], Awaitable[None]]


class RequestLoggingMiddleware:
    def __init__(self, app: App) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {
            key.decode("latin-1"): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }
        correlation_id = resolve_correlation_id(headers)
        token = bind_correlation_id(correlation_id)
        start = time.perf_counter()
        status = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                message["headers"] = [
                    *message.get("headers", []),
                    (REQUEST_ID_HEADER.encode("latin-1"), correlation_id.encode("latin-1")),
                ]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            # correlation_id est injecté automatiquement par le patcher loguru
            # (via le contextvar posé ci-dessus), pas besoin de le binder ici.
            logger.bind(
                method=scope.get("method"),
                path=scope.get("path"),
                status=status,
                duration_ms=duration_ms,
            ).info("requête traitée")
            reset_correlation_id(token)
