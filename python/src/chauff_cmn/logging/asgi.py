"""Middleware ASGI pur (FastAPI, Starlette, ou tout serveur ASGI) qui loggue chaque
requête en JSON et l'enveloppe dans un span OpenTelemetry SERVER. Aucune
dépendance supplémentaire au-delà d'opentelemetry-api/sdk (déjà des
dépendances core de chauff_cmn) : ne parle qu'au protocole ASGI.
"""

import time
from typing import Any, Awaitable, Callable, MutableMapping

from opentelemetry import trace
from opentelemetry.propagate import extract
from opentelemetry.trace import SpanKind, Status, StatusCode

from . import logger

__all__ = ["RequestLoggingMiddleware"]

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
App = Callable[[Scope, Receive, Send], Awaitable[None]]

_tracer = trace.get_tracer(__name__)


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
        method = scope.get("method")
        path = scope.get("path")
        # Continue le trace du `traceparent` entrant s'il est valide, sinon
        # `start_as_current_span` en démarre un nouveau — même politique que
        # Traefik en amont.
        parent_ctx = extract(headers)

        with _tracer.start_as_current_span(f"{method} {path}", context=parent_ctx, kind=SpanKind.SERVER) as span:
            span.set_attribute("http.method", method)
            span.set_attribute("http.target", path)
            start = time.perf_counter()
            status = 500

            async def send_wrapper(message: Message) -> None:
                nonlocal status
                if message["type"] == "http.response.start":
                    status = message["status"]
                await send(message)

            try:
                await self.app(scope, receive, send_wrapper)
            finally:
                duration_ms = round((time.perf_counter() - start) * 1000, 2)
                span.set_attribute("http.status_code", status)
                if status >= 500:
                    span.set_status(Status(StatusCode.ERROR))
                # trace_id/span_id sont injectés automatiquement par le patcher
                # loguru (via le span OTel courant), pas besoin de les binder
                # ici. Émis à l'intérieur du `with` pour que le patcher lise
                # bien ce span, pas un contexte déjà détaché.
                logger.bind(
                    method=method,
                    path=path,
                    status=status,
                    duration_ms=duration_ms,
                ).info("requête traitée")
