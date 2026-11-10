# divider corner check 20261110-pdk-resistors-2022314

**Result (simulated, not measured): **INCOMPLETE**: 43 of 54 runs divide to the expected N; 0 wrong, 11 not graded.**

- **Scope**: the real divider chain (`cml2cmos` + counters, 3-bit `acounter`, `design/netlist/divider.spice`) at SLOW (hbt_wcs, mos_ss, cap_wcs), TYP (hbt_typ, mos_tt, cap_typ) and FAST (hbt_bcs, mos_ff, cap_bcs) x -40 / 27 / 125 C, 3.3 V. TYP/27C is the nominal point. Not covered: supply other than 3.3 V, the real prescaler driving the converter (ideal 0.4 Vpp sine at 3.18 V common mode instead), layout, noise, Monte Carlo, N codes other than those listed.
- **Method**: `klt sim` corner requests (`gen_corner_requests.py`), batch fleet; tran with crossing measurements of `xd.ck`, `fb` and `mc` at 1.65 V; N = 8 x clocks + MC-high clocks per FB window (MC sampled 0.3 ns before each CK edge), required equal to 8 M + A on every window after the first (the first full window is start-up from the DC operating point, shown but not graded), >= 4 FB edges. Speed requests: 150 ns, fin 625 / 687.5 MHz (= 5.0 / 5.5 GHz / 8). Count request: 640 ns at 100 MHz.
- **Commit**: `2022314` of this repository

## speed

Request `divider_corner_speed.request.json` sha256 `fc4a19bb466acb2309ebfd0f2094c2ad2ecdb0a83194a2917a05b6ba4e12f1e6`; `ngspice-46`, job `klt-sim-6bdc4b09cbce`, m7i.4xlarge, spot; verdict **INCOMPLETE**.

| corner | fin (MHz) | M | A | FB edges | first window N (start-up, not graded) | CK/window | MC-high | N | expected N | result |
|---|---|---|---|---|---|---|---|---|---|---|
| SLOW/-40C | 625 | 12 | 4 | 8 | 100 | 12 | 4 | 100 | 100 | pass |
| SLOW/-40C | 687.5 | 12 | 4 | 9 | 100 | 12 | 4 | 100 | 100 | pass |
| SLOW/-40C | 687.5 | 12 | 0 | None | None | None | None | None | 96 | not-graded: did not converge |
| SLOW/-40C | 687.5 | 12 | 7 | 8 | 103 | 12 | 7 | 103 | 103 | pass |
| SLOW/27C | 625 | 12 | 4 | 8 | 100 | 12 | 4 | 100 | 100 | pass |
| SLOW/27C | 687.5 | 12 | 4 | 9 | 100 | 12 | 4 | 100 | 100 | pass |
| SLOW/27C | 687.5 | 12 | 0 | 9 | 96 | 12 | 0 | 96 | 96 | pass |
| SLOW/27C | 687.5 | 12 | 7 | 9 | 103 | 12 | 7 | 103 | 103 | pass |
| SLOW/125C | 625 | 12 | 4 | 0 | None | None | None | None | 100 | not-graded: no toggle (fewer than 4 FB edges) |
| SLOW/125C | 687.5 | 12 | 4 | 0 | None | None | None | None | 100 | not-graded: no toggle (fewer than 4 FB edges) |
| SLOW/125C | 687.5 | 12 | 0 | 0 | None | None | None | None | 96 | not-graded: no toggle (fewer than 4 FB edges) |
| SLOW/125C | 687.5 | 12 | 7 | None | None | None | None | None | 103 | not-graded: did not converge |
| TYP/-40C | 625 | 12 | 4 | 7 | 100 | 12 | 4 | 100 | 100 | pass |
| TYP/-40C | 687.5 | 12 | 4 | 8 | 100 | 12 | 4 | 100 | 100 | pass |
| TYP/-40C | 687.5 | 12 | 0 | 8 | 96 | 12 | 0 | 96 | 96 | pass |
| TYP/-40C | 687.5 | 12 | 7 | None | None | None | None | None | 103 | not-graded: did not converge |
| TYP/27C | 625 | 12 | 4 | 7 | 100 | 12 | 4 | 100 | 100 | pass |
| TYP/27C | 687.5 | 12 | 4 | 8 | 100 | 12 | 4 | 100 | 100 | pass |
| TYP/27C | 687.5 | 12 | 0 | 8 | 96 | 12 | 0 | 96 | 96 | pass |
| TYP/27C | 687.5 | 12 | 7 | 8 | 103 | 12 | 7 | 103 | 103 | pass |
| TYP/125C | 625 | 12 | 4 | 7 | 100 | 12 | 4 | 100 | 100 | pass |
| TYP/125C | 687.5 | 12 | 4 | 0 | None | None | None | None | 100 | not-graded: no toggle (fewer than 4 FB edges) |
| TYP/125C | 687.5 | 12 | 0 | 0 | None | None | None | None | 96 | not-graded: no toggle (fewer than 4 FB edges) |
| TYP/125C | 687.5 | 12 | 7 | 0 | None | None | None | None | 103 | not-graded: no toggle (fewer than 4 FB edges) |
| FAST/-40C | 625 | 12 | 4 | 7 | 100 | 12 | 4 | 100 | 100 | pass |
| FAST/-40C | 687.5 | 12 | 4 | 8 | 100 | 12 | 4 | 100 | 100 | pass |
| FAST/-40C | 687.5 | 12 | 0 | 8 | 96 | 12 | 0 | 96 | 96 | pass |
| FAST/-40C | 687.5 | 12 | 7 | 8 | 103 | 12 | 7 | 103 | 103 | pass |
| FAST/27C | 625 | 12 | 4 | 7 | 100 | 12 | 4 | 100 | 100 | pass |
| FAST/27C | 687.5 | 12 | 4 | 8 | 100 | 12 | 4 | 100 | 100 | pass |
| FAST/27C | 687.5 | 12 | 0 | 8 | 96 | 12 | 0 | 96 | 96 | pass |
| FAST/27C | 687.5 | 12 | 7 | 8 | 103 | 12 | 7 | 103 | 103 | pass |
| FAST/125C | 625 | 12 | 4 | 7 | 100 | 12 | 4 | 100 | 100 | pass |
| FAST/125C | 687.5 | 12 | 4 | 8 | 100 | 12 | 4 | 100 | 100 | pass |
| FAST/125C | 687.5 | 12 | 0 | 8 | 96 | 12 | 0 | 96 | 96 | pass |
| FAST/125C | 687.5 | 12 | 7 | 8 | 103 | 12 | 7 | 103 | 103 | pass |

## count

Request `divider_corner_count.request.json` sha256 `7db0ebd68f59fc7a9d30cd5e26547c4828557628076cceecdc0b056a033c00d1`; `ngspice-46`, job `klt-sim-175ff018bef4`, m7i.4xlarge, spot; verdict **INCOMPLETE**.

| corner | fin (MHz) | M | A | FB edges | first window N (start-up, not graded) | CK/window | MC-high | N | expected N | result |
|---|---|---|---|---|---|---|---|---|---|---|
| SLOW/-40C | 100 | 12 | 4 | 5 | 100 | 12 | 4 | 100 | 100 | pass |
| SLOW/-40C | 100 | 11 | 2 | 5 | 90 | 11 | 2 | 90 | 90 | pass |
| SLOW/27C | 100 | 12 | 4 | 5 | 100 | 12 | 4 | 100 | 100 | pass |
| SLOW/27C | 100 | 11 | 2 | None | None | None | None | None | 90 | not-graded: did not converge |
| SLOW/125C | 100 | 12 | 4 | 4 | 100 | 12 | 4 | 100 | 100 | pass |
| SLOW/125C | 100 | 11 | 2 | 6 | 90 | 11 | 2 | 90 | 90 | pass |
| TYP/-40C | 100 | 12 | 4 | 4 | 100 | 12 | 4 | 100 | 100 | pass |
| TYP/-40C | 100 | 11 | 2 | 5 | 90 | 11 | 2 | 90 | 90 | pass |
| TYP/27C | 100 | 12 | 4 | 4 | 100 | 12 | 4 | 100 | 100 | pass |
| TYP/27C | 100 | 11 | 2 | 5 | 90 | 11 | 2 | 90 | 90 | pass |
| TYP/125C | 100 | 12 | 4 | 4 | 100 | 12 | 4 | 100 | 100 | pass |
| TYP/125C | 100 | 11 | 2 | 5 | 90 | 11 | 2 | 90 | 90 | pass |
| FAST/-40C | 100 | 12 | 4 | 4 | 100 | 12 | 4 | 100 | 100 | pass |
| FAST/-40C | 100 | 11 | 2 | 5 | 90 | 11 | 2 | 90 | 90 | pass |
| FAST/27C | 100 | 12 | 4 | 4 | 100 | 12 | 4 | 100 | 100 | pass |
| FAST/27C | 100 | 11 | 2 | None | None | None | None | None | 90 | not-graded: did not converge |
| FAST/125C | 100 | 12 | 4 | 5 | 100 | 12 | 4 | 100 | 100 | pass |
| FAST/125C | 100 | 11 | 2 | 5 | 90 | 11 | 2 | 90 | 90 | pass |
