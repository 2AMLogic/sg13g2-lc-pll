# q2 miscapture at FAST 125 C 2.97 V is a setup violation on the clock -> Q -> logic -> D path (2026-11-04, base `bbda821`, issue #97)

**Result (simulated, not measured): PARTIAL, `fail` for the issue. The setup reading owed by `20261104-issue97-edge-trace-and-tc-buffer.md` is now shown directly: at FAST 125 C 2.97 V, D2 falls 40 ps before the divider clock rises, the q2 master node follows 80 ps later, and the master node then flips back (a glitch) when the master closes, so q2 keeps its old value. At TYP 27 C 2.97 V (divides) the same path has about 300 ps. No design change is made here. The divide-at-all-18 AC, the fix AC and the row-11 power re-report remain NOT met.**

## Method

`make_d2_settle_97.py` -> `request-d2settle-97-FAST-125-2.97.json` and `request-d2settle-97-TYP-27-2.97.json` (ramped start-up body, `tran 4p 274n`). For `xdiv.ckl`, the flop-internal `CLKB`/`CKBB`, `D2`, the q2 flop's master `M` and slave `S`, `q2`, `l2b`, `c2` and `tc`, the 1.485 V rise/fall crossing times 1..8 from 262 ns. One run per corner (repeatability not shown), `klt sim --batch-set --backend batch` on the fleet (jobs `klt-sim-6deb0cf9445c`, `klt-sim-4ba02e13e7cb`); ngspice 46 on the fleet against the pin of 47 (`sim/pins.json`), so the pin is not met; nothing was run locally. Raw crossing times: `20261104-issue97-d2-settle-measurements.json`.

## Measurement (ns, FAST 125 C 2.97 V)

| event | time |
|---|---|
| `ckl` rise (edge A) | 264.299 |
| `CLKB` fall / `CKBB` rise (master closes, slave opens) | 264.491 / 264.622 |
| `S` rise (slave follows) | 264.695 |
| `q2` rise | 265.111 |
| `D2` fall (consequence of q2 rise through `q2n` -> `a2` -> `D2`) | 265.863 |
| `ckl` rise (edge B, 1.604 ns after A) | 265.903 |
| `M` falls (follows D2) | 265.943 |
| `CLKB` fall / `CKBB` rise (master closes) | 266.075 / 266.203 |
| `M` rises again (glitch back to the old value, `D2` has not risen) | 266.133 |
| `S` falls | 273.497 (not at 266.2: the 0 was never captured) |

- Clock -> `q2` is 0.81 ns, and `q2` -> `D2` is 0.75 ns, so the loop is 1.56 ns against a 1.60 ns period. `D2` reaches the master with 40 ps to the clock edge and about 130 ps to where the master closes, and `M` is back high 58 ps after `CLKB` falls. This is a setup violation, not a hold one.
- TYP 27 C 2.97 V: `ckl` rise 266.003, `q2` rise 266.676 (0.67 ns), `D2` fall 267.289, next `ckl` rise 267.594: about 305 ps of margin, and no `M` glitch.
- This explains why the earlier trials missed: the TC/TCN drive and the clock-buffer drive (not on this path), and the D-input delay (the wrong direction: it adds to the violated path) did not shorten clock -> Q -> logic -> D. A fix has to cut that path (fewer stages between a counter flop and its own D, or a faster clock-to-Q), not slow D or speed `TC`.

## Not done / owed (the issue stays open)

1. A fix that shortens clock -> `q` -> D2 by roughly 150 ps at FAST 125 C 2.97 V (and the same at the other three 125 C corners): candidates are a flop variant with a direct `QN` tap (`SB` is already inverted inside `dff_tg_hv`, which removes the `q2n` inverter from the `a2` path) and a count sequence with less logic per bit. Either changes `design/divider.sch`; none was tried here, and the flop lives in the adopted `sg13g2-pll` cells.
2. The 18-corner re-run (14 of 18 divide as of `20261104-issue97-stage2-18-corner-after-selfbias.md`), the nominal row-11 power re-report against #84, `scripts/run-divider-elab.sh` at nominal, and the VCO swing/start-up re-check with the `cmo` coupling-cap load. Not touched here; no power number was taken and no design file changed.
