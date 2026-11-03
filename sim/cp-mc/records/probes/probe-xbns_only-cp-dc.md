# cp-dc run 20261103-055728-09dd595

**Result: mismatch at 1.65 V exceeds 2.0 % (2.731 %); no window around 1.65 V.** **Spec row 7 is NOT graded here.**

- **Scope**: typical corner (`mos_tt`) only, 27 C, nominal 3.3 V supply, one nominal I_cp = 200 uA. No corner grid, no Monte Carlo. **Spec row 7 is not graded:** its upper bound V_hi,req needs the VCO's graded f(Vctrl) curve (gate G4), which does not exist yet. This record lists only the measured window. The numbers are **simulated, not measured**.
- **Netlist**: `/tmp/v78/xbns_only.spice` sha256 `f94e456da66308b118b4681fbb6b4f2dd48ac160a6bf18fbadd01882efc62db0` (NOT the committed netlist: an override, see CP_NETLIST)
- **Deck**: `sim/cp-dc/cp_dc.spice.tmpl` sha256 `53205b18de1f7b878562605df3c3a8a3cbc5a838d139c7a601cf838ee6e5fe78`, placeholder substitution only
- **PDK**: IHP-Open-PDK v0.3.0 (model libraries hash-checked against `sim/pins.json`); PDK_ROOT `/home/ubuntu/share/pdk`; PSP103 OSDI `psp103.osdi` sha256 `2e4299c4683997e26469410dc1ab36b02ced924b1ac0972d6c4eae360e1fc796` (pinned)
- **Simulator**: `ngspice-46` (`/home/ubuntu/.local/bin/ngspice`), one local `ngspice -b`, exit status 0; scratch `.spiceinit` = `set ngbehavior=hsa`
- **Pin check**: Pin check: ngspice-46 != pinned 47 (mismatch)
- **Commit**: `09dd595` of this repository
- **Method**: one `.dc` sweep of V_out, 1.0 V to 3.3 V in 0.05 V steps (47 points). Two copies of `cp` in the same deck: copy A has UP=1, DN=0 (I_up = current it sources into the output node); copy B has UP=0, DN=1 (I_dn = current it sinks), its output tied to copy A's by a unity VCVS. IREF = 20 uA into each copy (I_cp = ~10 x IREF; 100-400 uA is IREF 10-40 uA, not exercised here).
- **Mismatch definition**: mismatch (%) = |I_up - I_dn| / I_cp,nom x 100, with I_cp,nom = 200 uA (spec row 6 typical), at the same V_out. It is a static DC quantity: no switching, no charge sharing, no pulse-width effect.
- **Window definition**: the contiguous run of sweep points with mismatch <= 2.0 % that contains 1.65 V, extended up and down; V_top is its upper end. Endpoints are not clipped: points outside compliance are reported as measured.
- **Host**: loom-worker-1, 2026-11-03T05:57:28Z

| V_out (V) | I_up (uA) | I_dn (uA) | mismatch (% of I_cp,nom) |
|---|---|---|---|
| 1.00 | 203.154 | 190.860 | 6.147 |
| 1.05 | 203.164 | 191.513 | 5.825 |
| 1.10 | 203.171 | 192.143 | 5.514 |
| 1.15 | 203.176 | 192.752 | 5.212 |
| 1.20 | 203.177 | 193.340 | 4.918 |
| 1.25 | 203.176 | 193.910 | 4.633 |
| 1.30 | 203.171 | 194.459 | 4.356 |
| 1.35 | 203.164 | 194.989 | 4.087 |
| 1.40 | 203.152 | 195.496 | 3.828 |
| 1.45 | 203.137 | 195.979 | 3.579 |
| 1.50 | 203.116 | 196.433 | 3.342 |
| 1.55 | 203.091 | 196.854 | 3.119 |
| 1.60 | 203.060 | 197.232 | 2.914 |
| 1.65 | 203.021 | 197.559 | 2.731 |
| 1.70 | 202.976 | 197.823 | 2.576 |
| 1.75 | 202.922 | 198.020 | 2.451 |
| 1.80 | 202.860 | 198.154 | 2.353 |
| 1.85 | 202.789 | 198.239 | 2.275 |
| 1.90 | 202.707 | 198.293 | 2.207 |
| 1.95 | 202.614 | 198.328 | 2.143 |
| 2.00 | 202.509 | 198.353 | 2.078 |
| 2.05 | 202.388 | 198.371 | 2.009 |
| 2.10 | 202.250 | 198.386 | 1.932 |
| 2.15 | 202.090 | 198.398 | 1.846 |
| 2.20 | 201.904 | 198.408 | 1.748 |
| 2.25 | 201.683 | 198.418 | 1.633 |
| 2.30 | 201.416 | 198.426 | 1.495 |
| 2.35 | 201.087 | 198.434 | 1.326 |
| 2.40 | 200.671 | 198.441 | 1.115 |
| 2.45 | 200.129 | 198.448 | 0.841 |
| 2.50 | 199.402 | 198.454 | 0.474 |
| 2.55 | 198.392 | 198.460 | 0.034 |
| 2.60 | 196.945 | 198.465 | 0.760 |
| 2.65 | 194.820 | 198.470 | 1.825 |
| 2.70 | 191.668 | 198.475 | 3.403 |
| 2.75 | 187.046 | 198.479 | 5.716 |
| 2.80 | 180.495 | 198.483 | 8.994 |
| 2.85 | 171.669 | 198.486 | 13.408 |
| 2.90 | 160.424 | 198.488 | 19.032 |
| 2.95 | 146.811 | 198.490 | 25.840 |
| 3.00 | 131.000 | 198.492 | 33.746 |
| 3.05 | 113.199 | 198.493 | 42.647 |
| 3.10 | 93.604 | 198.494 | 52.445 |
| 3.15 | 72.378 | 198.494 | 63.058 |
| 3.20 | 49.646 | 198.495 | 74.425 |
| 3.25 | 25.498 | 198.496 | 86.499 |
| 3.30 | -0.000 | 198.496 | 99.248 |

ngspice log: [`20261103-055728-09dd595-ngspice.txt`](20261103-055728-09dd595-ngspice.txt)
