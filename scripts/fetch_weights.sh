#!/usr/bin/env bash
# Downloads trained ONNX weights from the latest GitHub Release into backend/app/lv_outline/weights/
set -euo pipefail
REPO="kartikpagariya25/arterion-lv-outline"
DEST="$(dirname "$0")/../backend/app/lv_outline/weights"
mkdir -p "$DEST"
for f in lv_model.onnx; do
  echo "Downloading $f ..."
  curl -fL --retry 3 -o "$DEST/$f" "https://github.com/$REPO/releases/latest/download/$f"
done
echo "Done."
