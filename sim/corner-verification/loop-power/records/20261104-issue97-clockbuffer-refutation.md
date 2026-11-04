# Doubling the divider clock-buffer drive does not change the 125 C modulus (2026-11-04, base `2ce012d`, issue #97)

**Result (simulated, not measured): REFUTATION of one candidate, `fail` for the issue. A trial change doubled the drive of the local clock buffer in `design/divider.sch` (second `XBA` in parallel, three more `CKL` inverters `XBE`-`XBG` in parallel with `XBB`-`XBD`). The four 125 C corners that do not divide correctly gave the same FB period and TC period as without it (FAST 2.97 V 26.4 ns, SLOW 3.63 V 26.4 ns, TYP 2.97 V 28.8 ns; SLOW 2.97 V still never reaches TC). The trial change was reverted and is not in the tree. No design change lands in this increment. The divide-at-all-18 AC, the fix AC and the nominal row-11 power re-report remain NOT met.**

- **Method**: the same four single-corner requests as `20261104-issue97-125c-diagnosis.md` (`request-diag125-97-<proc>-<vdd>.json`, unchanged, 300 ns, ramped start-up body unchanged), run with `klt sim --batch-set ... --max-in-flight 4` on the batch fleet against the trial netlist. FB and `xdiv.tc` rising edges at 1.65 V from 40 ns. Each corner ran once; repeatability is not shown. Jobs: FAST `klt-sim-d77e19f7361b`, SLOW 3.63 V `klt-sim-9d91a83d0750`, TYP `klt-sim-8bc20ae359af`, SLOW 2.97 V `klt-sim-4559333365b6`. Raw numbers: `20261104-issue97-clockbuffer-refutation-measurements.json`. ngspice-46 on the fleet against the pin of 47 (`sim/pins.json`): the pin is not met; nothing was run locally.
- **Candidate tested**: the `CKL` edge into the M/A counter flops is slow, so the `CLKB`/`CKBB` pair inside `dff_tg_hv` overlaps (race-through). Stronger buffering should sharpen `CKL`. The trial doubled the `ckb` driver and the `CKL` drivers; it did not touch the adopted `dff_tg_hv`, the VCO or `cml2cmos` (so the `cmo` load is unchanged).

| corner (125 C) | FB rising edges (ns) | FB period (ns) | before (previous record) | TC period (ns) | class |
|---|---|---|---|---|---|
| FAST 2.97 V | 53.6, 80.0, 106.4, 132.8, ... | 26.4 | 26.4 | 26.4 | divides by about 132, unchanged |
| SLOW 3.63 V | 55.0, 81.4, 107.8, 134.2, ... | 26.4 | 26.4 | 26.4 | divides by about 132, unchanged |
| TYP 2.97 V | 56.8, 85.6, 114.4, 143.2, ... | 28.8 | 22.4 then 28.8 | 28.8 | divides by about 144, unchanged (the 22.4 ns first period is gone; it was the start-up) |
| SLOW 2.97 V | none | n/a | none | none | FB 0.00 V (+-1 mV), counter never reaches TC, unchanged |

Rail-to-rail swing of `CKL` holds at all four (-0.05 to 3.05 V at 2.97 V, to 3.73 V at 3.63 V).

## What this does and does not show

- It refutes the clock-buffer-drive version of the candidate: a roughly 2x drive change on the `CKL` buffer does not move the modulus at any of the four corners. Caveat: the `CKL` 10-90 % slew was not re-measured with the trial, so "the edge got faster" is assumed from the drive change, not shown.
- It does not refute a race inside the flop that is set by its own two inverters (`CLKB`, `CKBB`), which this change does not alter, nor a master/slave contention current at 125 C.
- The cause is still localised only to the M counter (previous record). The wrong-modulus pattern (about four extra clocks after the M reload) and the SLOW 2.97 V 7-clock cycle are unexplained.

## Not done / owed (the issue stays open)

1. A change to the flop's own timing or sizing at 125 C. `dff_tg_hv` is an adopted `sg13g2-pll` cell; changing it means a local variant in this repo with the reason recorded, or an issue on `sg13g2-pll`.
2. A gate-level trace of the M reload at FAST 125 C 2.97 V (the state at the load edge is not pinned; the sample points sit near the clock edge).
3. The 18-corner re-run after a fix, nominal row-11 power re-report against #84 (`scripts/run-divider-elab.sh` at nominal needs a host that loads `psp103.osdi`), and the VCO swing/start-up re-check with the `cmo` coupling cap load.
