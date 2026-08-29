import { logger } from "./index";
import { REQUEST_ID_HEADER, resolveCorrelationId, runWithCorrelationId } from "./_correlation";

// N'importe rien de spécifique à Next.js (Request/Response Web standard) :
// marche pour un App Router route handler tel quel, `NextRequest`/
// `NextResponse` étant des sous-types de `Request`/`Response`.
type RouteHandler<Args extends unknown[]> = (request: Request, ...args: Args) => Promise<Response> | Response;

// Équivalent, au niveau d'un route handler, de RequestLoggingMiddleware
// (Python, asgi.py) : id de corrélation résolu/propagé, une ligne de log
// "requête traitée" avec method/path/status/duration_ms à la fin.
//
// Contrairement au middleware ASGI, il n'existe pas d'équivalent Next.js qui
// enveloppe tout le cycle requête/réponse (middleware.ts s'exécute avant le
// handler et ne voit jamais la réponse) — ce wrapper doit donc être appliqué
// route par route.
export function withRequestLogging<Args extends unknown[]>(handler: RouteHandler<Args>): RouteHandler<Args> {
  return async (request: Request, ...args: Args): Promise<Response> => {
    const correlationId = resolveCorrelationId(request.headers);
    const start = performance.now();

    return runWithCorrelationId(correlationId, async () => {
      let status = 500;
      try {
        const response = await handler(request, ...args);
        status = response.status;
        response.headers.set(REQUEST_ID_HEADER, correlationId);
        return response;
      } finally {
        const duration_ms = Math.round((performance.now() - start) * 100) / 100;
        logger.info("requête traitée", {
          method: request.method,
          path: new URL(request.url).pathname,
          status,
          duration_ms,
        });
      }
    });
  };
}
