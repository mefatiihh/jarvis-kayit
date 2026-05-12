#!/bin/bash
# Evening Health Report Generator - for cron delivery
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TODAY=$(date +%Y-%m-%d)

python3 "$SCRIPT_DIR/health-parser.py" "$TODAY" daily 2>/dev/null

if [ $? -ne 0 ]; then
    echo "📊 $TODAY"
    echo "─" * 28
    echo ""
    echo "⚠️  Bugün için sağlık verisi bulunamadı."
    echo "💡 iPhone'dan Health Auto Export'u çalıştırmayı unutma."
fi
