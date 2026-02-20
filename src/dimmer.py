#!/usr/bin/env python3
# ABOUTME: Dims TASKMASTER stop hook output in iTerm2 via HighlightLine triggers.
# ABOUTME: Supports --once (apply), --off (remove), or daemon mode (watch new sessions).

import sys
import iterm2

from taskmaster_triggers import apply_to_session, remove_from_session


async def main(connection):
    app = await iterm2.async_get_app(connection)
    off_mode = "--off" in sys.argv

    updated = 0
    errors = 0
    for window in app.terminal_windows:
        for tab in window.tabs:
            for session in tab.sessions:
                try:
                    if off_mode:
                        await remove_from_session(session)
                    else:
                        await apply_to_session(session)
                    updated += 1
                except Exception as e:
                    errors += 1
                    print(f"  Error on {session.session_id}: {e}", file=sys.stderr)

    action = "Removed triggers from" if off_mode else "Applied triggers to"
    print(f"{action} {updated} sessions ({errors} errors)")

    if "--once" in sys.argv or off_mode:
        return

    print("Watching for new sessions... (Ctrl-C to stop)")
    async with iterm2.NewSessionMonitor(connection) as mon:
        while True:
            session_id = await mon.async_get()
            session = app.get_session_by_id(session_id)
            if session:
                try:
                    await apply_to_session(session)
                    print(f"  Applied to new session {session_id}")
                except Exception as e:
                    print(f"  Error on {session_id}: {e}", file=sys.stderr)


if "--once" in sys.argv or "--off" in sys.argv:
    iterm2.run_until_complete(main)
else:
    iterm2.run_forever(main)
