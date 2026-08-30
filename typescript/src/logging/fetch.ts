import { context, propagation, trace, type TextMapSetter, SpanKind, SpanStatusCode } from "@opentelemetry/api";

const tracer = trace.getTracer("chauff-cmn");

const headersSetter: TextMapSetter<Headers> = {
  set(carrier, key, value) {
    carrier.set(key, value);
  },
};

// Wrapper de `fetch` qui enveloppe chaque appel sortant dans un span
// OpenTelemetry CLIENT et propage le contexte de trace courant (W3C Trace
// Context) via le header `traceparent` — équivalent, pour `fetch`, de
// `create_traced_session()` côté Python (aiohttp_client.py). Contrairement à
// aiohttp qui expose un objet `ClientSession`/`TraceConfig` réutilisable,
// `fetch` est une fonction unique : l'équivalent naturel est donc un wrapper
// de la fonction elle-même, drop-in replacement de `fetch` global (même
// signature).
//
// Le span est enfant du span actif s'il y en a un (posé par
// `withRequestLogging`), sinon nouvelle trace racine — un appel sortant part
// toujours avec un traceparent, y compris depuis un job de fond hors contexte
// de requête entrante.
//
// Les headers déjà présents dans `init.headers` (`Headers`, tableau de
// tuples ou objet plat — les trois formes valides de `RequestInit.headers`)
// sont préservés : `traceparent` s'ajoute sans les écraser.
export async function tracedFetch(input: string | URL | Request, init?: RequestInit): Promise<Response> {
  const method = init?.method ?? (input instanceof Request ? input.method : "GET");
  const url = input instanceof Request ? input.url : input.toString();
  const span = tracer.startSpan(`${method} ${url}`, { kind: SpanKind.CLIENT });

  const headers = new Headers(init?.headers);
  propagation.inject(trace.setSpan(context.active(), span), headers, headersSetter);

  try {
    const response = await fetch(input, { ...init, headers });
    span.setAttribute("http.status_code", response.status);
    if (response.status >= 500) span.setStatus({ code: SpanStatusCode.ERROR });
    return response;
  } catch (error) {
    span.recordException(error as Error);
    span.setStatus({ code: SpanStatusCode.ERROR });
    throw error;
  } finally {
    span.end();
  }
}
