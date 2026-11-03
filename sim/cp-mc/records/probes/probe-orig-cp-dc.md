# cp-dc run 20261103-055726-09dd595

**Result: measured mismatch <= 2.0 % window = 1.15 V to 2.40 V** (contiguous around 1.65 V; mismatch at 1.65 V = 0.599 %). **Spec row 7 is NOT graded here.**

- **Scope**: typical corner (`mos_tt`) only, 27 C, nominal 3.3 V supply, one nominal I_cp = 200 uA. No corner grid, no Monte Carlo. **Spec row 7 is not graded:** its upper bound V_hi,req needs the VCO's graded f(Vctrl) curve (gate G4), which does not exist yet. This record lists only the measured window. The numbers are **simulated, not measured**.
- **Netlist**: `/tmp/v78/orig.spice` sha256 `99827833f70681faaf031e345f37730eeba9cb692f9eb46f59a149edfa9c213a` (NOT the committed netlist: an override, see CP_NETLIST)
- **Deck**: `sim/cp-dc/cp_dc.spice.tmpl` sha256 `53205b18de1f7b878562605df3c3a8a3cbc5a838d139c7a601cf838ee6e5fe78`, placeholder substitution only
- **PDK**: IHP-Open-PDK v0.3.0 (model libraries hash-checked against `sim/pins.json`); PDK_ROOT `/home/ubuntu/share/pdk`; PSP103 OSDI `psp103.osdi` sha256 `2e4299c4683997e26469410dc1ab36b02ced924b1ac0972d6c4eae360e1fc796` (pinned)
- **Simulator**: `ngspice-46` (`/home/ubuntu/.local/bin/ngspice`), one local `ngspice -b`, exit status 0; scratch `.spiceinit` = `set ngbehavior=hsa`
- **Pin check**: Pin check: ngspice-46 != pinned 47 (mismatch)
- **Commit**: `09dd595` of this repository
- **Method**: one `.dc` sweep of V_out, 1.0 V to 3.3 V in 0.05 V steps (47 points). Two copies of `cp` in the same deck: copy A has UP=1, DN=0 (I_up = current it sources into the output node); copy B has UP=0, DN=1 (I_dn = current it sinks), its output tied to copy A's by a unity VCVS. IREF = 20 uA into each copy (I_cp = ~10 x IREF; 100-400 uA is IREF 10-40 uA, not exercised here).
- **Mismatch definition**: mismatch (%) = |I_up - I_dn| / I_cp,nom x 100, with I_cp,nom = 200 uA (spec row 6 typical), at the same V_out. It is a static DC quantity: no switching, no charge sharing, no pulse-width effect.
- **Window definition**: the contiguous run of sweep points with mismatch <= 2.0 % that contains 1.65 V, extended up and down; V_top is its upper end. Endpoints are not clipped: points outside compliance are reported as measured.
- **Host**: loom-worker-1, 2026-11-03T05:57:26Z

| V_out (V) | I_up (uA) | I_dn (uA) | mismatch (% of I_cp,nom) |
|---|---|---|---|
| 1.00 | 196.343 | 190.860 | 2.741 |
| 1.05 | 196.354 | 191.513 | 2.421 |
| 1.10 | 196.364 | 192.143 | 2.111 |
| 1.15 | 196.372 | 192.752 | 1.810 |
| 1.20 | 196.377 | 193.340 | 1.518 |
| 1.25 | 196.380 | 193.910 | 1.235 |
| 1.30 | 196.382 | 194.459 | 0.961 |
| 1.35 | 196.382 | 194.989 | 0.697 |
| 1.40 | 196.381 | 195.496 | 0.442 |
| 1.45 | 196.378 | 195.979 | 0.200 |
| 1.50 | 196.375 | 196.433 | 0.029 |
| 1.55 | 196.371 | 196.854 | 0.241 |
| 1.60 | 196.366 | 197.232 | 0.433 |
| 1.65 | 196.361 | 197.559 | 0.599 |
| 1.70 | 196.354 | 197.823 | 0.735 |
| 1.75 | 196.346 | 198.020 | 0.837 |
| 1.80 | 196.337 | 198.154 | 0.909 |
| 1.85 | 196.326 | 198.239 | 0.957 |
| 1.90 | 196.312 | 198.293 | 0.991 |
| 1.95 | 196.295 | 198.328 | 1.017 |
| 2.00 | 196.273 | 198.353 | 1.040 |
| 2.05 | 196.244 | 198.371 | 1.064 |
| 2.10 | 196.203 | 198.386 | 1.091 |
| 2.15 | 196.146 | 198.398 | 1.126 |
| 2.20 | 196.061 | 198.408 | 1.174 |
| 2.25 | 195.929 | 198.418 | 1.244 |
| 2.30 | 195.720 | 198.426 | 1.353 |
| 2.35 | 195.384 | 198.434 | 1.525 |
| 2.40 | 194.849 | 198.441 | 1.796 |
| 2.45 | 194.024 | 198.448 | 2.212 |
| 2.50 | 192.789 | 198.454 | 2.832 |
| 2.55 | 191.003 | 198.460 | 3.728 |
| 2.60 | 188.483 | 198.465 | 4.991 |
| 2.65 | 185.006 | 198.470 | 6.732 |
| 2.70 | 180.332 | 198.475 | 9.072 |
| 2.75 | 174.229 | 198.479 | 12.125 |
| 2.80 | 166.515 | 198.483 | 15.984 |
| 2.85 | 157.084 | 198.486 | 20.701 |
| 2.90 | 145.903 | 198.488 | 26.293 |
| 2.95 | 132.997 | 198.490 | 32.747 |
| 3.00 | 118.428 | 198.492 | 40.032 |
| 3.05 | 102.271 | 198.493 | 48.111 |
| 3.10 | 84.603 | 198.494 | 56.945 |
| 3.15 | 65.491 | 198.494 | 66.502 |
| 3.20 | 44.992 | 198.495 | 76.752 |
| 3.25 | 23.150 | 198.496 | 87.673 |
| 3.30 | -0.000 | 198.496 | 99.248 |

ngspice log: [`20261103-055726-09dd595-ngspice.txt`](20261103-055726-09dd595-ngspice.txt)
