# ABOUTME: Shared data and functions for iTerm2 TASKMASTER dimming triggers.
# ABOUTME: Used by dimmer.py, toggle_taskmaster_dim.py, and AutoLaunch/taskmaster_dim.py.

import iterm2


# Phrases from the TASKMASTER stop hook, chosen to be short enough to survive
# line-wrapping and specific enough to avoid false positives.
PHRASES = [
    "TASKMASTER",
    "Incomplete tasks or recent",
    "detected in the session",
    "Verify that all work",
    "complete before stopping",
    "Before stopping",
    "do each of these checks",
    "RE-READ THE ORIGINAL",
    "USER MESSAGE",
    "discrete request",
    "acceptance criterion",
    "confirm it is fully",
    "fully addressed",
    "FULLY done",
    "explicitly changed",
    "withdrew a request",
    "told you to stop",
    "treat that item",
    "as resolved",
    "NOT continue working",
    "CHECK THE TASK LIST",
    "Review every task",
    "marked completed",
    "Do it now",
    "user indicated",
    "no longer wanted",
    "CHECK THE PLAN",
    "Walk through each step",
    "skipped or partially",
    "deprioritized",
    "CHECK FOR ERRORS",
    "tool call, build",
    "lint fail",
    "Fix it",
    "CHECK FOR LOOSE ENDS",
    "TODO comments",
    "placeholder code",
    "missing tests",
    "not acted on",
    "IMPORTANT:",
    "latest instructions",
    "always take priority",
    "said to stop, move on",
    "respect that",
    "force completion",
    "no longer wants",
    "genuinely 100",
    "confirm completion",
    "immediately continue",
    "whatever remains",
    "do not just describe",
    "ACTUALLY DO IT",
    "working on it",
    "partially done",
    "Finish it",
    "user redirected",
]

REGEX_PATTERNS = [
    r"Ran \d+ stop hook",
]


def make_null_safe(phrase):
    """Convert spaces to [\\x00 ] so triggers match both real spaces and
    null bytes (Claude Code's TUI uses \\x00 as padding in rendered text)."""
    return phrase.replace(" ", "[\\x00 ]")


def _tail_phrases(phrases, min_len=10):
    """For 3+ word phrases, generate all 2+ word tails at least min_len chars.
    When iTerm2 reflows text on resize, a phrase like "no longer wanted" can
    split so "longer wanted" lands on its own screen line with no matching
    trigger. These tails cover those fragments."""
    subs = set()
    for p in phrases:
        words = p.split()
        for i in range(1, len(words) - 1):
            tail = " ".join(words[i:])
            if len(tail) >= min_len:
                subs.add(tail)
    return sorted(subs - set(phrases))


_SUB_PHRASES = _tail_phrases(PHRASES)
_ALL_PHRASES = PHRASES + _SUB_PHRASES

# Single combined regex: all phrases + sub-phrases + regex patterns joined with |.
# One trigger instead of 80, tested in a single pass per output line.
TRIGGER_REGEX = "|".join(
    [make_null_safe(p) for p in _ALL_PHRASES] + REGEX_PATTERNS
)
TRIGGER_REGEXES = [TRIGGER_REGEX]

# For removal, match the combined regex AND individual patterns from older versions
ALL_PATTERNS = (set(_ALL_PHRASES)
                | {make_null_safe(p) for p in _ALL_PHRASES}
                | set(REGEX_PATTERNS)
                | set(TRIGGER_REGEXES))

# How far from background toward foreground (0.0 = invisible, 1.0 = full brightness).
DIM_FACTOR = 0.25

FALLBACK_DIM_PARAM = "{#555555,}"


def compute_dim_param(profile):
    """Derive a dim text color by interpolating from bg toward fg."""
    try:
        bg = profile.background_color
        fg = profile.foreground_color
        if bg is None or fg is None:
            return FALLBACK_DIM_PARAM
        r = max(0, min(255, int(round(bg.red + (fg.red - bg.red) * DIM_FACTOR))))
        g = max(0, min(255, int(round(bg.green + (fg.green - bg.green) * DIM_FACTOR))))
        b = max(0, min(255, int(round(bg.blue + (fg.blue - bg.blue) * DIM_FACTOR))))
        return "{" + f"#{r:02x}{g:02x}{b:02x}" + ",}"
    except (AttributeError, KeyError, TypeError):
        return FALLBACK_DIM_PARAM


def has_dim_triggers(profile):
    """Check whether the profile already has TASKMASTER dim triggers."""
    for t in (profile.triggers or []):
        if t.get("regex") in ALL_PATTERNS:
            return True
    return False


async def apply_to_session(session):
    """Add dim triggers to a session, replacing any stale ones.
    Returns the number of triggers added."""
    profile = await session.async_get_profile()
    existing = profile.triggers or []
    dim_param = compute_dim_param(profile)

    kept = [t for t in existing if t.get("regex") not in ALL_PATTERNS]
    new_triggers = [{
        "regex": p,
        "action": "iTermHighlightLineTrigger",
        "parameter": dim_param,
        "partial": True,
        "disabled": False,
    } for p in TRIGGER_REGEXES]

    wp = iterm2.LocalWriteOnlyProfile()
    wp.set_triggers(kept + new_triggers)
    await session.async_set_profile_properties(wp)
    return len(new_triggers)


async def remove_from_session(session):
    """Remove dim triggers from a session.
    Returns the number of triggers removed."""
    profile = await session.async_get_profile()
    existing = profile.triggers or []
    kept = [t for t in existing if t.get("regex") not in ALL_PATTERNS]
    removed = len(existing) - len(kept)

    wp = iterm2.LocalWriteOnlyProfile()
    wp.set_triggers(kept)
    await session.async_set_profile_properties(wp)
    return removed
