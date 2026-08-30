import json

from opentelemetry import trace

from chauff_cmn.logging import configure, logger

_tracer = trace.get_tracer(__name__)


def test_configure_emits_json_lines_without_a_span(capsys):
    configure(service="test-service", level="INFO")
    logger.info("hello")

    captured = capsys.readouterr()
    line = captured.out.strip().splitlines()[-1]
    payload = json.loads(line)

    assert payload["service"] == "test-service"
    assert payload["message"] == "hello"
    assert payload["level"] == "INFO"
    assert payload["trace_id"] is None
    assert payload["span_id"] is None


def test_trace_id_and_span_id_come_from_the_active_span(capsys):
    configure(service="test-service", level="INFO")

    with _tracer.start_as_current_span("test-span") as span:
        logger.info("hello")
        span_context = span.get_span_context()

    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])

    assert payload["trace_id"] == format(span_context.trace_id, "032x")
    assert payload["span_id"] == format(span_context.span_id, "016x")


def test_explicit_bind_wins_over_the_active_span(capsys):
    configure(service="test-service", level="INFO")

    with _tracer.start_as_current_span("test-span"):
        logger.bind(trace_id="4bf92f3577b34da6a3ce929d0e0e4736").info("hello")

    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert payload["trace_id"] == "4bf92f3577b34da6a3ce929d0e0e4736"
