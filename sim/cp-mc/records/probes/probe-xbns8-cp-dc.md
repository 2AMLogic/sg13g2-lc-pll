# cp-dc run 20261103-055732-09dd595

**Result: measured mismatch <= 2.0 % window = 1.40 V to 2.50 V** (contiguous around 1.65 V; mismatch at 1.65 V = 0.763 %). **Spec row 7 is NOT graded here.**

- **Scope**: typical corner (`mos_tt`) only, 27 C, nominal 3.3 V supply, one nominal I_cp = 200 uA. No corner grid, no Monte Carlo. **Spec row 7 is not graded:** its upper bound V_hi,req needs the VCO's graded f(Vctrl) curve (gate G4), which does not exist yet. This record lists only the measured window. The numbers are **simulated, not measured**.
- **Netlist**: `/tmp/v78/xbns8.spice` sha256 `104a0e036983b0f4fc2f14e8c1985b5cd284930a69464c339187fe01d5579bf7` (NOT the committed netlist: an override, see CP_NETLIST)
- **Deck**: `sim/cp-dc/cp_dc.spice.tmpl` sha256 `53205b18de1f7b878562605df3c3a8a3cbc5a838d139c7a601cf838ee6e5fe78`, placeholder substitution only
- **PDK**: IHP-Open-PDK v0.3.0 (model libraries hash-checked against `sim/pins.json`); PDK_ROOT `/home/ubuntu/share/pdk`; PSP103 OSDI `psp103.osdi` sha256 `2e4299c4683997e26469410dc1ab36b02ced924b1ac0972d6c4eae360e1fc796` (pinned)
- **Simulator**: `ngspice-46` (`/home/ubuntu/.local/bin/ngspice`), one local `ngspice -b`, exit status 0; scratch `.spiceinit` = `set ngbehavior=hsa`
- **Pin check**: Pin check: ngspice-46 != pinned 47 (mismatch)
- **Commit**: `09dd595` of this repository
- **Method**: one `.dc` sweep of V_out, 1.0 V to 3.3 V in 0.05 V steps (47 points). Two copies of `cp` in the same deck: copy A has UP=1, DN=0 (I_up = current it sources into the output node); copy B has UP=0, DN=1 (I_dn = current it sinks), its output tied to copy A's by a unity VCVS. IREF = 20 uA into each copy (I_cp = ~10 x IREF; 100-400 uA is IREF 10-40 uA, not exercised here).
- **Mismatch definition**: mismatch (%) = |I_up - I_dn| / I_cp,nom x 100, with I_cp,nom = 200 uA (spec row 6 typical), at the same V_out. It is a static DC quantity: no switching, no charge sharing, no pulse-width effect.
- **Window definition**: the contiguous run of sweep points with mismatch <= 2.0 % that contains 1.65 V, extended up and down; V_top is its upper end. Endpoints are not clipped: points outside compliance are reported as measured.
- **Host**: loom-worker-1, 2026-11-03T05:57:32Z

| V_out (V) | I_up (uA) | I_dn (uA) | mismatch (% of I_cp,nom) |
|---|---|---|---|
| 1.00 | 199.055 | 190.860 | 4.097 |
| 1.05 | 199.067 | 191.513 | 3.777 |
| 1.10 | 199.077 | 192.143 | 3.467 |
| 1.15 | 199.084 | 192.752 | 3.166 |
| 1.20 | 199.090 | 193.340 | 2.875 |
| 1.25 | 199.094 | 193.910 | 2.592 |
| 1.30 | 199.096 | 194.459 | 2.318 |
| 1.35 | 199.097 | 194.989 | 2.054 |
| 1.40 | 199.097 | 195.496 | 1.800 |
| 1.45 | 199.095 | 195.979 | 1.558 |
| 1.50 | 199.093 | 196.433 | 1.330 |
| 1.55 | 199.091 | 196.854 | 1.119 |
| 1.60 | 199.088 | 197.232 | 0.928 |
| 1.65 | 199.084 | 197.559 | 0.763 |
| 1.70 | 199.079 | 197.823 | 0.628 |
| 1.75 | 199.074 | 198.020 | 0.527 |
| 1.80 | 199.067 | 198.154 | 0.456 |
| 1.85 | 199.058 | 198.239 | 0.409 |
| 1.90 | 199.047 | 198.293 | 0.377 |
| 1.95 | 199.032 | 198.328 | 0.352 |
| 2.00 | 199.011 | 198.353 | 0.329 |
| 2.05 | 198.982 | 198.371 | 0.305 |
| 2.10 | 198.939 | 198.386 | 0.277 |
| 2.15 | 198.873 | 198.398 | 0.238 |
| 2.20 | 198.770 | 198.408 | 0.181 |
| 2.25 | 198.607 | 198.418 | 0.095 |
| 2.30 | 198.353 | 198.426 | 0.036 |
| 2.35 | 197.965 | 198.434 | 0.234 |
| 2.40 | 197.391 | 198.441 | 0.525 |
| 2.45 | 196.562 | 198.448 | 0.943 |
| 2.50 | 195.381 | 198.454 | 1.536 |
| 2.55 | 193.711 | 198.460 | 2.375 |
| 2.60 | 191.361 | 198.465 | 3.552 |
| 2.65 | 188.085 | 198.470 | 5.193 |
| 2.70 | 183.600 | 198.475 | 7.438 |
| 2.75 | 177.629 | 198.479 | 10.425 |
| 2.80 | 169.953 | 198.483 | 14.265 |
| 2.85 | 160.445 | 198.486 | 19.021 |
| 2.90 | 149.076 | 198.488 | 24.706 |
| 2.95 | 135.890 | 198.490 | 31.300 |
| 3.00 | 120.973 | 198.492 | 38.759 |
| 3.05 | 104.423 | 198.493 | 47.035 |
| 3.10 | 86.335 | 198.494 | 56.079 |
| 3.15 | 66.790 | 198.494 | 65.852 |
| 3.20 | 45.854 | 198.495 | 76.320 |
| 3.25 | 23.578 | 198.496 | 87.459 |
| 3.30 | -0.000 | 198.496 | 99.248 |

ngspice log: [`20261103-055732-09dd595-ngspice.txt`](20261103-055732-09dd595-ngspice.txt)
