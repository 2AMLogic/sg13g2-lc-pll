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

## `vco-prescaler-load/`: gate G2, VCO rows 1, 2, 6, 7 with the prescaler on the tank (issue #87)

`make_requests.py` writes the circuit bodies (`vco_{loaded,unloaded}.spice`: the fetched, sha256-verified pinned VCO deck, element lines verbatim,
supply and Vctrl as `.param` axes, plus the prescaler instance when loaded) and the requests; `make_record.py` grades the downloaded reports into
`vco-prescaler-load/records/`. Stage 2 (SLOW/TYP/FAST x 3 T x {2.970, 3.630} V x Vctrl {0, 1.65, 3.3} V = 54 units, loaded and unloaded) and
stage 1 (135 units at 3.300 V, Vctrl 1.65 V, loaded only) went to the Spot batch fleet; nothing ran on the dispatch host. The varactor OSDI is
`$PDK_ROOT/ihp-sg13g2/libs.tech/ngspice/osdi/mosvar.osdi`, resolved on the runner (byte-identical to the pinned compile). Simulator ngspice 46 on
the fleet, pin 47. Simulated, not measured. Fleet jobs: stage 2 `klt-sim-e55abdb69dac` (loaded) and `klt-sim-d42725e9af99` (unloaded), 125 C
`klt-sim-cb2cf885e9cb` / `klt-sim-3d331c63fa67`; stage 1 `klt-sim-f4d4f892ccf2`, `-b09e18b5da16`, `-03fff013900a`, `-a8d6993e1753`, `-f2d460923309`.

Findings, not relaxed:

- **Row 1 fails with and without the load**: 0 of 162 converged corners oscillate inside 4.5-5.5 GHz (3.69-4.30 GHz). The load shifts f by -20 to -7 MHz
  and adds 10-36 mV of swing; it is not the cause.
- **Row 7 swing holds** at every converged corner (min 0.446 V loaded, limit 0.40 V). The row 6 ratio g_m / loss is not extracted; only a startup-time
  proxy (0.2 V reached, 138-182 ps) is recorded.
- **125 C did not start at any corner** (loaded and unloaded): the transient aborts at its first timepoint (HBT, `timestep_too_small`). 125 C is
  therefore **not graded** for any of rows 1, 6, 7; whether this is a netlist or a start-up artifact is not established (filed on `sg13g2-vco` #280).
- Two whole-stage jobs hit the fleet's 3600 s ceiling (about 820 s per corner): the 125 C units were lost and re-run on their own; one shard job of a
  `--batch-set` was refused by the runner check and two stayed `interrupted`, so those were not used (klayout-tools#4885). The stage 2
  records merge the converged units of the jobs listed above; a later report supersedes an earlier one for the same corner.

G2 stays open: row 1 does not close, 125 C is ungraded, row 6 is a proxy.

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
