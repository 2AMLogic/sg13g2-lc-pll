# cp-dc run 20261103-060129-a520f7c-dirty

**Result: mismatch at 1.65 V exceeds 2.0 % (2.778 %); no window around 1.65 V.** **Spec row 7 is NOT graded here.**

- **Scope**: typical corner (`mos_tt`) only, 27 C, nominal 3.3 V supply, one nominal I_cp = 200 uA. No corner grid, no Monte Carlo. **Spec row 7 is not graded:** its upper bound V_hi,req needs the VCO's graded f(Vctrl) curve (gate G4), which does not exist yet. This record lists only the measured window. The numbers are **simulated, not measured**.
- **Netlist**: `/tmp/v78/t_3.2u.spice` sha256 `1feaf3f21038eb876366c7b9a0f606f06f2def9ce0857b3102e0ac525d6b00db` (NOT the committed netlist: an override, see CP_NETLIST)
- **Deck**: `sim/cp-dc/cp_dc.spice.tmpl` sha256 `53205b18de1f7b878562605df3c3a8a3cbc5a838d139c7a601cf838ee6e5fe78`, placeholder substitution only
- **PDK**: IHP-Open-PDK v0.3.0 (model libraries hash-checked against `sim/pins.json`); PDK_ROOT `/home/ubuntu/share/pdk`; PSP103 OSDI `psp103.osdi` sha256 `2e4299c4683997e26469410dc1ab36b02ced924b1ac0972d6c4eae360e1fc796` (pinned)
- **Simulator**: `ngspice-46` (`/home/ubuntu/.local/bin/ngspice`), one local `ngspice -b`, exit status 0; scratch `.spiceinit` = `set ngbehavior=hsa`
- **Pin check**: Pin check: ngspice-46 != pinned 47 (mismatch)
- **Commit**: `a520f7c-dirty` of this repository
- **Method**: one `.dc` sweep of V_out, 1.0 V to 3.3 V in 0.05 V steps (47 points). Two copies of `cp` in the same deck: copy A has UP=1, DN=0 (I_up = current it sources into the output node); copy B has UP=0, DN=1 (I_dn = current it sinks), its output tied to copy A's by a unity VCVS. IREF = 20 uA into each copy (I_cp = ~10 x IREF; 100-400 uA is IREF 10-40 uA, not exercised here).
- **Mismatch definition**: mismatch (%) = |I_up - I_dn| / I_cp,nom x 100, with I_cp,nom = 200 uA (spec row 6 typical), at the same V_out. It is a static DC quantity: no switching, no charge sharing, no pulse-width effect.
- **Window definition**: the contiguous run of sweep points with mismatch <= 2.0 % that contains 1.65 V, extended up and down; V_top is its upper end. Endpoints are not clipped: points outside compliance are reported as measured.
- **Host**: loom-worker-1, 2026-11-03T06:01:29Z

| V_out (V) | I_up (uA) | I_dn (uA) | mismatch (% of I_cp,nom) |
|---|---|---|---|
| 1.00 | 203.304 | 190.860 | 6.222 |
| 1.05 | 203.312 | 191.513 | 5.900 |
| 1.10 | 203.317 | 192.143 | 5.587 |
| 1.15 | 203.320 | 192.752 | 5.284 |
| 1.20 | 203.318 | 193.340 | 4.989 |
| 1.25 | 203.314 | 193.910 | 4.702 |
| 1.30 | 203.305 | 194.459 | 4.423 |
| 1.35 | 203.293 | 194.989 | 4.152 |
| 1.40 | 203.277 | 195.496 | 3.890 |
| 1.45 | 203.255 | 195.979 | 3.638 |
| 1.50 | 203.229 | 196.433 | 3.398 |
| 1.55 | 203.197 | 196.854 | 3.172 |
| 1.60 | 203.159 | 197.232 | 2.963 |
| 1.65 | 203.115 | 197.559 | 2.778 |
| 1.70 | 203.063 | 197.823 | 2.620 |
| 1.75 | 203.004 | 198.020 | 2.492 |
| 1.80 | 202.937 | 198.154 | 2.392 |
| 1.85 | 202.861 | 198.239 | 2.311 |
| 1.90 | 202.776 | 198.293 | 2.242 |
| 1.95 | 202.681 | 198.328 | 2.176 |
| 2.00 | 202.573 | 198.353 | 2.110 |
| 2.05 | 202.451 | 198.371 | 2.040 |
| 2.10 | 202.313 | 198.386 | 1.964 |
| 2.15 | 202.154 | 198.398 | 1.878 |
| 2.20 | 201.969 | 198.408 | 1.781 |
| 2.25 | 201.752 | 198.418 | 1.667 |
| 2.30 | 201.490 | 198.426 | 1.532 |
| 2.35 | 201.169 | 198.434 | 1.368 |
| 2.40 | 200.765 | 198.441 | 1.162 |
| 2.45 | 200.241 | 198.448 | 0.897 |
| 2.50 | 199.540 | 198.454 | 0.543 |
| 2.55 | 198.567 | 198.460 | 0.054 |
| 2.60 | 197.175 | 198.465 | 0.645 |
| 2.65 | 195.129 | 198.470 | 1.671 |
| 2.70 | 192.083 | 198.475 | 3.196 |
| 2.75 | 187.590 | 198.479 | 5.445 |
| 2.80 | 181.171 | 198.483 | 8.656 |
| 2.85 | 172.455 | 198.486 | 13.015 |
| 2.90 | 161.278 | 198.488 | 18.605 |
| 2.95 | 147.679 | 198.490 | 25.405 |
| 3.00 | 131.832 | 198.492 | 33.330 |
| 3.05 | 113.953 | 198.493 | 42.270 |
| 3.10 | 94.246 | 198.494 | 52.124 |
| 3.15 | 72.884 | 198.494 | 62.805 |
| 3.20 | 49.996 | 198.495 | 74.250 |
| 3.25 | 25.678 | 198.496 | 86.409 |
| 3.30 | -0.000 | 198.496 | 99.248 |

ngspice log: [`20261103-060129-a520f7c-dirty-ngspice.txt`](20261103-060129-a520f7c-dirty-ngspice.txt)
