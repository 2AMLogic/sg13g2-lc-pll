#!/usr/bin/env python3
"""Generate the klt sim requests of sim/prescaler-div89 (div89_*.request.json).

  python3 gen_requests.py            write the request files
  python3 gen_requests.py --check    exit 1 if the committed files differ from what this would write
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import corner_set  # noqa: E402  (the spec C-grid, defined once in sim/corner_set.py)

# The chain is HBT CML; the PDK poly resistors (rppd/rhigh, issue #164) ride the
# same process name: SLOW = high sheet R, FAST = low. No MOS or MIM in this netlist.
FAMILIES = ("hbt", "res")


def cross(**axes):
    """corners.params arrays are zipped by index, not crossed, so the cross product is expanded here."""
    rows = [{}]
    for k, vals in axes.items():
        rows = [dict(r, **{k: v}) for r in rows for v in vals]
    return {k: [r[k] for r in rows] for k in axes}


def xings(t_from):
    """Rising zero crossings of the differential output, plus +0.1 V rise / -0.1 V fall crossings: the swing rule
    (output >= 0.2 Vpp) is that the three series have the same count."""
    sig = "v(outp)-v(outn)"
    return [{"name": n, "unit": "s", "crossings": {"signal": sig, "level": lvl, "edge": e, "from": t_from, "max": 200}}
            for n, lvl, e in (("x_zero", 0.0, "rise"), ("x_hi", 0.1, "rise"), ("x_lo", -0.1, "fall"))]


def request(netlist, stop, t_from, params):
    return {
        "netlist": netlist,
        "engine": "ngspice",
        "models": {"pdk": "sg13g2"},
        "analysis": {"kind": "tran", "args": f"1p {stop} 0 2p"},
        "corners": {
            "process": [{"name": b, "sections": corner_set.bundle_sections(b, FAMILIES)}
                        for b in corner_set.BUNDLES],
            "temperature_c": list(corner_set.TEMPS),
            "params": params,
        },
        "options": {"stage_model_inputs": True, "ngspice_init": ["set ngbehavior=hsa"],
                    "osdi_preload": ["$PDK_ROOT/ihp-sg13g2/libs.tech/ngspice/osdi/r3_cmc.osdi"]},
        "measurements": xings(t_from),
    }


def build():
    chain = request("div89_chain.cir", "24n", "6n", cross(vddv=[2.97, 3.3, 3.63], fin=[5.0e9, 5.5e9], mcv=[0, 1]))
    # supply current (negative: it flows out of the source) averaged over 8-24 ns; power = -I x vddv, IREF branch included
    chain["measurements"].append({"name": "i_vdd_avg", "spice": ".meas tran i_vdd_avg AVG i(vdd) FROM=8n TO=24n", "unit": "A"})
    out = {"div89_chain.request.json": chain}
    # 288 async units, split by supply into two jobs so each stays well inside the fleet's 3600 s whole-job ceiling
    for tag, v in (("2p97", 2.97), ("3p63", 3.63)):
        out[f"div89_async_{tag}.request.json"] = request(
            "div89_async.cir", "34n", "0", cross(vddv=[v], fin=[5.5e9], phi=[round(i * 1e-10, 12) for i in range(16)]))
    return out


if __name__ == "__main__":
    bad = 0
    for fn, req in build().items():
        text = json.dumps(req, indent=2) + "\n"
        p = HERE / fn
        if "--check" in sys.argv:
            if not p.exists() or p.read_text() != text:
                print(f"stale: {fn}")
                bad = 1
        else:
            p.write_text(text)
    sys.exit(bad)
