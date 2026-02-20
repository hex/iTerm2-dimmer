#!/usr/bin/env bash
# ABOUTME: Removes iterm2-dimmer symlinks and optionally the venv.
# ABOUTME: Does not delete the repo itself.
set -euo pipefail

CONFIG_DIR="$HOME/.config/iterm2-dimmer"
SCRIPTS_DIR="$HOME/Library/Application Support/iTerm2/Scripts"
AUTOLAUNCH_DIR="$SCRIPTS_DIR/AutoLaunch"

echo "Uninstalling iterm2-dimmer"

# Remove triggers from active sessions first
if [ -x "$CONFIG_DIR/run.sh" ]; then
    echo "Removing triggers from active sessions..."
    "$CONFIG_DIR/run.sh" off 2>/dev/null || true
fi

# Remove symlinks (only if they are symlinks, not regular files)
for f in taskmaster_triggers.py dimmer.py run.sh; do
    target="$CONFIG_DIR/$f"
    if [ -L "$target" ]; then
        rm "$target"
        echo "  Removed $target"
    fi
done

target="$SCRIPTS_DIR/toggle_taskmaster_dim.py"
if [ -L "$target" ]; then
    rm "$target"
    echo "  Removed $target"
fi

target="$AUTOLAUNCH_DIR/taskmaster_dim.py"
if [ -L "$target" ]; then
    rm "$target"
    echo "  Removed $target"
fi

# Ask about venv
if [ -d "$CONFIG_DIR/.venv" ]; then
    read -rp "Remove virtual environment at $CONFIG_DIR/.venv? [y/N] " answer
    if [[ "$answer" =~ ^[Yy] ]]; then
        rm -rf "$CONFIG_DIR/.venv"
        echo "  Removed .venv"
    fi
fi

# Clean up empty config dir
if [ -d "$CONFIG_DIR" ] && [ -z "$(ls -A "$CONFIG_DIR")" ]; then
    rmdir "$CONFIG_DIR"
    echo "  Removed empty $CONFIG_DIR"
fi

echo "Done. Restart iTerm2 to fully deactivate."
