import json

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from chauff_cmn.logging import configure, logger
from chauff_cmn.logging.aiohttp import request_logging_middleware

VALID_TRACEPARENT = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"


async def _make_client(handler):
    app = web.Application(middlewares=(request_logging_middleware,))
    app.router.add_get("/ping", handler)
    return TestClient(TestServer(app))


async def test_logs_structured_fields_and_reuses_incoming_trace_id(capsys):
    configure(service="test-service", level="INFO")

    async def handler(request: web.Request) -> web.Response:
        return web.json_response({"ok": True})

    async with await _make_client(handler) as client:
        resp = await client.get("/ping", headers={"traceparent": VALID_TRACEPARENT})
        assert resp.status == 200
        assert "traceparent" not in resp.headers

    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])

    assert payload["method"] == "GET"
    assert payload["path"] == "/ping"
    assert payload["status"] == 200
    assert payload["trace_id"] == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert isinstance(payload["duration_ms"], (int, float))


async def test_generates_a_trace_id_when_absent(capsys):
    configure(service="test-service", level="INFO")

    async def handler(request: web.Request) -> web.Response:
        return web.json_response({"ok": True})

    async with await _make_client(handler) as client:
        resp = await client.get("/ping")
        assert "traceparent" not in resp.headers

    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert payload["trace_id"]


async def test_generates_a_trace_id_when_traceparent_is_malformed(capsys):
    configure(service="test-service", level="INFO")

    async def handler(request: web.Request) -> web.Response:
        return web.json_response({"ok": True})

    async with await _make_client(handler) as client:
        # Trop peu de segments.
        resp = await client.get("/ping", headers={"traceparent": "00-bad"})
        assert resp.status == 200

    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert payload["trace_id"]
    assert payload["trace_id"] != "bad"


async def test_generates_a_trace_id_when_trace_id_is_all_zero(capsys):
    configure(service="test-service", level="INFO")

    async def handler(request: web.Request) -> web.Response:
        return web.json_response({"ok": True})

    async with await _make_client(handler) as client:
        resp = await client.get(
            "/ping",
            headers={"traceparent": "00-00000000000000000000000000000000-00f067aa0ba902b7-01"},
        )
        assert resp.status == 200

    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert payload["trace_id"] != "00000000000000000000000000000000"
    assert payload["trace_id"]


async def test_no_response_header_is_set(capsys):
    configure(service="test-service", level="INFO")

    async def handler(request: web.Request) -> web.Response:
        return web.json_response({"ok": True})

    async with await _make_client(handler) as client:
        resp = await client.get("/ping", headers={"traceparent": VALID_TRACEPARENT})
        assert "traceparent" not in resp.headers
        assert "X-Request-Id" not in resp.headers


async def test_trace_id_reaches_logs_emitted_deep_inside_the_handler(capsys):
    configure(service="test-service", level="INFO")

    async def handler(request: web.Request) -> web.Response:
        # Ligne de log émise par la logique métier, pas par le middleware.
        logger.info("logique métier en cours")
        return web.json_response({"ok": True})

    async with await _make_client(handler) as client:
        await client.get("/ping", headers={"traceparent": VALID_TRACEPARENT})

    lines = [json.loads(line) for line in capsys.readouterr().out.strip().splitlines()]
    business_line = next(p for p in lines if p["message"] == "logique métier en cours")

    assert business_line["trace_id"] == "4bf92f3577b34da6a3ce929d0e0e4736"
