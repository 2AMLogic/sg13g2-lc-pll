#!/usr/bin/env python3
"""Grade the G2 C-grid klt sim reports into records/<id>.md and records/<id>-corners.csv.

python3 -I make_record.py [--dsubw --control <records/<id>-corners.csv> ... --note <file>] <id> <label>=<report.json> ...    label = loaded | unloaded (several reports per label are merged)
Every sentence this script writes is computed from the reports it is given (and from sim/pins.json for the simulator pin); it holds no run's outcome as literal text.
Commentary the reports cannot support -- a ruling's context, an untraced cause -- belongs in --note <file>, which is appended verbatim under a heading that marks it hand-written.
--dsubw (issue #173): the reports come from the vco_*_dsubw.spice decks (ONLY the varactor's dsubw diode card carries tnom = 125). Every 125 C
number is then labelled an approximation, the leakage bound is quoted, and the 27 C units are compared with the unmodified 27 C records named by --control.
A corner that errored is listed with its diagnostic code and is never counted as a pass. Nothing is relaxed:
row 1 = f in 4.5-5.5 GHz, row 7 = vpp >= 0.40 V (differential, 10-20 ns); startup is only the time v(OUTP)-v(OUTN)
first reaches 0.2 V from the 10 mV kick (a proxy, not the row 6 g_m / loss ratio).
"""
import collections
import csv
import glob
import json
import math
import os
import re
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


import hashlib
PSHA = hashlib.sha256(open(os.path.join(HERE, '..', '..', '..', 'design', 'netlist', 'prescaler.spice'), 'rb').read()).hexdigest()


APPROX = "approximation (`dsubw` TNOM = 125 C)"
# Leakage of one dsubw instance, reverse 1.65 V, 125 C, from 2AMLogic/sg13g2-vco#303 (record 20261107-213000-fe779ef-hot-startup-trace.md,
# local single-point ngspice-46 probe; re-run in the #303 Doctor round: 5.0872e-10 / 1.65775e-12 A). 32 varactor instances in the pinned VCO.
LEAK_27REF, LEAK_125REF, NINST = 5.09e-10, 1.66e-12, 32


def supply_currents(report_path):
    """|vsup#branch| printed in each 125 C unit's ngspice.log next to the report (the value is the same for every Vctrl at one Vdd: an operating-point
    figure, not an oscillation average)."""
    out = []
    for log in glob.glob(os.path.join(os.path.dirname(report_path), "*_125C_*", "ngspice.log")):
        m = re.search(r"^vsup#branch\s+(\S+)", open(log, errors="replace").read(), re.M)
        if m and m.group(1) not in ("-nan", "nan"):
            out.append(abs(float(m.group(1))))
    return out


def pins_ngspice():
    """The pinned ngspice version read from sim/pins.json (never hard-coded here), or None if it cannot be read."""
    try:
        with open(os.path.join(HERE, "..", "..", "pins.json")) as f:
            return str(json.load(f)["ngspice"]["version"])
    except (OSError, KeyError, TypeError, ValueError):
        return None


def vnum(s):
    """Leading version number of a version string ("ngspice-46", "46", "46.1"), for comparison with the pin."""
    m = re.search(r"\d+(?:\.\d+)*", str(s if s is not None else ""))
    return m.group(0) if m else None


def round4_half(v):
    """Half the last-place step of a %.4g rendering of v: the rounding uncertainty of the 4 significant figures the control CSVs carry."""
    v = abs(float(v))
    return 0.0 if v == 0.0 else 0.5 * 10 ** (math.floor(math.log10(v)) - 3)


def main():
    args = sys.argv[1:]
    dsubw = "--dsubw" in args
    controls = []
    while "--control" in args:
        i = args.index("--control")
        controls.append(args[i + 1])
        del args[i:i + 2]
    note = None
    while "--note" in args:
        i = args.index("--note")
        note = args[i + 1]
        del args[i:i + 2]
    args = [a for a in args if a != "--dsubw"]
    rid = args[0]
    data = collections.defaultdict(list)  # label -> rows
    env = {}
    isup = collections.defaultdict(list)
    jobs = []
    for a in args[1:]:
        label, path = a.split("=", 1)
        isup[label] += supply_currents(path)
        r, rr = rows(path)
        jobs.append("%s `%s`" % (os.path.basename(os.path.dirname(path)).replace("request-", ""), (r["environment"].get("remote") or {}).get("job_id")))
        # a later report supersedes an earlier one for the same corner (the 125 C units lost at the fleet's whole-job
        # ceiling in a whole-stage job are re-run in their own job)
        merged = {x["corner_id"]: x for x in data[label]}
        merged.update({x["corner_id"]: x for x in rr})
        data[label] = list(merged.values())
        env[label] = env.get(label) or r["environment"]
    allrows = [dict(x, case=l) for l in data for x in data[l]]
    with open(os.path.join(HERE, "records", rid + "-corners.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["case", "corner_id", "process", "T", "vddv", "vctrl", "status", "f_ghz", "vpp", "tst_ps", "diag"] + (["label"] if dsubw else []))
        w.writeheader()
        for x in allrows:
            if dsubw:
                x["label"] = APPROX if x["T"] == 125 else "control: same dsubw substitution at 27 C"
            w.writerow({k: ("" if x[k] is None else ("%.4g" % x[k] if isinstance(x[k], float) else x[k])) for k in w.fieldnames})
    L = ["# vco-prescaler-load C-grid %s" % rid, "",
         "**Result (simulated on the Spot batch fleet, not measured)**. Pinned `sg13g2-vco` unmodified; prescaler input on the tank (`loaded`) and without (`unloaded`).", ""]
    if dsubw:
        L += ["**%s: every 125 C figure in this record is an approximation, not the PDK card as shipped.** Only the varactor `dsubw` diode card carries `tnom = 125` "
              "(local copy `svar_dsubw125.spice`, the `rd` variant of 2AMLogic/sg13g2-vco#303; no other card, deck or VCO line changes; the 27 C units run the same substitution). "
              "Operator ruling 2026-11-10 (issue #173). Whether the unmodified abort is a solver artefact or physical is **open**: 2AMLogic/sg13g2-vco#309 "
              "(a verdict of \"physical failure\" there reopens gate G2 for 125 C).\n" % APPROX]
    for case in ("loaded", "unloaded"):
        d = data.get(case, [])
        if not d:
            continue
        if dsubw:
            for tc in sorted({x["T"] for x in d}):
                dd = [x for x in d if x["T"] == tc]
                ok = [x for x in dd if x["status"] == "pass" and x["f_ghz"]]
                tag = " (%s)" % APPROX if tc == 125 else " (control, same substitution)"
                L += ["## %s, %s C%s: %d units returned, %d converged and oscillating, %d errored" % (case, tc, tag, len(dd), len(ok), len(dd) - len(ok)), ""]
                if ok:
                    L += ["- f_osc %.3f to %.3f GHz; in the 4.5-5.5 GHz band (row 1): %d of %d." % (min(x["f_ghz"] for x in ok), max(x["f_ghz"] for x in ok), len([x for x in ok if 4.5 <= x["f_ghz"] <= 5.5]), len(ok)),
                          "- Vpp differential %.3f to %.3f V%s; below 0.40 V (row 7): %d of %d." % (min(x["vpp"] for x in ok), max(x["vpp"] for x in ok), " [%s]" % APPROX if tc == 125 else "", len([x for x in ok if x["vpp"] < 0.40]), len(ok)),
                          "- startup proxy (0.2 V reached) %.0f to %.0f ps%s%s." % (min(x["tst_ps"] for x in ok if x["tst_ps"]), max(x["tst_ps"] for x in ok if x["tst_ps"]), " [%s]" % APPROX if tc == 125 else "",
                                                                                   "; **not reached in %d unit(s)** (%s), startup ungraded there" % (len([x for x in ok if not x["tst_ps"]]), "; ".join("%s %s V / Vctrl %s V" % (x["process"], x["vddv"], x["vctrl"]) for x in ok if not x["tst_ps"])) if [x for x in ok if not x["tst_ps"]] else "")]
                    low = [x for x in ok if x["vpp"] < 0.40]
                    if low:
                        L += ["- row 7 failures%s: " % (" [%s]" % APPROX if tc == 125 else "") + "; ".join("%s %s V / Vctrl %s V: Vpp %.3f V" % (x["process"], x["vddv"], x["vctrl"], x["vpp"]) for x in low)]
                bad = [x for x in dd if x not in ok]
                if bad:
                    L += ["- errored (still `error`, never counted as a pass; none dropped): " + "; ".join(
                        "%s / %s V / Vctrl %s V: %s" % (x["process"], x["vddv"], x["vctrl"], x["diag"] or x["status"]) for x in bad)]
                L += [""]
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
    if data.get("loaded") and data.get("unloaded") and not dsubw:
        u = {x["corner_id"]: x for x in data["unloaded"] if x["f_ghz"]}
        sh = [(x["f_ghz"] - u[x["corner_id"]]["f_ghz"], x["vpp"] - u[x["corner_id"]]["vpp"], x) for x in data["loaded"] if x["f_ghz"] and x["corner_id"] in u]
        if sh:
            L += ["## Load effect, loaded minus unloaded, same corner (%d pairs)" % len(sh), "",
                  "- frequency shift: %.0f to %.0f MHz (mean %.0f MHz)." % (min(s[0] for s in sh) * 1e3, max(s[0] for s in sh) * 1e3, sum(s[0] for s in sh) / len(sh) * 1e3),
                  "- Vpp change: %.0f to %.0f mV (positive means the loaded VCO swings more)." % (min(s[1] for s in sh) * 1e3, max(s[1] for s in sh) * 1e3), ""]
    if dsubw:
        L += ["## 27 C control: same substitution vs the unmodified 27 C result", ""]
        base = {}
        for c in controls:
            for r in csv.DictReader(open(c)):
                base[(r["case"], r["corner_id"])] = r
        pairs = [(x, base[(case, x["corner_id"])]) for case in data for x in data[case] if x["T"] == 27 and x["f_ghz"] and (case, x["corner_id"]) in base and base[(case, x["corner_id"])]["f_ghz"]]
        n27 = len([1 for case in data for x in data[case] if x["T"] == 27])
        if pairs:
            df = [(x["f_ghz"] - float(b["f_ghz"])) * 1e3 for x, b in pairs]
            dv = [(x["vpp"] - float(b["vpp"])) * 1e3 for x, b in pairs]
            dt = [x["tst_ps"] - float(b["tst_ps"]) for x, b in pairs]
            L += ["- %d of %d 27 C units have an unmodified counterpart in %s and converged under both. Modified minus unmodified: f %+.1f to %+.1f MHz (max %.2f %% of f), Vpp %+.2f to %+.2f mV (max %.2f %%), startup proxy %+.2f to %+.2f ps."
                  % (len(pairs), n27, ", ".join("`%s`" % os.path.basename(c) for c in controls), min(df), max(df), max(abs(x["f_ghz"] - float(b["f_ghz"])) / float(b["f_ghz"]) for x, b in pairs) * 100,
                     min(dv), max(dv), max(abs(x["vpp"] - float(b["vpp"])) / float(b["vpp"]) for x, b in pairs) * 100, min(dt), max(dt)),
                  "- **The control is close but not identical.** " + "; ".join(
                      ("%s %s, above the unmodified value's 4-significant-figure rounding at %d of %d pairs"
                       % (nm,
                          "up at every pair" if all(v > 0 for v in dl) else "down at every pair" if all(v < 0 for v in dl)
                          else "mixed in sign (%d up, %d down, %d equal)" % (len([v for v in dl if v > 0]), len([v for v in dl if v < 0]), len([v for v in dl if v == 0])),
                          len([1 for m_, b_ in raw if abs(m_ - b_) > round4_half(b_)]), len(raw)))
                      for nm, dl, raw in (("f", df, [(x["f_ghz"], float(b["f_ghz"])) for x, b in pairs]),
                                          ("Vpp", dv, [(x["vpp"], float(b["vpp"])) for x, b in pairs]),
                                          ("startup proxy", dt, [(x["tst_ps"], float(b["tst_ps"])) for x, b in pairs])))
                  + ". The card's `tnom` rescales the diode's junction parameters as well as its leakage, so a 27 C shift is expected; the direction above is measured, not attributed.", ""]
        else:
            L += ["- no 27 C unit of this stage has an unmodified counterpart; control not available here.", ""]
        cur = [i for v in isup.values() for i in v]
        leak = (LEAK_27REF - LEAK_125REF) * NINST
        L += ["## Leakage bound for the approximation", "",
              "- One `dsubw` instance, reverse 1.65 V, 125 C: %.2e A with `tnom = 27`, %.2e A with `tnom = 125` (2AMLogic/sg13g2-vco#303, single-point ngspice-46 probe). "
              "Difference over the %d varactor instances: at most (%.2e - %.2e) x %d = **%.1f nA total**." % (LEAK_27REF, LEAK_125REF, NINST, LEAK_27REF, LEAK_125REF, NINST, leak * 1e9)]
        for lab, v in sorted(isup.items()):
            if v:
                L += ["- Supply current printed in the 125 C `%s` units' `ngspice.log` (`vsup#branch`, operating-point value, same for every Vctrl at one Vdd): %.0f to %.0f uA; the bound is %.1e to %.1e of it."
                      % (lab, min(v) * 1e6, max(v) * 1e6, leak / max(v), leak / min(v))]
        if not cur:
            L += ["- No 125 C unit printed a `vsup#branch` value here, so the bound is not expressed as a fraction of the supply current."]
        L += ["- The bound covers the **leakage** difference only, not the card's other `tnom` effect on the diode's junction parameters (see the 27 C control above).", "",
              "## Gate G2 at 125 C (this stage)", ""]
        for case in ("loaded", "unloaded"):
            h = [x for x in data.get(case, []) if x["T"] == 125]
            if not h:
                continue
            ok = [x for x in h if x["status"] == "pass" and x["f_ghz"]]
            low = [x for x in ok if x["vpp"] < 0.40]
            unr = [x for x in ok if not x["tst_ps"]]
            L += ["- %s: %d of %d 125 C units converged under the approximation; %d of those are below 0.40 V (row 7) and %d never reach the 0.2 V startup threshold. "
                  "Swing and startup are therefore graded for the converged units only, labelled %s; %d unit(s) remain `error` (ungraded)."
                  % (case, len(ok), len(h), len(low), len(unr), APPROX, len(h) - len(ok))]
        # The verdict follows the graded data: an errored unit is never a pass, and closure is printed only when every 125 C
        # unit of this stage is graded and row 7 holds at each. Row 1 and #309 are stated as scope, not as this run's outcome.
        h125 = [x for case in ("loaded", "unloaded") for x in data.get(case, []) if x["T"] == 125]
        ok125 = [x for x in h125 if x["status"] == "pass" and x["f_ghz"]]
        bad125 = [x for x in h125 if x not in ok125]
        low125 = [x for x in ok125 if x["vpp"] < 0.40]
        unr125 = [x for x in ok125 if not x["tst_ps"]]
        why = []
        if bad125:
            why.append("%d of %d 125 C units ungraded (still `error`)" % (len(bad125), len(h125)))
        if low125:
            why.append("%d of the %d converged units below the 0.40 V row 7 bound" % (len(low125), len(ok125)))
        if unr125:
            why.append("%d of the %d converged units never reaching the 0.2 V startup threshold (startup ungraded there)" % (len(unr125), len(ok125)))
        if not h125:
            L += ["- No 125 C unit was returned in this stage, so gate G2 at 125 C is **not graded** by this record."]
        elif why:
            L += ["- **G2 is NOT recorded as closed for 125 C by this stage**: closure under the %s label needs every 125 C unit graded and row 7 (Vpp >= 0.40 V differential) met at each. Not met here: %s."
                  % (APPROX, "; ".join(why))]
        else:
            L += ["- **G2 is recorded as closed for 125 C by this stage, under the %s label only**: all %d 125 C units are graded, every one meets row 7 (Vpp >= 0.40 V differential), and the 0.2 V startup proxy is reached at each. "
                  "The label is the approximation, not the PDK card as shipped." % (APPROX, len(h125))]
        if ok125:
            L += ["- Row 1 (4.5-5.5 GHz) is out of scope for this stage (#173); over the units graded here it is met at %d of %d converged 125 C units."
                  % (len([x for x in ok125 if 4.5 <= x["f_ghz"] <= 5.5]), len(ok125))]
        L += ["- A \"physical failure\" verdict on https://github.com/2AMLogic/sg13g2-vco/issues/309 reopens gate G2 for 125 C whatever this stage records."]
        if bad125:
            cc = collections.Counter(x["diag"] or x["status"] for x in bad125)
            L += ["- Diagnostic codes of the %d ungraded 125 C unit(s), from the reports: %s. Each unit's `ngspice.log` sits beside its report; this record does not attribute a cause."
                  % (len(bad125), "; ".join("%d x `%s`" % (n, dg) for dg, n in sorted(cc.items(), key=str)))]
        L += ["", "## Fleet jobs", "",
              "- One per request (`klt sim --batch-set ... --wait-for-capacity 600`): " + "; ".join(jobs) + ". A job state of `failed` here means a nonzero verdict exit (errored units), not a runner crash.", ""]
    L += ["Per-corner values: `%s-corners.csv`. The `tst` startup number is a proxy; the row 6 ratio g_m / tank loss >= 3.0 is **not** extracted." % rid, ""]
    e = next(iter(env.values()), {})
    eng, pin = e.get("engine_version"), pins_ngspice()
    engs = str(eng) if eng else "not reported"
    if pin is None:
        pinv = "the pin was not read (`sim/pins.json` unreadable here)"
    elif vnum(eng) is None:
        pinv = "pin is %s (`sim/pins.json`): **unchecked** - the reports carry no `engine_version`" % pin
    elif vnum(eng) == vnum(pin):
        pinv = "pin is %s (`sim/pins.json`): **match**" % pin
    else:
        pinv = "pin is %s (`sim/pins.json`): **mismatch** - every number in this record was produced on the reported version, not the pinned one" % pin
    L += ["- **Simulator**: %s on the fleet (`engine_version`), %s. OSDI `mosvar.osdi` (both cases) and `psp103.osdi` + `r3_cmc.osdi` (loaded case, for the prescaler's rppd/rhigh; cornerRES.lib `res_<mim corner>` added to the loaded process sections) resolved on the runner under `$PDK_ROOT/ihp-sg13g2/libs.tech/ngspice/osdi/` (`options.osdi_preload`, runner-resolved; the PDK's prebuilt mosvar.osdi is byte-identical to the pinned compile, sha256 `25e64a37...fb41`)." % (engs, pinv),
          "- **Method**: per corner one `tran 1p 20n 0 2p` from the deck's 10 mV `.ic` kick; fosc = 30 / time between zero rising crossings 40 and 70 of v(OUTP)-v(OUTN); Vpp over 10-20 ns. Same decks as `sim/vco-prescaler-load` except that the supply and Vctrl are `.param` axes and the probe BD is added (see `vco_*.spice`).",
          "- **Load presented**: the prescaler input as in `sim/vco-prescaler-load` (`design/netlist/prescaler.spice`, instance X1 on OUTP/OUTN, ideal 50 uA IREF, sha256 `%s`); G1 device-level figure from `sim/prescaler-div89/records/20261106-222812-0ffb789-cin.md`: 1.837 fF (5.0 GHz) / 1.950 fF (5.5 GHz) differential. Routing capacitance not included." % PSHA,
          "- **Provenance**: requests and bodies in this directory; commit `%s`." % os.environ.get("REC_SHA", "see git"), ""]
    if note:
        with open(note) as f:
            L += ["## Hand-written note (not computed from the reports)", "", f.read().rstrip(), ""]
    with open(os.path.join(HERE, "records", rid + ".md"), "w") as f:
        f.write("\n".join(L))
    print("\n".join(L))


main()
