#!/usr/bin/env python3
"""Plumbing shared by the `klt sim` corner-record writers, defined once (stdlib only).

The four writers (sim/prescaler-div89/div89_record.py, sim/prescaler-g1/vce_record.py,
sim/divider-elab/divider_corner_record.py, sim/cp-dc/icp_record.py) each grade a fleet report in
their own way but share this:

    import record_util as ru
    ru.verdict(states)                    # FAIL > INCOMPLETE > PASS; an empty collection is INCOMPLETE
    ru.section_of(block, "cornerHBT")     # the .lib section a request's process block names
    ru.request_corners(request)           # (blocks, temps, vddv, supplies) from a request's corner grid
    ru.ensure_new(rec, gz1, gz2)          # append-only check on every output path before any write
    ru.write_report_gz(gz, raw)           # deterministic archive: gzip level 9, mtime 0, no filename
    ru.sha256_bytes(data)

Import it the way sim/ngpin.py is imported: `sys.path.insert(0, str(HERE.parent))`.
"""
import gzip
import hashlib
from pathlib import Path


def verdict(states, *, ungraded=("INCOMPLETE",)):
    """One verdict rule: a failure takes precedence, an empty collection or any member in `ungraded`
    is INCOMPLETE, and only a nonempty collection of passes is PASS."""
    states = list(states)
    if "FAIL" in states:
        return "FAIL"
    if not states or any(s in ungraded for s in states):
        return "INCOMPLETE"
    return "PASS"


def section_of(block, prefix):
    """The block's section name for the lib whose basename starts with `prefix`; None when it has none."""
    for s in block.get("sections") or []:
        if isinstance(s, dict) and s.get("section") and Path(str(s.get("lib", ""))).name.startswith(prefix):
            return s["section"]
    return None


def request_corners(request):
    """(blocks, temps, vddv, supplies) from a `klt sim` request's corner grid: the named process blocks,
    the temperatures, the `vddv` param axis as requested, and its sorted distinct values. An axis the
    request leaves empty comes back empty."""
    grid = (request or {}).get("corners") or {}
    blocks = [b for b in grid.get("process") or [] if isinstance(b, dict) and "name" in b]
    temps = list(grid.get("temperature_c") or [])
    vddv = list((grid.get("params") or {}).get("vddv") or [])
    return blocks, temps, vddv, sorted(set(vddv))


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def ensure_new(*paths):
    """Records are append-only: exit naming the first of `paths` that already exists. Call it with
    every output path before creating the output directory or writing anything, so a collision
    leaves no partial record behind."""
    for p in paths:
        if Path(p).exists():
            raise SystemExit("records are append-only: %s exists" % p)


def write_report_gz(gz_path, raw):
    """Archive the raw report bytes at `gz_path`; same bytes in, same bytes out (zeroed gzip header)."""
    Path(gz_path).write_bytes(gzip.compress(raw, 9, mtime=0))
