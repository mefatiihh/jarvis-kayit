#!/bin/bash
# Daily git auto-backup
cd /Users/fatihyasar/.openclaw/workspace

# Only commit if there are changes
if [ -n "$(git status --porcelain)" ]; then
    git add -A
    git commit -m "Günlük yedek: $(date +%Y-%m-%d)"
    git push 2>&1 | tail -3
    echo "✅ Yedeklendi: $(date +%Y-%m-%d\ %H:%M)"
else
    echo "ℹ️  Değişiklik yok, yedek gerekmez."
fi
