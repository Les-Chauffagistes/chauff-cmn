import { AsyncLocalStorage } from "node:async_hooks";

export const REQUEST_ID_HEADER = "X-Request-Id";

interface CorrelationStore {
  correlationId: string;
}

// Portée par requête, façon contextvar Python : posée par le call site qui
// englobe une requête (ex. withRequestLogging), lue par write() dans
// index.ts pour injecter correlation_id dans CHAQUE ligne de log émise
// pendant le traitement, pas seulement une ligne dédiée au middleware.
const storage = new AsyncLocalStorage<CorrelationStore>();

type HeaderSource = Headers | Record<string, string | string[] | undefined>;

function readHeader(headers: HeaderSource, name: string): string | undefined {
  if (typeof (headers as Headers).get === "function") {
    return (headers as Headers).get(name) ?? undefined;
  }
  const record = headers as Record<string, string | string[] | undefined>;
  for (const key of Object.keys(record)) {
    if (key.toLowerCase() === name.toLowerCase()) {
      const value = record[key];
      return Array.isArray(value) ? value[0] : value;
    }
  }
  return undefined;
}

// Réutilise l'id de corrélation entrant s'il existe, sinon en génère un —
// équivalent de resolve_correlation_id côté Python.
export function resolveCorrelationId(headers: HeaderSource): string {
  const existing = readHeader(headers, REQUEST_ID_HEADER);
  return existing && existing.length > 0 ? existing : crypto.randomUUID();
}

export function runWithCorrelationId<T>(correlationId: string, fn: () => T): T {
  return storage.run({ correlationId }, fn);
}

export function getCorrelationId(): string | null {
  return storage.getStore()?.correlationId ?? null;
}
