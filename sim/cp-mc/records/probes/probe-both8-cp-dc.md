# cp-dc run 20261103-055746-09dd595

**Result: mismatch at 1.65 V exceeds 2.0 % (2.763 %); no window around 1.65 V.** **Spec row 7 is NOT graded here.**

- **Scope**: typical corner (`mos_tt`) only, 27 C, nominal 3.3 V supply, one nominal I_cp = 200 uA. No corner grid, no Monte Carlo. **Spec row 7 is not graded:** its upper bound V_hi,req needs the VCO's graded f(Vctrl) curve (gate G4), which does not exist yet. This record lists only the measured window. The numbers are **simulated, not measured**.
- **Netlist**: `/tmp/v78/both8.spice` sha256 `dcf1e3262f096944b09452a9674a47a51df5c138ce97ab3975e2d544f103e78f` (NOT the committed netlist: an override, see CP_NETLIST)
- **Deck**: `sim/cp-dc/cp_dc.spice.tmpl` sha256 `53205b18de1f7b878562605df3c3a8a3cbc5a838d139c7a601cf838ee6e5fe78`, placeholder substitution only
- **PDK**: IHP-Open-PDK v0.3.0 (model libraries hash-checked against `sim/pins.json`); PDK_ROOT `/home/ubuntu/share/pdk`; PSP103 OSDI `psp103.osdi` sha256 `2e4299c4683997e26469410dc1ab36b02ced924b1ac0972d6c4eae360e1fc796` (pinned)
- **Simulator**: `ngspice-46` (`/home/ubuntu/.local/bin/ngspice`), one local `ngspice -b`, exit status 0; scratch `.spiceinit` = `set ngbehavior=hsa`
- **Pin check**: Pin check: ngspice-46 != pinned 47 (mismatch)
- **Commit**: `09dd595` of this repository
- **Method**: one `.dc` sweep of V_out, 1.0 V to 3.3 V in 0.05 V steps (47 points). Two copies of `cp` in the same deck: copy A has UP=1, DN=0 (I_up = current it sources into the output node); copy B has UP=0, DN=1 (I_dn = current it sinks), its output tied to copy A's by a unity VCVS. IREF = 20 uA into each copy (I_cp = ~10 x IREF; 100-400 uA is IREF 10-40 uA, not exercised here).
- **Mismatch definition**: mismatch (%) = |I_up - I_dn| / I_cp,nom x 100, with I_cp,nom = 200 uA (spec row 6 typical), at the same V_out. It is a static DC quantity: no switching, no charge sharing, no pulse-width effect.
- **Window definition**: the contiguous run of sweep points with mismatch <= 2.0 % that contains 1.65 V, extended up and down; V_top is its upper end. Endpoints are not clipped: points outside compliance are reported as measured.
- **Host**: loom-worker-1, 2026-11-03T05:57:46Z

| V_out (V) | I_up (uA) | I_dn (uA) | mismatch (% of I_cp,nom) |
|---|---|---|---|
| 1.00 | 203.255 | 190.860 | 6.198 |
| 1.05 | 203.264 | 191.513 | 5.875 |
| 1.10 | 203.270 | 192.143 | 5.563 |
| 1.15 | 203.273 | 192.752 | 5.261 |
| 1.20 | 203.273 | 193.340 | 4.966 |
| 1.25 | 203.269 | 193.910 | 4.680 |
| 1.30 | 203.262 | 194.459 | 4.401 |
| 1.35 | 203.251 | 194.989 | 4.131 |
| 1.40 | 203.236 | 195.496 | 3.870 |
| 1.45 | 203.217 | 195.979 | 3.619 |
| 1.50 | 203.193 | 196.433 | 3.380 |
| 1.55 | 203.163 | 196.854 | 3.155 |
| 1.60 | 203.127 | 197.232 | 2.947 |
| 1.65 | 203.084 | 197.559 | 2.763 |
| 1.70 | 203.035 | 197.823 | 2.606 |
| 1.75 | 202.977 | 198.020 | 2.479 |
| 1.80 | 202.912 | 198.154 | 2.379 |
| 1.85 | 202.837 | 198.239 | 2.299 |
| 1.90 | 202.753 | 198.293 | 2.230 |
| 1.95 | 202.659 | 198.328 | 2.165 |
| 2.00 | 202.551 | 198.353 | 2.099 |
| 2.05 | 202.430 | 198.371 | 2.029 |
| 2.10 | 202.292 | 198.386 | 1.953 |
| 2.15 | 202.132 | 198.398 | 1.867 |
| 2.20 | 201.947 | 198.408 | 1.769 |
| 2.25 | 201.728 | 198.418 | 1.655 |
| 2.30 | 201.465 | 198.426 | 1.519 |
| 2.35 | 201.141 | 198.434 | 1.354 |
| 2.40 | 200.733 | 198.441 | 1.146 |
| 2.45 | 200.203 | 198.448 | 0.878 |
| 2.50 | 199.492 | 198.454 | 0.519 |
| 2.55 | 198.507 | 198.460 | 0.023 |
| 2.60 | 197.095 | 198.465 | 0.685 |
| 2.65 | 195.022 | 198.470 | 1.724 |
| 2.70 | 191.939 | 198.475 | 3.268 |
| 2.75 | 187.400 | 198.479 | 5.540 |
| 2.80 | 180.934 | 198.483 | 8.775 |
| 2.85 | 172.178 | 198.486 | 13.154 |
| 2.90 | 160.975 | 198.488 | 18.757 |
| 2.95 | 147.371 | 198.490 | 25.560 |
| 3.00 | 131.536 | 198.492 | 33.478 |
| 3.05 | 113.684 | 198.493 | 42.405 |
| 3.10 | 94.017 | 198.494 | 52.238 |
| 3.15 | 72.703 | 198.494 | 62.896 |
| 3.20 | 49.870 | 198.495 | 74.312 |
| 3.25 | 25.613 | 198.496 | 86.441 |
| 3.30 | -0.000 | 198.496 | 99.248 |

ngspice log: [`20261103-055746-09dd595-ngspice.txt`](20261103-055746-09dd595-ngspice.txt)
