# M-counter bit trace at the reload, FAST 125 C 2.97 V: only q2 misses, and two paths into D2 are co-critical (2026-11-05, base `e9f8965`, issue #97)

**Result (simulated, not measured): PARTIAL, `fail` for the issue. No design change. The owed "which bit's capture is wrong" trace is done: of `q0..q3` only `q2` misses its capture at the first count after the load. The same trace shows D2 settling 1.56 ns after the load edge by two different routes (q2 -> D2 and TC -> D2). That makes "both routes co-critical" a hypothesis that explains why the TC-fanout trial and the Q-bar-tap trial each moved nothing; it is not tested here. The divide-at-all-18 AC, the fix AC and the row-11 power re-report remain NOT met.**

- **Method**: `make_bit_trace_97.py` -> `request-bittrace-97-FAST-125-2.97.json` (ramped start-up body, `tran 4p 274n`), 1.485 V rise/fall crossing times 1..8 from 262 ns of `ckl`, `tc`, `xm.q0..q3`, `xm.d0..d3`. One run, one corner (repeatability not shown), `klt sim --backend batch`, fleet job `klt-sim-960719b60f1c`; ngspice 46 on the fleet against the pin of 47 (`sim/pins.json`): the pin is not met; nothing was run locally. 112 of 224 measurements are unreached by construction (fewer than 8 edges in the window), not findings. Raw: `20261105-issue97-bit-trace-measurements.json`.

## Reading (ns; edge A = `ckl` rise 264.299, edge B = 265.903)

| step | q3 | q2 | q1 | q0 | expected |
|---|---|---|---|---|---|
| after A (load 12 = 1100) | rise 265.064 | rise 265.111 | (low) | fall 265.196 | 1100, correct |
| after B (count to 11 = 1011) | no change | **no fall** (next fall 273.905) | rise 266.619 | rise 266.704 | q2 should fall |

- `q0`, `q1`, `q3` are captured correctly at B; only `q2` is not. The state then reads 1111 = 15, the "four above" seen in `20261104-issue97-125c-diagnosis.md`.
- `D2` falls at 265.863, 40 ps before B (265.903), then rises again at 267.044. Two routes reach that edge:
  - clock -> `q2` rise (0.81 ns) -> `q2n` -> `a2` -> `D2` (0.75 ns) = 1.56 ns;
  - clock -> `TC` fall (265.339, 1.04 ns) -> `l2b` -> `D2` (0.52 ns) = 1.56 ns.
  The match to the picosecond is from one run and may be partly coincidence; it is a reason to test both routes together, not a proof of which sets the edge.
- After B the clock period stretches (B to the next rise 2.0 ns, 267.910), so later edges are not a fixed 1.6 ns grid.

## Not done / owed (the issue stays open)

1. A trial that shortens **both** routes in one netlist (Q-bar tap on q2, as in `20261104-issue97-qn-tap-trial.md`, plus a TC drive that does not break the counter; the earlier TC split in `20261104-issue97-tc-fanout-split.md` stopped the counter altogether, so it never tested the TC route cleanly), then the four 125 C corners singly.
2. The 18-corner re-run (14 of 18 divide as of `20261104-issue97-stage2-18-corner-after-selfbias.md`), the nominal row-11 power re-report against #84, `scripts/run-divider-elab.sh` at nominal, and the VCO swing/start-up re-check with the `cmo` coupling-cap load.
