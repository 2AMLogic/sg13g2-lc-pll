# loop-power start-up probe, TYP 27 C 3.300 V (2026-11-03, base `b6ec1f3`, issue #70)

**Result (simulated, not measured): at TYP 27 C 3.300 V the divider divides to 50 MHz with BOTH start-ups, so the ramp is not what stops division at this point. Whether the non-dividing corners elsewhere are a start-up artifact or a design finding is NOT settled by this probe; it is reported as unresolved, not as a pass.**

- **Method**: two single-corner `klt sim` requests (`request-probe-ramp.json`, `request-probe-nominal.json`; `mos_tt/cap_typ/hbt_typ`, 27 C, vddv 3.3) submitted together with `--batch-set` to the batch fleet, jobs `klt-sim-81ecd652e3a8` (ramp) and `klt-sim-e4b79b1f4c85` (nominal start-up). Same transient `4p 120n`, same `.meas` window 40-120 ns and tfb check as the grid (58.5-61.5 ns = 50 MHz).
- **Why not local**: the dispatch host has ngspice-42, which cannot load the pinned `psp103.osdi` (it targets OSDI v0.4; ngspice-42 supports v0.3), so `scripts/run-loop-power.sh` fails here ("could not find a valid modelname") and the probe went to the fleet. Fleet ngspice is 46 against the pin of 47 (`sim/pins.json`): **the pin is not met.**
- **Start-ups**: *ramp* = `loop_power_body.spice` (supplies, IREF, drive common mode ramp 0 V over 3 ns). *nominal* = `loop_power_body_nominal_startup.spice` (DC supplies, DC 50 uA IREF, plain SIN drive, the `.nodeset` seeding of `sim/loop-power/loop_power.spice.tmpl`).

| start-up | converged | tfb (ns) | divides | prescaler (mW) | M/A divider (mW) |
|---|---|---|---|---|---|
| ramp | yes | 60.01 | yes | 6.42 | 14.60 |
| nominal (DC + nodeset) | yes | 59.99 | yes | 6.41 | 14.88 |

- **What this shows**: the two start-ups agree to within 0.3 mW on the divider and 0.01 mW on the prescaler, and the divider divides in both. So at the nominal corner the ramp is not a source of error.
- **What it does not show**: the same point (`mos_tt/cap_typ/hbt_typ`, 27 C, 3.3 V) was recorded as NOT converged in `20261103-133412-ce1d60d-dirty-stage1.md`, so convergence in the grid depends on something other than the circuit at that point (a shard of 5 units per job on a loaded Spot instance; the 2026-11-03 run below reports `timeout` and `budget_exceeded` diagnostics). Stage-2 non-division (13 of 18) and stage-1 non-division at corners other than TYP 27 C were not probed with the nominal start-up. **Unresolved, not relaxed**: no `loop_power_body.spice` change is made and no design-finding issue is filed from this evidence; the corners that do converge and do not divide stay not-a-row-11-number.
- **Owed**: lock detector, reference and clock buffering (not zero); PFD + CP + bias is the nominal constant from `sim/loop-power/records/20261103-065025-67d1431-dirty.md`.
