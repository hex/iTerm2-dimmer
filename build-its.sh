#!/usr/bin/env bash
# ABOUTME: Builds signed iTerm2 .its archives for script import.
# ABOUTME: Inlines triggers.py into each script and signs with Developer ID certificate.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC_DIR="$REPO_DIR/src"
BUILD_DIR="$REPO_DIR/build"
SIGN_TOOL="$REPO_DIR/tools/iterm2-sign"
IDENTITY="${SIGNING_IDENTITY:-Developer ID Application: Alexandru Geana}"

if [ ! -x "$SIGN_TOOL" ]; then
    echo "Error: sign tool not found at $SIGN_TOOL"
    echo ""
    echo "Build it from iTerm2 source:"
    echo "  git clone --depth 1 --filter=blob:none --sparse https://github.com/gnachman/iTerm2.git /tmp/iterm2-sa"
    echo "  cd /tmp/iterm2-sa && git sparse-checkout set SignedArchive"
    echo "  cd SignedArchive && xcodebuild -scheme sign -configuration Release BUILD_DIR=/tmp/iterm2-sign-build"
    echo "  mkdir -p $REPO_DIR/tools"
    echo "  cp /tmp/iterm2-sign-build/Release/sign $SIGN_TOOL"
    exit 1
fi

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Inline triggers.py into a consumer script, producing a single self-contained .py.
# Strips sys.path hack and import-from-triggers line; prepends triggers.py content.
inline_build() {
    local script="$1"
    local output="$2"

    # Triggers module (keep as-is including its imports)
    cat "$SRC_DIR/triggers.py" > "$output"
    echo "" >> "$output"
    echo "" >> "$output"

    # Consumer script with sys.path and triggers import stripped
    sed '/^import sys$/d
         /^import os$/d
         /^sys\.path\.insert/d
         /^from triggers import/d
         /^# ABOUTME:/d' "$script" \
        | sed '/^$/N;/^\n$/d' >> "$output"
}

# Build and sign one .its archive.
# Args: script_source output_name
build_one() {
    local script="$1"
    local name="$2"

    echo "Building ${name}.its..."
    local py="$BUILD_DIR/${name}.py"
    local zip="$BUILD_DIR/${name}.zip"
    local its="$REPO_DIR/${name}.its"

    inline_build "$script" "$py"
    (cd "$BUILD_DIR" && zip -qj "$zip" "${name}.py")
    "$SIGN_TOOL" "$zip" "$IDENTITY" "$its"
    echo "  Created ${name}.its ($(wc -c < "$its" | tr -d ' ') bytes)"
}

build_one "$SRC_DIR/scripts/taskmaster_dim.py" "Taskmaster"
build_one "$SRC_DIR/scripts/toggle_taskmaster_dim.py" "ToggleTaskmaster"
build_one "$SRC_DIR/scripts/toggle_claude_sessions_dim.py" "ToggleClaudeSessions"

rm -rf "$BUILD_DIR"
echo "Done."
