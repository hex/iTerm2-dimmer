# ABOUTME: Shared data and functions for iTerm2 dimming triggers.
# ABOUTME: Per-dimmer phrase lists, dim color computation, and trigger install/remove.

import re

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
            "Discoveries check: (1) Review existing entries in",
            "disproven or superseded by your recent work",
            "correct or remove them now. (2)",
            "new findings to add, use the Task tool",
            "nothing to change, just acknowledge and continue",
            "compact discoveries (follow the",
        ],
        "regex_patterns": [
            r"Archive has grown \(\d+ lines\)",
        ],
    },
}


def make_null_safe(phrase):
    """Escape regex metacharacters then convert spaces to [\\x00 ] so triggers
    match both real spaces and null bytes (Claude Code's TUI uses \\x00 as
    padding in rendered text)."""
    return re.escape(phrase).replace(r"\ ", "[\\x00 ]")


def _tail_phrases(phrases, min_len=15):
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


def _build_trie(word_lists):
    """Build a prefix trie from lists of regex-escaped words."""
    root = {}
    for words in word_lists:
        node = root
        for word in words:
            node = node.setdefault(word, {})
        node[None] = True
    return root


def _trie_to_regex(node, is_root=False):
    """Convert a prefix trie to a compact alternation regex.

    Shared prefixes are factored out so the regex engine rejects non-matching
    input after checking one word instead of trying every alternative.
    Words are joined with [\\x00 ] to match both null bytes and spaces."""
    SEP = "[\\x00 ]"
    children = {k: v for k, v in node.items() if k is not None}
    has_end = None in node

    if not children:
        return ""

    branches = []
    for word in sorted(children):
        suffix = _trie_to_regex(children[word])
        branches.append(word + suffix)

    if is_root:
        return "|".join(branches)

    if len(branches) == 1:
        inner = branches[0]
    else:
        inner = "(?:" + "|".join(branches) + ")"

    if has_end:
        return "(?:" + SEP + inner + ")?"
    return SEP + inner


def build_trigger_regex(dimmer_name):
    """Build a combined regex string for one dimmer's phrases and patterns.

    Phrases are organized into a prefix trie so the resulting alternation
    shares common prefixes, reducing the work the regex engine does per line."""
    config = DIMMERS[dimmer_name]
    phrases = config["phrases"]
    sub_phrases = _tail_phrases(phrases)
    all_phrases = phrases + sub_phrases

    word_lists = []
    for phrase in all_phrases:
        words = phrase.split()
        word_lists.append([re.escape(w) for w in words])

    trie = _build_trie(word_lists)
    trie_regex = _trie_to_regex(trie, is_root=True)

    regex_patterns = config.get("regex_patterns", [])
    if regex_patterns:
        return trie_regex + "|" + "|".join(regex_patterns)
    return trie_regex


# Pre-built per-dimmer regexes (one trigger per dimmer).
DIMMER_REGEXES = {name: build_trigger_regex(name) for name in DIMMERS}

_DIM_PARAM_RE = re.compile(r'^\{#[0-9a-f]{6},\}$')


def _is_dim_trigger(trigger):
    """Check if a trigger was installed by iTerm2-dimmer. Identifies by action
    type + parameter format rather than regex content, so stale triggers from
    any version are always caught."""
    return (trigger.get("action") == "iTermHighlightLineTrigger"
            and _DIM_PARAM_RE.match(trigger.get("parameter", "")))

# How far from background toward foreground (0.0 = invisible, 1.0 = full brightness).
DIM_FACTOR = 0.25

FALLBACK_DIM_PARAM = "{#555555,}"


def compute_dim_param(profile, dim_toward=None):
    """Derive a dim text color by interpolating from bg toward a target color.
    If dim_toward is None, interpolates toward the profile's foreground color.
    If dim_toward is an (r, g, b) tuple, interpolates toward that color instead."""
    try:
        bg = profile.background_color
        if bg is None:
            return FALLBACK_DIM_PARAM
        if dim_toward is not None:
            tr, tg, tb = dim_toward
        else:
            fg = profile.foreground_color
            if fg is None:
                return FALLBACK_DIM_PARAM
            tr, tg, tb = fg.red, fg.green, fg.blue
        r = max(0, min(255, int(round(bg.red + (tr - bg.red) * DIM_FACTOR))))
        g = max(0, min(255, int(round(bg.green + (tg - bg.green) * DIM_FACTOR))))
        b = max(0, min(255, int(round(bg.blue + (tb - bg.blue) * DIM_FACTOR))))
        return "{" + f"#{r:02x}{g:02x}{b:02x}" + ",}"
    except (AttributeError, KeyError, TypeError):
        return FALLBACK_DIM_PARAM


# -- Per-dimmer functions (used by toggle scripts) --

def has_dimmer(profile, dimmer_name):
    """Check whether a specific dimmer's trigger is installed."""
    if dimmer_name not in DIMMER_REGEXES:
        return False
    regex = DIMMER_REGEXES[dimmer_name]
    for t in (profile.triggers or []):
        if t.get("regex") == regex:
            return True
    return False


async def apply_dimmer(session, dimmer_name):
    """Install one dimmer's trigger, replacing any stale triggers."""
    if dimmer_name not in DIMMERS:
        return
    profile = await session.async_get_profile()
    dim_toward = DIMMERS[dimmer_name].get("dim_toward")
    dim_param = compute_dim_param(profile, dim_toward)
    regex = DIMMER_REGEXES[dimmer_name]

    # Remove stale triggers but keep other dimmers' triggers and user triggers
    kept = [t for t in (profile.triggers or []) if not _is_dim_trigger(t)
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
    if dimmer_name not in DIMMER_REGEXES:
        return
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
        if _is_dim_trigger(t):
            return True
    return False


async def apply_to_session(session):
    """Add all dimmer triggers to a session, replacing any stale ones.
    Returns the number of triggers added."""
    profile = await session.async_get_profile()
    existing = profile.triggers or []

    kept = [t for t in existing if not _is_dim_trigger(t)]
    new_triggers = [{
        "regex": DIMMER_REGEXES[name],
        "action": "iTermHighlightLineTrigger",
        "parameter": compute_dim_param(profile, DIMMERS[name].get("dim_toward")),
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
    kept = [t for t in existing if not _is_dim_trigger(t)]
    removed = len(existing) - len(kept)

    wp = iterm2.LocalWriteOnlyProfile()
    wp.set_triggers(kept)
    await session.async_set_profile_properties(wp)
    return removed
