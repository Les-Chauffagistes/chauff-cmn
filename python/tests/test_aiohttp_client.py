import aiohttp
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer
from opentelemetry import context as otel_context
from opentelemetry import trace
from opentelemetry.propagate import extract
from opentelemetry.trace import SpanKind

from chauff_cmn.logging.aiohttp_client import create_traced_session, traced_trace_config

INCOMING_TRACEPARENT = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"


async def _echo_headers(request: web.Request) -> web.Response:
    return web.json_response(dict(request.headers))


@pytest.fixture
async def echo_server():
    app = web.Application()
    app.router.add_get("/echo", _echo_headers)
    server = TestServer(app)
    await server.start_server()
    try:
        yield server
    finally:
        await server.close()


def _split_traceparent(value: str) -> tuple[str, str]:
    span_context = trace.get_current_span(extract({"traceparent": value})).get_span_context()
    return format(span_context.trace_id, "032x"), format(span_context.span_id, "016x")


async def test_outgoing_request_reuses_current_trace_id(echo_server, spans):
    # Simule le span serveur posé par RequestLoggingMiddleware/
    # request_logging_middleware pour une requête entrante avec ce trace-id.
    token = otel_context.attach(extract({"traceparent": INCOMING_TRACEPARENT}))
    try:
        async with create_traced_session() as session:
            resp = await session.get(echo_server.make_url("/echo"))
            data = await resp.json()
    finally:
        otel_context.detach(token)

    trace_id, _span_id = _split_traceparent(data["traceparent"])
    assert trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"


async def test_outgoing_request_generates_a_trace_id_when_no_context(echo_server, spans):
    # Aucun span actif : simule un appel sortant depuis un job de fond, hors
    # contexte de requête entrante.
    async with create_traced_session() as session:
        resp = await session.get(echo_server.make_url("/echo"))
        data = await resp.json()

    assert "traceparent" in data
    trace_id, _span_id = _split_traceparent(data["traceparent"])
    assert trace_id


async def test_span_id_changes_between_calls_but_trace_id_stays(echo_server, spans):
    token = otel_context.attach(extract({"traceparent": INCOMING_TRACEPARENT}))
    try:
        async with create_traced_session() as session:
            resp1 = await session.get(echo_server.make_url("/echo"))
            data1 = await resp1.json()
            resp2 = await session.get(echo_server.make_url("/echo"))
            data2 = await resp2.json()
    finally:
        otel_context.detach(token)

    trace_id1, span_id1 = _split_traceparent(data1["traceparent"])
    trace_id2, span_id2 = _split_traceparent(data2["traceparent"])

    assert trace_id1 == trace_id2 == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert span_id1 != span_id2


async def test_traced_trace_config_can_be_passed_manually(echo_server, spans):
    token = otel_context.attach(extract({"traceparent": INCOMING_TRACEPARENT}))
    try:
        async with aiohttp.ClientSession(trace_configs=[traced_trace_config()]) as session:
            resp = await session.get(echo_server.make_url("/echo"))
            data = await resp.json()
    finally:
        otel_context.detach(token)

    trace_id, _span_id = _split_traceparent(data["traceparent"])
    assert trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"


async def test_exports_a_client_span_per_call(echo_server, spans):
    async with create_traced_session() as session:
        resp = await session.get(echo_server.make_url("/echo"))
        await resp.json()

    (span,) = spans.get_finished_spans()
    assert span.kind == SpanKind.CLIENT
    assert span.attributes["http.status_code"] == 200
