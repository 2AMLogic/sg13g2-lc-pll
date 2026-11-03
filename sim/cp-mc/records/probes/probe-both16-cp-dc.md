# cp-dc run 20261103-055734-09dd595

**Result: mismatch at 1.65 V exceeds 2.0 % (2.785 %); no window around 1.65 V.** **Spec row 7 is NOT graded here.**

- **Scope**: typical corner (`mos_tt`) only, 27 C, nominal 3.3 V supply, one nominal I_cp = 200 uA. No corner grid, no Monte Carlo. **Spec row 7 is not graded:** its upper bound V_hi,req needs the VCO's graded f(Vctrl) curve (gate G4), which does not exist yet. This record lists only the measured window. The numbers are **simulated, not measured**.
- **Netlist**: `/tmp/v78/both16.spice` sha256 `615e64668e53bfc2b1132551fd183751bfb090cefdf1bfb7866db58e7444a713` (NOT the committed netlist: an override, see CP_NETLIST)
- **Deck**: `sim/cp-dc/cp_dc.spice.tmpl` sha256 `53205b18de1f7b878562605df3c3a8a3cbc5a838d139c7a601cf838ee6e5fe78`, placeholder substitution only
- **PDK**: IHP-Open-PDK v0.3.0 (model libraries hash-checked against `sim/pins.json`); PDK_ROOT `/home/ubuntu/share/pdk`; PSP103 OSDI `psp103.osdi` sha256 `2e4299c4683997e26469410dc1ab36b02ced924b1ac0972d6c4eae360e1fc796` (pinned)
- **Simulator**: `ngspice-46` (`/home/ubuntu/.local/bin/ngspice`), one local `ngspice -b`, exit status 0; scratch `.spiceinit` = `set ngbehavior=hsa`
- **Pin check**: Pin check: ngspice-46 != pinned 47 (mismatch)
- **Commit**: `09dd595` of this repository
- **Method**: one `.dc` sweep of V_out, 1.0 V to 3.3 V in 0.05 V steps (47 points). Two copies of `cp` in the same deck: copy A has UP=1, DN=0 (I_up = current it sources into the output node); copy B has UP=0, DN=1 (I_dn = current it sinks), its output tied to copy A's by a unity VCVS. IREF = 20 uA into each copy (I_cp = ~10 x IREF; 100-400 uA is IREF 10-40 uA, not exercised here).
- **Mismatch definition**: mismatch (%) = |I_up - I_dn| / I_cp,nom x 100, with I_cp,nom = 200 uA (spec row 6 typical), at the same V_out. It is a static DC quantity: no switching, no charge sharing, no pulse-width effect.
- **Window definition**: the contiguous run of sweep points with mismatch <= 2.0 % that contains 1.65 V, extended up and down; V_top is its upper end. Endpoints are not clipped: points outside compliance are reported as measured.
- **Host**: loom-worker-1, 2026-11-03T05:57:34Z

| V_out (V) | I_up (uA) | I_dn (uA) | mismatch (% of I_cp,nom) |
|---|---|---|---|
| 1.00 | 203.327 | 190.860 | 6.233 |
| 1.05 | 203.334 | 191.513 | 5.911 |
| 1.10 | 203.339 | 192.143 | 5.598 |
| 1.15 | 203.341 | 192.752 | 5.295 |
| 1.20 | 203.339 | 193.340 | 4.999 |
| 1.25 | 203.334 | 193.910 | 4.712 |
| 1.30 | 203.325 | 194.459 | 4.433 |
| 1.35 | 203.312 | 194.989 | 4.162 |
| 1.40 | 203.295 | 195.496 | 3.899 |
| 1.45 | 203.273 | 195.979 | 3.647 |
| 1.50 | 203.246 | 196.433 | 3.406 |
| 1.55 | 203.213 | 196.854 | 3.180 |
| 1.60 | 203.174 | 197.232 | 2.971 |
| 1.65 | 203.129 | 197.559 | 2.785 |
| 1.70 | 203.076 | 197.823 | 2.626 |
| 1.75 | 203.017 | 198.020 | 2.498 |
| 1.80 | 202.949 | 198.154 | 2.397 |
| 1.85 | 202.873 | 198.239 | 2.317 |
| 1.90 | 202.787 | 198.293 | 2.247 |
| 1.95 | 202.691 | 198.328 | 2.181 |
| 2.00 | 202.583 | 198.353 | 2.115 |
| 2.05 | 202.461 | 198.371 | 2.045 |
| 2.10 | 202.323 | 198.386 | 1.969 |
| 2.15 | 202.164 | 198.398 | 1.883 |
| 2.20 | 201.980 | 198.408 | 1.786 |
| 2.25 | 201.763 | 198.418 | 1.673 |
| 2.30 | 201.502 | 198.426 | 1.538 |
| 2.35 | 201.183 | 198.434 | 1.375 |
| 2.40 | 200.781 | 198.441 | 1.170 |
| 2.45 | 200.260 | 198.448 | 0.906 |
| 2.50 | 199.562 | 198.454 | 0.554 |
| 2.55 | 198.596 | 198.460 | 0.068 |
| 2.60 | 197.214 | 198.465 | 0.626 |
| 2.65 | 195.181 | 198.470 | 1.645 |
| 2.70 | 192.154 | 198.475 | 3.161 |
| 2.75 | 187.682 | 198.479 | 5.399 |
| 2.80 | 181.287 | 198.483 | 8.598 |
| 2.85 | 172.592 | 198.486 | 12.947 |
| 2.90 | 161.427 | 198.488 | 18.531 |
| 2.95 | 147.832 | 198.490 | 25.329 |
| 3.00 | 131.979 | 198.492 | 33.256 |
| 3.05 | 114.086 | 198.493 | 42.203 |
| 3.10 | 94.360 | 198.494 | 52.067 |
| 3.15 | 72.974 | 198.494 | 62.760 |
| 3.20 | 50.058 | 198.495 | 74.219 |
| 3.25 | 25.710 | 198.496 | 86.393 |
| 3.30 | -0.000 | 198.496 | 99.248 |

ngspice log: [`20261103-055734-09dd595-ngspice.txt`](20261103-055734-09dd595-ngspice.txt)
