import { describe, expect, it, vi } from "vitest";
import { trace } from "@opentelemetry/api";
import { activeTraceContext, extractTraceContext, setupTracing, withTraceContext } from "./tracing";
import { tracedFetch } from "./logging/fetch";
import { testSpanExporter } from "./vitest.setup";

const TRACEPARENT_HEADER = "traceparent";
const INCOMING_TRACEPARENT = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01";

describe("extractTraceContext / withTraceContext", () => {
  it("reprend le trace-id d'un traceparent extrait puis réinjecté explicitement", async () => {
    const fetchMock = vi.fn(async (_input: string | URL | Request, _init?: RequestInit) => new Response("ok"));
    vi.stubGlobal("fetch", fetchMock);

    const parentCtx = extractTraceContext(new Headers({ [TRACEPARENT_HEADER]: INCOMING_TRACEPARENT }));
    await withTraceContext(parentCtx, () => tracedFetch("http://backend/api"));

    const init = fetchMock.mock.calls[0][1] as RequestInit;
    const outHeaders = init.headers as Headers;
    expect(outHeaders.get(TRACEPARENT_HEADER)).toContain("4bf92f3577b34da6a3ce929d0e0e4736");

    vi.unstubAllGlobals();
  });

  it("survit à un await intermédiaire entre l'extraction et la réinjection", async () => {
    // Reproduit le cas d'une Server Action Next.js : le contexte est capturé
    // dès l'entrée, puis réinjecté explicitement bien plus tard dans
    // l'exécution (après une transaction DB, par ex.), pas par survie du
    // contexte ambiant.
    const fetchMock = vi.fn(async (_input: string | URL | Request, _init?: RequestInit) => new Response("ok"));
    vi.stubGlobal("fetch", fetchMock);

    const parentCtx = extractTraceContext(new Headers({ [TRACEPARENT_HEADER]: INCOMING_TRACEPARENT }));

    async function delayedCall() {
      await new Promise((resolve) => setTimeout(resolve, 0));
      return withTraceContext(parentCtx, () => tracedFetch("http://backend/api"));
    }
    await delayedCall();

    const init = fetchMock.mock.calls[0][1] as RequestInit;
    const outHeaders = init.headers as Headers;
    expect(outHeaders.get(TRACEPARENT_HEADER)).toContain("4bf92f3577b34da6a3ce929d0e0e4736");

    vi.unstubAllGlobals();
  });
});

describe("activeTraceContext", () => {
  it("capture le span actif courant", () => {
    const tracer = trace.getTracer("test");
    tracer.startActiveSpan("test-span", (span) => {
      const ctx = activeTraceContext();
      expect(trace.getSpan(ctx)).toBe(span);
      span.end();
    });
  });
});

describe("setupTracing({ handleShutdownSignal: false })", () => {
  it("n'enregistre pas de handler SIGTERM interne", () => {
    const before = process.listenerCount("SIGTERM");
    setupTracing({ service: "test", exporter: testSpanExporter, handleShutdownSignal: false });
    expect(process.listenerCount("SIGTERM")).toBe(before);
  });
});
