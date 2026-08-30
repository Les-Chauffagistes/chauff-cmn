import { context, propagation, type Context } from "@opentelemetry/api";
import { CompositePropagator, W3CBaggagePropagator, W3CTraceContextPropagator } from "@opentelemetry/core";
import { AsyncLocalStorageContextManager } from "@opentelemetry/context-async-hooks";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { resourceFromAttributes } from "@opentelemetry/resources";
import { BatchSpanProcessor, SimpleSpanProcessor, type SpanExporter } from "@opentelemetry/sdk-trace-base";
import { NodeTracerProvider } from "@opentelemetry/sdk-trace-node";
import { headersGetter } from "./logging/_headers";

export type { Context };

export const DEFAULT_ENDPOINT = "http://tempo:4318";

export interface SetupTracingOptions {
  service: string;
  endpoint?: string;
  /** Réservé aux tests : branche un exporteur (ex. `InMemorySpanExporter`) sur
   * un `SimpleSpanProcessor` (export synchrone à `span.end()`) plutôt que sur
   * le `BatchSpanProcessor` du fonctionnement normal. */
  exporter?: SpanExporter;
  /** Désactive l'auto-enregistrement du handler SIGTERM interne (défaut
   * `true`). À mettre à `false` si le consommateur orchestre déjà son propre
   * arrêt propre (ex. drainage de boucles de fond) — il doit alors appeler
   * `shutdownTracing()` lui-même, dans sa propre séquence, plutôt que de
   * laisser deux handlers SIGTERM indépendants se disputer l'ordre d'arrêt. */
  handleShutdownSignal?: boolean;
}

/** Capture le contexte de trace actif (le span courant, posé par
 * `withRequestLogging` ou un appel englobant à `withTraceContext`), pour le
 * réinjecter plus tard via `withTraceContext` — utile quand un chemin de code
 * (ex. une Server Action Next.js, jamais enveloppée par `withRequestLogging`)
 * doit capturer le contexte tôt puis le réappliquer explicitement autour
 * d'appels sortants plus loin dans l'exécution. */
export function activeTraceContext(): Context {
  return context.active();
}

/** Extrait le contexte de trace d'un `traceparent` entrant (ex. `headers()`
 * d'une Server Action Next.js, qui ne passe par aucun middleware). */
export function extractTraceContext(headers: Headers): Context {
  return propagation.extract(context.active(), headers, headersGetter);
}

/** Réapplique explicitement un contexte capturé plus tôt (voir
 * `activeTraceContext`/`extractTraceContext`) autour de `fn` — équivalent
 * OpenTelemetry de l'ancien `runWithTraceId`. */
export function withTraceContext<T>(ctx: Context, fn: () => T): T {
  return context.with(ctx, fn);
}

let provider: NodeTracerProvider | undefined;

// Propagateur composite W3C explicite : `NodeTracerProvider.register()` ne
// pose PAS de propagateur par défaut (contrairement à l'API OTel Python, qui
// en installe un depuis `OTEL_PROPAGATORS` à l'import), il faut le fournir.
const propagator = new CompositePropagator({
  propagators: [new W3CTraceContextPropagator(), new W3CBaggagePropagator()],
});

export function setupTracing(options: SetupTracingOptions): void {
  const spanProcessor = options.exporter
    ? new SimpleSpanProcessor(options.exporter)
    : new BatchSpanProcessor(
        new OTLPTraceExporter({
          url: `${(options.endpoint ?? process.env.OTEL_EXPORTER_OTLP_ENDPOINT ?? DEFAULT_ENDPOINT).replace(/\/$/, "")}/v1/traces`,
        }),
      );

  provider = new NodeTracerProvider({
    resource: resourceFromAttributes({ "service.name": options.service }),
    spanProcessors: [spanProcessor],
  });

  provider.register({
    contextManager: new AsyncLocalStorageContextManager(),
    propagator,
  });

  // Flush des spans bufferisés par le BatchSpanProcessor avant l'arrêt du
  // process — sans ça les spans en attente sont perdus sur un redéploiement
  // Swarm (SIGTERM). Next.js n'a pas de hook de lifecycle équivalent au
  // lifespan FastAPI / on_cleanup aiohttp côté Python, d'où ce handler
  // process-level par défaut. Si le consommateur a déjà sa propre séquence
  // d'arrêt (ex. drainage de boucles de fond), `handleShutdownSignal: false`
  // désactive ce handler pour éviter deux listeners SIGTERM indépendants qui
  // se disputent l'ordre d'arrêt — le consommateur appelle alors
  // `shutdownTracing()` lui-même, au bon endroit de sa propre séquence.
  if (options.handleShutdownSignal ?? true) {
    process.once("SIGTERM", () => {
      void shutdownTracing().finally(() => process.exit(0));
    });
  }
}

export async function shutdownTracing(): Promise<void> {
  if (provider) {
    await provider.shutdown();
    provider = undefined;
  }
}
