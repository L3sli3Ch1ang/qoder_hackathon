#!/usr/bin/env bash
set -u
cd /home/leslie/Documents/Qoder/2026-07-29/chat-2 || exit 1
LOG=/tmp/narrate2.log
echo "NARRATE_STARTED $(date +%s)" > "$LOG"

# Pick a python that has edge_tts available
PY=""
for cand in .venv/bin/python python3 python; do
  if "$cand" -c "import edge_tts" >/dev/null 2>&1; then
    PY="$cand"
    break
  fi
done
echo "PYTHON_CHOSEN=$PY" >> "$LOG"
if [ -z "$PY" ]; then
  echo "NO_PYTHON_WITH_EDGE_TTS" >> "$LOG"
  echo "NARRATE_EXIT=1" >> "$LOG"
  exit 1
fi

"$PY" demo-video/narration/build_narration.py >> "$LOG" 2>&1
echo "NARRATE_EXIT=$?" >> "$LOG"
