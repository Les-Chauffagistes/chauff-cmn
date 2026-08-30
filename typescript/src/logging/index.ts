import { trace } from "@opentelemetry/api";

type LogLevel = "debug" | "info" | "warn" | "error";

interface LoggerState {
  service: string;
}

const state: LoggerState = { service: "unknown" };

export function configure(options: { service: string }): void {
  state.service = options.service;
}

function write(level: LogLevel, args: unknown[]): void {
  const [first, ...rest] = args;
  // JSON.stringify(error) donne "{}" (message/stack ne sont pas énumérables) :
  // on extrait le message et la stack explicitement, comme le fait Python
  // avec record["exception"].
  const error = first instanceof Error ? first : undefined;
  const message = error ? error.message : typeof first === "string" ? first : JSON.stringify(first);
  const meta = rest.length === 1 && typeof rest[0] === "object" && rest[0] !== null ? rest[0] : rest.length ? { args: rest } : undefined;

  // trace_id/span_id proviennent du span OTel actif (posé par
  // withRequestLogging via `startActiveSpan`), pas d'un identifiant maison.
  const spanContext = trace.getActiveSpan()?.spanContext();

  const payload = {
    timestamp: new Date().toISOString(),
    level: level.toUpperCase(),
    service: state.service,
    message,
    trace_id: spanContext?.traceId ?? null,
    span_id: spanContext?.spanId ?? null,
    // Éclaté au top-level plutôt que sous une clé `meta`, pour matcher
    // record["extra"] côté Python (logger.bind(...) devient des clés JSON
    // top-level, voir _make_sink dans logging/__init__.py).
    ...(meta ? meta : {}),
    ...(error?.stack ? { exception: error.stack } : {}),
  };

  process.stdout.write(JSON.stringify(payload) + "\n");
}

// Drop-in replacement for `console`: same method names, so migrating a call site is a `console.` -> `logger.` rename.
export const logger = {
  log: (...args: unknown[]) => write("info", args),
  info: (...args: unknown[]) => write("info", args),
  warn: (...args: unknown[]) => write("warn", args),
  error: (...args: unknown[]) => write("error", args),
  debug: (...args: unknown[]) => write("debug", args),
};
