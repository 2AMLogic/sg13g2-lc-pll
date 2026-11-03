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

## `loop-power/`: row 11 (issue #70)

`make_requests.py` writes `request-stage{1,2}.json` (stage 1 = 5 MOS x 3 MIM x 3 HBT x 3 T at 3.300 V = 135; stage 2 = SLOW/TYP/FAST x 3 T x
{2.970, 3.630} V = 18); `loop_power_body.spice` is the prescaler + M/A divider at N = 100 driven at 5.0 GHz (same circuit as
`sim/loop-power`); `make_record.py` grades the downloaded corner artifacts into `loop-power/records/`. Both stages went to the Spot batch
fleet as sharded jobs (`--max-units-per-job`, the fleet's 3600 s whole-job ceiling); nothing ran on the dispatch host. Simulator: ngspice 46
on the fleet, pin is 47.

Findings, not relaxed:

- **Stage 2 (18 corners, all returned and converged)**: only 5 divide to 50 MHz (all at 2.970 V, mostly -40 and 27 C); 13 do not (every
  3.630 V corner, and 125 C). Those 13 are not-a-row-11-number. Over the 5 dividing corners the sum with the nominal PFD/CP/bias constant is
  18.63-19.96 mW before the owed lock detector, reference and clock buffering, so row 11 is **not** shown to pass.
- **Start-up caveat**: the HBT prescaler DC operating point did not converge from the powered state at most corners, so the bench ramps the
  supplies and drive from 0 V (see the file header). A first pass without the ramp converged 4 of 18. A divide failure here may be a start-up
  artifact of that ramp and is not proven to be a design failure; the earlier nominal record used a different start-up and divided.
- **Stage 1 is incomplete**: 40 of 135 corners returned (shard jobs failed or were interrupted, and 11 of 27 shards were never submitted
  because the batch submitter hit its time limit while the fleet was out of capacity); none of the returned corners divides. Not run locally.
  The remaining corners are owed.
- PFD + CP + bias is one nominal-corner constant (1.71 mW), not a corner value.

## Row status

| Row | State | Why |
|---|---|---|
| 6 | enveloped, in range at all 33 | `cp-dc` |
| 7 | **gap** | upper edge needs G4; lower edge fails at one corner (above) |
| 1, 9, 10 | **gap** | benches run on a behavioural VCO/divider stand-in; G4, G2, #61. A stand-in envelope is never reported as a pass |
| 5 | **gap** | method L (`sim/loop-model`) is not a `klt sim` request |
| 8 | **gap** | method L partial, method T not run (G6) |
| 11 | **gap, stage 2 reads `fail`** | `loop-power/`: stage 2 ran (18 corners, 5 divide to 50 MHz, 13 do not); stage 1 incomplete (40 of 135 returned, none usable) |

The prescaler follower Vce against BVCEO (2.2 V min) at the minimum-supply corner is **not**
reported: the CP netlist contains no prescaler. It belongs to the envelopes that include it.
