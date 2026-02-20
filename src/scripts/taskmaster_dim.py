#!/usr/bin/env python3
# ABOUTME: Auto-dims TASKMASTER stop hook output via phrase-based HighlightLine triggers.
# ABOUTME: Watches for new sessions, profile changes, and theme changes to keep dim colors current.

import sys
import os
import asyncio

sys.path.insert(0, os.path.expanduser("~/.config/iTerm2-dimmer"))

import iterm2
from taskmaster_triggers import apply_to_session


async def watch_profile(connection, session):
    """Reapply triggers when a session's profile changes (colors may differ)."""
    async with iterm2.VariableMonitor(
        connection,
        iterm2.VariableScopes.SESSION,
        "profileName",
        session.session_id,
    ) as mon:
        while True:
            await mon.async_get()
            try:
                await apply_to_session(session)
            except Exception:
                pass


async def watch_theme(connection):
    """Reapply triggers to all sessions when OS dark/light mode changes."""
    app = await iterm2.async_get_app(connection)
    async with iterm2.VariableMonitor(
        connection,
        iterm2.VariableScopes.APP,
        "effectiveTheme",
        None,
    ) as mon:
        while True:
            await mon.async_get()
            for window in app.terminal_windows:
                for tab in window.tabs:
                    for session in tab.sessions:
                        try:
                            await apply_to_session(session)
                        except Exception:
                            pass


async def watch_new_sessions(connection):
    """Apply triggers to new sessions and start per-session profile watchers."""
    app = await iterm2.async_get_app(connection)
    async with iterm2.NewSessionMonitor(connection) as mon:
        while True:
            session_id = await mon.async_get()
            session = app.get_session_by_id(session_id)
            if session:
                try:
                    await apply_to_session(session)
                except Exception:
                    pass
                asyncio.create_task(watch_profile(connection, session))


async def main(connection):
    app = await iterm2.async_get_app(connection)

    # Apply to all existing sessions and start per-session profile watchers
    for window in app.terminal_windows:
        for tab in window.tabs:
            for session in tab.sessions:
                try:
                    await apply_to_session(session)
                except Exception:
                    pass
                asyncio.create_task(watch_profile(connection, session))

    # Run theme watcher and new-session watcher concurrently
    await asyncio.gather(
        watch_theme(connection),
        watch_new_sessions(connection),
    )


iterm2.run_forever(main)
