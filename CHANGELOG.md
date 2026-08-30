# Changelog

Toutes les versions notables de `chauff-cmn` sont documentées ici.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) et le
projet respecte [Semantic Versioning](https://semver.org/lang/fr/). Une seule
version est taguée pour les deux packages (pip et npm) même si un seul des
deux a changé.

## [Unreleased]

## [0.1.0] - 2026-08-30

### Added
- TypeScript : `activeTraceContext()`, `extractTraceContext(headers)`,
  `withTraceContext(ctx, fn)` (module `tracing.ts`, type `Context` réexporté
  de `@opentelemetry/api`) — équivalent typé `Context` de l'ancien
  `resolveTraceId`/`runWithTraceId`, pour les chemins de code qui n'ont pas de
  contexte de trace ambiant posé par un middleware (ex. une Server Action
  Next.js, jamais enveloppée par `withRequestLogging`) : le contexte doit y
  être capturé explicitement (dès l'entrée, ou via `activeTraceContext()`
  quand un span existe déjà plus haut) puis réinjecté explicitement autour
  des appels sortants qui suivent, potentiellement après un `await`
  intermédiaire.
- TypeScript : `setupTracing({ ..., handleShutdownSignal: false })` — désactive
  l'auto-enregistrement du handler `SIGTERM` interne de `setupTracing()`.
  Nécessaire pour tout consommateur qui a déjà sa propre séquence d'arrêt
  (ex. drainage de boucles de fond) : deux handlers `SIGTERM` indépendants,
  dont un qui appelle `process.exit()`, ne s'exécutent pas forcément dans
  l'ordre voulu (Node ne garantit rien entre listeners `once` indépendants).
  Le consommateur appelle alors `shutdownTracing()` lui-même, au bon endroit
  de sa propre séquence d'arrêt.

### Changed
- **Breaking.** La propagation de trace-id maison (`chauff_cmn.logging._trace`
  / `logging/_trace.ts` : `trace_id_var`, `resolve_trace_id`/`resolveTraceId`,
  `bind_trace_id`/`reset_trace_id`/`runWithTraceId`, `TRACEPARENT_HEADER`,
  `format_traceparent`, `generate_trace_id`/`generate_span_id`) est
  entièrement supprimée et remplacée par le SDK OpenTelemetry natif. Jusqu'ici
  ce mécanisme ne faisait que recopier le trace-id d'un service à l'autre pour
  corréler les logs (Loki) — aucun span applicatif n'était créé ni exporté,
  alors que Tempo (`deploy/stacks/core/tempo.yml`) et le tracing OTLP de
  Traefik tournent déjà en infra depuis le 2026-08-29. Un seul mécanisme de
  propagation valait mieux que deux implémentations parallèles du même concept
  W3C Trace Context.
  - Nouveau module `chauff_cmn.tracing` / `tracing.ts` :
    `setup_tracing(service, endpoint=None)` / `setupTracing({ service,
    endpoint? })`, à appeler une fois au démarrage du service, installe un
    `TracerProvider` qui exporte en OTLP/HTTP vers Tempo (`http://tempo:4318`
    par défaut, override via `OTEL_EXPORTER_OTLP_ENDPOINT`) ; et
    `shutdown_tracing()` / `shutdownTracing()` pour flusher les spans
    bufferisés avant l'arrêt du process (à brancher explicitement sur le hook
    d'arrêt du framework côté Python — lifespan FastAPI, `on_cleanup` aiohttp
    — `atexit` seul ne suffit pas sur un `SIGTERM` non intercepté ; géré
    automatiquement via un handler `SIGTERM` côté TypeScript).
  - `RequestLoggingMiddleware`/`request_logging_middleware`/
    `withRequestLogging` créent désormais un vrai span `SERVER` par requête
    (continué depuis le `traceparent` entrant s'il est valide, sinon nouvelle
    trace racine — même politique qu'avant et que Traefik en amont), et
    `create_traced_session`/`traced_trace_config`/`tracedFetch` un vrai span
    `CLIENT` par appel sortant. Tempo affiche donc maintenant une trace
    distribuée détaillée par service, pas seulement le span Traefik en
    périphérie.
  - Le format du champ `trace_id` dans les logs JSON est inchangé (le lien
    Grafana Tempo→Loki, basé sur un substring match, n'est pas affecté) ;
    nouveau champ `span_id` ajouté à côté.
  - Les consommateurs devront migrer : appeler `setup_tracing`/`setupTracing`
    au démarrage et, côté Python, brancher `shutdown_tracing()` sur l'arrêt du
    framework.

## [0.0.11] - 2026-08-29

### Added
- `tracedFetch`, équivalent TypeScript de `create_traced_session()`
  (`chauff_cmn.logging.aiohttp_client`) pour `fetch` : pose `traceparent` sur
  chaque requête sortante, avec le trace-id du contexte de requête entrante
  en cours (ou un nouveau si aucun contexte, par exemple depuis un job de
  fond) et un span-id neuf à chaque appel. Sans ça, un trace démarré côté
  Next.js s'arrêtait à son premier appel `fetch` sortant vers un backend —
  même lacune que celle qui avait motivé `aiohttp_client.py` côté Python.
  Contrairement à `aiohttp` qui expose un objet `ClientSession`/`TraceConfig`
  réutilisable, `fetch` est une fonction unique : `tracedFetch` est donc un
  wrapper de la fonction elle-même (même signature que `fetch` global),
  drop-in replacement à utiliser à la place de `fetch` pour tout appel
  sortant depuis un Server Component ou un route handler.

## [0.0.10] - 2026-08-29

### Changed
- L'id de corrélation (`X-Request-Id`, généré en uuid4 si absent, écho sur la
  réponse) est remplacé par un mécanisme unique basé sur `traceparent` (W3C
  Trace Context). Deux identifiants maison qui se recoupaient sans se
  compléter (aucun des deux ne survivait à un appel sortant entre services)
  n'avaient plus de raison d'exister côte à côte : `traceparent` est déjà le
  format que Traefik pose en entrée de la plateforme, et le standardiser de
  bout en bout évite de traduire entre deux identifiants aux mêmes endroits
  où ça compte (logs, appels sortants). `resolve_trace_id`/`resolveTraceId`
  reprend le trace-id du `traceparent` entrant s'il est valide, en génère un
  nouveau sinon — jamais de valeur nulle, même politique que Traefik
  ("continue le trace existant si présent, sinon en démarre un nouveau"). Le
  sink JSON (Python et TypeScript) expose désormais `trace_id` au lieu de
  `correlation_id`.
- Plus aucun header n'est posé ou échoté sur la réponse HTTP par les
  middlewares serveur (`chauff_cmn.logging.aiohttp`, `chauff_cmn.logging.asgi`,
  `withRequestLogging`) : `traceparent` est un header de requête, pas de
  réponse, et le moins de headers/identifiants transportés est plus simple à
  raisonner que l'écho précédent.
- `python/src/chauff_cmn/logging/_correlation.py` et
  `typescript/src/logging/_correlation.ts` sont renommés en `_trace.py` /
  `_trace.ts` pour refléter le nouveau contenu.

### Added
- `chauff_cmn.logging.aiohttp_client` (extra `aiohttp`) : `traced_trace_config()`
  et `create_traced_session()` posent automatiquement `traceparent` sur
  chaque requête aiohttp sortante, avec le trace-id du contexte de requête
  entrante en cours (ou un nouveau si aucun contexte, par exemple depuis un
  job de fond) et un span-id neuf à chaque appel. Sans ça, un trace démarré
  par un service s'arrêtait à sa première requête sortante — les appels
  inter-services perdaient le fil.

## [0.0.9] - 2026-08-29

### Fixed
- Le logger TypeScript imbriquait les champs additionnels (`method`, `path`,
  `status`, `duration_ms`, etc.) sous une clé `meta` au lieu de les exposer au
  niveau racine du JSON, contrairement au sink Python
  (`logger.bind(...)` y devient des clés top-level). `withRequestLogging`
  produisait donc un format différent de `RequestLoggingMiddleware`/
  `request_logging_middleware` pour les mêmes champs. Les champs additionnels
  sont désormais éclatés au top-level des deux côtés.

## [0.0.8] - 2026-08-29

### Added
- Côté TypeScript, équivalent de la propagation d'id de corrélation Python
  (`AsyncLocalStorage` au lieu d'une `contextvar`) : `resolveCorrelationId`,
  `REQUEST_ID_HEADER`.
- `withRequestLogging`, wrapper de route handler Next.js (App Router) qui logge
  method/path/status/duration_ms et propage `X-Request-Id` — équivalent, au
  niveau d'un handler, de `chauff_cmn.logging.asgi.RequestLoggingMiddleware`.
  Contrairement à `asgi.py`, ne peut pas s'appliquer globalement via
  `middleware.ts` : ce fichier s'exécute avant le handler et ne voit jamais la
  réponse, donc pas de statut/durée disponible à ce niveau côté Next.js.

### Fixed
- Le logger TypeScript sérialisait un objet `Error` passé à `logger.error(e)`
  en `"{}"` (`message`/`stack` ne sont pas énumérables) — tout le contenu de
  l'erreur était perdu. Le message et la stack sont désormais extraits
  explicitement, la stack posée dans un champ `exception` (parité avec le sink
  Python).

## [0.0.7] - 2026-08-28

### Added
- Schéma OpenAPI initial avec le type partagé `ApiError`.
- Génération des modèles Python (Pydantic) et TypeScript depuis ce schéma.
- Wrapper de logging JSON pour Python (loguru) et TypeScript (remplaçant `console`).
- Middleware de log de requêtes structuré (méthode, chemin, statut, durée, id de
  corrélation propagé via `X-Request-Id`) : `chauff_cmn.logging.aiohttp` (extra
  `aiohttp`) et `chauff_cmn.logging.asgi` (FastAPI/Starlette, zéro dépendance
  supplémentaire).
- L'id de corrélation est propagé via une `contextvar` à toutes les lignes de
  log émises pendant une requête (pas seulement celle du middleware) grâce à un
  patcher loguru global — équivalent maison à ce que fait `asgi-correlation-id`
  côté FastAPI, mais partagé entre aiohttp et ASGI sans dépendance
  supplémentaire.

### Changed
- Le sink JSON expose désormais tous les champs bindés via `logger.bind(...)`
  comme clés top-level, pas seulement `correlation_id`.
