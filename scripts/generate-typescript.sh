#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

{
  echo "// Généré par scripts/generate-typescript.sh à partir de openapi/schema.yaml — ne pas éditer à la main."
  (cd typescript && npx openapi-typescript ../openapi/schema.yaml)
} > typescript/src/models/schema.ts
