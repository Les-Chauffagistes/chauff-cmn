import json

import httpx

from chauff_cmn.logging import configure, logger
from chauff_cmn.logging.asgi import RequestLoggingMiddleware


async def _app(scope, receive, send):
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"{}"})


async def test_logs_structured_fields_and_propagates_correlation_id(capsys):
    configure(service="test-service", level="INFO")
    app = RequestLoggingMiddleware(_app)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/ping", headers={"X-Request-Id": "req-456"})

    assert resp.status_code == 200
    assert resp.headers["x-request-id"] == "req-456"

    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])

    assert payload["method"] == "GET"
    assert payload["path"] == "/ping"
    assert payload["status"] == 200
    assert payload["correlation_id"] == "req-456"
    assert isinstance(payload["duration_ms"], (int, float))


async def test_generates_a_correlation_id_when_absent(capsys):
    configure(service="test-service", level="INFO")
    app = RequestLoggingMiddleware(_app)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/ping")

    assert resp.headers["x-request-id"]
    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert payload["correlation_id"]


async def test_correlation_id_reaches_logs_emitted_deep_inside_the_handler(capsys):
    configure(service="test-service", level="INFO")

    async def app(scope, receive, send):
        # Ligne de log émise par la logique métier, pas par le middleware.
        logger.info("logique métier en cours")
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"{}"})

    wrapped = RequestLoggingMiddleware(app)
    transport = httpx.ASGITransport(app=wrapped)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/ping", headers={"X-Request-Id": "req-789"})

    lines = [json.loads(line) for line in capsys.readouterr().out.strip().splitlines()]
    business_line = next(p for p in lines if p["message"] == "logique métier en cours")

    assert business_line["correlation_id"] == "req-789"
