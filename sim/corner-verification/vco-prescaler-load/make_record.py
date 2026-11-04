#!/usr/bin/env python3
"""Grade the G2 C-grid klt sim reports into records/<id>.md and records/<id>-corners.csv.

python3 -I make_record.py <id> <label>=<report.json> ...    label = loaded | unloaded (several reports per label are merged)
A corner that errored is listed with its diagnostic code and is never counted as a pass. Nothing is relaxed:
row 1 = f in 4.5-5.5 GHz, row 7 = vpp >= 0.40 V (differential, 10-20 ns); startup is only the time v(OUTP)-v(OUTN)
first reaches 0.2 V from the 10 mV kick (a proxy, not the row 6 g_m / loss ratio).
"""
import collections
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def rows(path):
    r = json.load(open(path))
    out = []
    for c in r["corners"]:
        m = {x["name"]: x["value"] for x in c["measurements"]}
        t = m.get("fosc_t40")
        diag = sorted({d["code"] for d in c.get("diagnostics", []) if d["severity"] == "error" and d["code"] not in ("measurement",)})
        out.append({"corner_id": c["corner_id"], "process": c["process"], "T": c["temperature_c"],
                    "vddv": c["params"]["vddv"], "vctrl": c["params"]["vctrl"], "status": c["status"],
                    "f_ghz": (30.0 / t / 1e9) if t else None, "vpp": m.get("vpp"), "tst_ps": (m["tst"] * 1e12) if m.get("tst") else None,
                    "diag": "+".join(diag)})
    return r, out


def main():
    rid = sys.argv[1]
    data = collections.defaultdict(list)  # label -> rows
    env = {}
    for a in sys.argv[2:]:
        label, path = a.split("=", 1)
        r, rr = rows(path)
        # a later report supersedes an earlier one for the same corner (the 125 C units lost at the fleet's whole-job
        # ceiling in a whole-stage job are re-run in their own job)
        merged = {x["corner_id"]: x for x in data[label]}
        merged.update({x["corner_id"]: x for x in rr})
        data[label] = list(merged.values())
        env[label] = env.get(label) or r["environment"]
    allrows = [dict(x, case=l) for l in data for x in data[l]]
    with open(os.path.join(HERE, "records", rid + "-corners.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["case", "corner_id", "process", "T", "vddv", "vctrl", "status", "f_ghz", "vpp", "tst_ps", "diag"])
        w.writeheader()
        for x in allrows:
            w.writerow({k: ("" if x[k] is None else ("%.4g" % x[k] if isinstance(x[k], float) else x[k])) for k in w.fieldnames})
    L = ["# vco-prescaler-load C-grid %s" % rid, "",
         "**Result (simulated on the Spot batch fleet, not measured)**. Pinned `sg13g2-vco` unmodified; prescaler input on the tank (`loaded`) and without (`unloaded`).", ""]
    for case in ("loaded", "unloaded"):
        d = data.get(case, [])
        if not d:
            continue
        ok = [x for x in d if x["status"] == "pass" and x["f_ghz"]]
        bad = [x for x in d if x not in ok]
        inband = [x for x in ok if 4.5 <= x["f_ghz"] <= 5.5]
        lowv = [x for x in ok if x["vpp"] < 0.40]
        L += ["## %s: %d units returned, %d converged and oscillating, %d errored" % (case, len(d), len(ok), len(bad)), ""]
        if ok:
            L += ["- f_osc over the converged corners: %.3f to %.3f GHz; **in the 4.5-5.5 GHz band (row 1): %d of %d**." % (min(x["f_ghz"] for x in ok), max(x["f_ghz"] for x in ok), len(inband), len(ok)),
                  "- Vpp differential: %.3f to %.3f V; below 0.40 V (row 7): %d of %d." % (min(x["vpp"] for x in ok), max(x["vpp"] for x in ok), len(lowv), len(ok)),
                  "- startup proxy (0.2 V reached): %.0f to %.0f ps." % (min(x["tst_ps"] for x in ok), max(x["tst_ps"] for x in ok))]
        if bad:
            c = collections.Counter((x["T"], x["diag"] or x["status"]) for x in bad)
            L += ["- errored/unreturned: " + "; ".join("%s C: %d x %s" % (t, n, dg) for (t, dg), n in sorted(c.items(), key=str))]
        L += [""]
    if data.get("loaded") and data.get("unloaded"):
        u = {x["corner_id"]: x for x in data["unloaded"] if x["f_ghz"]}
        sh = [(x["f_ghz"] - u[x["corner_id"]]["f_ghz"], x["vpp"] - u[x["corner_id"]]["vpp"], x) for x in data["loaded"] if x["f_ghz"] and x["corner_id"] in u]
        if sh:
            L += ["## Load effect, loaded minus unloaded, same corner (%d pairs)" % len(sh), "",
                  "- frequency shift: %.0f to %.0f MHz (mean %.0f MHz)." % (min(s[0] for s in sh) * 1e3, max(s[0] for s in sh) * 1e3, sum(s[0] for s in sh) / len(sh) * 1e3),
                  "- Vpp change: %.0f to %.0f mV (positive means the loaded VCO swings more)." % (min(s[1] for s in sh) * 1e3, max(s[1] for s in sh) * 1e3), ""]
    L += ["Per-corner values: `%s-corners.csv`. The `tst` startup number is a proxy; the row 6 ratio g_m / tank loss >= 3.0 is **not** extracted." % rid, ""]
    e = next(iter(env.values()), {})
    L += ["- **Simulator**: %s on the fleet (`engine_version`), pin is 47 (`sim/pins.json`): mismatch. OSDI `mosvar.osdi` and `psp103.osdi` resolved on the runner under `$PDK_ROOT/ihp-sg13g2/libs.tech/ngspice/osdi/` (`options.osdi_preload`, runner-resolved; the PDK's prebuilt mosvar.osdi is byte-identical to the pinned compile, sha256 `25e64a37...fb41`)." % e.get("engine_version"),
          "- **Method**: per corner one `tran 1p 20n 0 2p` from the deck's 10 mV `.ic` kick; fosc = 30 / time between zero rising crossings 40 and 70 of v(OUTP)-v(OUTN); Vpp over 10-20 ns. Same decks as `sim/vco-prescaler-load` except that the supply and Vctrl are `.param` axes and the probe BD is added (see `vco_*.spice`).",
          "- **Load presented**: the prescaler input as in `sim/vco-prescaler-load` (`design/netlist/prescaler.spice`, instance X1 on OUTP/OUTN, ideal 50 uA IREF); G1 device-level figure 1.373 fF differential. Routing capacitance not included.",
          "- **Provenance**: requests and bodies in this directory; commit `%s`." % os.environ.get("REC_SHA", "see git"), ""]
    with open(os.path.join(HERE, "records", rid + ".md"), "w") as f:
        f.write("\n".join(L))
    print("\n".join(L))


main()
