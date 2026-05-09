#!/bin/bash
# SFX Hunter — Download sound effect from URL and organize by category
# Usage: bash download_sfx.sh <url> <category> [filename]
# Example: bash download_sfx.sh "https://example.com/sound.mp3" "Whooshes" "cinematic-whoosh-01"

set -euo pipefail

URL="${1:?Error: Please provide a download URL}"
CATEGORY="${2:?Error: Please provide a category (Whooshes, Impacts, Risers, etc.)}"
FILENAME="${3:-}"

SFX_BASE="${SFX_LIBRARY:-$HOME/SFX_Library}"
DEST_DIR="$SFX_BASE/$CATEGORY"

mkdir -p "$DEST_DIR"

if [ -z "$FILENAME" ]; then
    FILENAME=$(basename "$URL" | sed 's/[?&].*//' | sed 's/\.[^.]*$//')
    FILENAME="${FILENAME:-sfx_$(date +%s)}"
fi

# Get file extension from URL
EXT="${URL##*.}"
EXT=$(echo "$EXT" | sed 's/[?&].*//' | tr '[:upper:]' '[:lower:]')

# Default to mp3 if extension not recognized
case "$EXT" in
    mp3|wav|ogg|aac|m4a|flac|wma)
        ;;
    *)
        EXT="mp3"
        ;;
esac

OUTPUT="$DEST_DIR/${FILENAME}.${EXT}"

echo "🎧 SFX Hunter — Downloading..."
echo "  URL:      $URL"
echo "  Category: $CATEGORY"
echo "  Output:   $OUTPUT"

if command -v curl &>/dev/null; then
    curl -L -o "$OUTPUT" "$URL" --progress-bar
elif command -v wget &>/dev/null; then
    wget -O "$OUTPUT" "$URL"
else
    echo "❌ Neither curl nor wget found. Install one of them."
    exit 1
fi

# Show file info
FILE_SIZE=$(du -h "$OUTPUT" | cut -f1)
echo "✅ Downloaded: $OUTPUT ($FILE_SIZE)"

# Get audio info if ffprobe available
if command -v ffprobe &>/dev/null; then
    echo ""
    echo "📊 Audio Info:"
    ffprobe -v quiet -print_format json -show_streams "$OUTPUT" 2>/dev/null | \
        python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    for s in d.get('streams', []):
        if s.get('codec_type') == 'audio':
            print(f\"  Format: {s.get('codec_name', '?')}\")
            print(f\"  Sample Rate: {s.get('sample_rate', '?')} Hz\")
            print(f\"  Channels: {s.get('channels', '?')}\")
            print(f\"  Duration: {float(s.get('duration', 0)):.1f}s\")
            print(f\"  Bitrate: {int(s.get('bit_rate', 0))/1000:.0f} kbps\")
except: pass
" 2>/dev/null || true
fi

echo ""
echo "📁 Library: $SFX_BASE"
ls -1 "$DEST_DIR" 2>/dev/null | head -10
echo "---"
echo "✅ Done!"
