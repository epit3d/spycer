#!/usr/bin/env bash
set -euo pipefail

export DISPLAY="${DISPLAY:-:1}"
export XVFB_WHD="${XVFB_WHD:-1600x900x24}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp/runtime-spycer}"

mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"

Xvfb "$DISPLAY" -screen 0 "$XVFB_WHD" -ac +extension GLX +render -noreset &
fluxbox >/tmp/fluxbox.log 2>&1 &
x11vnc -display "$DISPLAY" -forever -shared -rfbport 5900 -nopw >/tmp/x11vnc.log 2>&1 &
websockify --web /usr/share/novnc 6080 localhost:5900 >/tmp/novnc.log 2>&1 &

cd /app
exec python main.py
