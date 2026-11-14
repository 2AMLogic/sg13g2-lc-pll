#!/usr/bin/env python3
"""The ngspice pin check for the `klt sim` record generators, defined once.

A record's **Simulator** line has to state how the version that produced its numbers compares
with `ngspice.version` in `sim/pins.json`. `scripts/lib-ngpin.sh` does that for the local bench
drivers; this module does it for the generators that grade a fleet report, so the verdict is
computed from the report and the pin instead of being typed into the generator as the answer
that happened to be true the day it was written.

    import ngpin
    ngpin.verdict(report["environment"].get("engine_version"))
    ngpin.verdict([r["environment"].get("engine_version") for r in reports])
    ngpin.engine([...])                   # the version(s) to print beside the verdict

The comparison is the prefix rule of `scripts/lib-ngpin.sh`: 46 does not match a pin of 47,
47.1 does. Safe direction: with nothing to compare (no `engine_version`, or an unreadable pin)
the fragment says "unchecked" or "not read" -- it never says "match". Partial evidence is held
to the same rule: when some of a shard's reports carry a version and some do not, the missing
ones are named and the whole record reads "unchecked" rather than "match". A version that is
on file and does not match the pin still reads "mismatch" -- a known disagreement is evidence,
and is never softened into "unchecked" by a report that reported nothing.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PINS = os.path.join(HERE, "pins.json")


def pinned(path=PINS):
    """`ngspice.version` from sim/pins.json as a string, or None if it cannot be read."""
    try:
        with open(path) as f:
            return str(json.load(f)["ngspice"]["version"])
    except (OSError, KeyError, TypeError, ValueError):
        return None


def vnum(s):
    """Leading version number of a version string ("ngspice-46", "46", "47.1"), or None."""
    m = re.search(r"\d+(?:\.\d+)*", str(s if s is not None else ""))
    return m.group(0) if m else None


def matches(version, pin):
    """The prefix rule of scripts/lib-ngpin.sh: a point release matches its pin (47.1 matches a pin of 47),
    a different release does not (46 does not). Both arguments are examples, not the pin itself: the pin is read
    from sim/pins.json."""
    v, p = vnum(version), vnum(pin)
    return bool(v) and bool(p) and (v == p or v.startswith(p + "."))


def _entries(versions):
    """`versions` as a list of entries: one `engine_version` value, or an iterable of them.

    A non-string scalar (a JSON number, say) counts as one entry rather than something to
    iterate: `matches()` already compares such a value by stringifying it, and the generators
    hand this module `environment.engine_version` straight out of a report, whatever type the
    schema put there.
    """
    if isinstance(versions, (str, bytes, bytearray)):
        return [versions]
    try:
        return list(versions)
    except TypeError:
        return [versions]


def _scan(versions):
    """(version numbers in first-seen order, entries with no readable version, total entries).

    The gap count is the point: an entry whose version cannot be read is evidence that is
    *missing*, not evidence that is absent, so `verdict()` can refuse to answer **match** for a
    record when part of it never reported what it ran on.
    """
    entries = _entries(versions)
    numbers, gaps = [], 0
    for v in entries:
        n = vnum(v)
        if n is None:
            gaps += 1
        elif n not in numbers:
            numbers.append(n)
    return numbers, gaps, len(entries)


def _numbers(versions):
    """The version numbers of `versions` (a scalar or an iterable of them), in first-seen order."""
    return _scan(versions)[0]


def reported(versions, unknown="not reported"):
    """The distinct versions seen, for the record's own "ran on" wording; `unknown` if there are none."""
    got = _numbers(versions)
    if not got:
        return unknown
    if len(got) == 1:
        return got[0]
    return ", ".join(got[:-1]) + " and " + got[-1]


def engine(versions, unknown="an ngspice version the run did not report"):
    """The engine version(s), ready for a record's Simulator line: "`ngspice-46`", or `unknown` if none."""
    got = _numbers(versions)
    if not got:
        return unknown
    return " and ".join("`ngspice-%s`" % v for v in got)


def verdict(versions, source="the report", path=PINS):
    """The sentence fragment a record states beside its engine version.

    `versions` is one `environment.engine_version` or an iterable of them (a shard's worth of
    reports); `source` names where they were looked for, for the unchecked case. Returns one of:
    pin not read, unchecked, match, mismatch -- with the disagreement called out when the runs
    did not all report the same version, and with the gap called out when only some of them
    reported one at all.
    """
    pin = pinned(path)
    if pin is None:
        return "the pin was not read (`sim/pins.json` unreadable here)"
    got, gaps, total = _scan(versions)
    head = "pin is %s (`sim/pins.json`): " % pin
    if not got:
        return head + "**unchecked** - no `engine_version` in %s" % source
    ok = all(matches(v, pin) for v in got)
    if gaps:
        # Part of this record never reported a version, so the versions that did cannot speak
        # for the whole of it: the most this can say is **unchecked**, with the gap named. A
        # version that is on file and does not match the pin is still a **mismatch** -- a known
        # disagreement is evidence, and must not be softened into "unchecked" by a missing peer.
        gap = "no `engine_version` in %d of the %d runs here" % (gaps, total)
        if not ok:
            return head + "**mismatch** - %s, and the others report %s, not the pinned version" % (
                gap,
                reported(got),
            )
        return head + (
            "**unchecked** - %s; the others report %s and match the pin, but the pin cannot be "
            "confirmed for every number in this record" % (gap, reported(got))
        )
    if len(got) > 1:
        spread = "more than one version is reported here (%s)" % ", ".join(got)
        if ok:
            return head + "**match** - %s; each one matches the pin" % spread
        return head + "**mismatch** - %s; not every number in this record was produced on the pinned one" % spread
    if ok:
        return head + "**match**"
    return head + "**mismatch** - every number in this record was produced on the reported version, not the pinned one"
