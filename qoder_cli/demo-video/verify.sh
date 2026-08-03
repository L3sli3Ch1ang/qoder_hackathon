#!/usr/bin/env bash
set -u
cd /home/leslie/Documents/Qoder/2026-07-29/chat-2/demo-video || exit 1
OUT=/tmp/verify3.txt
FRAME=/tmp/frame87-v3.png
echo "VERIFY_STARTED $(date +%s)" > "$OUT"
{
  echo "=== STREAMS ==="
  ffprobe -v error -show_entries stream=codec_name,codec_type \
    -show_entries format=duration,size -of default=noprint_wrappers=1 output.mp4
  echo "=== AUDIO LEVELS ==="
  ffmpeg -hide_banner -i output.mp4 -map 0:a:0 -af astats=metadata=1:reset=0 -f null - 2>&1 \
    | grep -E "Peak level dB|RMS level dB|Overall"
  echo "=== TOGGLE FRAME 87s ==="
  ffmpeg -y -ss 87 -i output.mp4 -frames:v 1 "$FRAME" 2>&1 | tail -1
  ls -la "$FRAME"
} >> "$OUT" 2>&1
echo "VERIFY_EXIT=$?" >> "$OUT"
