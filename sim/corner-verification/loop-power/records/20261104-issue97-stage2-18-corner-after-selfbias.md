# Stage-2 18-corner grid after the cml2cmos self-bias change (2026-11-04, base `b4f6544`, issue #97)

**Result (simulated, not measured): PARTIAL, `fail`. With the AC-coupled self-biased `cml2cmos` first inverter (`20261104-issue97-cml2cmos-selfbias-attempt1.md`), 14 of 18 stage-2 corners divide to 50 MHz (before the change: 5 of 18). All 18 returned. 4 corners, all at 125 C, still converge and do not divide. The divide-at-all-18 AC, the cause-at-the-4-remaining AC and the nominal row-11 power re-report are NOT met.**

- **Method**: the 18 corners as 18 single-corner requests (`make_stage2_shards_97.py` from `request-stage2-97-fix1.json`, `timeout_s` 1800), submitted with `klt sim --batch-set ... --max-in-flight 4 --capacity-retries 3 --budget-s 3000` on the batch fleet; ramped start-up body `loop_power_body.spice` unchanged; tran `4p 120n`, window 40-120 ns; "divides" = `tfb` (3 FB periods) 58.5-61.5 ns. One corner (FAST -40 C 3.63 V) came back `batch_job_interrupted` (spot reclamation, a non-result) and was re-run singly: it divides. No corner was run twice otherwise, so repeatability is not shown. The first client was stopped by the harness at its 10 min cap and resumed with `--resume`; some units were resubmitted (jobs of the stopped client are not collected). ngspice-46 on the fleet against the pin of 47 (`sim/pins.json`): **the pin is not met**; nothing was run locally.
- This also answers "why 16 of 18 exceeded 600 s" from the attempt-1 record: sharded, each corner took 150-495 s of runtime, so the earlier failure was the serial 18-in-one-job shape against the 3600 s whole-job ceiling, not shown to be the new RC.

## Per-corner table (ramped start-up)

| process | T (C) | Vdd (V) | class | tfb (ns) | ipavg (mA) | idavg (mA) |
|---|---|---|---|---|---|---|
| SLOW | -40 | 2.97 | divides | 60.01 | 1.94 | 3.76 |
| SLOW | -40 | 3.63 | divides | 60.00 | 1.97 | 4.95 |
| SLOW | 27 | 2.97 | divides | 60.00 | 1.86 | 3.78 |
| SLOW | 27 | 3.63 | divides | 60.00 | 1.89 | 4.95 |
| SLOW | 125 | 2.97 | converged-no-divide, FB stuck low (0.00 V) | - | 1.76 | 3.38 |
| SLOW | 125 | 3.63 | converged-no-divide, FB toggles, 3 periods not reached | - | 1.78 | 4.92 |
| TYP | -40 | 2.97 | divides | 60.01 | 1.98 | 3.95 |
| TYP | -40 | 3.63 | divides | 60.00 | 2.00 | 5.17 |
| TYP | 27 | 2.97 | divides | 60.00 | 1.93 | 3.97 |
| TYP | 27 | 3.63 | divides | 60.00 | 1.96 | 5.18 |
| TYP | 125 | 2.97 | converged-no-divide, FB toggles, 3 periods not reached | - | 1.87 | 4.00 |
| TYP | 125 | 3.63 | divides | 60.00 | 1.89 | 5.26 |
| FAST | -40 | 2.97 | divides | 60.01 | 2.00 | 4.16 |
| FAST | -40 | 3.63 | divides | 60.00 | 2.03 | 5.43 |
| FAST | 27 | 2.97 | divides | 60.01 | 1.98 | 4.18 |
| FAST | 27 | 3.63 | divides | 60.00 | 2.00 | 5.44 |
| FAST | 125 | 2.97 | converged-no-divide, FB toggles, 3 periods not reached | - | 1.94 | 4.19 |
| FAST | 125 | 3.63 | divides | 60.00 | 1.97 | 5.53 |

`ipavg`/`idavg` are window means over 40-120 ns of the PLL-block rails (magnitudes); they are NOT a row-11 number (no PFD, CP, bias, lock detector, reference or buffering, window includes start-up).

## What is measured on the remaining four (all 125 C)

- **Clock into the divider is now good at TYP 125 C 2.97 V** (`request-clock-97-b.json` re-run on the changed netlist, job on the fleet, 33 samples at 0.1 ns from 140 ns): `ck` -0.02..3.02 V, `ckl` 0.05..2.98 V, `clkb` -0.06..3.10 V, `ckbb` -0.06..3.05 V, each above VDD/2 in 15-17 of 33 samples (about 50 % duty). Before the change `ckl` was high for most of each period, `clkb` peaked at 2.20 V. So the clock-pulse-width mechanism of `20261104-issue97-counter-state-clock-chain.md` is repaired at this corner, yet this corner still does not divide: the remaining failure is **not** that clock. Where it is is not traced.
- SLOW 125 C 2.97 V: FB is flat 0.00 V (+-1 mV) over 40-120 ns, the same signature as the pre-change TYP 125 C 2.97 V hang. SLOW 125 C 3.63 V, TYP and FAST 125 C 2.97 V: FB swings rail to rail (`fbmax` 3.74 / 3.06 / 3.05 V) but 3 FB periods were not reached in 40-120 ns, so the modulus there is unknown (needs a longer run with `fb` edge counts, as in `20261104-issue97-modulus-read.md`).
- Pattern: all four are 125 C; the 125 C corners that divide are TYP and FAST at 3.63 V. Not shown whether the cause is common.

## Load on the prescaler / VCO (CLAUDE.md)

Unchanged from attempt 1: the edit sits after the converter's diff pair. The prescaler output load and the tank load were NOT re-read; the VCO swing/start-up margin with the prescaler load was not re-checked here.

## Row-11 power vs #84

Not re-reported. The stage-2 grid has no nominal (TYP 27 C 3.30 V) point, and `idavg` of the dividing 3.63 V corners (5.2-5.5 mA) is a window mean including start-up. A raise relative to the non-dividing baseline is expected since a dividing divider switches; stated against #84, not hidden. Nominal re-report is owed.

## Owed

1. Cause at SLOW 125 C 2.97 V (FB stuck low) and at TYP/FAST 125 C 2.97 V and SLOW 125 C 3.63 V (modulus): longer run, `fb`/`tc` edge counts and counter-state sampling.
2. A fix for those, confined to the adopted divider/prescaler cells (not the VCO), then the 18-corner re-run (these 18 shard requests are reusable).
3. Nominal row-11 power re-report against #84; `scripts/run-divider-elab.sh` at nominal on a host that loads `psp103.osdi` (the dispatch host's ngspice-42 cannot).
4. Prescaler output / tank load re-read with the new `cmo` coupling cap.
