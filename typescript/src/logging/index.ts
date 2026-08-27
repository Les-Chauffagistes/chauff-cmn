type LogLevel = "debug" | "info" | "warn" | "error";

interface LoggerState {
  service: string;
  correlationId: string | null;
}

const state: LoggerState = { service: "unknown", correlationId: null };

export function configure(options: { service: string }): void {
  state.service = options.service;
}

function write(level: LogLevel, args: unknown[]): void {
  const [message, ...rest] = args;
  const meta = rest.length === 1 && typeof rest[0] === "object" && rest[0] !== null ? rest[0] : rest.length ? { args: rest } : undefined;

  const payload = {
    timestamp: new Date().toISOString(),
    level: level.toUpperCase(),
    service: state.service,
    message: typeof message === "string" ? message : JSON.stringify(message),
    correlation_id: state.correlationId,
    ...(meta ? { meta } : {}),
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
