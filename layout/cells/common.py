"""Shared machinery for the loop-block cell generators (layout/cells/<block>.py).

Each block generator turns one `.subckt` of `design/netlist/*.spice` into a placed-device
cell: flatten the subckt to leaf devices, group identical (class, W, L) devices, draw each
group with `klt gen mos_array|res_array|cap_array`, place the groups with `klt gen-compose`
(placement only, no routing: block-to-block and intra-block routing is #35), and stamp one
text label per `.subckt` port on a drawn terminal of that net.

Method adapted from 2AMLogic/sg13g2-pll layout/bin/pll_layout.py @ e71ff61 (netlist reader,
hierarchy flattening, (class, W, L) grouping, klt gen / gen-compose driving). Differences:
  * MOS / resistor `m=` multipliers are expanded into unit devices (the upstream netlists
    carry m>1 only on capacitors; this design's charge pump has m=5/10 on MOS devices, and
    dropping them would undercount the drawn area);
  * identical capacitors share one `cap_array` request;
  * the cell carries the subckt's port labels, which the upstream flow does not need.

Nothing here draws raw polygons except the port text labels (klayout.db).
"""
import hashlib
import json
import math
import os
import re
import subprocess
import sys

import klayout.db as db

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
NETLIST_DIR = os.path.join(ROOT, "design", "netlist")

PDK = "ihp-sg13g2"
MOS_MODELS = {"sg13_hv_nmos": "nfet", "sg13_hv_pmos": "pfet"}
RES_MODELS = {"rppd": "rppd", "rhigh": "rhigh"}
CAP_MODELS = {"cap_cmim"}
# Devices no klt generator draws on sg13g2 (SiGe HBT: bjt_array rejects the family, the PDK's
# pycell library is unusable without its pycell4klayout-api submodule, and the PDK ships no
# npn GDS). They are recorded in the provenance as undrawn, never silently dropped.
UNDRAWN_MODELS = {
    "npn13G2v": "no klt gen generator for sg13g2 bipolar (bjt_array: family not supported)",
    "ideal_res": "ideal SPICE resistor (value in ohms, no W/L or model): sizing a physical "
                 "rppd/rhigh is a schematic decision, out of scope for layout generation",
}
LEAF_MODELS = set(MOS_MODELS) | set(RES_MODELS) | CAP_MODELS | set(UNDRAWN_MODELS)
VOLTAGE_FLAVOR = "hv"   # thick-oxide marker (DR-002 Decision 0: 3.3 V devices throughout)

GROUP_SPACING_UM = 4.0
BLOCK_TARGET_WIDTH_UM = 220.0


class PlanError(Exception):
    pass


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --- netlist reading and flattening (pure) ---------------------------------------------


def read_subckts(path):
    """{subckt: {"ports": [...], "cards": [{name, model, nets, params}]}}; handles `+` lines."""
    joined = []
    with open(path) as f:
        for raw in f.read().splitlines():
            line = raw.rstrip()
            if line.startswith("+") and joined:
                joined[-1] += " " + line[1:].strip()
            else:
                joined.append(line)
    out, cur = {}, None
    for line in joined:
        s = line.strip()
        if s.startswith("**.subckt") or s.startswith("**.ends"):
            s = s[2:]
        if not s or s.startswith("*"):
            continue
        low = s.lower()
        if low.startswith(".subckt"):
            t = s.split()
            cur = t[1]
            out[cur] = {"ports": t[2:], "cards": []}
        elif low.startswith(".ends"):
            cur = None
        elif s.startswith(".") or cur is None:
            continue
        else:
            t = s.split()
            params, pos = {}, []
            for tok in t[1:]:
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    params[k.lower()] = v
                else:
                    pos.append(tok)
            if not pos:
                raise PlanError(f"unparsable card: {s!r}")
            if t[0][0] in "Rr" and len(pos) == 3:      # `Rname n1 n2 value`: ideal resistor
                pos = pos[:2] + ["ideal_res"]
            out[cur]["cards"].append({"name": t[0], "model": pos[-1], "nets": pos[:-1], "params": params})
    return out


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
    """Leaf devices of `top`: [{path, model, nets, params}], hierarchical nets namespaced."""
    if top not in subckts:
        raise PlanError(f"no .subckt {top!r}")
    out = []

    def walk(name, prefix, net_map):
        for c in subckts[name]["cards"]:
            nets = [n if n.endswith("!") else net_map.get(n, prefix + n) for n in c["nets"]]
            if c["model"] in LEAF_MODELS:
                out.append({"path": prefix + c["name"], "model": c["model"], "nets": nets,
                            "params": c["params"]})
            elif c["model"] in subckts:
                ports = subckts[c["model"]]["ports"]
                if len(ports) != len(nets):
                    raise PlanError(f"{prefix}{c['name']}: {c['model']} has {len(ports)} ports, "
                                    f"instantiated with {len(nets)}")
                walk(c["model"], prefix + c["name"] + ".", dict(zip(ports, nets)))
            else:
                raise PlanError(f"{prefix}{c['name']}: no layout primitive for model {c['model']!r}")

    walk(top, "", {})
    return out


def _slug(v):
    return f"{v:g}".replace(".", "p").replace("-", "m")


def plan(block, devices):
    """Group leaf devices into klt gen requests. Each unit gets the device's nets."""
    mos, res, caps = {}, {}, {}
    for d in devices:
        who, p = d["path"], d["params"]
        n = _mult(p, who)
        if d["model"] in UNDRAWN_MODELS:
            continue
        if d["model"] in MOS_MODELS:
            key = (MOS_MODELS[d["model"]], _num(p, "w", who), _num(p, "l", who), int(_num(p, "ng", who)) if "ng" in p else 1)
            mos.setdefault(key, []).extend([d] * n)
        elif d["model"] in RES_MODELS:
            res.setdefault((RES_MODELS[d["model"]], _num(p, "w", who), _num(p, "l", who)), []).extend([d] * n)
        else:
            caps.setdefault((_num(p, "w", who), _num(p, "l", who)), []).extend([d] * n)
    groups = []
    for (flav, w, l, ng), mem in sorted(mos.items()):
        rows = max(r for r in range(1, math.isqrt(len(mem)) + 1) if len(mem) % r == 0)
        groups.append({
            "id": f"{block}_{flav}_w{_slug(w)}_l{_slug(l)}" + (f"_ng{ng}" if ng > 1 else ""),
            "generator": "mos_array", "klass": flav, "count": len(mem),
            "params": {"w_um": w, "l_um": l, "fingers": ng, "rows": rows, "cols": len(mem) // rows,
                       "dummy": 0, "flavor": flav, "voltage_flavor": VOLTAGE_FLAVOR,
                       "topology": "array", "gate_contact": True},
            "terminals": [{"port": f"U{i}_{t}", "net": m["nets"][k], "unit": m["path"]}
                          for i, m in enumerate(mem) for k, t in enumerate("DGS")],
        })
    for (flav, w, l), mem in sorted(res.items()):
        groups.append({
            "id": f"{block}_res{flav}_w{_slug(w)}_l{_slug(l)}",
            "generator": "res_array", "klass": flav, "count": len(mem),
            "params": {"length_um": l, "width_um": w, "num": len(mem), "dummy": 0, "rows": 1,
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
    return groups


# --- klt driving ---------------------------------------------------------------------------


def klt(args, cwd, pdk_root=None):
    a = list(args)
    p = subprocess.run(["klt"] + a, capture_output=True, text=True, cwd=cwd)
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


def port_net_label_sites(groups, reports, origins):
    """{net: (x_um, y_um, layer, datatype)}: the first drawn terminal of each net, block frame."""
    site = {}
    for g in groups:
        rep = reports[g["id"]]
        pos = {p["name"]: p for p in rep["ports"]}
        for t in g["terminals"]:
            p = pos.get(t["port"])
            if p is None or t["net"] in site:
                continue
            o = origins[g["id"]]
            site[t["net"]] = (o["x"] + p["x_um"], o["y"] + p["y_um"], p["layer"]["layer"], p["layer"]["datatype"])
    return site


def build_block(cell, subckt, netlist, out_dir, input_first=()):
    """Generate `cell` (a placed-device cell with port labels) for `subckt` in `netlist`.

    input_first: port names whose gate-connected device group is placed first (at the origin),
    so a tank-loading input (prescaler INP/INN) sits at the cell edge and stays compact.
    Returns the provenance record for the cell. Raises PlanError / RuntimeError on any failure.
    """
    os.makedirs(out_dir, exist_ok=True)
    subckts = read_subckts(netlist)
    ports = subckts[subckt]["ports"]
    devices = flatten(subckts, subckt)
    groups = plan(cell, devices)
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
        return 0 if any(t["net"] in input_first and t["port"].split("_")[1] == "G" for t in g["terminals"]) else 1
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
        if rep.get("device_count", g["count"]) != g["count"] and g["generator"] != "cap_array":
            raise RuntimeError(f"{g['id']}: drew {rep.get('device_count')} devices, planned {g['count']}")

    groups = [g for g in groups if g["id"] not in refused]
    sizes = []
    for g in groups:
        b = reports[g["id"]]["bbox_um"]
        sizes.append((g["id"], b["x1"] - b["x0"], b["y1"] - b["y0"]))
    origins = shelf_pack(sizes, BLOCK_TARGET_WIDTH_UM, GROUP_SPACING_UM)
    req = {"schema": "klt.gen_compose.request/1", "pdk": {"variant": PDK},
           "blocks": [{"id": g["id"], "generator_report": reports[g["id"]]} for g in groups],
           "placement": {"strategy": "explicit", "order": [g["id"] for g in groups], "origins_um": origins},
           "options": {"cell_name": cell, "output": f"{cell}.raw.gds"}}
    with open(os.path.join(out_dir, f"{cell}.compose.json"), "w") as f:
        json.dump(req, f, indent=1, sort_keys=True)
    rc, rep = klt(["gen-compose", f"{cell}.compose.json", "--format", "json"], out_dir)
    if rc != 0 or "error" in rep:
        raise RuntimeError(f"klt gen-compose failed for {cell}: {rep}")

    # Stamp port labels on a drawn terminal of each port net.
    sites = port_net_label_sites(groups, reports, origins)
    missing = [p for p in ports if p not in sites]
    ly = db.Layout()
    ly.read(os.path.join(out_dir, f"{cell}.raw.gds"))
    top = ly.cell(cell)
    if top is None:
        raise RuntimeError(f"{cell}.raw.gds has no cell {cell!r}")
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
    return {
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
                    "bbox_um": [reports[g["id"]]["bbox_um"][k] for k in ("x0", "y0", "x1", "y1")]}
                   for g in groups],
        "commands": cmds + [f"klt gen-compose {cell}.compose.json --format json"],
    }
