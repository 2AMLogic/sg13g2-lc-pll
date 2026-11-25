# loop-power ad-hoc requests: psp103_nqs probe accounting 20261124-235121-d0a486d-dirty

**Result (probe, simulated not measured): of the 43 tracked `sim/corner-verification/loop-power/request-*.json` files outside PR #447's three, exactly one is measurable today and it was positive: `request-flop-toggle-97.json` logged 96 `Unknown model type pspnqs103va - ignored` lines at its declared corner and 0 after adding `psp103_nqs.osdi` (the only change). The other 42 abort during netlist parsing (`Error: unknown subckt: ... rppd`) before model setup, so their NQS baseline is inconclusive: they load no resistor model library and no `r3_cmc` OSDI, while `design/netlist/prescaler.spice` and `divider.spice` have instantiated PDK `rppd`/`rhigh` resistors since PR #169 (commit `22f2579`, 2026-11-09). That resistor-loading gap is a separate, pre-existing defect (tracked by `make_requests.py`'s own `res_stage2()` note, "The request files written before that carried no resistor model") and is filed separately; it is not fixed here because the issue's probe protocol requires each request's own deck and model sections to be kept as found.**

- **Scope**: issue #451's 43 loop-power requests = the 46 tracked `request-*.json` minus the three PR #447 already covers (`request-stage1.json`, `request-stage2.json`, `request-stage2-nominal-startup.json`).
- **Method**: for each request, a scratch copy `scratch451-<stem>.json` written beside it (relative netlist and `.include ../../../design/netlist/...` paths preserved), `corners` trimmed to ONE declared combination (the filename-encoded process/temperature/vddv where the name carries one, else the first declared entry; `request-stage2-97-fix1.json` -> SLOW/-40C/2.97V) and `options.keep_artifacts` set; then `klt sim <scratch> --backend local -o <fresh dir> --timeout-s 100`. Count = `Unknown model type` lines in the fresh per-corner `ngspice.log`. Nothing else differed from the tracked file during the baseline runs.
- **Simulator**: `ngspice-47` (`/home/ubuntu/.local/bin/ngspice`, binary sha256 `39ca1adb826660324c3626f72bd946ec40704f0f3fc8e243c623f76e24b3eee2`), one local `klt sim` unit per request, `OMP_NUM_THREADS=2`; no run reached its 100 s timeout (each aborts in about 2 s; the flop-toggle baseline and fixed runs completed on their own).
- **PDK**: IHP-Open-PDK v0.3.0, `PDK_ROOT=/home/ubuntu/share/pdk`; `cornerMOShv.lib`/`cornerCAP.lib`/`cornerHBT.lib` (the sections each request declares), `psp103.osdi` and `psp103_nqs.osdi` hash-match `sim/pins.json`.
- **Commit**: `d0a486d-dirty` of this repository (worktree of issue #451; `request-flop-toggle-97.json` differs from HEAD only by this fix; no other tracked request or body deck changed)
- **Host**: loom-crew-1, 2026-11-24
- **Uniformity check**: the 42 parse-abort logs normalize (output paths, scratch names, timestamps blanked) to exactly one distinct signature; one representative log is archived. Every abort log contains 0 `Unknown model type` lines because ngspice aborts at subcircuit elaboration, before model-card setup - the count is not evidence of a correct preload, which is why these are recorded as inconclusive, not as zero.

| request | probed corner | unit status | outcome | baseline Unknown-model-type lines |
|---|---|---|---|---|
| `request-bittrace-97-FAST-125-2.97.json` | FAST/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-bittrace2-97-SLOW-125-2.97.json` | SLOW/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-bittrace2-97-TYP-125-2.97.json` | TYP/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-bittrace3-97-SLOW-125-2.97.json` | SLOW/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-clock-97-a.json` | TYP/27C/3.63V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-clock-97-b.json` | TYP/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-d2settle-97-FAST-125-2.97.json` | FAST/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-d2settle-97-TYP-27-2.97.json` | TYP/27C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-diag-97.json` | TYP/27C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-diag125-97-FAST-2.97.json` | FAST/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-diag125-97-SLOW-2.97.json` | SLOW/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-diag125-97-SLOW-3.63.json` | SLOW/125C/3.63V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-diag125-97-TYP-2.97.json` | TYP/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-dtgate-97-SLOW-125-2.97.json` | SLOW/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-dtgate-97-SLOW-125-2.97-n34.json` | SLOW/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-edge-97-FAST-125-2.97.json` | FAST/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-edge-97-TYP-27-2.97.json` | TYP/27C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-fbcount-97.json` | TYP/27C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-fbcount-97-a.json` | TYP/27C/3.63V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-fbcount-97-b.json` | TYP/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-flop-toggle-97.json` | SLOW/125C/2.97V | pass | **96 -> 0 after the fix** (fixed run completed) | 96 (model setup ran; see fix-verification table) |
| `request-forced-97-SLOW-125-2.97.json` | SLOW/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-forcedprobe-97-FAST-125-2.97.json` | FAST/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-forcedprobe-97-SLOW-125-2.97.json` | SLOW/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-forcedprobe-97-TYP-125-2.97.json` | TYP/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-forcedprobe2-97-SLOW-125-2.97.json` | SLOW/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-modulus-97-a.json` | TYP/27C/3.63V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-modulus-97-a2.json` | TYP/27C/3.63V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-modulus-97-b.json` | TYP/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-modulus-97-b2.json` | TYP/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-probe-97-b.json` | TYP/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-probe-nominal.json` | TYP/27C/3.3V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-probe-ramp.json` | TYP/27C/3.3V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-slew-97-SLOW-125-2.97.json` | SLOW/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-slew-97-TYP-125-2.97.json` | TYP/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-slew-97-TYP-27-2.97.json` | TYP/27C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-stage2-97-fix1.json` | SLOW/-40C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-state-97-a.json` | TYP/27C/3.63V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-state-97-b.json` | TYP/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-state-97-c.json` | TYP/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-statesnap-97-FAST-125-2.97.json` | FAST/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-tclevels-97-SLOW-125-2.97.json` | SLOW/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |
| `request-tclevels-97-TYP-125-2.97.json` | TYP/125C/2.97V | error | inconclusive: aborted at netlist parse before model setup | 0 (model setup never ran) |

**Fix verification for the one measurable request** (`request-flop-toggle-97.json`, standalone `flop_toggle_body.spice`; it does `.include` `design/netlist/divider.spice`, but it parses because it never *elaborates* a resistor-bearing subcircuit: the `rppd`/`rhigh` instances in `divider.spice` all sit inside `.subckt cml2cmos`, and the deck instantiates only `dff_tg_hv` and `inv_hv`, neither of which reaches `cml2cmos`. The other 42 abort because they elaborate `prescaler.spice`, whose `XRREF ... rppd` (line 14) is instantiated. The predicate for the parse abort is therefore "elaborates a resistor-bearing subckt", not "includes the divider/prescaler netlist"):

| run | osdi_preload | Unknown-model-type lines | run outcome |
|---|---|---|---|
| baseline | `psp103.osdi` | 96 | completed, all `.meas` returned |
| fixed | `psp103.osdi` + `psp103_nqs.osdi` | 0 | completed, all `.meas` returned |

`request-flop-toggle-97.json` has no generator (`git grep` finds no script writing it), so the tracked-file edit is the complete change; the #97 shard sources (`request-stage2-97-fix1.json` and its derived shard/bit-trace requests) are among the 42 inconclusive and were left untouched, so source/derived consistency is unchanged.

ngspice logs: [`20261124-235121-d0a486d-dirty-nqs-preload-probe-accounting-floptoggle-base-ngspice.txt`](20261124-235121-d0a486d-dirty-nqs-preload-probe-accounting-floptoggle-base-ngspice.txt), [`20261124-235121-d0a486d-dirty-nqs-preload-probe-accounting-floptoggle-fixed-ngspice.txt`](20261124-235121-d0a486d-dirty-nqs-preload-probe-accounting-floptoggle-fixed-ngspice.txt), [`20261124-235121-d0a486d-dirty-nqs-preload-probe-accounting-parse-abort-representative-ngspice.txt`](20261124-235121-d0a486d-dirty-nqs-preload-probe-accounting-parse-abort-representative-ngspice.txt)
