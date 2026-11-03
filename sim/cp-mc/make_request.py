#!/usr/bin/env python3
"""Build the klt sim Monte Carlo request + deck for the charge-pump mismatch campaign (stdlib only).

  make_request.py --cp-netlist F --outdir D --n N --seed S [--probe]

Writes D/cp_mc.spice and D/request.json. Every number below that is a stated allowance is named as
one and echoed into the request's `description`; nothing is tuned to pass.
"""
import argparse, cmath, json, math, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ICP_NOM = 200e-6            # spec row 6 typical; mismatch is |I_up - I_dn| / ICP_NOM
F_REF = 50e6                # spec row 2
TRST_FRAC = 0.1             # t_rst / T_ref: DR-001 section Row 7 stated allowance, NOT derived
VOUTS = [1.65, 2.00, 2.25, 2.45]   # 1.65 V is the ratified lower edge; the rest probe where V_hi,req could fall (open, gate G4)
MM_LIMIT_PCT = 2.0          # spec row 7 target
VR_LIMIT_MV = 0.52          # spec row 9 target ripple budget (DR-001 section Row 9)
MOS = ["tt", "ss", "ff", "sf", "fs"]
TEMPS = [-40, 27, 125]

def z_mag(flt, f):
    s = 2j * math.pi * f
    r1, c1, c2, r3, c3 = (flt[k] for k in ("r1_ohm", "c1_f", "c2_f", "r3_ohm", "c3_f"))
    ceq = c1 * c2 / (c1 + c2)
    z = (1 + s * r1 * c1) / (s * (c1 + c2) * (1 + s * r1 * ceq)) / (1 + s * r3 * c3)
    return abs(z)

def tag(v):
    return "v%03d" % round(v * 100)

def units(probe):
    if probe:
        return [{"process": "mos_tt_mismatch", "temperature_c": 27, "supply_v": {"vdd": 3.3}}]
    u = [{"process": "mos_%s_mismatch" % m, "temperature_c": t, "supply_v": {"vdd": 3.3}} for m in MOS for t in TEMPS]
    # stage 2 (spec "Corner set"): SLOW = ss, TYP = tt, FAST = ff; the CP has no MIM or HBT, so those axes of stage 1 do not apply
    u += [{"process": "mos_%s_mismatch" % m, "temperature_c": t, "supply_v": {"vdd": v}}
          for v in (2.97, 3.63) for m in ("ss", "tt", "ff") for t in TEMPS]
    return u

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cp-netlist", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--probe", action="store_true")
    a = ap.parse_args()
    out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
    flt = json.loads((ROOT / "sim/loop-model/loop-filter.json").read_text())
    zf = z_mag(flt, F_REF)
    deck = (ROOT / "sim/cp-mc/cp_mc.spice.tmpl").read_text().replace("@@CP_SUBCKTS@@", Path(a.cp_netlist).read_text())
    (out / "cp_mc.spice").write_text(deck)

    steps = []
    for v in VOUTS:
        for nm, su, sd in (("up", 1, 0), ("dn", 0, 1)):
            steps.append({"name": "%s_%s" % (nm, tag(v)), "analysis": {"kind": "op", "args": ""},
                          "alter": {"VSU": su, "VSD": sd, "VO": v},
                          "measurements": [{"name": "cur", "expr": "i(VO)", "unit": "A"}]})
    meas = []
    for v in VOUTS:
        t = tag(v)
        d = "abs(up_%s.cur + dn_%s.cur)" % (t, t)
        meas.append({"name": "mm_%s_pct" % t, "expr": "100*%s/%.6g" % (d, ICP_NOM), "unit": "%",
                     "limits": {"max": MM_LIMIT_PCT}})
        meas.append({"name": "vr_%s_mv" % t, "expr": "1e3*2*%s*%.6g*%.9g" % (d, TRST_FRAC, zf), "unit": "mV",
                     "limits": {"max": VR_LIMIT_MV}})
    req = {
        "description": ("sg13g2-lc-pll charge-pump up/down mismatch Monte Carlo. Simulated, not measured. "
                        "mm = |I_up - I_dn| / %g uA x 100 at one V_out (static DC, one CP instance, one mismatch draw per sample); "
                        "vr = 2 |I_up - I_dn| (t_rst/T_ref = %g, stated allowance) |Z_filter(%g MHz)| (%.6g ohm from sim/loop-model/loop-filter.json) "
                        "= first-harmonic reference ripple from the mismatch only, NOT the locked-loop spur."
                        % (ICP_NOM * 1e6, TRST_FRAC, F_REF / 1e6, zf)),
        "netlist": "cp_mc.spice",
        "engine": "ngspice",
        "backend": "batch",
        "models": {"pdk": "sg13g2", "lib": "libs.tech/ngspice/models/cornerMOShv.lib"},
        "corners": {"units": units(a.probe)},
        "monte_carlo": {"n": a.n, "seed": a.seed, "vary": "mismatch", "quantiles": [1, 50, 99], "k_sigma": 3},
        "analysis_steps": steps,
        "measurements": meas,
        "options": {"timeout_s": 5, "stage_model_inputs": True,
                    "osdi_preload": ["$PDK_ROOT/ihp-sg13g2/libs.tech/ngspice/osdi/psp103.osdi"],
                    "threads_per_worker": 1,
                    "ngspice_init": ["set ngbehavior=hsa", "set num_threads=1"]},
    }
    (out / "request.json").write_text(json.dumps(req, indent=2) + "\n")
    print(json.dumps({"units": len(req["corners"]["units"]), "n": a.n, "z_ohm": zf}))

if __name__ == "__main__":
    main()
