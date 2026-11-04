#!/usr/bin/env python3
"""Per-device-group mismatch attribution for the charge pump (T1 item 6, issue #78). Stdlib only.

  attribute.py groups                         list the groups and check they partition every MOS in cp.spice
  attribute.py netlist GROUP CP.spice OUT     write CP.spice with mm_ok=0 on every MOS instance NOT in GROUP
  attribute.py report REPORT.json ...         render the attribution table from klt sim reports named GROUP=path

Method: the IHP mismatch subckt (sg13g2_moshv_mod_mismatch.lib) takes an instance parameter mm_ok (default 1);
mm_ok=0 turns that instance's agauss() draws off. Each run leaves mismatch on in ONE group only, so its
mean-square of the signed up/down current difference is that group's contribution. Independent groups add in
mean-square: the sum over groups is compared with the all-on run. mm = |I_up - I_dn|/200 uA x 100, so
mean(mm^2) is the mean square of the signed difference (the sign drops out of the square).
"""
import json, re, sys

# (subckt, instance) per group. Every sg13_hv_* instance of design/netlist/cp.spice must appear exactly once.
GROUPS = {
    # n-side: XBN1 is the IREF diode whose gate IS the n-leg mirror gate; XBN2 copies IREF to the p-side bias (IBP), XBNS to ICP;
    # XBNC/XBNA bias the n-leg cascode. p-side: XBP1 is the IBP diode (= p-leg mirror gate); XBPS/XBPA copy IBP; XBPC biases the p-leg cascode.
    "bn_ref":   [("cp_bias", "XBN1")],
    "bn_xbn2":  [("cp_bias", "XBN2")],
    "bn_xbns":  [("cp_bias", "XBNS")],
    "bn_casc":  [("cp_bias", i) for i in ("XBNC", "XBNA")],
    "bp_ref":   [("cp_bias", "XBP1")],
    "bp_copy":  [("cp_bias", i) for i in ("XBPS", "XBPA")],
    "bp_casc":  [("cp_bias", "XBPC")],
    "leg_p":    [("cp_leg_p", "XM1"), ("cp_leg_p", "XM2")],
    "leg_n":    [("cp_leg_n", "XM1"), ("cp_leg_n", "XM2")],
    "switches": [("cp", i) for i in ("XIUP_P", "XIUP_N", "XIDN_P", "XIDN_N")]
                + [(s, i) for s in ("cp_leg_p", "cp_leg_n") for i in ("XSWO", "XSWD")]
                + [("cp_dumpbuf", "XM1"), ("cp_dumpbuf", "XM2")],
}

def mos_instances(text):
    sub, out = None, []
    for ln in text.splitlines():
        m = re.match(r"\.subckt\s+(\S+)", ln, re.I)
        if m: sub = m.group(1)
        elif ln.lower().startswith(".ends"): sub = None
        elif sub and re.match(r"X\S+\s.*\ssg13_hv_[np]mos\s", ln):
            out.append((sub, ln.split()[0]))
    return out

def write_netlist(group, text):
    keep = set(GROUPS[group]) if group in GROUPS else set(mos_instances(text)) if group == "all" else set()
    sub, out = None, []
    for ln in text.splitlines():
        m = re.match(r"\.subckt\s+(\S+)", ln, re.I)
        if m: sub = m.group(1)
        elif ln.lower().startswith(".ends"): sub = None
        elif sub and re.match(r"X\S+\s.*\ssg13_hv_[np]mos\s", ln) and (sub, ln.split()[0]) not in keep:
            ln += " mm_ok=0"
        out.append(ln)
    return "\n".join(out) + "\n"

def check_partition(text):
    allm = mos_instances(text); grouped = [x for g in GROUPS.values() for x in g]
    assert sorted(allm) == sorted(grouped), "groups do not partition cp.spice: missing %s extra %s" % (
        sorted(set(allm) - set(grouped)), sorted(set(grouped) - set(allm)))
    assert len(set(grouped)) == len(grouped)
    return len(allm)

def samples(report):
    d = {}
    for c in report["corners"]:
        for m in c["measurements"]:
            if m.get("value") is not None and m["name"].startswith("mm_"):
                d.setdefault(m["name"], []).append(m["value"])
    return d

def main():
    cmd = sys.argv[1]
    if cmd == "groups":
        n = check_partition(open(sys.argv[2]).read())
        print("ok: %d MOS instances partitioned into %s" % (n, {g: len(v) for g, v in GROUPS.items()}))
    elif cmd == "netlist":
        open(sys.argv[4], "w").write(write_netlist(sys.argv[2], open(sys.argv[3]).read()))
    elif cmd == "report":
        # mean-square of mm = systematic^2 + random^2 (cross term averages out). The `none` run (mismatch off everywhere)
        # measures the deterministic part; it is subtracted so each group's number is its random contribution.
        runs = {a.split("=", 1)[0]: samples(json.load(open(a.split("=", 1)[1]))) for a in sys.argv[2:]}
        names = sorted(next(iter(runs.values())))
        gs = [g for g in runs if g in GROUPS]
        print("| measurement | systematic (none) | " + " | ".join(gs) + " | sum of groups | all-on random | sum / all-on |")
        print("|---|---|" + "---|" * (len(gs) + 3))
        for n in names:
            ms = {g: sum(v * v for v in r[n]) / len(r[n]) for g, r in runs.items()}
            sysm = ms["none"]; rnd = {g: max(ms[g] - sysm, 0.0) for g in gs}; tot = ms["all"] - sysm; sg = sum(rnd.values())
            print("| %s | %.3f | " % (n, sysm ** .5) + " | ".join("%.3f (%.0f %%)" % (rnd[g] ** .5, 100 * rnd[g] / tot) for g in gs)
                  + " | %.3f | %.3f | %.2f |" % (sg ** .5, tot ** .5, sg / tot))
        print("\nAll entries are rms of mm in %; the percentage is the group's share of the all-on random mean-square (all-on minus the `none` systematic). n per run: "
              + ", ".join("%s=%d" % (g, len(r[names[0]])) for g, r in runs.items()))
    else:
        sys.exit(__doc__)

if __name__ == "__main__":
    main()
