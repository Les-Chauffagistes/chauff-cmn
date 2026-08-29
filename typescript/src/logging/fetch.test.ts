import { afterEach, describe, expect, it, vi } from "vitest";
import { tracedFetch } from "./fetch";
import { TRACEPARENT_HEADER, runWithTraceId } from "./_trace";

const HEX_32_RE = /^[0-9a-f]{32}$/;

function parseTraceparent(value: string | null): { traceId: string; spanId: string } {
  expect(value).not.toBeNull();
  const parts = (value as string).split("-");
  expect(parts).toHaveLength(4);
  return { traceId: parts[1], spanId: parts[2] };
}

describe("tracedFetch", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("réutilise le trace-id du contexte de trace actif", async () => {
    const fetchMock = vi.fn(async (_input: string | URL | Request, _init?: RequestInit) => new Response("ok"));
    vi.stubGlobal("fetch", fetchMock);

    await runWithTraceId("4bf92f3577b34da6a3ce929d0e0e4736", () => tracedFetch("http://backend/api"));

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

    await runWithTraceId("4bf92f3577b34da6a3ce929d0e0e4736", async () => {
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
});
