#!/usr/bin/env bash
# Assemble the per-scene PNG frames in $PLY_FRAMES into an animated GIF.
# Usage: capture/make-gif.sh [out.gif]   (env: HOLD seconds, WIDTH px)
set -euo pipefail
FRAMES="${PLY_FRAMES:-/tmp/ply-frames}"
OUT="${1:-docs/demo.gif}"
HOLD="${HOLD:-2.4}"
WIDTH="${WIDTH:-1200}"

shopt -s nullglob
imgs=("$FRAMES"/[0-9][0-9]-*.png)
if [ ${#imgs[@]} -eq 0 ]; then
    echo "no frames (NN-*.png) in $FRAMES" >&2
    exit 1
fi

LIST="$(mktemp)"
: > "$LIST"
for f in "${imgs[@]}"; do
    printf "file '%s'\nduration %s\n" "$f" "$HOLD" >> "$LIST"
done
# concat demuxer holds the final image only if it is listed once more.
printf "file '%s'\n" "${imgs[${#imgs[@]}-1]}" >> "$LIST"

ffmpeg -y -f concat -safe 0 -i "$LIST" \
    -vf "scale=${WIDTH}:-1:flags=lanczos,split[s0][s1];[s0]palettegen=stats_mode=diff[p];[s1][p]paletteuse=dither=bayer" \
    -loop 0 "$OUT"

rm -f "$LIST"
echo "wrote $OUT"
ls -la "$OUT"
