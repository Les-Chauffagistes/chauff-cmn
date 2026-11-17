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


def test_exception_field_contains_the_traceback(capsys):
    configure(service="test-service", level="INFO")

    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("boom")

    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert "Traceback (most recent call last)" in payload["exception"]
    assert "ZeroDivisionError: division by zero" in payload["exception"]


def test_intercept_stdlib_routes_stdlib_records_to_json(capsys):
    import logging

    configure(service="test-service", level="INFO", intercept_stdlib=True)
    logging.getLogger("some.lib").warning("valeur %s", 42)

    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert payload["level"] == "WARNING"
    assert payload["message"] == "valeur 42"
    assert payload["function"] == "test_intercept_stdlib_routes_stdlib_records_to_json"
    assert payload["module"] == "test_logging"


def test_intercept_stdlib_keeps_exc_info_and_takes_over_uvicorn(capsys):
    import logging

    uvicorn_logger = logging.getLogger("uvicorn.error")
    uvicorn_logger.addHandler(logging.StreamHandler())
    uvicorn_logger.propagate = False

    configure(service="test-service", level="INFO", intercept_stdlib=True)
    try:
        1 / 0
    except ZeroDivisionError:
        logging.getLogger("some.lib").exception("échec")
    uvicorn_logger.info("Started")

    lines = [json.loads(line) for line in capsys.readouterr().out.strip().splitlines()]
    assert "ZeroDivisionError" in lines[-2]["exception"]
    assert lines[-1]["message"] == "Started"
