#!/usr/bin/env bash
# ABOUTME: Installs iTerm2-dimmer by creating a venv and symlinking files into place.
# ABOUTME: Targets: ~/.config/iTerm2-dimmer/ and ~/Library/Application Support/iTerm2/Scripts/.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$REPO_DIR/src"
CONFIG_DIR="$HOME/.config/iTerm2-dimmer"
SCRIPTS_DIR="$HOME/Library/Application Support/iTerm2/Scripts"
AUTOLAUNCH_DIR="$SCRIPTS_DIR/AutoLaunch"
SUBMENU_DIR="$SCRIPTS_DIR/iTerm2 Dimmer"

echo "Installing iTerm2-dimmer from $REPO_DIR"

# Migrate config dir casing (case-insensitive FS needs two-step rename)
actual_name=$(ls -1 "$HOME/.config/" 2>/dev/null | grep -xi "iterm2-dimmer" || true)
if [ -n "$actual_name" ] && [ "$actual_name" != "iTerm2-dimmer" ]; then
    echo "  Migrating config dir casing from $actual_name..."
    mv "$HOME/.config/$actual_name" "$HOME/.config/iTerm2-dimmer-migrating"
    mv "$HOME/.config/iTerm2-dimmer-migrating" "$CONFIG_DIR"
fi

# Create target directories
mkdir -p "$CONFIG_DIR"
mkdir -p "$SCRIPTS_DIR"
mkdir -p "$AUTOLAUNCH_DIR"
mkdir -p "$SUBMENU_DIR"

# Create or update venv
install_deps() {
    if command -v uv &>/dev/null; then
        uv pip install --quiet --python "$CONFIG_DIR/.venv/bin/python3" -r "$REPO_DIR/requirements.txt"
    else
        "$CONFIG_DIR/.venv/bin/pip" install --quiet -r "$REPO_DIR/requirements.txt"
    fi
}

if [ ! -d "$CONFIG_DIR/.venv" ]; then
    echo "Creating Python virtual environment..."
    if command -v uv &>/dev/null; then
        uv venv "$CONFIG_DIR/.venv"
    else
        python3 -m venv "$CONFIG_DIR/.venv"
    fi
    install_deps
else
    echo "Virtual environment already exists, updating dependencies..."
    install_deps
fi

# Symlink core files to ~/.config/iTerm2-dimmer/
for f in triggers.py dimmer.py run.sh; do
    target="$CONFIG_DIR/$f"
    if [ -e "$target" ] && [ ! -L "$target" ]; then
        echo "  Backing up existing $target to $target.bak"
        mv "$target" "$target.bak"
    fi
    ln -sf "$SRC_DIR/$f" "$target"
    echo "  Linked $f -> $target"
done

# Remove old-style symlinks from previous installs
for old in "$SCRIPTS_DIR/toggle_taskmaster_dim.py" "$AUTOLAUNCH_DIR/taskmaster_dim.py" "$CONFIG_DIR/taskmaster_triggers.py"; do
    if [ -L "$old" ]; then
        rm "$old"
        echo "  Removed old symlink: $old"
    fi
done

# Symlink iTerm2 scripts with human-friendly names
target="$SUBMENU_DIR/Toggle Taskmaster.py"
if [ -e "$target" ] && [ ! -L "$target" ]; then
    mv "$target" "$target.bak"
fi
ln -sf "$SRC_DIR/scripts/toggle_taskmaster_dim.py" "$target"
echo "  Linked Toggle Taskmaster.py -> $target"

target="$AUTOLAUNCH_DIR/Taskmaster.py"
if [ -e "$target" ] && [ ! -L "$target" ]; then
    mv "$target" "$target.bak"
fi
ln -sf "$SRC_DIR/scripts/taskmaster_dim.py" "$target"
echo "  Linked Taskmaster.py -> $target"

# Make run.sh executable
chmod +x "$SRC_DIR/run.sh"

echo ""
echo "Done. Restart iTerm2 (or reload Scripts) to activate the AutoLaunch daemon."
echo "CLI usage: $CONFIG_DIR/run.sh on|off|daemon"
