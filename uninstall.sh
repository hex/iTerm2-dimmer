#!/usr/bin/env bash
# ABOUTME: Removes iTerm2-dimmer symlinks and optionally the venv.
# ABOUTME: Does not delete the repo itself.
set -euo pipefail

CONFIG_DIR="$HOME/.config/iTerm2-dimmer"
SCRIPTS_DIR="$HOME/Library/Application Support/iTerm2/Scripts"
AUTOLAUNCH_DIR="$SCRIPTS_DIR/AutoLaunch"
SUBMENU_DIR="$SCRIPTS_DIR/iTerm2 Dimmer"

echo "Uninstalling iTerm2-dimmer"

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

# Remove current symlinks
for target in \
    "$SUBMENU_DIR/Toggle Taskmaster.py" \
    "$AUTOLAUNCH_DIR/Taskmaster.py" \
    "$SCRIPTS_DIR/toggle_taskmaster_dim.py" \
    "$AUTOLAUNCH_DIR/taskmaster_dim.py"; do
    if [ -L "$target" ]; then
        rm "$target"
        echo "  Removed $target"
    fi
done

# Remove submenu directory if empty
if [ -d "$SUBMENU_DIR" ] && [ -z "$(ls -A "$SUBMENU_DIR")" ]; then
    rmdir "$SUBMENU_DIR"
    echo "  Removed empty $SUBMENU_DIR"
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
