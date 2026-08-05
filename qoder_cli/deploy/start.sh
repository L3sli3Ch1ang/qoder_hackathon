#!/bin/sh
set -e

# Honor PORT injected by the host (Render sets PORT; HF Spaces expects 7860).
PORT="${PORT:-7860}"

echo "SkillBridge SG starting on 0.0.0.0:${PORT}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}" --workers 1
