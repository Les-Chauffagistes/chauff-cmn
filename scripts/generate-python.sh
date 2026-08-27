#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

datamodel-codegen \
  --input openapi/schema.yaml \
  --input-file-type openapi \
  --output python/src/chauff_cmn/models/__init__.py \
  --output-model-type pydantic_v2.BaseModel \
  --use-schema-description \
  --target-python-version 3.10 \
  --custom-file-header "# Généré par scripts/generate-python.sh à partir de openapi/schema.yaml — ne pas éditer à la main."
