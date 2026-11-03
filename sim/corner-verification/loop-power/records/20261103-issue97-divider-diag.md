# divider/prescaler non-division diagnostic, TYP x {27, 125 C} x {2.97, 3.63 V} (2026-11-03, base `0a8000d`, issue #97)

**Result (simulated, not measured): PARTIAL. One mechanism located (cml2cmos does not toggle the clock at TYP 125 C 3.63 V); the 27 C 3.63 V and 125 C 2.97 V failures are classified as converged-no-divide but their cause is NOT yet traced. No design change is made; the issue's fix acceptance criterion is NOT met.**

- **Method**: one `klt sim` request (`request-diag-97.json`, stage-2 body and ramped start-up unchanged, 4 units) on the batch fleet, job `klt-sim-b0087e22c650`. Added `.meas` max/min over 40-120 ns on `xdiv.ck` (cml2cmos output), `xdiv.ckl` (buffered clock), `xdiv.tc`, `xdiv.xcv.{cmo,d1,tail,gp}`, and mean of `psp`/`psn`. `tfb` check as in the grid (58.5-61.5 ns = 50 MHz). No waveform files were pulled: swing/min/max only.
- **Simulator**: ngspice-46 on the fleet, against the pin of 47 (`sim/pins.json`): **the pin is not met.** The dispatch host (ngspice-42) cannot load the pinned `psp103.osdi`, so nothing was run locally. A first submit was refused `batch_no_capacity`; the second, with `--wait-for-capacity 420`, ran.
- **Scope of evidence**: 4 TYP corners only, not the 18 stage-2 corners; nothing here was re-run singly or twice.

| corner | converged | divides (tfb) | ck min..max (V) | ckl min..max (V) | cmo min..max (V) | classification |
|---|---|---|---|---|---|---|
| TYP 27 C 2.97 V | yes | yes (60.02 ns) | -0.05..3.04 | -0.04..3.04 | 0.49..2.82 | divides (control) |
| TYP 27 C 3.63 V | yes | NO (tfb unreached) | -0.03..3.68 | -0.05..3.71 | 0.85..3.49 | converged-no-divide; clock toggles rail to rail, FB toggles 0..3.74 V, so the counter is not dead; cause untraced |
| TYP 125 C 2.97 V | yes | NO (tfb unreached) | -0.04..3.03 | -0.03..3.04 | 0.63..2.74 | converged-no-divide; clock toggles rail to rail; cause untraced |
| TYP 125 C 3.63 V | yes | NO (tfb unreached) | **2.94..3.67** | **3.629..3.632** | **1.52..3.47** | converged-no-divide; **clock never goes low**: FB is flat at ~0 V (<0.3 uV), divider current 0.32 mA vs 1.8-3.9 mA elsewhere |

- **Located (measured in simulation)**: at TYP 125 C 3.63 V `cmo` bottoms out at 1.52 V, above the first `inv_hv` threshold, so `ck` never falls below 2.94 V and the divider sees a stuck-high clock. That candidate (the cml2cmos output level versus the clock-inverter threshold at high VDD and hot) is supported at this corner. The prescaler output itself is present (`pspp` 0.245 V, common mode 3.52 V), so the prescaler is not the cause here.
- **Not located**: at 27 C 3.63 V and 125 C 2.97 V the clock is full swing and `fb` swings, yet three FB periods do not complete in 40-120 ns (FB period is not 20 ns). Whether the divider counts a different modulus (timing margin of the retimed flop / counter at these corners, candidate 1 in the issue) was not measured. `tfb` unreached does not say what the ratio is; a `fb` edge-count `.meas` is the next probe.
- **Not refuted**: start-up. TYP 27 C 3.30 V divides under both start-ups (`20261103-startup-probe.md`), and the 27 C 2.97 V control divides here, but only this point set was probed.
- **Owed**: the 18-corner per-corner table (AC 1) and the post-fix grid and nominal power re-report (ACs 3-4). Nominal row-11 power (relates to #84) is not re-reported because nothing changed.
