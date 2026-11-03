# cp-dc run 20261103-055730-09dd595

**Result: mismatch at 1.65 V exceeds 2.0 % (2.750 %); no window around 1.65 V.** **Spec row 7 is NOT graded here.**

- **Scope**: typical corner (`mos_tt`) only, 27 C, nominal 3.3 V supply, one nominal I_cp = 200 uA. No corner grid, no Monte Carlo. **Spec row 7 is not graded:** its upper bound V_hi,req needs the VCO's graded f(Vctrl) curve (gate G4), which does not exist yet. This record lists only the measured window. The numbers are **simulated, not measured**.
- **Netlist**: `/tmp/v78/xbpa_only.spice` sha256 `da55160b779295b37e1187a203764bb1c1e882fd1ea7cfe92a6b91d947d2c183` (NOT the committed netlist: an override, see CP_NETLIST)
- **Deck**: `sim/cp-dc/cp_dc.spice.tmpl` sha256 `53205b18de1f7b878562605df3c3a8a3cbc5a838d139c7a601cf838ee6e5fe78`, placeholder substitution only
- **PDK**: IHP-Open-PDK v0.3.0 (model libraries hash-checked against `sim/pins.json`); PDK_ROOT `/home/ubuntu/share/pdk`; PSP103 OSDI `psp103.osdi` sha256 `2e4299c4683997e26469410dc1ab36b02ced924b1ac0972d6c4eae360e1fc796` (pinned)
- **Simulator**: `ngspice-46` (`/home/ubuntu/.local/bin/ngspice`), one local `ngspice -b`, exit status 0; scratch `.spiceinit` = `set ngbehavior=hsa`
- **Pin check**: Pin check: ngspice-46 != pinned 47 (mismatch)
- **Commit**: `09dd595` of this repository
- **Method**: one `.dc` sweep of V_out, 1.0 V to 3.3 V in 0.05 V steps (47 points). Two copies of `cp` in the same deck: copy A has UP=1, DN=0 (I_up = current it sources into the output node); copy B has UP=0, DN=1 (I_dn = current it sinks), its output tied to copy A's by a unity VCVS. IREF = 20 uA into each copy (I_cp = ~10 x IREF; 100-400 uA is IREF 10-40 uA, not exercised here).
- **Mismatch definition**: mismatch (%) = |I_up - I_dn| / I_cp,nom x 100, with I_cp,nom = 200 uA (spec row 6 typical), at the same V_out. It is a static DC quantity: no switching, no charge sharing, no pulse-width effect.
- **Window definition**: the contiguous run of sweep points with mismatch <= 2.0 % that contains 1.65 V, extended up and down; V_top is its upper end. Endpoints are not clipped: points outside compliance are reported as measured.
- **Host**: loom-worker-1, 2026-11-03T05:57:30Z

| V_out (V) | I_up (uA) | I_dn (uA) | mismatch (% of I_cp,nom) |
|---|---|---|---|
| 1.00 | 203.214 | 190.860 | 6.177 |
| 1.05 | 203.223 | 191.513 | 5.855 |
| 1.10 | 203.230 | 192.143 | 5.544 |
| 1.15 | 203.234 | 192.752 | 5.241 |
| 1.20 | 203.234 | 193.340 | 4.947 |
| 1.25 | 203.232 | 193.910 | 4.661 |
| 1.30 | 203.226 | 194.459 | 4.383 |
| 1.35 | 203.216 | 194.989 | 4.114 |
| 1.40 | 203.202 | 195.496 | 3.853 |
| 1.45 | 203.185 | 195.979 | 3.603 |
| 1.50 | 203.162 | 196.433 | 3.364 |
| 1.55 | 203.134 | 196.854 | 3.140 |
| 1.60 | 203.100 | 197.232 | 2.934 |
| 1.65 | 203.059 | 197.559 | 2.750 |
| 1.70 | 203.011 | 197.823 | 2.594 |
| 1.75 | 202.955 | 198.020 | 2.467 |
| 1.80 | 202.891 | 198.154 | 2.368 |
| 1.85 | 202.818 | 198.239 | 2.289 |
| 1.90 | 202.735 | 198.293 | 2.221 |
| 1.95 | 202.641 | 198.328 | 2.156 |
| 2.00 | 202.534 | 198.353 | 2.091 |
| 2.05 | 202.413 | 198.371 | 2.021 |
| 2.10 | 202.275 | 198.386 | 1.944 |
| 2.15 | 202.115 | 198.398 | 1.859 |
| 2.20 | 201.929 | 198.408 | 1.761 |
| 2.25 | 201.709 | 198.418 | 1.646 |
| 2.30 | 201.445 | 198.426 | 1.509 |
| 2.35 | 201.118 | 198.434 | 1.342 |
| 2.40 | 200.707 | 198.441 | 1.133 |
| 2.45 | 200.172 | 198.448 | 0.862 |
| 2.50 | 199.454 | 198.454 | 0.500 |
| 2.55 | 198.459 | 198.460 | 0.000 |
| 2.60 | 197.032 | 198.465 | 0.716 |
| 2.65 | 194.937 | 198.470 | 1.767 |
| 2.70 | 191.825 | 198.475 | 3.325 |
| 2.75 | 187.251 | 198.479 | 5.614 |
| 2.80 | 180.749 | 198.483 | 8.867 |
| 2.85 | 171.963 | 198.486 | 13.262 |
| 2.90 | 160.742 | 198.488 | 18.873 |
| 2.95 | 147.133 | 198.490 | 25.678 |
| 3.00 | 131.308 | 198.492 | 33.592 |
| 3.05 | 113.478 | 198.493 | 42.508 |
| 3.10 | 93.841 | 198.494 | 52.326 |
| 3.15 | 72.565 | 198.494 | 62.965 |
| 3.20 | 49.775 | 198.495 | 74.360 |
| 3.25 | 25.564 | 198.496 | 86.466 |
| 3.30 | -0.000 | 198.496 | 99.248 |

ngspice log: [`20261103-055730-09dd595-ngspice.txt`](20261103-055730-09dd595-ngspice.txt)
