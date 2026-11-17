# divider corner check 20261110-ramped-start-f27b2f0

**Result (simulated, not measured): **INCOMPLETE**: 47 of 54 runs divide to the expected N; 0 wrong, 7 not graded.**

- **Scope**: the real divider chain (`cml2cmos` + counters, 3-bit `acounter`, `design/netlist/divider.spice`) at SLOW (hbt_wcs, mos_ss, cap_wcs), TYP (hbt_typ, mos_tt, cap_typ) and FAST (hbt_bcs, mos_ff, cap_bcs) x -40 / 27 / 125 C, 3.3 V. TYP/27C is the nominal point. Not covered: supply other than 3.3 V, the real prescaler driving the converter (ideal 0.4 Vpp sine at 3.18 V common mode instead), layout, noise, Monte Carlo, N codes other than those listed.
- **Method**: `klt sim` corner requests (`gen_corner_requests.py`), batch fleet; tran with crossing measurements of `xd.ck`, `fb` and `mc` at 1.65 V; N = 8 x clocks + MC-high clocks per FB window (MC sampled 0.3 ns before each CK edge), required equal to 8 M + A on every window after the first (the first full window is start-up, shown but not graded; VDD, IREF and the input common mode ramp from 0 V over 3 ns and the sine starts at the end of the ramp), >= 4 FB edges. Speed requests: 160 ns, fin 625 / 687.5 MHz (= 5.0 / 5.5 GHz / 8). Count request: 650 ns at 100 MHz.
- **Commit**: `f27b2f0` of this repository

## speed

Request `divider_corner_speed.request.json` sha256 `b3add79e127649086c33fd6955b1572ad3b49ffe270db0f9b69daa849cc5a2d6`; `ngspice-46`, job `klt-sim-82f857aaa154`, m7i.4xlarge, spot; verdict **INCOMPLETE**.

| corner | fin (MHz) | M | A | FB edges | first window N (start-up, not graded) | CK/window | MC-high | N | expected N | result |
|---|---|---|---|---|---|---|---|---|---|---|
| SLOW/-40C | 625 | 12 | 4 | 8 | 128 | 12 | 4 | 100 | 100 | pass |
| SLOW/-40C | 687.5 | 12 | 4 | 9 | 137 | 12 | 4 | 100 | 100 | pass |
| SLOW/-40C | 687.5 | 12 | 0 | 9 | 137 | 12 | 0 | 96 | 96 | pass |
| SLOW/-40C | 687.5 | 12 | 7 | 9 | 138 | 12 | 7 | 103 | 103 | pass |
| SLOW/27C | 625 | 12 | 4 | 9 | 111 | 12 | 4 | 100 | 100 | pass |
| SLOW/27C | 687.5 | 12 | 4 | 9 | 121 | 12 | 4 | 100 | 100 | pass |
| SLOW/27C | 687.5 | 12 | 0 | 9 | 121 | 12 | 0 | 96 | 96 | pass |
| SLOW/27C | 687.5 | 12 | 7 | 9 | 121 | 12 | 7 | 103 | 103 | pass |
| SLOW/125C | 625 | 12 | 4 | 1 | None | None | None | None | 100 | not-graded: no toggle (fewer than 4 FB edges) |
| SLOW/125C | 687.5 | 12 | 4 | 1 | None | None | None | None | 100 | not-graded: no toggle (fewer than 4 FB edges) |
| SLOW/125C | 687.5 | 12 | 0 | 1 | None | None | None | None | 96 | not-graded: no toggle (fewer than 4 FB edges) |
| SLOW/125C | 687.5 | 12 | 7 | 1 | None | None | None | None | 103 | not-graded: no toggle (fewer than 4 FB edges) |
| TYP/-40C | 625 | 12 | 4 | 8 | 137 | 12 | 4 | 100 | 100 | pass |
| TYP/-40C | 687.5 | 12 | 4 | 9 | 128 | 12 | 4 | 100 | 100 | pass |
| TYP/-40C | 687.5 | 12 | 0 | 9 | 128 | 12 | 0 | 96 | 96 | pass |
| TYP/-40C | 687.5 | 12 | 7 | 9 | 129 | 12 | 7 | 103 | 103 | pass |
| TYP/27C | 625 | 12 | 4 | 9 | 105 | 12 | 4 | 100 | 100 | pass |
| TYP/27C | 687.5 | 12 | 4 | 10 | 105 | 12 | 4 | 100 | 100 | pass |
| TYP/27C | 687.5 | 12 | 0 | 10 | 105 | 12 | 0 | 96 | 96 | pass |
| TYP/27C | 687.5 | 12 | 7 | 10 | 105 | 12 | 7 | 103 | 103 | pass |
| TYP/125C | 625 | 12 | 4 | 9 | 120 | 12 | 4 | 100 | 100 | pass |
| TYP/125C | 687.5 | 12 | 4 | 1 | None | None | None | None | 100 | not-graded: no toggle (fewer than 4 FB edges) |
| TYP/125C | 687.5 | 12 | 0 | 1 | None | None | None | None | 96 | not-graded: no toggle (fewer than 4 FB edges) |
| TYP/125C | 687.5 | 12 | 7 | 1 | None | None | None | None | 103 | not-graded: no toggle (fewer than 4 FB edges) |
| FAST/-40C | 625 | 12 | 4 | 9 | 128 | 12 | 4 | 100 | 100 | pass |
| FAST/-40C | 687.5 | 12 | 4 | 9 | 128 | 12 | 4 | 100 | 100 | pass |
| FAST/-40C | 687.5 | 12 | 0 | 9 | 128 | 12 | 0 | 96 | 96 | pass |
| FAST/-40C | 687.5 | 12 | 7 | 9 | 129 | 12 | 7 | 103 | 103 | pass |
| FAST/27C | 625 | 12 | 4 | 9 | 120 | 12 | 4 | 100 | 100 | pass |
| FAST/27C | 687.5 | 12 | 4 | 9 | 120 | 12 | 4 | 100 | 100 | pass |
| FAST/27C | 687.5 | 12 | 0 | 9 | 120 | 12 | 0 | 96 | 96 | pass |
| FAST/27C | 687.5 | 12 | 7 | 9 | 121 | 12 | 7 | 103 | 103 | pass |
| FAST/125C | 625 | 12 | 4 | 9 | 111 | 12 | 4 | 100 | 100 | pass |
| FAST/125C | 687.5 | 12 | 4 | 9 | 111 | 12 | 4 | 100 | 100 | pass |
| FAST/125C | 687.5 | 12 | 0 | 9 | 111 | 12 | 0 | 96 | 96 | pass |
| FAST/125C | 687.5 | 12 | 7 | 9 | 112 | 12 | 7 | 103 | 103 | pass |

## count

Request `divider_corner_count.request.json` sha256 `535867f0d4e8f5d841c0e33079c956500bc3bba9575767a7b76a329bb62243fa`; `ngspice-46`, job `klt-sim-1f8b73d815b9`, m7i.4xlarge, spot; verdict **PASS**.

| corner | fin (MHz) | M | A | FB edges | first window N (start-up, not graded) | CK/window | MC-high | N | expected N | result |
|---|---|---|---|---|---|---|---|---|---|---|
| SLOW/-40C | 100 | 12 | 4 | 6 | 128 | 12 | 4 | 100 | 100 | pass |
| SLOW/-40C | 100 | 11 | 2 | 6 | 136 | 11 | 2 | 90 | 90 | pass |
| SLOW/27C | 100 | 12 | 4 | 6 | 111 | 12 | 4 | 100 | 100 | pass |
| SLOW/27C | 100 | 11 | 2 | 6 | 119 | 11 | 2 | 90 | 90 | pass |
| SLOW/125C | 100 | 12 | 4 | 6 | 111 | 12 | 4 | 100 | 100 | pass |
| SLOW/125C | 100 | 11 | 2 | 6 | 119 | 11 | 2 | 90 | 90 | pass |
| TYP/-40C | 100 | 12 | 4 | 6 | 128 | 12 | 4 | 100 | 100 | pass |
| TYP/-40C | 100 | 11 | 2 | 6 | 136 | 11 | 2 | 90 | 90 | pass |
| TYP/27C | 100 | 12 | 4 | 6 | 96 | 12 | 4 | 100 | 100 | pass |
| TYP/27C | 100 | 11 | 2 | 6 | 152 | 11 | 2 | 90 | 90 | pass |
| TYP/125C | 100 | 12 | 4 | 6 | 111 | 12 | 4 | 100 | 100 | pass |
| TYP/125C | 100 | 11 | 2 | 6 | 119 | 11 | 2 | 90 | 90 | pass |
| FAST/-40C | 100 | 12 | 4 | 6 | 128 | 12 | 4 | 100 | 100 | pass |
| FAST/-40C | 100 | 11 | 2 | 6 | 136 | 11 | 2 | 90 | 90 | pass |
| FAST/27C | 100 | 12 | 4 | 6 | 120 | 12 | 4 | 100 | 100 | pass |
| FAST/27C | 100 | 11 | 2 | 6 | 128 | 11 | 2 | 90 | 90 | pass |
| FAST/125C | 100 | 12 | 4 | 6 | 111 | 12 | 4 | 100 | 100 | pass |
| FAST/125C | 100 | 11 | 2 | 6 | 119 | 11 | 2 | 90 | 90 | pass |
## Findings (issue #166)

- **Bench change**: VDD, IREF and the input common mode ramp from 0 V over 3 ns (`divider_corner.cir`, `.param tr`), the sine starts at the end of the ramp, stop times +10 ns (160 ns speed, 650 ns count). The divider netlist, speed targets and the 4-FB-edge criterion are unchanged. Baseline: `20261110-pdk-resistors-2022314-corners.md` (43 of 54, 11 not graded).
- **Convergence failures: gone.** All 5 `did not converge` units of the baseline (SLOW/-40C 687.5 MHz A=0, SLOW/125C 687.5 MHz A=7, TYP/-40C 687.5 MHz A=7, SLOW/27C and FAST/27C count M=11 A=2) now converge and divide to the expected N. 0 of 54 fail to converge, so those were bench start-up fragility.
- **Unchanged results**: every unit that passed in the baseline still passes with the same N. TYP/27C: all six units give the same N as before (100, 100, 96, 103 speed; 100, 90 count); only the ungraded first-window N differs (start-up window).
- **Hot no-toggle persists: 7 of 54, a speed failure, not a start-up artefact.** SLOW/125C at 625 MHz A=4 and at 687.5 MHz A=4, 0, 7, and TYP/125C at 687.5 MHz A=4, 0, 7. In each, CK keeps toggling to the end of the run (98 to 108 rising edges, last at 158.8 to 159.2 ns) while FB shows a single rising edge at 1.6 to 1.7 ns and MC at most one rise and one fall: the counter chain stops dividing right after start-up. The 625 MHz SLOW/125C unit differs from the baseline only in having one FB edge instead of none. Cause inside the chain is not traced (no waveform inspection beyond the crossing lists). TYP/125C 625 MHz A=4 and all FAST/125C units pass. The 625 / 687.5 MHz targets are not relaxed.
