#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
SOURCE="$ROOT/../AussieEcoLense"
TARGET="$ROOT/gcp/cloudrun_processor"

cp "$SOURCE/model.pt" "$TARGET/model.pt"
cp "$SOURCE/mdv5a.pt" "$TARGET/mdv5a.pt"
cp "$SOURCE/labels.txt" "$TARGET/labels.txt"

echo "Copied model.pt, mdv5a.pt, and labels.txt into gcp/cloudrun_processor."

