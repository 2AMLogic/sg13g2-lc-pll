#!/usr/bin/env python3
"""The one reader of a cp_icp_corners `klt sim` report (the I_cp corner grid).

Both consumers of the paired I_up/I_dn currents go through `currents` here: the
charge-pump record writer (`icp_record.py`) and the row-5 loop model
(`sim/loop-model/envelope.py`, which keeps its own uA-to-A conversion). The
reader checks the report against the grid of `cp_icp_corners.request.json`
before anything looks at the values: each expected (process, paired supply,
temperature) combination must be covered exactly once, so an incomplete or
duplicated corner grid cannot produce a record (#368).
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REQUEST_PATH = HERE / "cp_icp_corners.request.json"

MEASUREMENTS = ("i_up_ua", "i_dn_ua")


def load_request(path=None):
    """The parsed corner request whose grid a report must cover."""
    return json.loads(Path(path or REQUEST_PATH).read_text())


def corner_key(corner):
    """The (process, paired supply, temperature) grid point of a report corner."""
    return (corner["process"], tuple(sorted(corner["supply_v"].items())), corner["temperature_c"])


def _fmt(key):
    proc, supply, temp = key
    return "%s %s %gC" % (proc, " ".join("%s=%g" % kv for kv in supply), temp)


def grid(request):
    """Every (process, paired supply, temperature) point the request asks `klt sim` to run.

    `corners.supply_v` moves its rails together -- paired by list index, never
    crossed -- which is how the 18 supply sub-corners ran: 3 processes x 2
    paired supplies x 3 temperatures.
    """
    cs = request["corners"]
    rails = cs["supply_v"]
    names = sorted(rails)
    lengths = {len(rails[r]) for r in names}
    if len(lengths) != 1:
        raise SystemExit("cp_icp_corners supply rails cannot be paired: %s"
                         % ", ".join("%s has %d values" % (r, len(rails[r])) for r in names))
    supplies = [tuple((r, rails[r][i]) for r in names) for i in range(lengths.pop())]
    return [(p, s, t) for p in [b["name"] for b in cs["process"]]
            for s in supplies for t in cs["temperature_c"]]


def currents(report, request):
    """[(corner_id, i_up_uA, i_dn_uA)] covering the request's grid exactly once.

    Raises SystemExit (so both CLIs exit nonzero before writing any output) for a
    report that misses a grid point, duplicates one, runs a corner off the grid,
    or has a corner that produced neither current value.
    """
    points = grid(request)
    expected = set(points)
    seen = {}
    rows = []
    for c in report["corners"]:
        key = corner_key(c)
        cid = c.get("corner_id", "?")
        if key not in expected:
            raise SystemExit("corner %s (%s) is not on the cp_icp_corners request grid" % (cid, _fmt(key)))
        if key in seen:
            raise SystemExit("corner %s duplicates the grid point %s already covered by corner %s"
                             % (cid, _fmt(key), seen[key]))
        m = {x["name"]: x.get("value") for x in c["measurements"]}
        if c["status"] not in ("pass", "fail") or any(m.get(k) is None for k in MEASUREMENTS):
            raise SystemExit("corner %s did not produce I_up/I_dn (status %s)" % (cid, c["status"]))
        seen[key] = cid
        rows.append((cid, abs(m["i_up_ua"]), abs(m["i_dn_ua"])))
    missing = [k for k in points if k not in seen]
    if missing:
        raise SystemExit("report covers %d of the %d cp_icp_corners grid points; missing %s"
                         % (len(seen), len(points), _fmt(missing[0])))
    return rows
