# Changelog

Toutes les versions notables de `chauff-cmn` sont documentées ici.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) et le
projet respecte [Semantic Versioning](https://semver.org/lang/fr/). Une seule
version est taguée pour les deux packages (pip et npm) même si un seul des
deux a changé.

## [Unreleased]

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
