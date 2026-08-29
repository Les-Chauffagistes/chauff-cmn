import json

import httpx

from chauff_cmn.logging import configure, logger
from chauff_cmn.logging.asgi import RequestLoggingMiddleware

VALID_TRACEPARENT = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"


async def _app(scope, receive, send):
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"{}"})


async def test_logs_structured_fields_and_reuses_incoming_trace_id(capsys):
    configure(service="test-service", level="INFO")
    app = RequestLoggingMiddleware(_app)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/ping", headers={"traceparent": VALID_TRACEPARENT})

    assert resp.status_code == 200
    assert "traceparent" not in resp.headers

    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])

    assert payload["method"] == "GET"
    assert payload["path"] == "/ping"
    assert payload["status"] == 200
    assert payload["trace_id"] == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert isinstance(payload["duration_ms"], (int, float))


async def test_generates_a_trace_id_when_absent(capsys):
    configure(service="test-service", level="INFO")
    app = RequestLoggingMiddleware(_app)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/ping")

    assert "traceparent" not in resp.headers
    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert payload["trace_id"]


async def test_generates_a_trace_id_when_traceparent_is_malformed(capsys):
    configure(service="test-service", level="INFO")
    app = RequestLoggingMiddleware(_app)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # trace-id pas hex.
        resp = await client.get(
            "/ping", headers={"traceparent": "00-zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz-00f067aa0ba902b7-01"}
        )

    assert resp.status_code == 200
    payload = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert payload["trace_id"]
    assert payload["trace_id"] != "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"


async def test_no_response_header_is_set(capsys):
    configure(service="test-service", level="INFO")
    app = RequestLoggingMiddleware(_app)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/ping", headers={"traceparent": VALID_TRACEPARENT})

    assert "traceparent" not in resp.headers
    assert "x-request-id" not in resp.headers


async def test_trace_id_reaches_logs_emitted_deep_inside_the_handler(capsys):
    configure(service="test-service", level="INFO")

    async def app(scope, receive, send):
        # Ligne de log émise par la logique métier, pas par le middleware.
        logger.info("logique métier en cours")
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"{}"})

    wrapped = RequestLoggingMiddleware(app)
    transport = httpx.ASGITransport(app=wrapped)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/ping", headers={"traceparent": VALID_TRACEPARENT})

    lines = [json.loads(line) for line in capsys.readouterr().out.strip().splitlines()]
    business_line = next(p for p in lines if p["message"] == "logique métier en cours")

    assert business_line["trace_id"] == "4bf92f3577b34da6a3ce929d0e0e4736"
