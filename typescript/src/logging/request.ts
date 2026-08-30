import { context, propagation, trace, SpanKind, SpanStatusCode } from "@opentelemetry/api";
import { logger } from "./index";
import { headersGetter } from "./_headers";

// N'importe rien de spécifique à Next.js (Request/Response Web standard) :
// marche pour un App Router route handler tel quel, `NextRequest`/
// `NextResponse` étant des sous-types de `Request`/`Response`.
type RouteHandler<Args extends unknown[]> = (request: Request, ...args: Args) => Promise<Response> | Response;

const tracer = trace.getTracer("chauff-cmn");

// Équivalent, au niveau d'un route handler, de RequestLoggingMiddleware
// (Python, asgi.py) : span SERVER OpenTelemetry couvrant la requête, continué
// depuis le `traceparent` entrant s'il est présent, plus une ligne de log
// "requête traitée" avec method/path/status/duration_ms à la fin. Aucun
// header n'est posé sur la réponse (pas d'écho, un seul mécanisme de
// corrélation : `traceparent` en entrée).
//
// Contrairement au middleware ASGI, il n'existe pas d'équivalent Next.js qui
// enveloppe tout le cycle requête/réponse (middleware.ts s'exécute avant le
// handler et ne voit jamais la réponse) — ce wrapper doit donc être appliqué
// route par route.
export function withRequestLogging<Args extends unknown[]>(handler: RouteHandler<Args>): RouteHandler<Args> {
  return async (request: Request, ...args: Args): Promise<Response> => {
    const parentCtx = propagation.extract(context.active(), request.headers, headersGetter);
    const method = request.method;
    const path = new URL(request.url).pathname;

    return tracer.startActiveSpan(`${method} ${path}`, { kind: SpanKind.SERVER }, parentCtx, async (span) => {
      const start = performance.now();
      let status = 500;
      try {
        const response = await handler(request, ...args);
        status = response.status;
        return response;
      } finally {
        const duration_ms = Math.round((performance.now() - start) * 100) / 100;
        span.setAttribute("http.status_code", status);
        if (status >= 500) span.setStatus({ code: SpanStatusCode.ERROR });
        logger.info("requête traitée", { method, path, status, duration_ms });
        span.end();
      }
    });
  };
}
