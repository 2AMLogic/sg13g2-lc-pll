# cp-dc run 20261103-055748-09dd595

**Result: mismatch at 1.65 V exceeds 2.0 % (2.449 %); no window around 1.65 V.** **Spec row 7 is NOT graded here.**

- **Scope**: typical corner (`mos_tt`) only, 27 C, nominal 3.3 V supply, one nominal I_cp = 200 uA. No corner grid, no Monte Carlo. **Spec row 7 is not graded:** its upper bound V_hi,req needs the VCO's graded f(Vctrl) curve (gate G4), which does not exist yet. This record lists only the measured window. The numbers are **simulated, not measured**.
- **Netlist**: `/tmp/v78/xbns12.spice` sha256 `8c83c800f3d53bd4f19f278599c630e9219c5a59e5d7de25c4940f2bc5f1f45e` (NOT the committed netlist: an override, see CP_NETLIST)
- **Deck**: `sim/cp-dc/cp_dc.spice.tmpl` sha256 `53205b18de1f7b878562605df3c3a8a3cbc5a838d139c7a601cf838ee6e5fe78`, placeholder substitution only
- **PDK**: IHP-Open-PDK v0.3.0 (model libraries hash-checked against `sim/pins.json`); PDK_ROOT `/home/ubuntu/share/pdk`; PSP103 OSDI `psp103.osdi` sha256 `2e4299c4683997e26469410dc1ab36b02ced924b1ac0972d6c4eae360e1fc796` (pinned)
- **Simulator**: `ngspice-46` (`/home/ubuntu/.local/bin/ngspice`), one local `ngspice -b`, exit status 0; scratch `.spiceinit` = `set ngbehavior=hsa`
- **Pin check**: Pin check: ngspice-46 != pinned 47 (mismatch)
- **Commit**: `09dd595` of this repository
- **Method**: one `.dc` sweep of V_out, 1.0 V to 3.3 V in 0.05 V steps (47 points). Two copies of `cp` in the same deck: copy A has UP=1, DN=0 (I_up = current it sources into the output node); copy B has UP=0, DN=1 (I_dn = current it sinks), its output tied to copy A's by a unity VCVS. IREF = 20 uA into each copy (I_cp = ~10 x IREF; 100-400 uA is IREF 10-40 uA, not exercised here).
- **Mismatch definition**: mismatch (%) = |I_up - I_dn| / I_cp,nom x 100, with I_cp,nom = 200 uA (spec row 6 typical), at the same V_out. It is a static DC quantity: no switching, no charge sharing, no pulse-width effect.
- **Window definition**: the contiguous run of sweep points with mismatch <= 2.0 % that contains 1.65 V, extended up and down; V_top is its upper end. Endpoints are not clipped: points outside compliance are reported as measured.
- **Host**: loom-worker-1, 2026-11-03T05:57:48Z

| V_out (V) | I_up (uA) | I_dn (uA) | mismatch (% of I_cp,nom) |
|---|---|---|---|
| 1.00 | 202.442 | 190.860 | 5.791 |
| 1.05 | 202.454 | 191.513 | 5.470 |
| 1.10 | 202.464 | 192.143 | 5.160 |
| 1.15 | 202.471 | 192.752 | 4.860 |
| 1.20 | 202.477 | 193.340 | 4.568 |
| 1.25 | 202.481 | 193.910 | 4.286 |
| 1.30 | 202.483 | 194.459 | 4.012 |
| 1.35 | 202.484 | 194.989 | 3.747 |
| 1.40 | 202.483 | 195.496 | 3.493 |
| 1.45 | 202.481 | 195.979 | 3.251 |
| 1.50 | 202.478 | 196.433 | 3.022 |
| 1.55 | 202.473 | 196.854 | 2.810 |
| 1.60 | 202.467 | 197.232 | 2.617 |
| 1.65 | 202.457 | 197.559 | 2.449 |
| 1.70 | 202.444 | 197.823 | 2.310 |
| 1.75 | 202.424 | 198.020 | 2.202 |
| 1.80 | 202.397 | 198.154 | 2.121 |
| 1.85 | 202.359 | 198.239 | 2.060 |
| 1.90 | 202.308 | 198.293 | 2.007 |
| 1.95 | 202.241 | 198.328 | 1.956 |
| 2.00 | 202.157 | 198.353 | 1.902 |
| 2.05 | 202.052 | 198.371 | 1.840 |
| 2.10 | 201.924 | 198.386 | 1.769 |
| 2.15 | 201.769 | 198.398 | 1.685 |
| 2.20 | 201.580 | 198.408 | 1.586 |
| 2.25 | 201.348 | 198.418 | 1.465 |
| 2.30 | 201.062 | 198.426 | 1.318 |
| 2.35 | 200.701 | 198.434 | 1.134 |
| 2.40 | 200.236 | 198.441 | 0.898 |
| 2.45 | 199.623 | 198.448 | 0.588 |
| 2.50 | 198.791 | 198.454 | 0.169 |
| 2.55 | 197.629 | 198.460 | 0.416 |
| 2.60 | 195.963 | 198.465 | 1.251 |
| 2.65 | 193.536 | 198.470 | 2.467 |
| 2.70 | 189.998 | 198.475 | 4.239 |
| 2.75 | 184.933 | 198.479 | 6.773 |
| 2.80 | 177.952 | 198.483 | 10.265 |
| 2.85 | 168.796 | 198.486 | 14.845 |
| 2.90 | 157.381 | 198.488 | 20.554 |
| 2.95 | 143.777 | 198.490 | 27.357 |
| 3.00 | 128.137 | 198.492 | 35.177 |
| 3.05 | 110.639 | 198.493 | 43.927 |
| 3.10 | 91.446 | 198.494 | 53.524 |
| 3.15 | 70.694 | 198.494 | 63.900 |
| 3.20 | 48.488 | 198.495 | 75.003 |
| 3.25 | 24.905 | 198.496 | 86.795 |
| 3.30 | -0.000 | 198.496 | 99.248 |

ngspice log: [`20261103-055748-09dd595-ngspice.txt`](20261103-055748-09dd595-ngspice.txt)
