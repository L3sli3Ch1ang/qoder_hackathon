#!/usr/bin/env bash
set -u
cd /home/leslie/Documents/Qoder/2026-07-29/chat-2/demo-video || exit 1
{
  echo "=== CROP top 220px of raw candidate screenshot (header region) ==="
  ffmpeg -y -i assets/screenshot-candidate.png -vf "crop=1920:220:0:0" /tmp/crop-header.png 2>&1 | tail -1
  ls -la /tmp/crop-header.png
} > /tmp/crop.txt 2>&1
echo "CROP_EXIT=$?" >> /tmp/crop.txt
