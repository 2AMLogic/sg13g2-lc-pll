# cp-dc run 20261103-060131-a520f7c-dirty

**Result: mismatch at 1.65 V exceeds 2.0 % (2.635 %); no window around 1.65 V.** **Spec row 7 is NOT graded here.**

- **Scope**: typical corner (`mos_tt`) only, 27 C, nominal 3.3 V supply, one nominal I_cp = 200 uA. No corner grid, no Monte Carlo. **Spec row 7 is not graded:** its upper bound V_hi,req needs the VCO's graded f(Vctrl) curve (gate G4), which does not exist yet. This record lists only the measured window. The numbers are **simulated, not measured**.
- **Netlist**: `/tmp/v78/t_3.6u.spice` sha256 `beec5f422ddfcddbfe21740383f020ad42566299122f4d661981fd2397e3cd6f` (NOT the committed netlist: an override, see CP_NETLIST)
- **Deck**: `sim/cp-dc/cp_dc.spice.tmpl` sha256 `53205b18de1f7b878562605df3c3a8a3cbc5a838d139c7a601cf838ee6e5fe78`, placeholder substitution only
- **PDK**: IHP-Open-PDK v0.3.0 (model libraries hash-checked against `sim/pins.json`); PDK_ROOT `/home/ubuntu/share/pdk`; PSP103 OSDI `psp103.osdi` sha256 `2e4299c4683997e26469410dc1ab36b02ced924b1ac0972d6c4eae360e1fc796` (pinned)
- **Simulator**: `ngspice-46` (`/home/ubuntu/.local/bin/ngspice`), one local `ngspice -b`, exit status 0; scratch `.spiceinit` = `set ngbehavior=hsa`
- **Pin check**: Pin check: ngspice-46 != pinned 47 (mismatch)
- **Commit**: `a520f7c-dirty` of this repository
- **Method**: one `.dc` sweep of V_out, 1.0 V to 3.3 V in 0.05 V steps (47 points). Two copies of `cp` in the same deck: copy A has UP=1, DN=0 (I_up = current it sources into the output node); copy B has UP=0, DN=1 (I_dn = current it sinks), its output tied to copy A's by a unity VCVS. IREF = 20 uA into each copy (I_cp = ~10 x IREF; 100-400 uA is IREF 10-40 uA, not exercised here).
- **Mismatch definition**: mismatch (%) = |I_up - I_dn| / I_cp,nom x 100, with I_cp,nom = 200 uA (spec row 6 typical), at the same V_out. It is a static DC quantity: no switching, no charge sharing, no pulse-width effect.
- **Window definition**: the contiguous run of sweep points with mismatch <= 2.0 % that contains 1.65 V, extended up and down; V_top is its upper end. Endpoints are not clipped: points outside compliance are reported as measured.
- **Host**: loom-worker-1, 2026-11-03T06:01:31Z

| V_out (V) | I_up (uA) | I_dn (uA) | mismatch (% of I_cp,nom) |
|---|---|---|---|
| 1.00 | 202.873 | 190.860 | 6.007 |
| 1.05 | 202.885 | 191.513 | 5.686 |
| 1.10 | 202.894 | 192.143 | 5.376 |
| 1.15 | 202.901 | 192.752 | 5.075 |
| 1.20 | 202.906 | 193.340 | 4.783 |
| 1.25 | 202.908 | 193.910 | 4.499 |
| 1.30 | 202.908 | 194.459 | 4.224 |
| 1.35 | 202.906 | 194.989 | 3.959 |
| 1.40 | 202.902 | 195.496 | 3.703 |
| 1.45 | 202.895 | 195.979 | 3.458 |
| 1.50 | 202.885 | 196.433 | 3.226 |
| 1.55 | 202.872 | 196.854 | 3.009 |
| 1.60 | 202.853 | 197.232 | 2.811 |
| 1.65 | 202.829 | 197.559 | 2.635 |
| 1.70 | 202.797 | 197.823 | 2.487 |
| 1.75 | 202.757 | 198.020 | 2.368 |
| 1.80 | 202.707 | 198.154 | 2.276 |
| 1.85 | 202.646 | 198.239 | 2.203 |
| 1.90 | 202.573 | 198.293 | 2.140 |
| 1.95 | 202.488 | 198.328 | 2.080 |
| 2.00 | 202.388 | 198.353 | 2.017 |
| 2.05 | 202.271 | 198.371 | 1.950 |
| 2.10 | 202.135 | 198.386 | 1.875 |
| 2.15 | 201.976 | 198.398 | 1.789 |
| 2.20 | 201.787 | 198.408 | 1.689 |
| 2.25 | 201.561 | 198.418 | 1.572 |
| 2.30 | 201.285 | 198.426 | 1.430 |
| 2.35 | 200.943 | 198.434 | 1.255 |
| 2.40 | 200.508 | 198.441 | 1.033 |
| 2.45 | 199.938 | 198.448 | 0.745 |
| 2.50 | 199.169 | 198.454 | 0.357 |
| 2.55 | 198.098 | 198.460 | 0.181 |
| 2.60 | 196.563 | 198.465 | 0.951 |
| 2.65 | 194.314 | 198.470 | 2.078 |
| 2.70 | 191.000 | 198.475 | 3.737 |
| 2.75 | 186.188 | 198.479 | 6.146 |
| 2.80 | 179.447 | 198.483 | 9.518 |
| 2.85 | 170.469 | 198.486 | 14.009 |
| 2.90 | 159.138 | 198.488 | 19.675 |
| 2.95 | 145.518 | 198.490 | 26.486 |
| 3.00 | 129.772 | 198.492 | 34.360 |
| 3.05 | 112.095 | 198.493 | 43.199 |
| 3.10 | 92.669 | 198.494 | 52.912 |
| 3.15 | 71.646 | 198.494 | 63.424 |
| 3.20 | 49.141 | 198.495 | 74.677 |
| 3.25 | 25.238 | 198.496 | 86.629 |
| 3.30 | -0.000 | 198.496 | 99.248 |

ngspice log: [`20261103-060131-a520f7c-dirty-ngspice.txt`](20261103-060131-a520f7c-dirty-ngspice.txt)
