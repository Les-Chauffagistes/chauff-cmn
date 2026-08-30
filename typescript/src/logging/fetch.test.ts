import { afterEach, describe, expect, it, vi } from "vitest";
import { context, propagation, SpanKind } from "@opentelemetry/api";
import { tracedFetch } from "./fetch";
import { testSpanExporter } from "../vitest.setup";

const TRACEPARENT_HEADER = "traceparent";
const HEX_32_RE = /^[0-9a-f]{32}$/;
const INCOMING_TRACEPARENT = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01";

function parseTraceparent(value: string | null): { traceId: string; spanId: string } {
  expect(value).not.toBeNull();
  const parts = (value as string).split("-");
  expect(parts).toHaveLength(4);
  return { traceId: parts[1], spanId: parts[2] };
}

// Simule le span serveur posé par `withRequestLogging` pour une requête
// entrante avec ce trace-id, en extrayant un `traceparent` comme le ferait le
// middleware.
function withIncomingTraceContext<T>(fn: () => T): T {
  const headers = new Headers({ [TRACEPARENT_HEADER]: INCOMING_TRACEPARENT });
  const ctx = propagation.extract(context.active(), headers, {
    get: (carrier, key) => carrier.get(key) ?? undefined,
    keys: (carrier) => Array.from(carrier.keys()),
  });
  return context.with(ctx, fn);
}

describe("tracedFetch", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("réutilise le trace-id du contexte de trace actif", async () => {
    const fetchMock = vi.fn(async (_input: string | URL | Request, _init?: RequestInit) => new Response("ok"));
    vi.stubGlobal("fetch", fetchMock);

    await withIncomingTraceContext(() => tracedFetch("http://backend/api"));

    const init = fetchMock.mock.calls[0][1] as RequestInit;
    const headers = init.headers as Headers;
    const { traceId } = parseTraceparent(headers.get(TRACEPARENT_HEADER));
    expect(traceId).toBe("4bf92f3577b34da6a3ce929d0e0e4736");
  });

  it("génère un nouveau trace-id hors contexte de trace", async () => {
    const fetchMock = vi.fn(async (_input: string | URL | Request, _init?: RequestInit) => new Response("ok"));
    vi.stubGlobal("fetch", fetchMock);

    await tracedFetch("http://backend/api");

    const init = fetchMock.mock.calls[0][1] as RequestInit;
    const headers = init.headers as Headers;
    const { traceId } = parseTraceparent(headers.get(TRACEPARENT_HEADER));
    expect(traceId).toMatch(HEX_32_RE);
  });

  it("garde le même trace-id mais génère un span-id différent entre deux appels du même contexte", async () => {
    const fetchMock = vi.fn(async (_input: string | URL | Request, _init?: RequestInit) => new Response("ok"));
    vi.stubGlobal("fetch", fetchMock);

    await withIncomingTraceContext(async () => {
      await tracedFetch("http://backend/api/one");
      await tracedFetch("http://backend/api/two");
    });

    const init1 = fetchMock.mock.calls[0][1] as RequestInit;
    const init2 = fetchMock.mock.calls[1][1] as RequestInit;
    const first = parseTraceparent((init1.headers as Headers).get(TRACEPARENT_HEADER));
    const second = parseTraceparent((init2.headers as Headers).get(TRACEPARENT_HEADER));

    expect(first.traceId).toBe("4bf92f3577b34da6a3ce929d0e0e4736");
    expect(second.traceId).toBe("4bf92f3577b34da6a3ce929d0e0e4736");
    expect(first.spanId).not.toBe(second.spanId);
  });

  it("préserve les headers déjà présents sous forme d'objet Headers", async () => {
    const fetchMock = vi.fn(async (_input: string | URL | Request, _init?: RequestInit) => new Response("ok"));
    vi.stubGlobal("fetch", fetchMock);

    await tracedFetch("http://backend/api", { headers: new Headers({ Authorization: "Bearer token" }) });

    const init = fetchMock.mock.calls[0][1] as RequestInit;
    const headers = init.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer token");
    expect(headers.get(TRACEPARENT_HEADER)).not.toBeNull();
  });

  it("préserve les headers déjà présents sous forme de tableau de tuples", async () => {
    const fetchMock = vi.fn(async (_input: string | URL | Request, _init?: RequestInit) => new Response("ok"));
    vi.stubGlobal("fetch", fetchMock);

    await tracedFetch("http://backend/api", {
      headers: [
        ["Authorization", "Bearer token"],
        ["X-Custom", "value"],
      ],
    });

    const init = fetchMock.mock.calls[0][1] as RequestInit;
    const headers = init.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer token");
    expect(headers.get("X-Custom")).toBe("value");
    expect(headers.get(TRACEPARENT_HEADER)).not.toBeNull();
  });

  it("préserve les headers déjà présents sous forme d'objet plat", async () => {
    const fetchMock = vi.fn(async (_input: string | URL | Request, _init?: RequestInit) => new Response("ok"));
    vi.stubGlobal("fetch", fetchMock);

    await tracedFetch("http://backend/api", {
      headers: { Authorization: "Bearer token", "X-Custom": "value" },
    });

    const init = fetchMock.mock.calls[0][1] as RequestInit;
    const headers = init.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer token");
    expect(headers.get("X-Custom")).toBe("value");
    expect(headers.get(TRACEPARENT_HEADER)).not.toBeNull();
  });

  it("exporte un span CLIENT par appel avec le statut HTTP", async () => {
    const fetchMock = vi.fn(async (_input: string | URL | Request, _init?: RequestInit) => new Response("ok", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    await tracedFetch("http://backend/api");

    const [span] = testSpanExporter.getFinishedSpans();
    expect(span.kind).toBe(SpanKind.CLIENT);
    expect(span.attributes["http.status_code"]).toBe(200);
  });
});
