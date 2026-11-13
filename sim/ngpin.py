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
the fragment says "unchecked" or "not read" -- it never says "match".
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


def _numbers(versions):
    """The version numbers of `versions` (a string or an iterable of them), in first-seen order."""
    if versions is None:
        return []
    if isinstance(versions, str):
        versions = [versions]
    out = []
    for v in versions:
        n = vnum(v)
        if n is not None and n not in out:
            out.append(n)
    return out


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
    did not all report the same version.
    """
    pin = pinned(path)
    if pin is None:
        return "the pin was not read (`sim/pins.json` unreadable here)"
    got = _numbers(versions)
    head = "pin is %s (`sim/pins.json`): " % pin
    if not got:
        return head + "**unchecked** - no `engine_version` in %s" % source
    ok = all(matches(v, pin) for v in got)
    if len(got) > 1:
        spread = "more than one version is reported here (%s)" % ", ".join(got)
        if ok:
            return head + "**match** - %s; each one matches the pin" % spread
        return head + "**mismatch** - %s; not every number in this record was produced on the pinned one" % spread
    if ok:
        return head + "**match**"
    return head + "**mismatch** - every number in this record was produced on the reported version, not the pinned one"
