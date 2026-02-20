#!/usr/bin/env python3
# ABOUTME: Toggles claude-sessions dimming on/off across all iTerm2 sessions.
# ABOUTME: Appears in iTerm2's Scripts menu as a clickable toggle.

import sys
import os

sys.path.insert(0, os.path.expanduser("~/.config/iTerm2-dimmer"))

import iterm2
from triggers import apply_dimmer, remove_dimmer, has_dimmer


async def main(connection):
    app = await iterm2.async_get_app(connection)

    session = app.current_terminal_window.current_tab.current_session
    profile = await session.async_get_profile()
    currently_on = has_dimmer(profile, "claude-sessions")

    count = 0
    for window in app.terminal_windows:
        for tab in window.tabs:
            for s in tab.sessions:
                try:
                    if currently_on:
                        await remove_dimmer(s, "claude-sessions")
                    else:
                        await apply_dimmer(s, "claude-sessions")
                    count += 1
                except Exception:
                    pass

    state = "OFF" if currently_on else "ON"
    alert = iterm2.Alert("claude-sessions Dimmer", f"Dimming turned {state} ({count} sessions)")
    await alert.async_run(connection)


iterm2.run_until_complete(main)
