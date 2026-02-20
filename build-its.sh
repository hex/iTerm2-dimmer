#!/usr/bin/env bash
# ABOUTME: Builds iTerm2 .its archives for script import.
# ABOUTME: Creates taskmaster_dim.its (AutoLaunch) and toggle_taskmaster_dim.its (toggle).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$REPO_DIR/src"
BUILD_DIR="$REPO_DIR/build"

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Strip sys.path lines from a script for .its packaging (shared module is bundled alongside)
strip_sys_path() {
    sed '/^import sys$/d; /^import os$/d; /^sys\.path\.insert/d' "$1" \
        | sed '/^$/N;/^\n$/d'
}

# Build AutoLaunch .its
echo "Building taskmaster_dim.its..."
STAGE="$BUILD_DIR/taskmaster_dim"
mkdir -p "$STAGE"
strip_sys_path "$SRC_DIR/scripts/taskmaster_dim.py" > "$STAGE/taskmaster_dim.py"
cp "$SRC_DIR/taskmaster_triggers.py" "$STAGE/"
(cd "$BUILD_DIR" && zip -qr "$REPO_DIR/taskmaster_dim.its" taskmaster_dim/)
echo "  Created taskmaster_dim.its"

# Build toggle .its
echo "Building toggle_taskmaster_dim.its..."
STAGE="$BUILD_DIR/toggle_taskmaster_dim"
mkdir -p "$STAGE"
strip_sys_path "$SRC_DIR/scripts/toggle_taskmaster_dim.py" > "$STAGE/toggle_taskmaster_dim.py"
cp "$SRC_DIR/taskmaster_triggers.py" "$STAGE/"
(cd "$BUILD_DIR" && zip -qr "$REPO_DIR/toggle_taskmaster_dim.its" toggle_taskmaster_dim/)
echo "  Created toggle_taskmaster_dim.its"

rm -rf "$BUILD_DIR"
echo "Done."
