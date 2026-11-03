# cp-dc run 20261103-060133-a520f7c-dirty

**Result: mismatch at 1.65 V exceeds 2.0 % (9.296 %); no window around 1.65 V.** **Spec row 7 is NOT graded here.**

- **Scope**: typical corner (`mos_tt`) only, 27 C, nominal 3.3 V supply, one nominal I_cp = 200 uA. No corner grid, no Monte Carlo. **Spec row 7 is not graded:** its upper bound V_hi,req needs the VCO's graded f(Vctrl) curve (gate G4), which does not exist yet. This record lists only the measured window. The numbers are **simulated, not measured**.
- **Netlist**: `/tmp/v78/t_4.4u.spice` sha256 `3187c475677fd3e60c5afe5490d6f36962103e52c3f3c509bf46f4aaeef1275b` (NOT the committed netlist: an override, see CP_NETLIST)
- **Deck**: `sim/cp-dc/cp_dc.spice.tmpl` sha256 `53205b18de1f7b878562605df3c3a8a3cbc5a838d139c7a601cf838ee6e5fe78`, placeholder substitution only
- **PDK**: IHP-Open-PDK v0.3.0 (model libraries hash-checked against `sim/pins.json`); PDK_ROOT `/home/ubuntu/share/pdk`; PSP103 OSDI `psp103.osdi` sha256 `2e4299c4683997e26469410dc1ab36b02ced924b1ac0972d6c4eae360e1fc796` (pinned)
- **Simulator**: `ngspice-46` (`/home/ubuntu/.local/bin/ngspice`), one local `ngspice -b`, exit status 0; scratch `.spiceinit` = `set ngbehavior=hsa`
- **Pin check**: Pin check: ngspice-46 != pinned 47 (mismatch)
- **Commit**: `a520f7c-dirty` of this repository
- **Method**: one `.dc` sweep of V_out, 1.0 V to 3.3 V in 0.05 V steps (47 points). Two copies of `cp` in the same deck: copy A has UP=1, DN=0 (I_up = current it sources into the output node); copy B has UP=0, DN=1 (I_dn = current it sinks), its output tied to copy A's by a unity VCVS. IREF = 20 uA into each copy (I_cp = ~10 x IREF; 100-400 uA is IREF 10-40 uA, not exercised here).
- **Mismatch definition**: mismatch (%) = |I_up - I_dn| / I_cp,nom x 100, with I_cp,nom = 200 uA (spec row 6 typical), at the same V_out. It is a static DC quantity: no switching, no charge sharing, no pulse-width effect.
- **Window definition**: the contiguous run of sweep points with mismatch <= 2.0 % that contains 1.65 V, extended up and down; V_top is its upper end. Endpoints are not clipped: points outside compliance are reported as measured.
- **Host**: loom-worker-1, 2026-11-03T06:01:33Z

| V_out (V) | I_up (uA) | I_dn (uA) | mismatch (% of I_cp,nom) |
|---|---|---|---|
| 1.00 | 178.998 | 190.860 | 5.931 |
| 1.05 | 179.009 | 191.513 | 6.252 |
| 1.10 | 179.017 | 192.143 | 6.563 |
| 1.15 | 179.023 | 192.752 | 6.864 |
| 1.20 | 179.027 | 193.340 | 7.157 |
| 1.25 | 179.028 | 193.910 | 7.441 |
| 1.30 | 179.027 | 194.459 | 7.716 |
| 1.35 | 179.024 | 194.989 | 7.983 |
| 1.40 | 179.018 | 195.496 | 8.239 |
| 1.45 | 179.011 | 195.979 | 8.484 |
| 1.50 | 179.003 | 196.433 | 8.715 |
| 1.55 | 178.993 | 196.854 | 8.931 |
| 1.60 | 178.981 | 197.232 | 9.126 |
| 1.65 | 178.967 | 197.559 | 9.296 |
| 1.70 | 178.952 | 197.823 | 9.436 |
| 1.75 | 178.934 | 198.020 | 9.543 |
| 1.80 | 178.915 | 198.154 | 9.620 |
| 1.85 | 178.893 | 198.239 | 9.673 |
| 1.90 | 178.868 | 198.293 | 9.713 |
| 1.95 | 178.839 | 198.328 | 9.745 |
| 2.00 | 178.806 | 198.353 | 9.773 |
| 2.05 | 178.768 | 198.371 | 9.802 |
| 2.10 | 178.721 | 198.386 | 9.832 |
| 2.15 | 178.664 | 198.398 | 9.867 |
| 2.20 | 178.592 | 198.408 | 9.908 |
| 2.25 | 178.496 | 198.418 | 9.961 |
| 2.30 | 178.366 | 198.426 | 10.030 |
| 2.35 | 178.179 | 198.434 | 10.127 |
| 2.40 | 177.898 | 198.441 | 10.271 |
| 2.45 | 177.456 | 198.448 | 10.496 |
| 2.50 | 176.739 | 198.454 | 10.857 |
| 2.55 | 175.566 | 198.460 | 11.447 |
| 2.60 | 173.696 | 198.465 | 12.385 |
| 2.65 | 170.861 | 198.470 | 13.805 |
| 2.70 | 166.826 | 198.475 | 15.825 |
| 2.75 | 161.411 | 198.479 | 18.534 |
| 2.80 | 154.495 | 198.483 | 21.994 |
| 2.85 | 146.004 | 198.486 | 26.241 |
| 2.90 | 135.902 | 198.488 | 31.293 |
| 2.95 | 124.189 | 198.490 | 37.150 |
| 3.00 | 110.888 | 198.492 | 43.802 |
| 3.05 | 96.034 | 198.493 | 51.229 |
| 3.10 | 79.674 | 198.494 | 59.410 |
| 3.15 | 61.852 | 198.494 | 68.321 |
| 3.20 | 42.609 | 198.495 | 77.943 |
| 3.25 | 21.982 | 198.496 | 88.257 |
| 3.30 | -0.000 | 198.496 | 99.248 |

ngspice log: [`20261103-060133-a520f7c-dirty-ngspice.txt`](20261103-060133-a520f7c-dirty-ngspice.txt)
