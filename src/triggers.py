# ABOUTME: Shared data and functions for iTerm2 dimming triggers.
# ABOUTME: Per-dimmer phrase lists, dim color computation, and trigger install/remove.

import iterm2


# Per-dimmer phrase and regex configuration. Each dimmer gets its own combined
# regex trigger that can be independently installed/removed via the toggle scripts.
DIMMERS = {
    "taskmaster": {
        "phrases": [
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
        ],
        "regex_patterns": [
            r"Ran \d+ stop hook",
        ],
    },
    "claude-sessions": {
        "phrases": [
            "Stop hook error",
            "Discoveries check",
            "Review existing entries",
            "disproven or superseded",
            "correct or remove them now",
            "new findings to add",
            "run_in_background to append",
            "just acknowledge and continue",
            "Archive has grown",
            "compact discoveries",
        ],
        "regex_patterns": [],
    },
}


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


def build_trigger_regex(dimmer_name):
    """Build a combined regex string for one dimmer's phrases and patterns."""
    config = DIMMERS[dimmer_name]
    phrases = config["phrases"]
    sub_phrases = _tail_phrases(phrases)
    all_phrases = phrases + sub_phrases
    return "|".join(
        [make_null_safe(p) for p in all_phrases] + config["regex_patterns"]
    )


# Pre-built per-dimmer regexes (one trigger per dimmer).
DIMMER_REGEXES = {name: build_trigger_regex(name) for name in DIMMERS}

# For removal, match per-dimmer regexes AND individual patterns AND the old
# combined regex from previous versions, so upgrades clean up stale triggers.
_all_phrases = []
for config in DIMMERS.values():
    phrases = config["phrases"]
    _all_phrases.extend(phrases)
    _all_phrases.extend(_tail_phrases(phrases))

_OLD_COMBINED_REGEX = "|".join(
    [make_null_safe(p) for p in _all_phrases]
    + [p for c in DIMMERS.values() for p in c["regex_patterns"]]
)

ALL_PATTERNS = (
    {make_null_safe(p) for p in _all_phrases}
    | set(_all_phrases)
    | {p for c in DIMMERS.values() for p in c["regex_patterns"]}
    | set(DIMMER_REGEXES.values())
    | {_OLD_COMBINED_REGEX}
)

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


# -- Per-dimmer functions (used by toggle scripts) --

def has_dimmer(profile, dimmer_name):
    """Check whether a specific dimmer's trigger is installed."""
    regex = DIMMER_REGEXES[dimmer_name]
    for t in (profile.triggers or []):
        if t.get("regex") == regex:
            return True
    return False


async def apply_dimmer(session, dimmer_name):
    """Install one dimmer's trigger, replacing any stale triggers."""
    profile = await session.async_get_profile()
    dim_param = compute_dim_param(profile)
    regex = DIMMER_REGEXES[dimmer_name]

    # Remove stale triggers but keep other dimmers' triggers and user triggers
    kept = [t for t in (profile.triggers or []) if t.get("regex") not in ALL_PATTERNS
            or (t.get("regex") in DIMMER_REGEXES.values()
                and t.get("regex") != regex)]
    new_trigger = {
        "regex": regex,
        "action": "iTermHighlightLineTrigger",
        "parameter": dim_param,
        "partial": True,
        "disabled": False,
    }

    wp = iterm2.LocalWriteOnlyProfile()
    wp.set_triggers(kept + [new_trigger])
    await session.async_set_profile_properties(wp)


async def remove_dimmer(session, dimmer_name):
    """Remove one dimmer's trigger from a session."""
    profile = await session.async_get_profile()
    regex = DIMMER_REGEXES[dimmer_name]
    existing = profile.triggers or []
    kept = [t for t in existing if t.get("regex") != regex]

    if len(kept) != len(existing):
        wp = iterm2.LocalWriteOnlyProfile()
        wp.set_triggers(kept)
        await session.async_set_profile_properties(wp)


# -- All-dimmers wrappers (used by CLI and AutoLaunch daemon) --

def has_dim_triggers(profile):
    """Check whether any dimmer trigger is installed."""
    for t in (profile.triggers or []):
        if t.get("regex") in ALL_PATTERNS:
            return True
    return False


async def apply_to_session(session):
    """Add all dimmer triggers to a session, replacing any stale ones.
    Returns the number of triggers added."""
    profile = await session.async_get_profile()
    existing = profile.triggers or []
    dim_param = compute_dim_param(profile)

    kept = [t for t in existing if t.get("regex") not in ALL_PATTERNS]
    new_triggers = [{
        "regex": DIMMER_REGEXES[name],
        "action": "iTermHighlightLineTrigger",
        "parameter": dim_param,
        "partial": True,
        "disabled": False,
    } for name in DIMMERS]

    wp = iterm2.LocalWriteOnlyProfile()
    wp.set_triggers(kept + new_triggers)
    await session.async_set_profile_properties(wp)
    return len(new_triggers)


async def remove_from_session(session):
    """Remove all dimmer triggers from a session.
    Returns the number of triggers removed."""
    profile = await session.async_get_profile()
    existing = profile.triggers or []
    kept = [t for t in existing if t.get("regex") not in ALL_PATTERNS]
    removed = len(existing) - len(kept)

    wp = iterm2.LocalWriteOnlyProfile()
    wp.set_triggers(kept)
    await session.async_set_profile_properties(wp)
    return removed
