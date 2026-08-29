import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from chauff_cmn.logging._trace import bind_trace_id, reset_trace_id
from chauff_cmn.logging.aiohttp_client import create_traced_session, traced_trace_config


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
    parts = value.split("-")
    return parts[1], parts[2]  # trace-id, span-id


async def test_outgoing_request_reuses_current_trace_id(echo_server):
    token = bind_trace_id("4bf92f3577b34da6a3ce929d0e0e4736")
    try:
        async with create_traced_session() as session:
            resp = await session.get(echo_server.make_url("/echo"))
            data = await resp.json()
    finally:
        reset_trace_id(token)

    trace_id, _span_id = _split_traceparent(data["traceparent"])
    assert trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"


async def test_outgoing_request_generates_a_trace_id_when_no_context(echo_server):
    # Aucun trace_id_var lié : simule un appel sortant depuis un job de fond,
    # hors contexte de requête entrante.
    async with create_traced_session() as session:
        resp = await session.get(echo_server.make_url("/echo"))
        data = await resp.json()

    assert "traceparent" in data
    trace_id, _span_id = _split_traceparent(data["traceparent"])
    assert trace_id


async def test_span_id_changes_between_calls_but_trace_id_stays(echo_server):
    token = bind_trace_id("4bf92f3577b34da6a3ce929d0e0e4736")
    try:
        async with create_traced_session() as session:
            resp1 = await session.get(echo_server.make_url("/echo"))
            data1 = await resp1.json()
            resp2 = await session.get(echo_server.make_url("/echo"))
            data2 = await resp2.json()
    finally:
        reset_trace_id(token)

    trace_id1, span_id1 = _split_traceparent(data1["traceparent"])
    trace_id2, span_id2 = _split_traceparent(data2["traceparent"])

    assert trace_id1 == trace_id2 == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert span_id1 != span_id2


async def test_traced_trace_config_can_be_passed_manually(echo_server):
    import aiohttp

    token = bind_trace_id("4bf92f3577b34da6a3ce929d0e0e4736")
    try:
        async with aiohttp.ClientSession(trace_configs=[traced_trace_config()]) as session:
            resp = await session.get(echo_server.make_url("/echo"))
            data = await resp.json()
    finally:
        reset_trace_id(token)

    trace_id, _span_id = _split_traceparent(data["traceparent"])
    assert trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
