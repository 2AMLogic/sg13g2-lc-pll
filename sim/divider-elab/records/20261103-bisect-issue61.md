# divider speed bisect (issue #61), 2026-11-03

Which stage stops the divider from dividing at the prescaler output rate. Simulated, **nominal corner only**
(`hbt_typ` / `mos_tt` / `cap_typ`, 27 C, 3.3 V), ngspice-47 (source build, throwaway prefix; the standing host has ngspice-42,
which cannot load the pinned PSP103 OSDI v0.4). Not measured. Transient, 20 ps max step, 60-150 ns, rising edges at 1.65 V
counted after the first quarter of the run. Ideal CMOS clock = 0..3.3 V pulse, 5 % edges, 45 % high. M = 12 (1100), A = 2 (10).
These were one-off scratch decks (not committed); the committed, repeatable check is `scripts/run-divider-elab.sh` (speed section
of the sibling record).

| probe | clock | result |
|---|---|---|
| `cml2cmos` alone, ideal 0.4 Vpp diff sine at 3.18 V | 500 / 625 / 687.5 MHz | CK swings -0.06..3.40 V / -0.07..3.40 V / -0.07..3.40 V, duty 0.58 / 0.59 / 0.59: **full CMOS levels, converter not limiting** |
| `dff_tg_hv` as toggle (D = Q-bar) | 500 / 625 / 687.5 / 800 MHz | toggles at every rate, -0.07..3.39 V: **first flop not limiting** |
| `mcounter` + `acounter` + FB flop, ideal CMOS clock | 500 MHz | divides (4 FB rises in 150 ns) |
| same | 625 and 687.5 MHz | **FB flat at 0 V, 0 rises** |
| same, counters ideal-clocked | 520 / 550 / 580 / 600 MHz | 520: FB toggles (3 rises, low duty); **550, 580, 600: stuck at 0** |
| `mcounter` internals | 625 MHz | q0 and q1, q2 toggle; **q3 stuck at 3.3 V, TC stuck at 0**; at 687.5 q2 also stuck; at 800 only q0 toggles |

**Failing stage**: the `mcounter` next-state logic (decode + terminal-count + load path, about six `*_hv` gates between a flop
output and the next D), not `cml2cmos` and not the flop. With an ideal CMOS clock the counters stop dividing between 520 and 550 MHz
at the nominal corner, below the 625 MHz that 5.0 GHz / 8 requires (and the 500 MHz of the swallow phase is only just inside).
The failure is therefore independent of the converter and of the prescaler's output swing.

**Not done / open**: the fix (retime or pipeline the terminal-count/load path, or a faster counter style within the adopted
`sg13g2-pll` cells) is not in this record; no superseding spec decision is filed. Corners other than nominal are not run.
