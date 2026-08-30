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
