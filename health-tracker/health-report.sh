#!/bin/bash
# Health Report Runner - for cron jobs
# Usage: ./health-report.sh [daily|weekly|compact]
# Sends the report to stdout for cron delivery

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODE="${1:-daily}"
TARGET_DATE="${2:-$(date +%Y-%m-%d)}"

# Run the parser - export.xml regex parsing doesn't need expat
python3 "$SCRIPT_DIR/health-parser.py" "$TARGET_DATE" "$MODE" 2>/dev/null

exit $?
