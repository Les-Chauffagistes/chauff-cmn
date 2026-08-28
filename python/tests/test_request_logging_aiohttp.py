import json

from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from chauff_cmn.logging import configure, logger
from chauff_cmn.logging.aiohttp import request_logging_middleware


async def test_logs_structured_fields_and_propagates_correlation_id(capsys):
    configure(service="test-service", level="INFO")

    async def handler(request: web.Request) -> web.Response:
        return web.json_response({"ok": True})

    app = web.Application(middlewares=(request_logging_middleware,))
    app.router.add_get("/ping", handler)

    async with TestClient(TestServer(app)) as client:
        resp = await client.get("/ping", headers={"X-Request-Id": "req-123"})
        assert resp.status == 200
        assert resp.headers["X-Request-Id"] == "req-123"

    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])

    assert payload["method"] == "GET"
    assert payload["path"] == "/ping"
    assert payload["status"] == 200
    assert payload["correlation_id"] == "req-123"
    assert isinstance(payload["duration_ms"], (int, float))


async def test_generates_a_correlation_id_when_absent(capsys):
    configure(service="test-service", level="INFO")

    async def handler(request: web.Request) -> web.Response:
        return web.json_response({"ok": True})

    app = web.Application(middlewares=(request_logging_middleware,))
    app.router.add_get("/ping", handler)

    async with TestClient(TestServer(app)) as client:
        resp = await client.get("/ping")
        assert "X-Request-Id" in resp.headers

    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert payload["correlation_id"]


async def test_correlation_id_reaches_logs_emitted_deep_inside_the_handler(capsys):
    configure(service="test-service", level="INFO")

    async def handler(request: web.Request) -> web.Response:
        # Ligne de log émise par la logique métier, pas par le middleware.
        logger.info("logique métier en cours")
        return web.json_response({"ok": True})

    app = web.Application(middlewares=(request_logging_middleware,))
    app.router.add_get("/ping", handler)

    async with TestClient(TestServer(app)) as client:
        await client.get("/ping", headers={"X-Request-Id": "req-789"})

    lines = [json.loads(line) for line in capsys.readouterr().out.strip().splitlines()]
    business_line = next(p for p in lines if p["message"] == "logique métier en cours")

    assert business_line["correlation_id"] == "req-789"
