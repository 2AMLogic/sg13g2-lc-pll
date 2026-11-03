# cp-dc run 20261103-060134-a520f7c-dirty

**Result: mismatch at 1.65 V exceeds 2.0 % (15.661 %); no window around 1.65 V.** **Spec row 7 is NOT graded here.**

- **Scope**: typical corner (`mos_tt`) only, 27 C, nominal 3.3 V supply, one nominal I_cp = 200 uA. No corner grid, no Monte Carlo. **Spec row 7 is not graded:** its upper bound V_hi,req needs the VCO's graded f(Vctrl) curve (gate G4), which does not exist yet. This record lists only the measured window. The numbers are **simulated, not measured**.
- **Netlist**: `/tmp/v78/t_5u.spice` sha256 `431c741e81851381480226ef5fddf805536d2b31cbf52e0cec3db22ceb276218` (NOT the committed netlist: an override, see CP_NETLIST)
- **Deck**: `sim/cp-dc/cp_dc.spice.tmpl` sha256 `53205b18de1f7b878562605df3c3a8a3cbc5a838d139c7a601cf838ee6e5fe78`, placeholder substitution only
- **PDK**: IHP-Open-PDK v0.3.0 (model libraries hash-checked against `sim/pins.json`); PDK_ROOT `/home/ubuntu/share/pdk`; PSP103 OSDI `psp103.osdi` sha256 `2e4299c4683997e26469410dc1ab36b02ced924b1ac0972d6c4eae360e1fc796` (pinned)
- **Simulator**: `ngspice-46` (`/home/ubuntu/.local/bin/ngspice`), one local `ngspice -b`, exit status 0; scratch `.spiceinit` = `set ngbehavior=hsa`
- **Pin check**: Pin check: ngspice-46 != pinned 47 (mismatch)
- **Commit**: `a520f7c-dirty` of this repository
- **Method**: one `.dc` sweep of V_out, 1.0 V to 3.3 V in 0.05 V steps (47 points). Two copies of `cp` in the same deck: copy A has UP=1, DN=0 (I_up = current it sources into the output node); copy B has UP=0, DN=1 (I_dn = current it sinks), its output tied to copy A's by a unity VCVS. IREF = 20 uA into each copy (I_cp = ~10 x IREF; 100-400 uA is IREF 10-40 uA, not exercised here).
- **Mismatch definition**: mismatch (%) = |I_up - I_dn| / I_cp,nom x 100, with I_cp,nom = 200 uA (spec row 6 typical), at the same V_out. It is a static DC quantity: no switching, no charge sharing, no pulse-width effect.
- **Window definition**: the contiguous run of sweep points with mismatch <= 2.0 % that contains 1.65 V, extended up and down; V_top is its upper end. Endpoints are not clipped: points outside compliance are reported as measured.
- **Host**: loom-worker-1, 2026-11-03T06:01:35Z

| V_out (V) | I_up (uA) | I_dn (uA) | mismatch (% of I_cp,nom) |
|---|---|---|---|
| 1.00 | 166.284 | 190.860 | 12.288 |
| 1.05 | 166.294 | 191.513 | 12.609 |
| 1.10 | 166.302 | 192.143 | 12.920 |
| 1.15 | 166.308 | 192.752 | 13.222 |
| 1.20 | 166.311 | 193.340 | 13.515 |
| 1.25 | 166.311 | 193.910 | 13.799 |
| 1.30 | 166.309 | 194.459 | 14.075 |
| 1.35 | 166.305 | 194.989 | 14.342 |
| 1.40 | 166.299 | 195.496 | 14.599 |
| 1.45 | 166.290 | 195.979 | 14.844 |
| 1.50 | 166.280 | 196.433 | 15.077 |
| 1.55 | 166.267 | 196.854 | 15.293 |
| 1.60 | 166.253 | 197.232 | 15.490 |
| 1.65 | 166.237 | 197.559 | 15.661 |
| 1.70 | 166.219 | 197.823 | 15.802 |
| 1.75 | 166.199 | 198.020 | 15.910 |
| 1.80 | 166.177 | 198.154 | 15.988 |
| 1.85 | 166.153 | 198.239 | 16.043 |
| 1.90 | 166.126 | 198.293 | 16.084 |
| 1.95 | 166.096 | 198.328 | 16.116 |
| 2.00 | 166.062 | 198.353 | 16.146 |
| 2.05 | 166.023 | 198.371 | 16.174 |
| 2.10 | 165.978 | 198.386 | 16.204 |
| 2.15 | 165.925 | 198.398 | 16.236 |
| 2.20 | 165.862 | 198.408 | 16.273 |
| 2.25 | 165.782 | 198.418 | 16.318 |
| 2.30 | 165.680 | 198.426 | 16.373 |
| 2.35 | 165.544 | 198.434 | 16.445 |
| 2.40 | 165.351 | 198.441 | 16.545 |
| 2.45 | 165.067 | 198.448 | 16.690 |
| 2.50 | 164.625 | 198.454 | 16.915 |
| 2.55 | 163.906 | 198.460 | 17.277 |
| 2.60 | 162.714 | 198.465 | 17.876 |
| 2.65 | 160.762 | 198.470 | 18.854 |
| 2.70 | 157.720 | 198.475 | 20.377 |
| 2.75 | 153.306 | 198.479 | 22.587 |
| 2.80 | 147.339 | 198.483 | 25.572 |
| 2.85 | 139.737 | 198.486 | 29.374 |
| 2.90 | 130.476 | 198.488 | 34.006 |
| 2.95 | 119.565 | 198.490 | 39.463 |
| 3.00 | 107.031 | 198.492 | 45.730 |
| 3.05 | 92.912 | 198.493 | 52.790 |
| 3.10 | 77.251 | 198.494 | 60.621 |
| 3.15 | 60.090 | 198.494 | 69.202 |
| 3.20 | 41.471 | 198.495 | 78.512 |
| 3.25 | 21.430 | 198.496 | 88.533 |
| 3.30 | -0.000 | 198.496 | 99.248 |

ngspice log: [`20261103-060134-a520f7c-dirty-ngspice.txt`](20261103-060134-a520f7c-dirty-ngspice.txt)
