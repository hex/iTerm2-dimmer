# iterm2-dimmer

Dims [TASKMASTER](https://github.com/blader/taskmaster) stop hook output in iTerm2 using phrase-based HighlightLine triggers. The dim color is computed dynamically from each session's profile colors, so it works with any color scheme and adapts to profile switches and dark/light mode changes.

## What it does

TASKMASTER's stop hook prints a multi-line checklist every time a Claude Code agent tries to stop. This is useful for the agent but noisy for humans. iterm2-dimmer makes that output nearly invisible by coloring it close to your terminal's background color.

The dimmer installs iTerm2 triggers (HighlightLine rules) on each session that match short phrases from the stop hook output. Triggers are session-local and don't modify your saved profiles.

## Components

- **AutoLaunch daemon** -- starts with iTerm2, applies triggers to all sessions, watches for new sessions, profile changes, and OS theme changes
- **Toggle script** -- appears in iTerm2's Scripts menu, toggles dimming on/off with a confirmation alert
- **CLI tool** -- `run.sh on|off|daemon` for scripted control

## Install

### From source (recommended)

```bash
git clone https://github.com/hex/iterm2-dimmer.git ~/GitHub/iterm2-dimmer
cd ~/GitHub/iterm2-dimmer
./install.sh
```

### Homebrew

```bash
brew tap hex/tap
brew install --head iterm2-dimmer
iterm2-dimmer install
```

### iTerm2 Script Import

Download `taskmaster_dim.its` and/or `toggle_taskmaster_dim.its` from the [releases page](https://github.com/hex/iterm2-dimmer/releases), then import via iTerm2 > Scripts > Import.

Note: `.its` imports only install the iTerm2 scripts. For the CLI tool, use one of the other install methods.

## Uninstall

```bash
cd ~/GitHub/iterm2-dimmer
./uninstall.sh
```

Or if installed via Homebrew:

```bash
iterm2-dimmer uninstall
brew uninstall iterm2-dimmer
brew untap hex/tap
```

## Configuration

Edit `src/taskmaster_triggers.py` to adjust:

- **`DIM_FACTOR`** (default `0.25`) -- how visible the dimmed text is. `0.0` = invisible, `1.0` = full brightness.
- **`PHRASES`** -- the list of text fragments to match. Short, wrap-resistant fragments work best.

After editing, run `run.sh off && run.sh on` (or restart iTerm2) to reapply.

## Requirements

- iTerm2 with Python Runtime enabled (Preferences > General > Magic > Enable Python API)
- Python 3.9+
- macOS

## How it works

Each phrase in `PHRASES` is converted to a null-safe regex (spaces become `[\x00 ]` to match Claude Code's TUI rendering) and installed as an iTerm2 HighlightLine trigger. The trigger's text color is interpolated between the session's background and foreground colors at `DIM_FACTOR`, making the text blend into the background.

The AutoLaunch daemon monitors three things concurrently:
- **New sessions** -- applies triggers immediately
- **Profile changes** -- recomputes the dim color when a session's profile changes (e.g., switching from a dark to light profile)
- **Theme changes** -- recomputes all sessions' dim colors when macOS dark/light mode toggles
