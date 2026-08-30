"""Configuration du tracing distribué OpenTelemetry, exporté en OTLP vers
Tempo. `setup_tracing()` est à appeler une fois au démarrage du service ;
les middlewares/clients de `chauff_cmn.logging` créent ensuite de vrais spans
sur ce provider (récupéré via `opentelemetry.trace.get_tracer()`, safe à
appeler avant `setup_tracing()` grâce au proxy tracer de l'API OTel).
"""

import atexit
import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor, SpanExporter

__all__ = ["setup_tracing", "shutdown_tracing"]

DEFAULT_ENDPOINT = "http://tempo:4318"

_provider: Optional[TracerProvider] = None


def setup_tracing(service: str, endpoint: Optional[str] = None, exporter: Optional[SpanExporter] = None) -> None:
    """Installe un `TracerProvider` global qui exporte en OTLP/HTTP vers Tempo.

    `endpoint` (base URL, sans `/v1/traces`) retombe sur la variable d'env
    standard `OTEL_EXPORTER_OTLP_ENDPOINT`, puis sur `http://tempo:4318`
    (hostname Swarm interne, cf. `deploy/stacks/core/tempo.yml`).

    `exporter` est réservé aux tests : un exporteur fourni explicitement (ex.
    `InMemorySpanExporter`) est branché sur un `SimpleSpanProcessor` (export
    synchrone à `span.end()`) plutôt que sur le `BatchSpanProcessor` utilisé en
    fonctionnement normal, pour que les spans soient immédiatement visibles
    sans attendre un flush.
    """
    global _provider

    provider = TracerProvider(resource=Resource.create({"service.name": service}))

    if exporter is None:
        base = (endpoint or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") or DEFAULT_ENDPOINT).rstrip("/")
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{base}/v1/traces")))
    else:
        provider.add_span_processor(SimpleSpanProcessor(exporter))

    trace.set_tracer_provider(provider)
    _provider = provider
    atexit.register(shutdown_tracing)


def shutdown_tracing() -> None:
    """Flush et arrête le `TracerProvider` — les spans bufferisés par le
    `BatchSpanProcessor` sont perdus si le process se termine sans ça.
    `atexit` (posé par `setup_tracing`) ne suffit pas sur un `SIGTERM` non
    intercepté : à brancher explicitement sur le hook d'arrêt du framework
    (lifespan FastAPI, `on_cleanup` aiohttp, etc.).
    """
    global _provider
    if _provider is not None:
        _provider.shutdown()
        _provider = None
