#!/usr/bin/env bash
set -u
cd /home/leslie/Documents/Qoder/2026-07-29/chat-2/demo-video || exit 1
export PRODUCER_HEADLESS_SHELL_PATH=$(which chromium)
export HF_DE_PARALLEL_ROUTER=false
echo "RENDER_STARTED $(date +%s)" > /tmp/hf-render4.log
npx --yes hyperframes render --output output.mp4 >> /tmp/hf-render4.log 2>&1
echo "RENDER_EXIT=$?" >> /tmp/hf-render4.log
