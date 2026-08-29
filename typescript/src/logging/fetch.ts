import { TRACEPARENT_HEADER, formatTraceparent, generateTraceId, getTraceId } from "./_trace";

// Wrapper de `fetch` qui pose systématiquement un header `traceparent`
// sortant — équivalent, pour `fetch`, de `create_traced_session()` côté
// Python (aiohttp_client.py). Contrairement à aiohttp qui expose un objet
// `ClientSession`/`TraceConfig` réutilisable, `fetch` est une fonction
// unique : l'équivalent naturel est donc un wrapper de la fonction
// elle-même, drop-in replacement de `fetch` global (même signature).
//
// Reprend le trace_id du contexte de requête entrante en cours s'il y en a
// un (posé par `withRequestLogging`), sinon en génère un nouveau à la volée
// — un appel sortant part toujours avec un traceparent, y compris depuis un
// job de fond hors contexte de requête entrante. Un span-id neuf est généré
// à chaque appel, jamais réutilisé (même politique que
// `_on_request_start` côté aiohttp).
//
// Les headers déjà présents dans `init.headers` (`Headers`, tableau de
// tuples ou objet plat — les trois formes valides de `RequestInit.headers`)
// sont préservés : `traceparent` s'ajoute sans les écraser.
export function tracedFetch(input: string | URL | Request, init?: RequestInit): Promise<Response> {
  const traceId = getTraceId() ?? generateTraceId();
  const headers = new Headers(init?.headers);
  headers.set(TRACEPARENT_HEADER, formatTraceparent(traceId));

  return fetch(input, { ...init, headers });
}
