# Splitting the TC/TCN fanout makes the 125 C corners worse, not better (2026-11-04, base `dac89ce`, issue #97)

**Result (simulated, not measured): REFUTATION of one candidate, `fail` for the issue. A trial netlist change duplicated the terminal-count flops `XFT`/`XFTN` in `mcounter` (second pair `XFT2`/`XFTN2` on the same `DT`/`DTN`) and moved the 14 in-counter loads of TC/TCN onto the copies, leaving the original `TC`/`TCN` to drive only the `acounter` and the FB flop. At all four 125 C corners that previously divided by the wrong ratio or stuck, FB and `xdiv.tc` then never rose in 300 ns (FB within +-2 mV of 0 V, TC at most 41 mV). The trial was reverted and is not in the tree. The divide-at-all-18 AC, the fix AC and the row-11 power re-report remain NOT met.**

- **Candidate tested**: TC/TCN each drive about 10-11 gate inputs from the minimum-size output inverter of an adopted `dff_tg_hv`, so at hot/low-VDD/SLOW the load-value path (TC -> `nand` -> D, in a 1.6 ns clock) may not settle before the next edge (setup slack), giving a wrong reload. Halving the TC fanout should shorten that path and move the modulus toward 12.5 clocks.
- **Method**: the four single-corner requests of `20261104-issue97-125c-diagnosis.md` (`request-diag125-97-<proc>-<vdd>.json`, unchanged: ramped start-up, 300 ns, FB/TC edges from 40 ns) run with `klt sim --batch-set ... --max-in-flight 4` on the batch fleet against the trial `design/netlist/divider.spice` (netlist-only edit, `divider.sch` untouched). Each corner ran once; repeatability not shown. Jobs: FAST 2.97 V `klt-sim-9ee81ed3d923`, SLOW 3.63 V `klt-sim-89496a5095da`, TYP 2.97 V `klt-sim-7238c618e48c`, SLOW 2.97 V `klt-sim-c48f0c575360`. Raw numbers: `20261104-issue97-tc-fanout-split-measurements.json`. ngspice-46 on the fleet against the pin of 47 (`sim/pins.json`): the pin is not met; nothing was run locally.

| corner (125 C) | before (previous records) | with TC fanout split |
|---|---|---|
| FAST 2.97 V | FB period 26.4 ns (about 132) | no FB or TC edge; FB +-1.4 mV, TC max 36 mV |
| SLOW 3.63 V | FB period 26.4 ns | no edge; FB +-1.8 mV, TC max 41 mV |
| TYP 2.97 V | FB period 28.8 ns | no edge; FB +-1.4 mV, TC max 35 mV |
| SLOW 2.97 V | no edge (stuck) | no edge (stuck), unchanged |

## What this does and does not show

- The split does not help at any corner and removes the (wrong-ratio) division at three. The candidate "TC fanout slows the reload path" is not supported by this trial.
- Why it got worse is **not** determined; the counter state was not traced. Plausible but untested: `TC` and `TC2` can disagree after the ramped start (the counter is self-starting only through the first TC), or `DT`/`DTN` are now loaded by two flops each. So this is a weak refutation of "fanout is the cause", not proof that it is not.
- Nothing here changes the earlier localisation to the M counter flops at 125 C.

## Not done / owed (the issue stays open)

1. A direct measurement of setup slack on the TC -> D path (TC arrival and D settle against the next `CKL` edge) at FAST 125 C 2.97 V and a dividing reference, instead of another structural trial. A `.meas` cannot reference an earlier measured edge time portably; this needs a clock-aligned sampling grid or waveform output from `klt sim`.
2. A local variant of `dff_tg_hv` (or an issue on `sg13g2-pll`) if the flop's own timing at 125 C is the cause.
3. The 18-corner re-run after a fix, the nominal row-11 power re-report against #84 (`scripts/run-divider-elab.sh` at nominal needs a host that loads `psp103.osdi`), and the VCO swing/start-up re-check with the `cmo` coupling-cap load.
