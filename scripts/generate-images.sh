#!/usr/bin/env bash
set -euo pipefail

# Generate WebP and AVIF variants for all images in static/images/
# Requires: cwebp (from webp), avifenc (from libavif / libavif-bin)

STATIC_DIR="${1:-static/images}"
WEBP_QUALITY=80
AVIF_SPEED=6

convert_image() {
  local src="$1"
  local base="${src%.*}"
  local webp="${base}.webp"
  local avif="${base}.avif"

  # WebP
  if [ ! -f "$webp" ] || [ "$src" -nt "$webp" ]; then
    echo "  WebP: $(basename "$webp")"
    cwebp -q "$WEBP_QUALITY" -m 6 -quiet "$src" -o "$webp" 2>/dev/null || true
  fi

  # AVIF
  if [ ! -f "$avif" ] || [ "$src" -nt "$avif" ]; then
    echo "  AVIF: $(basename "$avif")"
    avifenc -s "$AVIF_SPEED" -j all -q 65 "$src" "$avif" 2>/dev/null || true
  fi
}

echo "Generating WebP and AVIF variants in ${STATIC_DIR}..."
count=0

while IFS= read -r -d '' file; do
  echo "$(basename "$file")"
  convert_image "$file"
  count=$((count + 1))
done < <(find "$STATIC_DIR" -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) -print0)

echo "Done. Processed ${count} images."
