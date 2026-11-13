#!/usr/bin/env python3
"""Method-L linear phase-domain model of the integer-N LC PLL (spec section 4).

Linearized type-II, third-order charge-pump PLL of spec section 2 row 5:
series R1-C1, shunt C2, plus one extra unloaded RC pole (R3-C3).

    L(s) = I_cp * Kvco * Z(s) / (N * s)          (Kvco in Hz/V)
    Z(s) = (1 + s R1 C1) / (s (C1 + C2) (1 + s R1 C1 C2/(C1 + C2)))
           * 1 / (1 + s R3 C3)

This is the open-loop gain (I_cp/2pi A/rad) * Z * (2pi Kvco / s) / N written
with the 2pi factors cancelled. Stdlib + numpy only. No ngspice: this is the
model that method L defines; the circuit-level run is a later issue.

The three in-band terms (reference x N^2, PFD/CP x N^2, divider/prescaler) are
*inputs*, supplied by --noise-inputs. A term with no input is reported as missing
(JSON null and a name in missing_terms), never as 0.0, so a partial result cannot
be summed as if it were complete. The VCO input is a target (spec section 4), not
measured.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
FILTER_JSON = HERE / "loop-filter.json"

# Spec section 2 rows 1-3, 5, 6 and section 3 / section 4.
N_DIV = 100
F_REF_HZ = 50e6
F_OUT_HZ = N_DIV * F_REF_HZ
FC_TARGET_HZ = 1e6
FC_BAND_HZ = (0.5e6, 2.0e6)
PM_MIN_DEG = 45.0
ICP_DESIGN_A = 200e-6
KVCO_DESIGN_HZ_PER_V = 480e6
KVCO_RANGE_HZ_PER_V = (381e6, 606e6)
ICP_RANGE_A = (100e-6, 400e-6)
KVCO_GRID = [381e6, 430e6, 480e6, 540e6, 606e6]
ICP_GRID = [100e-6, 150e-6, 200e-6, 300e-6, 400e-6]

# Sizing recipe (design choices, not spec values): zero a factor 4 below f_c,
# second pole a factor 4 above, extra RC pole a factor 8 above, R3 = R1.
ZERO_RATIO = 4.0
POLE2_RATIO = 4.0
POLE3_RATIO = 8.0

# Method-L jitter estimator (spec section 4).
JITTER_BAND_HZ = (10e3, 10e6)
JITTER_PTS_PER_DECADE = 30
VCO_PN_DBC_HZ_AT_1MHZ = -105.0
TEMP_K = 300.15  # 27 C
K_B = 1.380649e-23

# Spec section 4's three in-band contributions. Each is an *input* to this model
# (--noise-inputs), not a constant: a term with no input is missing, never 0.0.
NOISE_INPUT_TERMS = ("reference_x_N2", "pfd_cp_x_N2", "divider_prescaler")


class NoiseInputError(ValueError):
    """An unusable --noise-inputs file: unknown term, no source, or a bad table."""


def load_noise_inputs(path):
    """Read the optional in-band noise-input file; {} when no path is given.

    Format (one entry per term of NOISE_INPUT_TERMS, all optional):

        {"pfd_cp_x_N2": {"ssb_dbc_per_hz": [[f_hz, dBc/Hz], ...],
                         "source": "where this number comes from"}}

    Each table is single-sideband phase noise **referred to the PFD input**
    (spec section 4: "reference x N^2, PFD/CP input-referred noise x N^2";
    budget line "-138 dBc/Hz referred to the PFD input"). `source` is mandatory:
    spec section 4 requires every input to state its source. Raises
    NoiseInputError on an unknown term name, a missing source or a bad table.
    """
    if not path:
        return {}
    try:
        doc = json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        raise NoiseInputError("%s: %s" % (path, exc))
    if not isinstance(doc, dict):
        raise NoiseInputError("%s: top level must be an object keyed by term name" % path)
    out = {}
    for name, spec in doc.items():
        if name not in NOISE_INPUT_TERMS:
            raise NoiseInputError("unknown term %r (known: %s)" % (name, ", ".join(NOISE_INPUT_TERMS)))
        if not isinstance(spec, dict):
            raise NoiseInputError("%s: must be an object with ssb_dbc_per_hz and source" % name)
        source = spec.get("source")
        if not isinstance(source, str) or not source.strip():
            raise NoiseInputError(
                "%s: a non-empty 'source' string is mandatory (spec section 4: every input states its source)" % name)
        table = spec.get("ssb_dbc_per_hz")
        if not isinstance(table, list) or not table:
            raise NoiseInputError("%s: 'ssb_dbc_per_hz' must be a non-empty list of [f_hz, dBc/Hz] pairs" % name)
        pts = []
        for row in table:
            ok = (isinstance(row, (list, tuple)) and len(row) == 2
                  and all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) for x in row))
            if not ok:
                raise NoiseInputError(
                    "%s: each ssb_dbc_per_hz entry must be [f_hz, dBc/Hz] finite numbers, got %r" % (name, row))
            if row[0] <= 0:
                raise NoiseInputError("%s: f_hz must be > 0 (the table is interpolated over log f), got %r" % (name, row[0]))
            pts.append([float(row[0]), float(row[1])])
        if any(pts[i][0] >= pts[i + 1][0] for i in range(len(pts) - 1)):
            raise NoiseInputError("%s: ssb_dbc_per_hz must be strictly increasing in f_hz" % name)
        out[name] = {"ssb_dbc_per_hz": pts, "source": source}
    return out


def _interp_ssb_dbc(table, f_hz):
    """dBc/Hz at f: linear in dB over log f, held flat beyond the end points."""
    fs = np.array([p[0] for p in table], dtype=float)
    db = np.array([p[1] for p in table], dtype=float)
    if fs.size == 1:  # a single point is a flat floor
        return np.full(np.shape(f_hz), db[0], dtype=float)
    return np.interp(np.log(np.asarray(f_hz, dtype=float)), np.log(fs), db)


def _ssb_input_summary(table):
    """One-line description of an in-band input, for the method block."""
    plane = "SSB phase noise referred to the PFD input, shaped by N^2 |L/(1+L)|^2"
    if len(table) == 1:
        return "%s; flat floor at %.1f dBc/Hz" % (plane, table[0][1])
    return "%s; %d-point table over %.4g-%.4g Hz, linear in dB over log f, flat beyond the end points" % (
        plane, len(table), table[0][0], table[-1][0])


def jitter_label(missing_terms):
    """The completeness label every jitter value carries, from the missing list."""
    tail = "VCO input is target, not measured"
    if missing_terms:
        return "method L, partial: no input for %s (reported missing, not zero); %s" % (
            ", ".join(missing_terms), tail)
    return "method L, all five section 4 terms supplied; %s" % tail


def open_loop(f_hz, flt, icp_a, kvco_hz_per_v):
    """Complex open-loop gain L(j 2 pi f)."""
    s = 2j * math.pi * np.asarray(f_hz, dtype=float)
    r1, c1, c2, r3, c3 = (flt[k] for k in ("r1_ohm", "c1_f", "c2_f", "r3_ohm", "c3_f"))
    ceq = c1 * c2 / (c1 + c2)
    z1 = (1 + s * r1 * c1) / (s * (c1 + c2) * (1 + s * r1 * ceq))
    return icp_a * kvco_hz_per_v * z1 / (1 + s * r3 * c3) / (N_DIV * s)


def phase_margin_deg(f_hz, flt):
    """PM from the factor phases (no unwrap): the 1/s^2 integrators give -180."""
    w = 2 * math.pi * f_hz
    r1, c1, c2, r3, c3 = (flt[k] for k in ("r1_ohm", "c1_f", "c2_f", "r3_ohm", "c3_f"))
    ceq = c1 * c2 / (c1 + c2)
    return math.degrees(
        math.atan(w * r1 * c1) - math.atan(w * r1 * ceq) - math.atan(w * r3 * c3)
    )


def unity_gain_hz(flt, icp_a, kvco_hz_per_v, lo=1e3, hi=1e9):
    """Unity-gain crossing of |L| by bisection on log f (|L| falls monotonically)."""
    def mag(f):
        return abs(open_loop(f, flt, icp_a, kvco_hz_per_v))
    if mag(lo) < 1 or mag(hi) > 1:
        return float("nan")
    llo, lhi = math.log(lo), math.log(hi)
    for _ in range(200):
        mid = 0.5 * (llo + lhi)
        if mag(math.exp(mid)) > 1:
            llo = mid
        else:
            lhi = mid
    return math.exp(0.5 * (llo + lhi))


def _shape(r1):
    """Filter with the zero/pole frequencies pinned relative to f_c, given R1."""
    wc = 2 * math.pi * FC_TARGET_HZ
    c1 = ZERO_RATIO / (wc * r1)
    ceq = 1 / (POLE2_RATIO * wc * r1)
    c2 = ceq * c1 / (c1 - ceq)
    r3 = r1
    c3 = 1 / (POLE3_RATIO * wc * r3)
    return {"r1_ohm": r1, "c1_f": c1, "c2_f": c2, "r3_ohm": r3, "c3_f": c3}


def size_filter(icp_a=ICP_DESIGN_A, kvco_hz_per_v=KVCO_DESIGN_HZ_PER_V):
    """Type-II recipe at f_c = FC_TARGET_HZ; R1 solved so the exact |L| = 1 there."""
    def mag(r1):
        return abs(open_loop(FC_TARGET_HZ, _shape(r1), icp_a, kvco_hz_per_v))
    lo, hi = 100.0, 1e6  # ohm; |L| rises with R1
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        if mag(mid) < 1:
            lo = mid
        else:
            hi = mid
    return _shape(math.sqrt(lo * hi))


def check_point(f_c_hz, pm_deg):
    """Spec row 5 gate; returns the list of violated bounds (empty = pass)."""
    bad = []
    if not (FC_BAND_HZ[0] <= f_c_hz <= FC_BAND_HZ[1]):  # NaN fails too
        bad.append("f_c outside [%.1f, %.1f] MHz" % (FC_BAND_HZ[0] / 1e6, FC_BAND_HZ[1] / 1e6))
    if not pm_deg >= PM_MIN_DEG:
        bad.append("PM < %.0f deg" % PM_MIN_DEG)
    return bad


def _trapz_logf(f, y):
    """Trapezoid of y df on a log-f grid: integrate y*f over ln f."""
    g = y * f
    return float(np.sum(0.5 * (g[1:] + g[:-1]) * np.diff(np.log(f))))


def jitter(flt, icp_a, kvco_hz_per_v, noise_inputs=None):
    """Method-L rms jitter: VCO target line + R1 noise + any supplied in-band term.

    L(f) = S_phi/2 (single-sideband, dBc/Hz linear). sigma_phi^2 = 2 int L df.
    A term of NOISE_INPUT_TERMS with no entry in noise_inputs is reported as None
    in sigma_phi_sq_rad2_by_term and named in missing_terms; it is never 0.0.
    """
    noise_inputs = noise_inputs or {}
    decades = math.log10(JITTER_BAND_HZ[1] / JITTER_BAND_HZ[0])
    f = np.logspace(
        math.log10(JITTER_BAND_HZ[0]), math.log10(JITTER_BAND_HZ[1]),
        int(round(decades * JITTER_PTS_PER_DECADE)) + 1,
    )
    s = 2j * math.pi * f
    loop = open_loop(f, flt, icp_a, kvco_hz_per_v)
    err = np.abs(1 / (1 + loop)) ** 2  # high-pass seen by the VCO

    l_vco = 10 ** (VCO_PN_DBC_HZ_AT_1MHZ / 10) * (1e6 / f) ** 2 * err

    r1, c1, c2, r3, c3 = (flt[k] for k in ("r1_ohm", "c1_f", "c2_f", "r3_ohm", "c3_f"))
    # R1 voltage source in the series R1-C1 branch, C2 across it, CP open (unloaded).
    vx = (1 / (s * c2)) / (1 / (s * c2) + r1 + 1 / (s * c1))
    t_r1 = vx / (1 + s * r3 * c3)
    l_r1 = 0.5 * 4 * K_B * TEMP_K * r1 * np.abs(t_r1) ** 2 * (kvco_hz_per_v / f) ** 2 * err

    terms = {"vco_target_line": l_vco, "r1_thermal": l_r1}
    # In-band terms: an SSB table referred to the PFD input, shaped to the output by
    # N^2 |L/(1+L)|^2 (spec section 4 "reference x N^2, PFD/CP input-referred x N^2").
    cl = np.abs(loop / (1 + loop)) ** 2
    for name in NOISE_INPUT_TERMS:
        spec = noise_inputs.get(name)
        if spec is not None:
            l_in = 10 ** (_interp_ssb_dbc(spec["ssb_dbc_per_hz"], f) / 10)
            terms[name] = l_in * N_DIV ** 2 * cl
    var = {k: 2 * _trapz_logf(f, v) for k, v in terms.items()}
    sigma_phi = math.sqrt(sum(var.values()))
    by_term = {"vco_target_line": var["vco_target_line"], "r1_thermal": var["r1_thermal"]}
    for name in NOISE_INPUT_TERMS:
        by_term[name] = var.get(name)  # None -> JSON null: no input, NOT zero noise
    return {
        "jitter_rms_s": sigma_phi / (2 * math.pi * F_OUT_HZ),
        "sigma_phi_rad": sigma_phi,
        "sigma_phi_sq_rad2_by_term": by_term,
        "missing_terms": [k for k in NOISE_INPUT_TERMS if k not in terms],
    }


def sweep(flt, noise_inputs=None):
    """f_c, PM and jitter at every (Kvco, I_cp) grid point."""
    noise_inputs = noise_inputs or {}
    points = []
    for icp in ICP_GRID:
        for kvco in KVCO_GRID:
            f_c = unity_gain_hz(flt, icp, kvco)
            pm = phase_margin_deg(f_c, flt)
            j = jitter(flt, icp, kvco, noise_inputs)
            points.append({
                "kvco_hz_per_v": kvco,
                "icp_a": icp,
                "f_c_hz": f_c,
                "pm_deg": pm,
                "jitter_rms_s": j["jitter_rms_s"],
                "sigma_phi_rad": j["sigma_phi_rad"],
                "sigma_phi_sq_rad2_by_term": j["sigma_phi_sq_rad2_by_term"],
                "missing_terms": j["missing_terms"],
                "jitter_label": jitter_label(j["missing_terms"]),
                "gated": icp == ICP_DESIGN_A,
                "violations": check_point(f_c, pm),
            })
    return points


def method_block(noise_inputs=None):
    noise_inputs = noise_inputs or {}
    missing = [k for k in NOISE_INPUT_TERMS if k not in noise_inputs]
    return {
        "method": "L (linear phase-domain model), spec/target-spec.md section 4",
        "jitter_label": jitter_label(missing),
        "missing_terms": missing,
        "model": "L(s) = I_cp*Kvco*Z(s)/(N*s); Z = (R1-C1 || C2) then unloaded R3-C3 low-pass",
        "assumptions": [
            "R3-C3 is an unloaded RC after the first stage (no loading of C2 node by R3)",
            "R3 = R1 by sizing choice; R3 thermal noise is not included",
            "first-order: no in-loop peaking beyond L(s), no sampling-time effects, no CP nonlinearity",
            "supply/substrate coupling into the tank is not modelled (graded post-layout)",
            "the three in-band terms are taken at one reference plane, the PFD input, and shaped"
            " to the output by N^2 |L/(1+L)|^2; for divider/prescaler that plane is a reading of"
            " spec section 4 ('divider/prescaler jitter'), which does not fix one (#252)",
            "a term with no input is missing, not zero: its true contribution is unknown",
        ],
        "inputs": {
            "N": {"value": N_DIV, "source": "spec section 2 row 3"},
            "f_ref_hz": {"value": F_REF_HZ, "source": "spec section 2 row 2"},
            "f_out_hz": {"value": F_OUT_HZ, "source": "N * f_ref; spec section 2 row 1"},
            "f_c_target_hz": {"value": FC_TARGET_HZ, "source": "spec section 2 row 5"},
            "f_c_band_hz": {"value": list(FC_BAND_HZ), "source": "spec section 2 row 5"},
            "pm_min_deg": {"value": PM_MIN_DEG, "source": "spec section 2 row 5"},
            "icp_design_a": {"value": ICP_DESIGN_A, "source": "spec section 2 row 6"},
            "icp_range_a": {"value": list(ICP_RANGE_A), "source": "spec section 2 row 6"},
            "kvco_design_hz_per_v": {"value": KVCO_DESIGN_HZ_PER_V, "source": "spec section 3 (geometric mid)"},
            "kvco_range_hz_per_v": {"value": list(KVCO_RANGE_HZ_PER_V), "source": "spec section 3"},
            "kvco_grid_hz_per_v": {"value": KVCO_GRID, "source": "this model: grid across spec section 3 range"},
            "icp_grid_a": {"value": ICP_GRID, "source": "this model: grid across spec section 2 row 6 range"},
            "vco_phase_noise": {
                "value": "1/f^2 line through %.0f dBc/Hz @ 1 MHz" % VCO_PN_DBC_HZ_AT_1MHZ,
                "source": "spec section 4 / sg13g2-vco row 4 TARGET; target, not measured",
            },
            "r1_thermal_noise": {"value": "4kT*R1, T = %.2f K" % TEMP_K, "source": "spec section 4"},
            **{
                name: {
                    "value": _ssb_input_summary(noise_inputs[name]["ssb_dbc_per_hz"]),
                    "ssb_dbc_per_hz": noise_inputs[name]["ssb_dbc_per_hz"],
                    "source": noise_inputs[name]["source"],
                }
                for name in NOISE_INPUT_TERMS if name in noise_inputs
            },
        },
        "estimator": {
            "band_hz": list(JITTER_BAND_HZ),
            "points_per_decade": JITTER_PTS_PER_DECADE,
            "integration": "trapezoid on log f",
            "sigma_phi_sq": "2 * integral L(f) df",
            "sigma_t": "sigma_phi / (2 pi f_out)",
        },
        "gate": "exit non-zero if any Kvco in the design range at I_cp = 200 uA has f_c outside [0.5, 2.0] MHz or PM < 45 deg; other grid points are reported and flagged, not gated",
    }


def run(flt, noise_inputs=None):
    noise_inputs = noise_inputs or {}
    points = sweep(flt, noise_inputs)
    gated = [p for p in points if p["gated"]]
    return {
        "method": method_block(noise_inputs),
        "loop_filter": flt,
        "design_point": {
            "kvco_hz_per_v": KVCO_DESIGN_HZ_PER_V,
            "icp_a": ICP_DESIGN_A,
            "f_c_hz": unity_gain_hz(flt, ICP_DESIGN_A, KVCO_DESIGN_HZ_PER_V),
            "pm_deg": phase_margin_deg(unity_gain_hz(flt, ICP_DESIGN_A, KVCO_DESIGN_HZ_PER_V), flt),
        },
        "points": points,
        "flagged_outside_spec_not_gated": [
            {"kvco_hz_per_v": p["kvco_hz_per_v"], "icp_a": p["icp_a"], "violations": p["violations"]}
            for p in points if p["violations"] and not p["gated"]
        ],
        "gate_pass": not any(p["violations"] for p in gated),
        "gate_violations": [
            {"kvco_hz_per_v": p["kvco_hz_per_v"], "icp_a": p["icp_a"], "violations": p["violations"]}
            for p in gated if p["violations"]
        ],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", help="write results JSON here")
    ap.add_argument("--filter", default=str(FILTER_JSON), help="loop-filter JSON (default: committed design)")
    ap.add_argument("--write-filter", action="store_true", help="re-derive the design filter and write it to --filter")
    ap.add_argument("--noise-inputs", help="JSON file of in-band SSB phase-noise tables referred to the PFD "
                                           "input (%s), each with a mandatory source; a term with no entry is "
                                           "reported as missing, never as 0.0" % ", ".join(NOISE_INPUT_TERMS))
    args = ap.parse_args(argv)

    try:
        noise_inputs = load_noise_inputs(args.noise_inputs)
    except NoiseInputError as exc:
        print("loop_model: --noise-inputs: %s" % exc, file=sys.stderr)
        return 2

    if args.write_filter:
        flt = size_filter()
        doc = {
            "design_point": {"n": N_DIV, "f_ref_hz": F_REF_HZ, "f_c_hz": FC_TARGET_HZ,
                             "kvco_hz_per_v": KVCO_DESIGN_HZ_PER_V, "icp_a": ICP_DESIGN_A},
            "topology": "series R1-C1, shunt C2, unloaded R3-C3 pole; spec section 2 row 5",
            "sizing": {"zero_ratio": ZERO_RATIO, "pole2_ratio": POLE2_RATIO, "pole3_ratio": POLE3_RATIO, "r3": "R1"},
            **flt,
        }
        Path(args.filter).write_text(json.dumps(doc, indent=2) + "\n")
    flt = {k: v for k, v in json.loads(Path(args.filter).read_text()).items()
           if k in ("r1_ohm", "c1_f", "c2_f", "r3_ohm", "c3_f")}

    res = run(flt, noise_inputs)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(res, indent=2, allow_nan=True) + "\n")
    missing = res["method"]["missing_terms"]
    tag = ("L, partial, missing " + ", ".join(missing)) if missing else "L, all five terms"
    for p in res["points"]:
        mark = "" if not p["violations"] else ("  GATE FAIL: " if p["gated"] else "  flagged: ") + "; ".join(p["violations"])
        print("Kvco %3.0f MHz/V  Icp %3.0f uA  f_c %.3f MHz  PM %5.1f deg  jitter %.3f ps (%s)%s" % (
            p["kvco_hz_per_v"] / 1e6, p["icp_a"] * 1e6, p["f_c_hz"] / 1e6, p["pm_deg"], p["jitter_rms_s"] * 1e12, tag, mark))
    if not res["gate_pass"]:
        print("GATE FAIL: design-range point(s) at I_cp = 200 uA violate spec row 5", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
