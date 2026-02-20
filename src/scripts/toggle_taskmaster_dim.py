#!/usr/bin/env python3
# ABOUTME: Toggles TASKMASTER dimming on/off across all iTerm2 sessions.
# ABOUTME: Appears in iTerm2's Scripts menu as a clickable toggle.

import sys
import os

sys.path.insert(0, os.path.expanduser("~/.config/iterm2-dimmer"))

import iterm2
from taskmaster_triggers import apply_to_session, remove_from_session, has_dim_triggers


async def main(connection):
    app = await iterm2.async_get_app(connection)

    session = app.current_terminal_window.current_tab.current_session
    profile = await session.async_get_profile()
    currently_on = has_dim_triggers(profile)

    count = 0
    for window in app.terminal_windows:
        for tab in window.tabs:
            for s in tab.sessions:
                try:
                    if currently_on:
                        await remove_from_session(s)
                    else:
                        await apply_to_session(s)
                    count += 1
                except Exception:
                    pass

    state = "OFF" if currently_on else "ON"
    alert = iterm2.Alert("TASKMASTER Dimmer", f"Dimming turned {state} ({count} sessions)")
    await alert.async_run(connection)


iterm2.run_until_complete(main)
