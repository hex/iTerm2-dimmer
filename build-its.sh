#!/usr/bin/env bash
# ABOUTME: Builds iTerm2 .its archives for script import.
# ABOUTME: Creates Taskmaster.its (AutoLaunch) and Toggle Taskmaster.its (toggle).
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
echo "Building Taskmaster.its..."
STAGE="$BUILD_DIR/Taskmaster"
mkdir -p "$STAGE"
strip_sys_path "$SRC_DIR/scripts/taskmaster_dim.py" > "$STAGE/Taskmaster.py"
cp "$SRC_DIR/taskmaster_triggers.py" "$STAGE/"
(cd "$BUILD_DIR" && zip -qr "$REPO_DIR/Taskmaster.its" Taskmaster/)
echo "  Created Taskmaster.its"

# Build toggle .its
echo "Building Toggle Taskmaster.its..."
STAGE="$BUILD_DIR/Toggle Taskmaster"
mkdir -p "$STAGE"
strip_sys_path "$SRC_DIR/scripts/toggle_taskmaster_dim.py" > "$STAGE/Toggle Taskmaster.py"
cp "$SRC_DIR/taskmaster_triggers.py" "$STAGE/"
(cd "$BUILD_DIR" && zip -qr "$REPO_DIR/Toggle Taskmaster.its" "Toggle Taskmaster/")
echo "  Created Toggle Taskmaster.its"

rm -rf "$BUILD_DIR"
echo "Done."
