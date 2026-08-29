import { AsyncLocalStorage } from "node:async_hooks";

export const TRACEPARENT_HEADER = "traceparent";

interface TraceStore {
  traceId: string;
}

// Portée par requête, façon contextvar Python : posée par le call site qui
// englobe une requête (ex. withRequestLogging), lue par write() dans
// index.ts pour injecter trace_id dans CHAQUE ligne de log émise pendant le
// traitement, pas seulement une ligne dédiée au middleware.
const storage = new AsyncLocalStorage<TraceStore>();

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

const HEX_32_RE = /^[0-9a-fA-F]{32}$/;
const ALL_ZERO_TRACE_ID = "0".repeat(32);

// Extrait le trace-id d'une valeur de header `traceparent` (W3C Trace
// Context) valide, sinon undefined.
//
// Format attendu: `<version 2 hex>-<trace-id 32 hex>-<parent-id 16 hex>-
// <flags 2 hex>`, ex. `00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`.
// On ne valide que ce dont on a besoin : au moins 4 segments, trace-id de 32
// caractères hexadécimaux, pas entièrement à zéro (valeur invalide selon la
// spec W3C).
function parseTraceparent(value: string | undefined): string | undefined {
  if (!value) return undefined;
  const parts = value.split("-");
  if (parts.length < 4) return undefined;
  const traceId = parts[1];
  if (!HEX_32_RE.test(traceId)) return undefined;
  if (traceId.toLowerCase() === ALL_ZERO_TRACE_ID) return undefined;
  return traceId.toLowerCase();
}

function randomHex(byteLength: number): string {
  const bytes = new Uint8Array(byteLength);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
}

export function generateTraceId(): string {
  return randomHex(16); // 32 caractères hex
}

export function generateSpanId(): string {
  return randomHex(8); // 16 caractères hex
}

export function formatTraceparent(traceId: string): string {
  return `00-${traceId}-${generateSpanId()}-01`;
}

// Réutilise le trace-id du `traceparent` entrant s'il est valide, sinon en
// génère un nouveau — équivalent de resolve_trace_id côté Python. Ne retourne
// jamais une chaîne vide.
export function resolveTraceId(headers: HeaderSource): string {
  return parseTraceparent(readHeader(headers, TRACEPARENT_HEADER)) ?? generateTraceId();
}

export function runWithTraceId<T>(traceId: string, fn: () => T): T {
  return storage.run({ traceId }, fn);
}

export function getTraceId(): string | null {
  return storage.getStore()?.traceId ?? null;
}
