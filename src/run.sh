#!/usr/bin/env bash
# ABOUTME: Toggle iTerm2 TASKMASTER dimmer on/off.
# ABOUTME: Usage: run.sh on | off | daemon
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="$SCRIPT_DIR/.venv/bin/python3"

case "${1:-on}" in
  on)
    exec "$PYTHON" "$SCRIPT_DIR/dimmer.py" --once
    ;;
  off)
    exec "$PYTHON" "$SCRIPT_DIR/dimmer.py" --off
    ;;
  daemon)
    exec "$PYTHON" "$SCRIPT_DIR/dimmer.py"
    ;;
  *)
    echo "Usage: run.sh [on|off|daemon]"
    exit 1
    ;;
esac
