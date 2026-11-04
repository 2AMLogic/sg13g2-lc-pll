# cml2cmos AC-coupled self-biased first inverter, attempt 1 (2026-11-04, base `550cc32`, issue #97)

**Result (simulated, not measured): INCONCLUSIVE, PARTIAL. A design change to `cml2cmos` is made, and the 18-corner stage-2 grid could NOT be completed on the fleet: 2 of 18 corners returned (both FAST, 125 C), 16 did not. One of the two returned corners, FAST 125 C 3.63 V, now divides to 50 MHz; it did not divide before. That is one corner, not evidence that the fix works. The fix AC, the 18-corner AC and the power re-report are NOT met.**

- **Change** (`design/cml2cmos.sch`, regenerated `design/netlist/divider.spice` and `design/netlist/pll_top.spice` with `design/netlist.sh`, `--check` clean): the first `inv_hv` (`XI1`) no longer sees `cmo` directly. `cmo` goes through a 95 fF MIM (`XCI1`, 8 u x 8 u) to node `xin`, and a 100 k resistor (`RF1`) from `cmob` to `xin` self-biases that inverter at its switching point. Intended effect: the threshold tracks the `cmo` common mode (60-65 % of VDD at the failing corners per `20261104-issue97-counter-state-clock-chain.md`), so the clock keeps about 50 % duty. This is the direction named as untested in that record. VCO netlist, prescaler and counters untouched.
- **Load on the prescaler (state it, CLAUDE.md)**: the converter's input is still the same coupling caps and diff pair; the added elements sit after the diff pair, on `cmo`. `cmo` now sees about 95 fF in series with the inverter input instead of the inverter input alone. The load the prescaler sees at `INP`/`INN` is unchanged by this edit; the prescaler's own output load and the tank load were NOT re-read.
- **Method**: `klt sim` on the batch fleet, `request-stage2.json` grid (SLOW/TYP/FAST x -40/27/125 C x 2.970/3.630 V, ramped start-up body `loop_power_body.spice` unchanged, tran `4p 120n`, window 40-120 ns, `tfb` = 3 FB periods must be 58.5-61.5 ns). ngspice-46 on the fleet against the pin of 47 (`sim/pins.json`): **the pin is not met**; nothing was run locally. Nominal-corner `scripts/run-divider-elab.sh` was NOT re-run (the host's ngspice-42 cannot load the pinned `psp103.osdi`).
- **Fleet attempts**:
  1. Job `klt-sim-d71e04390512`, `request-stage2.json` (`timeout_s` 600): 2 pass, 16 killed at 600 s (`timeout`). Each of the two returned corners ran about 182-187 s.
  2. Job `klt-sim-2820898ba1f6`, `request-stage2-97-fix1.json` (`timeout_s` 1800): spot reclamation, state `interrupted`, no results.
  3. Job `klt-sim-d28ce8d9671f`, same request: all 18 units `batch_job_timeout` at the fleet's 3600 s whole-job ceiling (the client also warned the serial upper bound, 32520 s, exceeds that ceiling and advised `request.remote.hosts` >= 18). No result from this job.
  Not shown whether the slowness is the new RC (a slow-settling node under the ramp) or fleet load; the earlier unmodified stage-2 grid finished within one job, so a slowdown caused by this change is possible and **not tested**.

| corner | T (C) | Vdd (V) | returned | divides | ipavg (mA) | idavg (mA) | tfb (ns) |
|---|---|---|---|---|---|---|---|
| FAST | 125 | 2.97 | yes | NO (`tfb` target not reached) | -1.94 | -4.19 | - |
| FAST | 125 | 3.63 | yes | yes | -1.97 | -5.53 | 60.0 |
| the other 16 | | | no (killed at 600 s / job ceiling) | not determined | - | - | - |

The two currents are window means over 40-120 ns from the first attempt; the dividing corner's `idavg` is not a row-11 number (nominal-corner power was not re-reported). Before the change FAST 125 C 3.63 V did not divide (`20261103-133405-ce1d60d-dirty-stage2.md`, M/A divider 1.47 mW); after, it divides, with the divider drawing 5.53 mA x 3.63 V = 20.1 mW in the window, far above the 20 mW row budget share. Whether that is the divider dividing (and so drawing its real dynamic current) rather than sitting idle is the natural reading, **not proven**; it bears on #84 and is stated against it, not hidden.

## Owed
1. Re-run the 18 corners in shards (`request.remote.hosts` >= 18, or `--max-units-per-job`) so each fits the fleet ceiling, and the four TYP failing corners singly; classify each as divides / converged-no-divide / non-convergent.
2. Establish why 16 corners exceeded 600 s (change vs fleet).
3. Nominal row-11 power re-report against #84.
4. Prescaler output and VCO tank load re-read with the new `cmo` coupling cap, and `scripts/run-divider-elab.sh` at nominal on a host that can load `psp103.osdi`.
