# Changelog

Toutes les versions notables de `chauff-cmn` sont documentées ici.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) et le
projet respecte [Semantic Versioning](https://semver.org/lang/fr/). Une seule
version est taguée pour les deux packages (pip et npm) même si un seul des
deux a changé.

## [Unreleased]

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
