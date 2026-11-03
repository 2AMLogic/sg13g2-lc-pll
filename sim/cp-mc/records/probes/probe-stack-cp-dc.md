# cp-dc run 20261103-060114-a520f7c-dirty

**Result: mismatch at 1.65 V exceeds 2.0 % (2.967 %); no window around 1.65 V.** **Spec row 7 is NOT graded here.**

- **Scope**: typical corner (`mos_tt`) only, 27 C, nominal 3.3 V supply, one nominal I_cp = 200 uA. No corner grid, no Monte Carlo. **Spec row 7 is not graded:** its upper bound V_hi,req needs the VCO's graded f(Vctrl) curve (gate G4), which does not exist yet. This record lists only the measured window. The numbers are **simulated, not measured**.
- **Netlist**: `design/netlist/cp.spice` sha256 `93aca82ad0f380e9c38aea7f621fc6a82fa9876a7fca61e92d8cff774d5a9300`, checked against design/cp.sch with design/netlist.sh --check
- **Deck**: `sim/cp-dc/cp_dc.spice.tmpl` sha256 `53205b18de1f7b878562605df3c3a8a3cbc5a838d139c7a601cf838ee6e5fe78`, placeholder substitution only
- **PDK**: IHP-Open-PDK v0.3.0 (model libraries hash-checked against `sim/pins.json`); PDK_ROOT `/home/ubuntu/share/pdk`; PSP103 OSDI `psp103.osdi` sha256 `2e4299c4683997e26469410dc1ab36b02ced924b1ac0972d6c4eae360e1fc796` (pinned)
- **Simulator**: `ngspice-46` (`/home/ubuntu/.local/bin/ngspice`), one local `ngspice -b`, exit status 0; scratch `.spiceinit` = `set ngbehavior=hsa`
- **Pin check**: Pin check: ngspice-46 != pinned 47 (mismatch)
- **Commit**: `a520f7c-dirty` of this repository
- **Method**: one `.dc` sweep of V_out, 1.0 V to 3.3 V in 0.05 V steps (47 points). Two copies of `cp` in the same deck: copy A has UP=1, DN=0 (I_up = current it sources into the output node); copy B has UP=0, DN=1 (I_dn = current it sinks), its output tied to copy A's by a unity VCVS. IREF = 20 uA into each copy (I_cp = ~10 x IREF; 100-400 uA is IREF 10-40 uA, not exercised here).
- **Mismatch definition**: mismatch (%) = |I_up - I_dn| / I_cp,nom x 100, with I_cp,nom = 200 uA (spec row 6 typical), at the same V_out. It is a static DC quantity: no switching, no charge sharing, no pulse-width effect.
- **Window definition**: the contiguous run of sweep points with mismatch <= 2.0 % that contains 1.65 V, extended up and down; V_top is its upper end. Endpoints are not clipped: points outside compliance are reported as measured.
- **Host**: loom-worker-1, 2026-11-03T06:01:14Z

| V_out (V) | I_up (uA) | I_dn (uA) | mismatch (% of I_cp,nom) |
|---|---|---|---|
| 1.00 | 191.625 | 190.860 | 0.382 |
| 1.05 | 191.636 | 191.513 | 0.061 |
| 1.10 | 191.645 | 192.143 | 0.249 |
| 1.15 | 191.652 | 192.752 | 0.550 |
| 1.20 | 191.657 | 193.340 | 0.842 |
| 1.25 | 191.659 | 193.910 | 1.125 |
| 1.30 | 191.660 | 194.459 | 1.400 |
| 1.35 | 191.659 | 194.989 | 1.665 |
| 1.40 | 191.656 | 195.496 | 1.920 |
| 1.45 | 191.652 | 195.979 | 2.164 |
| 1.50 | 191.647 | 196.433 | 2.393 |
| 1.55 | 191.641 | 196.854 | 2.607 |
| 1.60 | 191.633 | 197.232 | 2.800 |
| 1.65 | 191.625 | 197.559 | 2.967 |
| 1.70 | 191.615 | 197.823 | 3.104 |
| 1.75 | 191.603 | 198.020 | 3.209 |
| 1.80 | 191.590 | 198.154 | 3.282 |
| 1.85 | 191.574 | 198.239 | 3.333 |
| 1.90 | 191.556 | 198.293 | 3.369 |
| 1.95 | 191.534 | 198.328 | 3.397 |
| 2.00 | 191.508 | 198.353 | 3.423 |
| 2.05 | 191.474 | 198.371 | 3.448 |
| 2.10 | 191.431 | 198.386 | 3.477 |
| 2.15 | 191.374 | 198.398 | 3.512 |
| 2.20 | 191.295 | 198.408 | 3.557 |
| 2.25 | 191.179 | 198.418 | 3.619 |
| 2.30 | 191.005 | 198.426 | 3.710 |
| 2.35 | 190.731 | 198.434 | 3.851 |
| 2.40 | 190.289 | 198.441 | 4.076 |
| 2.45 | 189.573 | 198.448 | 4.437 |
| 2.50 | 188.440 | 198.454 | 5.007 |
| 2.55 | 186.717 | 198.460 | 5.871 |
| 2.60 | 184.212 | 198.465 | 7.126 |
| 2.65 | 180.723 | 198.470 | 8.874 |
| 2.70 | 176.045 | 198.475 | 11.215 |
| 2.75 | 169.988 | 198.479 | 14.245 |
| 2.80 | 162.403 | 198.483 | 18.040 |
| 2.85 | 153.192 | 198.486 | 22.647 |
| 2.90 | 142.318 | 198.488 | 28.085 |
| 2.95 | 129.791 | 198.490 | 34.350 |
| 3.00 | 115.649 | 198.492 | 41.421 |
| 3.05 | 99.951 | 198.493 | 49.271 |
| 3.10 | 82.754 | 198.494 | 57.870 |
| 3.15 | 64.117 | 198.494 | 67.189 |
| 3.20 | 44.087 | 198.495 | 77.204 |
| 3.25 | 22.704 | 198.496 | 87.896 |
| 3.30 | -0.000 | 198.496 | 99.248 |

ngspice log: [`20261103-060114-a520f7c-dirty-ngspice.txt`](20261103-060114-a520f7c-dirty-ngspice.txt)
