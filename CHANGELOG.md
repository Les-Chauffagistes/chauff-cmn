# Changelog

Toutes les versions notables de `chauff-cmn` sont documentées ici.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/) et le
projet respecte [Semantic Versioning](https://semver.org/lang/fr/). Une seule
version est taguée pour les deux packages (pip et npm) même si un seul des
deux a changé.

## [Unreleased]

### Added
- Schéma OpenAPI initial avec le type partagé `ApiError`.
- Génération des modèles Python (Pydantic) et TypeScript depuis ce schéma.
- Wrapper de logging JSON pour Python (loguru) et TypeScript (remplaçant `console`).
