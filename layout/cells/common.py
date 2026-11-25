"""Shared machinery for the loop-block cell generators (layout/cells/<block>.py).

Each block generator turns one `.subckt` of `design/netlist/*.spice` into a cell: flatten
the subckt to leaf devices, group identical (class, W, L) devices, draw each group with
`klt gen mos_array|res_array|cap_array`, place the groups with `klt gen-compose`, and stamp
one text label per `.subckt` port on a drawn terminal of that net. Blocks built with
``route=True`` (#343) additionally wire the cell: the compose request carries a
``connectivity[]`` entry per flattened net (every unit terminal pin, plus the guard-ring
``TAP_*`` ports tied to the group's bulk net) and a ``routing`` plane pair, so the wiring
is drawn by `klt gen-compose`'s router, never by a local polygon helper. Blocks built
without it are placement-only (block-to-block routing is #35; the remaining cells are
follow-ups of #343).

Method adapted from 2AMLogic/sg13g2-pll layout/bin/pll_layout.py @ e71ff61 (netlist reader,
hierarchy flattening, (class, W, L) grouping, klt gen / gen-compose driving). Differences:
  * MOS / resistor `m=` multipliers are expanded into unit devices (the upstream netlists
    carry m>1 only on capacitors; this design's charge pump has m=5/10 on MOS devices, and
    dropping them would undercount the drawn area);
  * identical capacitors share one `cap_array` request;
  * the cell carries the subckt's port labels, which the upstream flow does not need.

Nothing here draws raw polygons except the port text labels (klayout.db).
"""
from collections import Counter
import hashlib
import json
import math
import os
import re
import subprocess
import sys

import klayout.db as db

from . import netlist
from .netlist import PlanError, read_subckts  # noqa: F401  (re-exported)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

PDK = "ihp-sg13g2"
MOS_MODELS = {"sg13_hv_nmos": "nfet", "sg13_hv_pmos": "pfet"}
RES_MODELS = {"rppd": "rppd", "rhigh": "rhigh"}
CAP_MODELS = {"cap_cmim"}
# SiGe HBT cells placed from the PDK's own sg13g2_pr.gds by `klt gen bjt_array` (needs a klt
# carrying klayout-tools#4855; the host klt predates it, see klt_cmd()). Nx=<n> emitters are
# expanded into n unit cells (as `m=`), an approximation stated in the provenance.
HBT_MODELS = {"npn13G2v": "npn13G2v"}
# Devices no klt generator draws on sg13g2. They are recorded in the provenance as undrawn,
# never silently dropped.
UNDRAWN_MODELS = {
    "ideal_res": "ideal SPICE resistor (value in ohms, no W/L or model): sizing a physical "
                 "rppd/rhigh is a schematic decision, out of scope for layout generation",
}
LEAF_MODELS = set(MOS_MODELS) | set(HBT_MODELS) | set(RES_MODELS) | CAP_MODELS | set(UNDRAWN_MODELS)
VOLTAGE_FLAVOR = "hv"   # thick-oxide marker (DR-002 Decision 0: 3.3 V devices throughout)

MOS_W_FLOOR_UM = 0.42   # below this mos_array needs dogbone_terminals (klayout-tools#4851)
GROUP_SPACING_UM = 4.0
BLOCK_TARGET_WIDTH_UM = 220.0
# A MOS card is `D G S B <model>`: the bulk net a tap ring would carry is the 4th node.
MOS_BULK_INDEX = 3
# nfet N+Activ inside the p-well needs a pSD substrate tie within 20 um (native rule LU.b).
# `mos_array add_guard_ring` draws that ring itself on ihp-sg13g2 from klayout-tools#5231
# (klt >= 0.9.2.dev887+gec7400b7d8e5); older builds drew an n-well tie with off-grid Cont
# instead, which is why the tie was not drawn before (layout/drc/README.md "LU.b substrate taps").
TAP_RING_FLAVORS = ("nfet",)
# Routed cells (#343) also ring the pfet groups: a `mos_array flavor="pfet"` group with
# `add_guard_ring` draws its tap ring inside the group's own n-well (the ring's well tie
# merges with the array well), and its TAP_* ports tie that well to the cards' 4th node.
# Placement-only cells keep pfet groups ringless so their committed geometry is unchanged.
ROUTE_TAP_RING_FLAVORS = ("nfet", "pfet")
# Intra-cell routing planes (klt gen-compose `routing`, ihp-sg13g2 roles): Metal2 backbone
# with Via1 drops to the Metal1 terminal pads, Metal3 as the retry plane for a leg whose
# backbone crosses an already-routed net. No generator draws Metal2/Metal3, so the planes
# hold router geometry only. Width is floored by the deck's own Metal2 minimum-width rule.
ROUTE_LAYER_ROLE = "metal2"
ROUTE_CROSS_LAYER_ROLE = "metal3"
ROUTE_WIDTH_UM = 0.6
# The router's default landing pads are kept: a smaller request is refused for the cmim
# groups, whose pins sit on Metal5/TopMetal1 (deck floors 0.62 / 1.26 um).
# Bulk nets (a group's tap_net: VDD/VSS) route last, together on the highest routing plane
# (metal3 is the topmost role the family resolves), so their trunks never share -- and so
# never block a via drop on -- the signal planes below.
ROUTE_RAIL_LAYER_ROLES = ("metal3",)
# SG13G2 metal pin/net text purpose (#416): both the PDK LVS runset (`sg13g2.lvs`:
# `rule_decks/layers_definitions.lvs` + `general_connections.lvs:57-63`) and klt's curated
# `sg13g2` `EXTRACTION_DECK.metal_labels` (`klayout_tools/decks/sg13g2.py`) attach metal labels
# exclusively from datatype 25 (`Metal1..5.text`, `TopMetal1..2.text`) and ignore drawing `/0`.
METAL_TEXT_DATATYPE = 25
METAL_TEXT_LAYERS = {
    8: METAL_TEXT_DATATYPE,    # Metal1.text
    10: METAL_TEXT_DATATYPE,   # Metal2.text
    30: METAL_TEXT_DATATYPE,   # Metal3.text
    50: METAL_TEXT_DATATYPE,   # Metal4.text
    67: METAL_TEXT_DATATYPE,   # Metal5.text
    126: METAL_TEXT_DATATYPE,  # TopMetal1.text
    134: METAL_TEXT_DATATYPE,  # TopMetal2.text
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def digest(ly, cell):
    """Writer-independent geometry digest of `cell` in `ly`: merged polygons per layer plus
    label text/position. Shared by gen_cells.py and gen_integrated.py (one copy -- the pre-#308
    pair had diverged on label positions and had to be fixed twice for #263).

    Layers are hashed in ascending (layer, datatype) order, NOT in `ly.layer_indexes()`
    enumeration order: that order is an artefact of the writer and is not preserved across a
    GDS round trip, so hashing in it made the digest move for a stream that had merely been
    re-saved -- a geometry mismatch that is not one (#263). Every caller reads `ly` from a
    stream, where KLayout creates exactly one layer index per (layer, datatype), so the key is
    a total order over the layers being hashed.

    Label positions are hashed in the digest target cell's own coordinate system: the instance
    transform is applied (`it.trans() * s.text_trans.disp`), so a label deep in the hierarchy
    hashes where the cell's reader sees it. This is also the only convention consistent with the
    committed records: for the six generated cells the two positions coincide and both
    conventions reproduce layout/cells.provenance.json, but layout/provenance.json's top-cell
    digest -- pinned 2026-11-15 -- reproduces only with the transform applied.
    """
    h = hashlib.sha256()
    for li in sorted(ly.layer_indexes(), key=lambda i: (ly.get_info(i).layer, ly.get_info(i).datatype)):
        info = ly.get_info(li)
        r = db.Region(cell.begin_shapes_rec(li))
        r.merge()
        polys = sorted(str(p) for p in r.each())
        txt = sorted(f"{s.text_string}@{(it.trans() * s.text_trans.disp).x},{(it.trans() * s.text_trans.disp).y}"
                     for it in cell.begin_shapes_rec(li) for s in [it.shape()] if s.is_text())
        if polys or txt:
            h.update(f"{info.layer}/{info.datatype}|{';'.join(polys)}|{';'.join(txt)}\n".encode())
    return h.hexdigest()


# --- netlist reading and flattening (pure) ---------------------------------------------


def _num(params, key, who):
    raw = params.get(key)
    if raw is None:
        raise PlanError(f"{who}: no {key!r} param")
    m = re.fullmatch(r"([0-9.eE+-]+)([uU]?)", raw)
    if not m:
        raise PlanError(f"{who}: {key}={raw!r} is not a number")
    return float(m.group(1))


def _mult(params, who):
    m = float(params.get("m", "1"))
    if m < 1 or m != int(m):
        raise PlanError(f"{who}: m={params.get('m')!r} is not a positive integer")
    return int(m)


def flatten(subckts, top):
    """Leaf devices of `top` (layout primitives only): see netlist.flatten."""
    return netlist.flatten(subckts, top, LEAF_MODELS)


def _slug(v):
    return f"{v:g}".replace(".", "p").replace("-", "m")


def _tap_net(block, flav, w, l, mem, flavors=TAP_RING_FLAVORS):
    """The bulk net a `flav` group's tap ring carries, or None if that flavor gets no ring.

    The net is read from the device cards' 4th node, never invented. One ring is one body
    potential, so a group whose units disagree on it is refused rather than tied together.
    """
    if flav not in flavors:
        return None
    who = f"{block} {flav} w={w:g} l={l:g}"
    short = [m for m in mem if len(m["nets"]) <= MOS_BULK_INDEX]
    if short:
        raise PlanError(f"{who}: {short[0]['path']} has {len(short[0]['nets'])} nodes, "
                        "need D G S B for a tap ring")
    bulks = sorted({m["nets"][MOS_BULK_INDEX] for m in mem})
    if len(bulks) != 1:
        raise PlanError(f"{who}: units sit on different bulk nets {bulks}; "
                        "one tap ring cannot carry two body potentials")
    return bulks[0]


def plan(block, devices, hbt_split_bases=(), tap_flavors=TAP_RING_FLAVORS, res_rows=1):
    """Group leaf devices into klt gen requests. Each unit gets the device's nets.

    hbt_split_bases: HBT base nets (e.g. a tank-loading input pair) whose units are pulled out
    of the one-per-flavour array into singleton arrays, so the integrator can place each under
    its own pin (#345). The vacated slots are refilled with dummy devices (params dummy=N), real
    geometry with no nets, so the remaining array keeps a factorable shape (129 = 3x43 stays
    3x43 as 127 units + 2 dummies instead of collapsing to 1x127). The dummies carry no ports;
    LVS (#37) will have to exclude them.
    """
    mos, res, caps, hbt = {}, {}, {}, {}
    for d in devices:
        who, p = d["path"], d["params"]
        n = _mult(p, who)
        if d["model"] in UNDRAWN_MODELS:
            continue
        if d["model"] in HBT_MODELS:
            if float(p.get("el", "1")) != 1:
                raise PlanError(f"{who}: El={p.get('el')} unsupported (PDK cell has a fixed emitter)")
            nx = int(_num(p, "nx", who))
            hbt.setdefault(HBT_MODELS[d["model"]], []).extend([d] * (n * nx))
        elif d["model"] in MOS_MODELS:
            key = (MOS_MODELS[d["model"]], _num(p, "w", who), _num(p, "l", who), int(_num(p, "ng", who)) if "ng" in p else 1)
            mos.setdefault(key, []).extend([d] * n)
        elif d["model"] in RES_MODELS:
            res.setdefault((RES_MODELS[d["model"]], _num(p, "w", who), _num(p, "l", who)), []).extend([d] * n)
        else:
            caps.setdefault((_num(p, "w", who), _num(p, "l", who)), []).extend([d] * n)
    groups = []
    for (flav, w, l, ng), mem in sorted(mos.items()):
        rows = max(r for r in range(1, math.isqrt(len(mem)) + 1) if len(mem) % r == 0)
        tap_net = _tap_net(block, flav, w, l, mem, tap_flavors)
        groups.append({
            "id": f"{block}_{flav}_w{_slug(w)}_l{_slug(l)}" + (f"_ng{ng}" if ng > 1 else ""),
            "generator": "mos_array", "klass": flav, "count": len(mem),
            "params": {"w_um": w, "l_um": l, "fingers": ng, "rows": rows, "cols": len(mem) // rows,
                       "dummy": 0, "flavor": flav, "voltage_flavor": VOLTAGE_FLAVOR,
                       "topology": "array", "gate_contact": True,
                       **({"dogbone_terminals": True} if w < MOS_W_FLOOR_UM else {}),
                       **({"add_guard_ring": True} if tap_net is not None else {})},
            **({"tap_net": tap_net} if tap_net is not None else {}),
            "terminals": [{"port": f"U{i}_{t}", "net": m["nets"][k], "unit": m["path"]}
                          for i, m in enumerate(mem) for k, t in enumerate("DGS")],
        })
    for flav, mem in sorted(hbt.items()):
        split = [m for m in mem if m["nets"][1] in hbt_split_bases]
        keep = [m for m in mem if m["nets"][1] not in hbt_split_bases]
        if split and not keep:
            raise PlanError(f"{block}: every {flav} unit would be split off {hbt_split_bases}")
        n_pos = len(keep) + len(split)
        rows = max(r for r in range(1, math.isqrt(n_pos) + 1) if n_pos % r == 0)
        groups.append({
            "id": f"{block}_hbt_{flav.lower()}",
            "generator": "bjt_array", "klass": flav, "count": len(keep),
            "params": {"flavor": flav, "rows": rows, "cols": n_pos // rows, "dummy": len(split),
                       "topology": "array",
                       "add_collector_ring": False},
            "terminals": [{"port": f"Q{i + 1}_{t}", "net": m["nets"][k], "unit": m["path"]}
                          for i, m in enumerate(keep) for k, t in enumerate("CBE")],
        })
        for m in split:
            groups.append({
                "id": f"{block}_hbt_{flav.lower()}_base_{m['nets'][1].lower()}",
                "generator": "bjt_array", "klass": flav, "count": 1,
                "params": {"flavor": flav, "rows": 1, "cols": 1, "dummy": 0,
                           "topology": "array",
                           "add_collector_ring": False},
                "terminals": [{"port": f"Q1_{t}", "net": m["nets"][k], "unit": m["path"]}
                              for k, t in enumerate("CBE")],
            })
    for (flav, w, l), mem in sorted(res.items()):
        groups.append({
            "id": f"{block}_res{flav}_w{_slug(w)}_l{_slug(l)}",
            "generator": "res_array", "klass": flav, "count": len(mem),
            # res_rows=2 folds a multi-unit group boustrophedon (R1 mirrored above R0), so
            # one net's A/B pads never sit on the same row as a neighbour's: a Manhattan
            # escape from one row then cannot run along a foreign pad (routed cells only;
            # placement-only cells keep the committed single-row geometry).
            "params": {"length_um": l, "width_um": w, "num": len(mem), "dummy": 0, "rows": res_rows,
                       "flavor": flav},
            "terminals": [{"port": f"R{i}_{t}", "net": m["nets"][k], "unit": m["path"]}
                          for i, m in enumerate(mem) for k, t in enumerate("AB")],
        })
    for (w, l), mem in sorted(caps.items()):
        groups.append({
            "id": f"{block}_cmim_w{_slug(w)}_l{_slug(l)}",
            "generator": "cap_array", "klass": "cap_cmim", "count": len(mem),
            "params": {"plate_w_um": w, "plate_h_um": l, "num": len(mem)},
            "terminals": [{"port": f"C{i}_{t}", "net": m["nets"][k], "unit": m["path"]}
                          for i, m in enumerate(mem) for k, t in enumerate(("TOP", "BOT"))],
        })
    # One post-assembly uniqueness check (#415): a split-off singleton's id is derived from
    # the unit's base net, so two units of one flavour sharing a split base net (including
    # the .lower()-folded spelling of two different nets) would emit two groups with one id
    # -- which build_block keys reports, origins and explicit_origins by, silently
    # collapsing them. Refuse here; one check over every assembled id covers the
    # mos/res/cap paths too.
    dupes = {gid for gid, n in Counter(g["id"] for g in groups).items() if n > 1}
    if dupes:
        units = {gid: sorted({t["unit"] for g in groups if g["id"] == gid for t in g["terminals"]})
                 for gid in dupes}
        raise PlanError(f"{block}: colliding group ids: "
                        + "; ".join(f"{gid} (units {', '.join(units[gid])})" for gid in sorted(dupes)))
    return groups


# --- klt driving ---------------------------------------------------------------------------


def klt_cmd():
    """The klt argv prefix: $KLT_CMD (e.g. `uvx --from git+...@<sha> klt`) or plain `klt`."""
    return os.environ.get("KLT_CMD", "klt").split()


def klt(args, cwd):
    a = list(args)
    p = subprocess.run(klt_cmd() + a, capture_output=True, text=True, cwd=cwd)
    raw = p.stdout.strip() or p.stderr.strip()
    try:
        rep = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        rep = {"unparsed_output": raw}
    return p.returncode, rep


def shelf_pack(sizes, width, gap):
    org, x, y, sh = {}, 0.0, 0.0, 0.0
    for gid, w, h in sizes:
        if x > 0 and x + w > width:
            y += sh + gap
            x, sh = 0.0, 0.0
        org[gid] = {"x": round(x, 3), "y": round(y, 3)}
        x += w + gap
        sh = max(sh, h)
    return org


def port_net_label_sites(groups, reports, origins, ports=None):
    """{net: (x_um, y_um, layer, datatype)}: the first drawn terminal of each port net, block frame,
    mapped from its drawing layer onto the SG13G2 metal text purpose (<layer>/25, #416)."""
    want = set(ports) if ports is not None else None
    site = {}
    for g in groups:
        rep = reports[g["id"]]
        pos = {p["name"]: p for p in rep["ports"]}
        for t in g["terminals"]:
            net = t["net"]
            if (want is not None and net not in want) or net in site:
                continue
            p = pos.get(t["port"])
            if p is None:
                continue
            la = p["layer"]["layer"]
            dt = METAL_TEXT_LAYERS.get(la)
            if dt is None:
                raise PlanError(
                    f"{g['id']}.{t['port']} (port {net!r}): terminal layer "
                    f"{la}/{p['layer']['datatype']} has no SG13G2 metal text purpose "
                    f"(supported: {sorted(METAL_TEXT_LAYERS)})"
                )
            o = origins[g["id"]]
            site[net] = (o["x"] + p["x_um"], o["y"] + p["y_um"], la, dt)
    return site


def net_pins(groups, reports, origins):
    """{net: [pin]}: every unit-terminal pin, plus one TAP_* ring port per guarded group
    tied to the group's bulk net (a closed tap ring is one conductor, so one landing biases
    the whole ring and, for a pfet group, the merged n-well underneath; landing all four
    TAP_* ports would multiply the rail bundles by four for no electrical difference). Each
    pin carries its composed-frame pad position (origin + port position) for routing policy."""
    nets = {}
    for g in groups:
        pos = {p["name"]: p for p in reports[g["id"]]["ports"]}
        o = origins[g["id"]]
        for t in g["terminals"]:
            p = pos[t["port"]]
            nets.setdefault(t["net"], []).append({"block": g["id"], "port": t["port"],
                                                  "x": o["x"] + p["x_um"], "y": o["y"] + p["y_um"]})
        if "tap_net" in g:
            tap = next((p for p in reports[g["id"]]["ports"] if p["name"].startswith("TAP_")), None)
            if tap is not None:
                nets.setdefault(g["tap_net"], []).append(
                    {"block": g["id"], "port": tap["name"],
                     "x": o["x"] + tap["x_um"], "y": o["y"] + tap["y_um"]})
    return nets


# Two terminals report the same pad-column x when their centres are closer than this. The
# generated arrays place same-column pads on one x (S columns, D columns, gate columns), so
# 0.3 um separates distinct columns and never merges two.
COLUMN_TOL_UM = 0.3
# Per-(net, block) routing trunk: one horizontal track above the block's bbox, stacked
# 1.0 um per net so neighbouring trunks clear the deck's Metal2/Metal3 spacing.
TRUNK_MARGIN_UM = 1.2
TRUNK_TRACK_UM = 1.0


def _pin(p):
    return {"block": p["block"], "port": p["port"]}


def _block_chains(pins):
    """{block: [chain, ...]}: same-block pins clustered into pad columns (x within
    COLUMN_TOL_UM), each chain sorted bottom-up -- S columns, D columns and gate columns of
    a generated array each sit on one x, so a chain is one terminal column of one net."""
    by_block = {}
    for pin in pins:
        by_block.setdefault(pin["block"], []).append(pin)
    out = {}
    for block, bpins in by_block.items():
        cols = []
        for pin in sorted(bpins, key=lambda p: p["x"]):
            if cols and abs(pin["x"] - cols[-1][0]) <= COLUMN_TOL_UM:
                cols[-1][1].append(pin)
            else:
                cols.append((pin["x"], [pin]))
        out[block] = [sorted(c, key=lambda p: p["y"]) for _, c in cols]
    return out


def column_chains(pins):
    """Legs chaining same-net pins that share a pad column. The auto backbone for a
    same-column pair runs vertically at the pins' own column (or one stub to its side,
    which per-card mirrored arrays keep on same-net pad territory), so it never runs
    along a foreign pad row -- unlike the nearest-first horizontal pairs, whose backbone
    crosses the interleaved pads of another net on that row and poisons their via drops.
    Seeded into the bundle's legs[] before the automatic search."""
    legs = []
    for chains in _block_chains(pins).values():
        for chain in chains:
            for a, b in zip(chain, chain[1:]):
                legs.append({"from_pin": _pin(a), "to_pin": _pin(b)})
    return legs


def chain_links(pins, bboxes, tracks, plane):
    """Legs tying one (net, block)'s column chains (and its TAP_* ring port) together
    through one horizontal trunk above the block: a leg between two chain tops is forced
    through waypoints at (chain-top x, trunk y), so its vertical escape runs at the pin's
    own column -- crossing only same-net rows and the gate rows at their own x -- and the
    horizontal run sits above every pad of the block. `tracks` stacks the per-net trunks
    (keyed by block; rails and signals stack independently per `plane`)."""
    legs = []
    for block, chains in sorted(_block_chains(pins).items()):
        if len(chains) < 2:
            continue
        k = tracks.get((block, plane), 0)
        tracks[(block, plane)] = k + 1
        yt = bboxes[block]["y1"] + TRUNK_MARGIN_UM + k * TRUNK_TRACK_UM
        tops = [c[-1] for c in sorted(chains, key=lambda c: c[-1]["x"])]
        for a, b in zip(tops, tops[1:]):
            legs.append({"from_pin": _pin(a), "to_pin": _pin(b),
                         "waypoints_um": [[a["x"], yt], [b["x"], yt]]})
    return legs


def build_block(cell, subckt, netlist, out_dir, input_first=(), hbt_split_bases=(), explicit_origins=None,
                route=False):
    """Generate `cell` (a placed-device cell with port labels) for `subckt` in `netlist`.

    input_first: port names whose gate-connected device group is placed first (at the origin),
    so a tank-loading input (prescaler INP/INN) sits at the cell edge and stays compact.
    hbt_split_bases / explicit_origins: see plan(); explicit_origins maps group id -> (x, y) and
    overrides the shelf-pack origin of that group (the split input pair is placed by the pin
    span, not by shelf order).
    route: also wire the cell intra-cell through `klt gen-compose` routing (#343) -- one
    connectivity[] entry per flattened net on the ROUTE_* plane pair, pfet groups ringed and
    their wells tied. Returns the provenance record for the cell. Raises PlanError /
    RuntimeError on any failure.
    """
    os.makedirs(out_dir, exist_ok=True)
    subckts = read_subckts(netlist)
    ports = subckts[subckt]["ports"]
    devices = flatten(subckts, subckt)
    groups = plan(cell, devices, hbt_split_bases,
                  tap_flavors=ROUTE_TAP_RING_FLAVORS if route else TAP_RING_FLAVORS,
                  res_rows=2 if route else 1)
    undrawn = [{"device": d["path"], "model": d["model"], "nets": d["nets"],
                "params": d["params"], "reason": UNDRAWN_MODELS[d["model"]]}
               for d in devices if d["model"] in UNDRAWN_MODELS]
    if not groups:   # nothing drawable (e.g. all-HBT block): record, draw no cell
        return {"cell": cell, "subckt": subckt, "status": "undrawn",
                "netlist": os.path.relpath(netlist, ROOT), "netlist_sha256": sha256(netlist),
                "device_units": 0, "ports": ports, "ports_unlabelled": list(ports),
                "port_labels": {}, "undrawn_devices": undrawn, "undrawn_only_ports": list(ports),
                "groups": [], "commands": [], "area_um2": 0.0}
    # Prefer groups driving the named inputs first.
    def first_rank(g):
        return 0 if any(t["net"] in input_first and t["port"].split("_")[1] in ("G", "B") for t in g["terminals"]) else 1
    groups.sort(key=lambda g: (first_rank(g), g["id"]))

    reports, cmds, refused = {}, [], []
    for g in groups:
        args = ["gen", g["generator"], "--pdk", PDK, "--params", json.dumps(g["params"], sort_keys=True),
                "--cell-name", g["id"], "-o", f"{g['id']}.gds", "--format", "json"]
        rc, rep = klt(args, out_dir)
        if rc != 0 or "error" in rep:
            # The generator refused this group (e.g. a W below its floor): record every device
            # in it as undrawn with klt's own message, never drop it silently.
            msg = (rep.get("error") or {}).get("message", str(rep))
            for u in sorted({t["unit"] for t in g["terminals"]}):
                d = next(x for x in devices if x["path"] == u)
                undrawn.append({"device": u, "model": d["model"], "nets": d["nets"],
                                "params": d["params"], "reason": f"klt gen {g['generator']} refused: {msg}"})
            refused.append(g["id"])
            continue
        reports[g["id"]] = rep
        cmds.append("klt " + " ".join(json.dumps(a) if " " in a or "{" in a else a for a in args))
        # bjt_array reports every drawn position, dummy refill included; mos/res groups carry
        # no dummies today, so the +dummy term is zero for them.
        if rep.get("device_count", g["count"]) != g["count"] + g["params"].get("dummy", 0) \
                and g["generator"] != "cap_array":
            raise RuntimeError(f"{g['id']}: drew {rep.get('device_count')} devices, planned {g['count']}")

    groups = [g for g in groups if g["id"] not in refused]
    sizes = []
    for g in groups:
        b = reports[g["id"]]["bbox_um"]
        sizes.append((g["id"], b["x1"] - b["x0"], b["y1"] - b["y0"]))
    origins = shelf_pack(sizes, BLOCK_TARGET_WIDTH_UM, GROUP_SPACING_UM)
    if explicit_origins:
        for gid, o in explicit_origins.items():
            if gid not in origins:
                raise RuntimeError(f"{cell}: explicit origin for unknown group {gid!r}")
            origins[gid] = {"x": round(float(o[0]), 3), "y": round(float(o[1]), 3)}
    req = {"schema": "klt.gen_compose.request/1", "pdk": {"variant": PDK},
           "blocks": [{"id": g["id"], "generator_report": reports[g["id"]]} for g in groups],
           "placement": {"strategy": "explicit", "order": [g["id"] for g in groups], "origins_um": origins},
           "options": {"cell_name": cell, "output": f"{cell}.raw.gds"}}
    routing_rec = None
    if route:
        pins = net_pins(groups, reports, origins)
        rails = sorted({g["tap_net"] for g in groups if "tap_net" in g})
        # Signals first (biggest bundle first: it claims the primary plane with its trunk,
        # and a later net whose backbone crosses it is retried on the cross plane -- not the
        # other way round), bulk nets last on their own dedicated planes. Deterministic.
        def net_order(item):
            n, p = item
            return (n in rails, -len(p), n)
        conn = []
        for n, p in sorted(pins.items(), key=net_order):
            if len(p) < 2:
                continue
            e = {"net": n, "pins": [{"block": q["block"], "port": q["port"]} for q in p]}
            chains = column_chains(p)
            if chains:
                e["legs"] = chains
            if n in rails:
                e["layer_role"] = ROUTE_RAIL_LAYER_ROLES[rails.index(n) % len(ROUTE_RAIL_LAYER_ROLES)]
            conn.append(e)
        req["connectivity"] = conn
        req["routing"] = {"layer_role": ROUTE_LAYER_ROLE, "width_um": ROUTE_WIDTH_UM,
                          "cross_block_layer_role": ROUTE_CROSS_LAYER_ROLE}
        routing_rec = {"requested": True, "layer_role": ROUTE_LAYER_ROLE, "width_um": ROUTE_WIDTH_UM,
                       "cross_block_layer_role": ROUTE_CROSS_LAYER_ROLE,
                       "single_pin_nets": sorted(n for n, p in pins.items() if len(p) < 2)}
    with open(os.path.join(out_dir, f"{cell}.compose.json"), "w") as f:
        json.dump(req, f, indent=1, sort_keys=True)
    rc, rep = klt(["gen-compose", f"{cell}.compose.json", "--format", "json"], out_dir)
    # exit 3 is gen-compose's partial success (nets in unrouted_nets[]): recorded below,
    # never silently accepted; every other non-zero exit is a failure.
    if rc not in (0, 3) or "error" in rep:
        raise RuntimeError(f"klt gen-compose failed for {cell}: {rep}")
    if route:
        nets_rep, unrouted = rep.get("nets", []), rep.get("unrouted_nets", [])
        routing_rec.update({
            "nets": [{"net": n.get("net"), "status": n.get("status"), "routed": n.get("routed"),
                      "landed_on_block": n.get("landed_on_block"),
                      "length_um": n.get("route_length_um")} for n in nets_rep],
            "unrouted_nets": unrouted,
            "status": ("routed" if nets_rep and not unrouted and all(n.get("routed") for n in nets_rep)
                       else "partial"),
        })

    # Stamp port labels on a drawn terminal of each port net (SG13G2 metal text purpose /25).
    sites = port_net_label_sites(groups, reports, origins, ports)
    missing = [p for p in ports if p not in sites]
    ly = db.Layout()
    ly.read(os.path.join(out_dir, f"{cell}.raw.gds"))
    top = ly.cell(cell)
    if top is None:
        raise RuntimeError(f"{cell}.raw.gds has no cell {cell!r}")
    if route:
        # gen-compose labels every net it routes, the `.subckt` port nets included, so sparing
        # router texts whose string is a port name double-labels those ports against the stamp
        # below (#349: the routed loop filter shipped two labels per port that way). Erase all
        # of the composed cell's own texts -- direct shapes only; PDK child-cell text (the
        # sg13g2 HBT's B/C/E) sits below instances and is untouched -- and let the stamp loop
        # place exactly one label per port at the site `port_labels` records.
        for li in ly.layer_indexes():
            for sh in list(top.shapes(li).each(db.Shapes.STexts)):
                top.shapes(li).erase(sh)
    placed = {}
    for p in ports:
        if p in sites:
            x, y, la, dt = sites[p]
            top.shapes(ly.layer(la, dt)).insert(db.DText(p, x, y))
            placed[p] = {"x_um": round(x, 3), "y_um": round(y, 3), "layer": f"{la}/{dt}"}
    gds = os.path.join(out_dir, f"{cell}.gds")
    ly.write(gds)
    os.remove(os.path.join(out_dir, f"{cell}.raw.gds"))

    bb = top.dbbox()
    rec = {
        "cell": cell, "subckt": subckt, "status": "partial" if undrawn else "drawn", "netlist": os.path.relpath(netlist, ROOT),
        "netlist_sha256": sha256(netlist), "gds": os.path.relpath(gds, ROOT),
        "bbox_um": [round(bb.left, 3), round(bb.bottom, 3), round(bb.right, 3), round(bb.top, 3)],
        "area_um2": round(bb.width() * bb.height(), 1),
        "device_units": sum(g["count"] for g in groups),
        "ports": ports, "ports_unlabelled": missing, "port_labels": placed,
        "undrawn_devices": undrawn,
        "undrawn_only_ports": [p for p in missing
                               if any(p in u["nets"] for u in undrawn)],
        "groups": [{"id": g["id"], "generator": g["generator"], "klass": g["klass"], "units": g["count"],
                    "params": g["params"], "origin_um": origins[g["id"]],
                    **({"tap_net": g["tap_net"]} if "tap_net" in g else {}),
                    "bbox_um": [reports[g["id"]]["bbox_um"][k] for k in ("x0", "y0", "x1", "y1")]}
                   for g in groups],
        **({"routing": routing_rec} if routing_rec is not None else {}),
        "commands": cmds + [f"klt gen-compose {cell}.compose.json --format json"],
    }
    if hbt_split_bases:
        rec["input_pair_split"] = {
            "bases": list(hbt_split_bases),
            "dummy_refill": sum(g["params"].get("dummy", 0) for g in groups),
            "explicit_origins": {k: dict(x=origins[k]["x"], y=origins[k]["y"])
                                 for k in (explicit_origins or {}) if k in origins},
            "note": ("the named base-net units are singleton arrays at explicit origins so the "
                     "integrated top can drop one tank route on each (#345); the vacated flavour-"
                     "array slots are refilled with portless dummy devices (real geometry, no "
                     "nets; LVS #37 must exclude them)"),
        }
    return rec
