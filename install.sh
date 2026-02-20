#!/usr/bin/env bash
# ABOUTME: Installs iterm2-dimmer by creating a venv and symlinking files into place.
# ABOUTME: Targets: ~/.config/iterm2-dimmer/ and ~/Library/Application Support/iTerm2/Scripts/.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$REPO_DIR/src"
CONFIG_DIR="$HOME/.config/iterm2-dimmer"
SCRIPTS_DIR="$HOME/Library/Application Support/iTerm2/Scripts"
AUTOLAUNCH_DIR="$SCRIPTS_DIR/AutoLaunch"

echo "Installing iterm2-dimmer from $REPO_DIR"

# Create target directories
mkdir -p "$CONFIG_DIR"
mkdir -p "$SCRIPTS_DIR"
mkdir -p "$AUTOLAUNCH_DIR"

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

# Symlink core files to ~/.config/iterm2-dimmer/
for f in taskmaster_triggers.py dimmer.py run.sh; do
    target="$CONFIG_DIR/$f"
    if [ -e "$target" ] && [ ! -L "$target" ]; then
        echo "  Backing up existing $target to $target.bak"
        mv "$target" "$target.bak"
    fi
    ln -sf "$SRC_DIR/$f" "$target"
    echo "  Linked $f -> $target"
done

# Symlink iTerm2 scripts
for script in toggle_taskmaster_dim.py; do
    target="$SCRIPTS_DIR/$script"
    if [ -e "$target" ] && [ ! -L "$target" ]; then
        mv "$target" "$target.bak"
    fi
    ln -sf "$SRC_DIR/scripts/$script" "$target"
    echo "  Linked $script -> $target"
done

target="$AUTOLAUNCH_DIR/taskmaster_dim.py"
if [ -e "$target" ] && [ ! -L "$target" ]; then
    mv "$target" "$target.bak"
fi
ln -sf "$SRC_DIR/scripts/taskmaster_dim.py" "$target"
echo "  Linked taskmaster_dim.py -> $target"

# Make run.sh executable
chmod +x "$SRC_DIR/run.sh"

echo ""
echo "Done. Restart iTerm2 (or reload Scripts) to activate the AutoLaunch daemon."
echo "CLI usage: $CONFIG_DIR/run.sh on|off|daemon"
