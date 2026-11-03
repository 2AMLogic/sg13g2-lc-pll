# sim/corner-verification

T1 item 5 (full corner verification), tracker #5, issue #39. `klt sim` corner envelopes over the
spec C-grid (`spec/target-spec.md` §Corner set). **Simulated, not measured.** This is the first
slice; item 5 is `unmet` and stays so (see "Row status").

## Where the grid ran

Both requests went to the Spot batch fleet (`backend: batch`, `klt sim --wait-for-capacity`), not
the dispatch host. A first stage-1 submit was refused with `batch_no_capacity` (shared spot vCPU
quota full); it was retried with a bounded capacity wait and was not run locally. Job ids:
stage 1 `klt-sim-68a7987fe626`, stage 2 `klt-sim-370cccc80aa5` (an earlier identical-circuit pass,
`klt-sim-d98401a6c111` / `klt-sim-573cc2fb2559`, ran before the `spec_row` tags were added and gave
the same verdicts and values). **Simulator: ngspice 46 on the fleet, against the pin of 47**
(`sim/pins.json`). The records carry the version in `environment`; the pin is not met.

## `cp-dc/`: charge pump, rows 6 and 7

`make_requests.py` writes `request-stage{1,2}.json`; `cp_body.spice` is the circuit body (same
circuit as `sim/cp-dc`). The CP holds only HV MOS, so the HBT and MIM axes do not touch it: the
135-point grid collapses to 15 distinct points (stage 1, 3.300 V) and the 18 supply sub-corners
(stage 2, SLOW/TYP/FAST = `mos_ss`/`mos_tt`/`mos_ff` here). Records are append-only under
`cp-dc/records/`. Measured at V_out = 1.65 V with IREF = 20 uA: I_up, I_dn (limits 100-400 uA, row 6
design range) and mismatch (limit 2 %, row 7 lower edge). `vtop_est` is the top of the <= 2 %
window assuming mismatch rises monotonically from 1.65 V; it is reported, not graded.

| | stage 1 (15, 3.300 V) | stage 2 (18, 2.970 / 3.630 V) |
|---|---|---|
| verdict | 15 pass | 17 pass, **1 fail** |
| I_up, I_dn at 1.65 V | 195-202 uA (all inside 100-400 uA) | 191-206 uA (all inside) |
| mismatch at 1.65 V, worst | 0.65 % (`mos_ff`, 125 C) | **2.19 % (FAST, 3.630 V, -40 C)** |
| window top `vtop_est` | 2.30-2.60 V | 1.90-2.90 V (binding: SLOW/2.970 V/125 C, 1.90 V) |

Finding, not relaxed: FAST at 3.630 V and -40 C exceeds the 2 % row-7 bound at the lower edge
(2.19 %). Row 6 itself is inside its range at every corner, but the stage-2 envelope reads `fail`
as a whole, so the manifest cites it and item 5 reads `unmet / check_failed`.

The window top at 2.97 V is 1.9-2.2 V, far below the VCO window top of 3.30 V. Whether that
matters is decided by V_hi,req (gate G4, VCO graded f(Vctrl)); it is not graded here.

## Row status

| Row | State | Why |
|---|---|---|
| 6 | enveloped, in range at all 33 | `cp-dc` |
| 7 | **gap** | upper edge needs G4; lower edge fails at one corner (above) |
| 1, 9, 10 | **gap** | benches run on a behavioural VCO/divider stand-in; G4, G2, #61. A stand-in envelope is never reported as a pass |
| 5 | **gap** | method L (`sim/loop-model`) is not a `klt sim` request |
| 8 | **gap** | method L partial, method T not run (G6) |
| 11 | **gap** | divider does not divide at 625 MHz (#61) |

The prescaler follower Vce against BVCEO (2.2 V min) at the minimum-supply corner is **not**
reported: the CP netlist contains no prescaler. It belongs to the envelopes that include it.
