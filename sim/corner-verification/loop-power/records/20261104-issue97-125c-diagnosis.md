# The four 125 C corners that still do not divide: what the counter does (2026-11-04, base `3421acf`, issue #97)

**Result (simulated, not measured): PARTIAL, `fail`. No design change in this increment. The four remaining corners (SLOW 125 C 2.97 V and 3.63 V, TYP 125 C 2.97 V, FAST 125 C 2.97 V) were re-run for 300 ns with edge counts and counter-state sampling. Three of them divide, but by the wrong ratio (FB period 22.8-28.8 ns against 20 ns); one (SLOW 125 C 2.97 V) never reaches terminal count. The cause is localised to the M counter, not traced to a gate. The divide-at-all-18 AC, the fix AC and the nominal row-11 power re-report are NOT met.**

- **Method**: four single-corner `klt sim` requests (`make_125c_requests_97.py`, base `request-stage2-97-s-<proc>-125-<vdd>.json`), `klt sim --batch-set ... --max-in-flight 4` on the batch fleet, ramped start-up body `loop_power_body.spice` unchanged, `tran 4p 300n`. FB and `xdiv.tc` rising edges (1.65 V, from 40 ns), min/max of FB, TC, `ck`, `ckl` over 200-300 ns, and `.meas find` of `q0..q3`, `b1..b3`, `tc`, `s0`, `s1`, `mc` every 1.6 ns for 24 clocks from 200 ns. Each corner ran once; repeatability is not shown. Raw numbers: `20261104-issue97-125c-diagnosis-measurements.json` (jobs `klt-sim-5f24a1a533a6`, `-614dab7690dc`, `-1d9f76e3a2bf`, `-7dfc92d6fcec`). ngspice-46 on the fleet against the pin of 47 (`sim/pins.json`): **the pin is not met**; nothing was run locally.
- **Why this changes the previous record**: `20261104-issue97-stage2-18-corner-after-selfbias.md` called three of these "3 periods not reached in 40-120 ns". With 300 ns they do produce FB edges. The 120 ns window was too short for a ~26 ns FB period that starts at 50 ns, so "converged-no-divide" there is correct for the 120 ns criterion, and the modulus is now known.

| corner (125 C) | FB rising edges (ns) | FB period (ns) | expected | TC edges | class |
|---|---|---|---|---|---|
| FAST 2.97 V | 53.7, 80.1, 106.5, 132.9, 159.3, ... | 26.4 steady | 20.0 | 52.7, 79.1, ... (26.4) | converged, divides by about 132 |
| SLOW 3.63 V | 55.0, 81.4, 107.8, 134.2, ... | 26.4 steady | 20.0 | 53.9, 80.3, ... (26.4) | converged, divides by about 132 |
| TYP 2.97 V | 50.5, 72.9, 101.7, 130.5, 159.3, ... | 22.4 then 28.8 steady | 20.0 | 49.7, 72.1, 100.9, ... | converged, divides by about 144 |
| SLOW 2.97 V | none | FB 0.00 V (+-1 mV) over 200-300 ns | 20.0 | none, TC 0.02 V max | converged, counter never reaches TC |

26.4 ns is 16.5 clocks of 1.6 ns against 12.5 expected (12 plus the swallowed clocks), i.e. about four clocks too many per FB period. `ck`/`ckl` swing the full rail in all four (`ckl` 0.05-2.98 V at TYP 2.97 V, 0.09-2.93 V at SLOW 2.97 V), so, with the self-bias in place, the clock reaching the counter is not the failing element at these corners (as already found at TYP 125 C 2.97 V).

## Counter state (what the sampling shows)

- **FAST 125 C 2.97 V**: Q counts down 8, 7, 6, 5, 4, 3, 2, 1 with TC rising at Q = 1 (correct), then at the next clock loads 12 (`q3 q2 q1 q0` = 1100, M = 12, correct), but the next sampled states read 15, 14 (q0 mid-transition), 14, 13, 12, 11, ... so the count after the load starts about four above the value it should have (11). That is the extra four clocks. The samples sit close to a clock edge, so a single row can be a pre-edge value; the offset is consistent over the following rows, but the exact state at the load edge is not pinned.
- **SLOW 125 C 3.63 V**: the same load-then-count sequence, and from clock 12 on `q0`, `b1`, `b2` sit at intermediate levels (1.3-2.4 V, 1.0-3.4 V) for several clocks: the flops are not resolving to rails within the sampling window. Not a rail-to-rail logic count at this corner.
- **SLOW 125 C 2.97 V**: `q3 = q2 = 1` and `b2 = b3 = 0` in every sampled clock, with `q0`, `q1`, `b1` cycling through a 7-clock pattern (clock k and k + 7 are identical, to 0.1 V) and `q0`/`q1` at 0.5-2.7 V (not on a rail) in most rows. TC and TCN never fire. The counter is in a cycle that does not pass Q = 0001: a state it does not leave, with intermediate levels, which points at the flops not completing a transition rather than at a pure logic error.

## Clock-slew candidate (probe, `make_slew_probe_97.py`)

Candidate: the local `CLKB`/`CKBB` inverter pair inside each `dff_tg_hv` overlaps (race-through) when the divider clock `CKL` edge is slow against one inverter delay. Three corners, 300 ns, edges measured 250-300 ns (jobs `klt-sim-a557478e89f3`, `-a99205c65c63`, `-9bf99636255f`; some start/target orderings returned negative times, which are measurement-order artefacts, not results, and are not used):

| corner | `ckl` fall 80-20 % (ps) | `ckl` rise 20-80 % (ps) | `clkb` rise / fall (ps) | `ckbb` rise / fall (ps) | `ckl`->`clkb` fall (ps) | `ckl`->`ckbb` rise (ps) | divides |
|---|---|---|---|---|---|---|---|
| TYP 27 C 2.97 V | 191 | 254 | 148 / 157 | 89 / 77 | 159 | 280 | yes |
| TYP 125 C 2.97 V | 246 | 308 | 221 / n.a. | 114 / 111 | 184 | n.a. | no (modulus) |
| SLOW 125 C 2.97 V | 267 | n.a. | 241 / 196 | 127 / 133 | 234 | 378 | no (stuck) |

The `clkb`-to-`ckbb` spacing (the overlap window) goes from 121 ps (dividing) to 144 ps (SLOW 125 C), 19 % wider, and `ckl` is 20-40 % slower. The direction fits the race candidate but the margin is small and one probe does not separate "race-through" from "slower flop with the same logic". **The candidate is neither confirmed nor refuted.** A direct test (a node-level sweep of the clock-buffer strength at the failing corners, or the master/slave contention current) is not done.

## Not done / owed (the issue stays open)

1. A design change aimed at the M counter flops at 125 C, confined to the adopted divider cells (not the VCO), then the 18-corner re-run (the 18 shard requests are reusable; the four 125 C corners need a >= 300 ns window, not 120 ns, to be graded as "divides" by edge count rather than `tfb`).
2. A discriminating test of the flop-overlap candidate (e.g. stronger or locally buffered clock into `dff_tg_hv`, then the same four corners).
3. Nominal row-11 power re-report against #84 (the stage-2 grid has no nominal point); `scripts/run-divider-elab.sh` at nominal on a host that loads `psp103.osdi` (the dispatch host's ngspice-42 cannot).
4. Prescaler output / tank load re-read with the `cmo` coupling cap, and the VCO swing/start-up re-check with that load (CLAUDE.md).

Friction (klt): `klt sim --batch-set` cannot be combined with `--submit-only`, so a set can only be driven by a client that stays attached to the end, which the interactive harness caps at 10 minutes; a detached submit-then-attach flow for sets would remove the resume steps.
