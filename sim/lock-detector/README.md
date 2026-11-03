# sim/lock-detector

Gate G5, lock-detector half (spec section 7): the pinned `sg13g2-pll@e71ff61` PFD driving the pinned,
**unmodified** `lock_detector` at REF = 50 MHz (T_ref = 20 ns), 3.3 V. Everything here is **simulated, not
measured**, pre-layout, and the numbers are quasi-static (see Method); the PFD half is in [`../pfd/`](../pfd/README.md).

```bash
scripts/run-lock-detector.sh nominal                 # ONE local ngspice (mos_tt/cap_typ/res_typ, 27 C, 3.3 V), ~10 min
scripts/run-lock-detector.sh closed PHI_PS V0 TUS    # ONE closed-loop transient, nothing held (spot check)
scripts/run-lock-detector.sh grid1                   # klt sim --backend batch: 45 points at 3.3 V   (never local)
scripts/run-lock-detector.sh grid2                   # klt sim --backend batch: 18 supply sub-corners (never local)
scripts/run-lock-detector.sh report <grid dir>       # rebuild the record .md from request.json + report.json
scripts/test-fetch-vco.sh 2AMLogic/sg13g2-pll fetch-pll.sh design/pfd.sch                            # negative controls for the pin (now 30 files)
```

Method (held-VWIN, why, the estimators): [`method.md`](method.md), reproduced in every record. A failed batch submit is
reported (exit non-zero), never run locally.

## Verdict (records dated 2026-11-03, commit `7fb70bf`)

| Check | Result | Records |
|---|---|---|
| Assert window `twin` (ERR 50 % to ERRD 50 %, the `delaywin_hv` delay) vs the >= 2.5 ns floor of spec section 7 | **PASS**: nominal 5.20 ns rise / 3.68 ns fall; smallest of 63 corners 2.70 ns (SLOW, 27 C, 2.97 V, fall) | nominal, grid1, grid2 |
| PFD at 50 MHz presents | UP and DN each >= 0.76 ns wide at phi = 0 (reset-chain pulse); ERR (UP xor DN) = |phi| + about 0.2 ns | nominal table |
| LOCK trip phase errors, as a fraction of T_ref | **outside DR-006's recorded 11.7-24.4 % / 18.7-36.6 %**. Nominal: VWIN-rising trip at 7.6-7.8 ns = 38-39 % T_ref, VWIN-falling trip at 10.0 ns = 49.9 % (the T_ref/2 edge of the sweep); hysteresis about 2.3 ns. Over grid1 the rising-trip phase error spans 4.98-9.93 ns (24.9-49.6 % T_ref) | nominal, grid1, grid2 |
| Can LOCK be driven to its out-of-window level at all within |phi| <= T_ref/2? | **No in 24 of 45 (grid1) and 9 of 18 (grid2) corners** (+side): the VWIN-falling trip is never reached; hot and slow corners are worst | grid1, grid2 |
| **LOCK polarity** | **active-low as netlisted**: `schmitt_hv` is inverting and VWIN charges up when the phase error is inside the window, so LOCK = 0 when phase-locked and rises to VDD when the phase error is large. Confirmed in a closed-loop transient (phi = 0, VWIN(0) = 0: LOCK falls as VWIN crosses about 2.1 V, matching the 2.138 V ramp-measured trip) | closed-phi0 |
| Held-VWIN model vs closed loop | consistent: phi = 9 ns, VWIN(0) = 3.3 V dips to 0.41 V and recovers toward the model's V_eq = 1.44 V (1.30 V at 7 us, still rising); phi = 0 charges through the upper trip at the modelled time | closed-phi0, closed-phi9000 |
| LOCK steady state, no chatter | at phi = 0 and 9 ns the Schmitt output stays on one level once past its trip; no multiple crossings in the sampled points (only 10 samples per run: this is not a chatter proof) | closed-* |

**Gate G5, lock detector: not closed.** The delay-window criterion passes everywhere it was run, but at 50 MHz the
detector's thresholds sit at a quarter to a half of a reference period and in about half the corners cannot flag even a
T_ref/2 phase error, and `LOCK` is active-low where the name and `pll_top`'s consumers presumably expect active-high. Spec
section 7 asks for the 50 MHz re-grade and the >= 2.5 ns window; it states no lock-threshold row, and spec row 10 (lock time) is
defined on frequency and static phase error, not on `LOCK`, so no spec row is relaxed or failed here. The finding is filed on
`2AMLogic/sg13g2-pll#296`; no local copy of the cell was made.

## What this does not establish

- No closed-loop LOCK threshold sweep: the thresholds are quasi-static balances of simulated currents (resolved only to the 0.5-2 ns
  phase grid), cross-checked by two closed-loop spot checks at the nominal corner. A closed-loop run per phase point costs hours.
- Corners: the C-grid here has no HBT axis (no HBT in the cells) and pairs the rhigh corner with the MIM corner by name; the
  spec defines no resistor axis. Stage 3 (405-point cross) not run. No Monte Carlo, no post-layout, no supply-noise coupling.
- `ngspice-46` on both the standing host and the fleet; `sim/pins.json` pins 47 (warning in each record).
- One batch submission (45 units as a single job) was abandoned before completion because klt itself warned it would exceed the
  fleet's 3600 s job ceiling; it was resubmitted sharded at 2 units per job. No result from it is used.

## Files

- `method.md`: method text shared by every record. `records/`: dated, append-only (`*-nominal.md`, `*-closed-*.md`,
  `*-grid1.md`, `*-grid2.md`, with the request, merged report, and first partial report in the matching directories).
  `negative-control-fetch-pll-*.txt`: output of `scripts/test-fetch-pll.sh` after the pin gained `lock_detector.spice`.
- The 20261103-004411 closed-loop record's time column was corrected after the fact from its own ngspice log (the script
  labelled the samples one step early); the log and values are unchanged.
