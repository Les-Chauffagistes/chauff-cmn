import pytest
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from chauff_cmn.tracing import setup_tracing

_exporter = InMemorySpanExporter()
setup_tracing(service="test-service", exporter=_exporter)


@pytest.fixture(autouse=True)
def spans():
    _exporter.clear()
    yield _exporter
    _exporter.clear()


@pytest.fixture(autouse=True)
def restore_stdlib_logging():
    # `configure(intercept_stdlib=True)` remplace les handlers du root logger et d'uvicorn : on remet
    # l'état d'avant pour ne pas polluer stdout des tests suivants avec les logs de httpx/asyncio.
    import logging

    root = logging.getLogger()
    saved = (root.handlers[:], root.level)
    uvicorn_loggers = [logging.getLogger(n) for n in ("uvicorn", "uvicorn.error", "uvicorn.access")]
    saved_uvicorn = [(lg.handlers[:], lg.propagate) for lg in uvicorn_loggers]
    yield
    root.handlers[:], root.level = saved[0], saved[1]
    for lg, (handlers, propagate) in zip(uvicorn_loggers, saved_uvicorn):
        lg.handlers[:], lg.propagate = handlers, propagate
