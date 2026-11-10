# design

Schematic capture for the loop blocks owned here. The VCO is not here: it comes from
`sg13g2-vco` by pin (`reuse.lock.json`) and is never edited.

```
design/
  xschemrc            xschem config (resolves the SG13G2 PDK, adds design/ to the symbol path)
  netlist.sh          derives design/netlist/*.spice from the schematics through `klt netlist`
  netlist/cp.spice    committed derived netlist (checked by `netlist.sh --check`)
  cp.sch / .sym       charge pump top: UP/DN inverters, bias, two legs, dump buffer
  cp_bias.sch/.sym    IREF -> IBP / ICN / ICP (high-swing cascode bias per polarity)
  cp_leg_p.sch/.sym   PMOS source leg: mirror + cascode + dual steering switches
  cp_leg_n.sch/.sym   NMOS sink leg
  cp_dumpbuf.sch/.sym VDUMP tracking follower
  netlist/prescaler.spice   committed derived netlist of the prescaler (hierarchical)
  prescaler.sch/.sym        top: /2/3 dual-modulus CML first stage on the VCO, then fixed /4 (P = 8/9), one IREF
  div2_cml.sch/.sym         fixed /2 first stage (the pre-DR-005 /8-/10 prescaler; no longer instantiated)
  div2_ef_hs, div2_latch_hs first-stage follower pair and latch (higher current)
  div89_dm.sch/.sym         /8/9: /2/3 cell on the VCO + two /2 stages; M = MC AND S1 AND S2 (MC high = /9)
  div45_dm.sch/.sym         /4/5 (pre-DR-005, no longer instantiated): /2/3 cell + /2 toggle + modulus gating
  cml_div23, cml_dff, cml_latch, cml_ef, cml_and2, div2_cml_ls, mc_conv   prescaler cells
  mos_latch.sch/.sym        G3 comparison only (HV-NMOS version of the CML latch); not in the prescaler
  loopfilter.sch/.sym       type-II 3rd-order passive filter (R1-C1, C2, R3-C3), values from sim/loop-model/loop-filter.json
  cml2cmos.sch/.sym         prescaler CML output -> CMOS clock
  mcounter.sch/.sym         program counter M (4-bit down counter, loads M at terminal count)
  dff_tg_hv_qn.sch/.sym     pinned dff_tg_hv with the slave node brought out as QN; used by mcounter bit 2 only (issue #97)
  acounter.sch/.sym         swallow counter A (2-bit down counter, MC = count != 0)
  divider.sch/.sym          cml2cmos + mcounter + acounter + retimed feedback flop
  vco.sym                   BLACK-BOX interface symbol for the pinned sg13g2-vco (no schematic, no .subckt emitted)
  pll_top.sch/.sym          loop top: pfd, cp, loopfilter, vco, prescaler, divider, lock_detector
```

## Deriving the netlist

```bash
design/netlist.sh            # regenerate design/netlist/cp.spice
design/netlist.sh --check    # regenerate to a temp dir and diff; exit 1 if the committed copy is stale
```

The underlying command, for one block (never raw `xschem`; `klt netlist` forces the headless
flags and kills a hung run):

```bash
PDK=ihp-sg13g2 PDK_ROOT=<parent of ihp-sg13g2> klt netlist --backend local --block \
    --rcfile design/xschemrc -o <out>.spice design/cp.sch
```

`netlist.sh` then rewrites the absolute `** sch_path:` / `** sym_path:` stamp comments to
repo-relative form so the committed bytes do not depend on the checkout. `scripts/run-cp-dc.sh`
and `scripts/run-pfd-sweep.sh` both refuse to run if `--check` reports the committed netlist stale.

## Provenance

- **Charge pump (`cp*`)**: designed here, starting from the topology of `sg13g2-pll`'s
  `cp` / `cp_leg_p` / `cp_leg_n` / `cp_dumpbuf` at `83e59fe` (spec section 7: "keep, design here").
  Changes: the bias generation is inside the block (`cp_bias`, one input `IREF`); mirror and cascode
  retargeted so I_cp is about 200 uA at IREF = 20 uA (spec row 6). I_cp scales with IREF; 100-400 uA
  is IREF 10-40 uA, and there is **no on-chip trim DAC** yet. Every device is `sg13_hv_nmos` /
  `sg13_hv_pmos`. Sized at the typical corner and nominal supply only (`sim/cp-dc/`); no corner grid.
- **PFD**: **adopted by pin, not copied**. `reuse.lock.json` pins `2AMLogic/sg13g2-pll@e71ff61`
  `design/netlist/pfd.spice` plus the `pfd`, `edgedet`, `srlatch`, `nand2_hv`, `inv_hv`, `inv2x_hv`
  schematics and symbols (sha256-verified, fetched into the gitignored `.fetched/`):
  `scripts/fetch-pll.sh`, negative controls in `scripts/test-fetch-vco.sh 2AMLogic/sg13g2-pll fetch-pll.sh design/pfd.sch`. Spec section 7 makes the
  adoption conditional on a 50 MHz re-grade; `sim/pfd/` is that re-grade. The first pin (`83e59fe`)
  failed it (reset-chain parity); the re-pin to `e71ff61` (upstream fix `sg13g2-pll#284`) passes it
  (see `sim/pfd/README.md` and its newest record). No locally designed PFD is committed.

## Prescaler (`prescaler`)

Designed here (spec row 4, section 7). Everything runs from the 3.3 V rail; the only bias input is
`IREF` (50 uA nominal): a diode-connected `npn13G2v` + 2.4 kohm reference at the top, every tail is
k x IREF (emitter-degenerated mirror). `INP`/`INN` are the tank-node inputs: the base of one
`npn13G2v` emitter follower each (Nx = 1), DC-coupled, common mode 3.3 V (the VCO tank returns to
VDD). `MC` is a CMOS-level (0/3.3 V) modulus control: low = /8, high = /9. `OUTP`/`OUTN` are CML
levels (not CMOS; the level converter belongs with the divider, #32). The schematics were emitted
by a script and are plain xschem; edit them in xschem and regenerate the netlist.

Derived from nothing in `sg13g2-pll` (spec section 7: no sibling block runs at the VCO frequency).
Resistors are PDK `rppd` / `rhigh` instances (issue #164; no ideal `R` card remains in `prescaler`, `mos_latch`,
`divider`, `pll_top`). `sim/prescaler-g1/` and `sim/prescaler-g3/` records predate this change (ideal `R`, nominal only;
the g1 bench probes nodes the /8-/9 prescaler no longer has and was not re-run; the g3 chain deck drove the old /4/5 second
stage and is retired (DR-006); the g3 pairs bench was re-run with the PDK resistors, see `sim/prescaler-g3/records/`); the /8-/9 corner grid with PDK resistors is
`sim/prescaler-div89/records/*-pdk-resistors.md`. With the resistor corner models loaded (`cornerRES.lib`, `r3_cmc.osdi`) the
divider corners are `sim/divider-elab/records/20261110-pdk-resistors-2022314-corners.md` (0 wrong N, 11 of 54 not graded: 125 C
no toggle, a few non-converged; INCOMPLETE as before, 16 not graded then) and the loop-power stage 2 is
`sim/corner-verification/loop-power/records/20261110-051905-2022314-stage2.md` plus `20261110-053343-2022314-stage2.md` (-40 C).

**Resistor devices (issue #164).** Values are the unchanged ideal values; W/L were set from the `r3_cmc` model's own DC
resistance at `res_typ`, 27 C (R = ~70 ohm end resistance + ~257 ohm/um x L at W = 1 um for `rppd`; ~327 ohm + ~3240 ohm/um at
W = 0.5 um for `rhigh`). Drawn width 2 um is used on the two tail values (600, 1200 ohm) to cut the relative width error;
everything else is W = 1 um `rppd`. `rhigh` is used only for the 50 k / 100 k bias and feedback values, where `rppd` would
need about 190 / 380 um of length. Squares = L/W. Tolerance is the PDK corner spread of sheet resistance: `rppd` 234 / 260 /
286 ohm per square (`res_bcs` / `typ` / `wcs`), `rhigh` 1020 / 1360 / 1700. The model includes the area/perimeter parasitic
capacitance of each resistor; it was not separately extracted per resistor, only exercised in the corner runs below.

| value (ohm) | where | device | W (um) | L (um) | squares | modelled R (ohm, typ 27 C) |
|---|---|---|---|---|---|---|
| 600 | `cml2cmos` tail RT | `rppd` | 2 | 4.4 | 2.2 | 603.6 |
| 1200 (1.2k) | CML tails RT / RTC (`cml_latch`, `cml_and2`, `div2_latch_hs`), `prescaler` RT, `mc_conv` RT | `rppd` | 2 | 9.05 | 4.5 | 1204.5 |
| 1500 | `div2_latch_hs` RL (not instantiated) | `rppd` | 1 | 5.57 | 5.6 | not run (model fit ~1500) |
| 2400 (2.4k) | CML loads RL, followers RF, RREF, RTC, `mc_conv` RL | `rppd` | 1 | 9.05 | 9.1 | 2398 (9.07 um: 2400.3) |
| 4k | `cml_ef` / `div2_ef_hs` RDF | `rppd` | 1 | 15.3 | 15.3 | 4001 |
| 12k, 28k | `mc_conv` RD1, RD2 | `rppd` | 1 | 46.4, 108.8 | 46 / 109 | 11991 / 28023 |
| 20k | `mc_conv` RIN | `rppd` | 1 | 77.7 | 78 | 20032 |
| 50k | `cml2cmos` RB1, RB2, RV1, RV2 | `rhigh` | 0.5 | 15.35 | 31 | 50025 |
| 100k | `cml2cmos` RF1 | `rhigh` | 0.5 | 30.8 | 62 | 100054 |

The "71" of the issue title does not reproduce; the netlist cards were enumerated directly (27 in `prescaler`, 2 in
`mos_latch`, 6 in `divider`, 33 in `pll_top`, which embeds the others). In `sim/prescaler-div89` the resistor corner is
tied to the HBT corner (SLOW = `hbt_wcs` + `res_wcs`).

**Result of the swap (simulated):** `/8` and `/9` hold at 5.0 GHz at all 54 chain corners, and at 5.5 GHz at every corner
except SLOW / 125 C (all three supplies), where the 5.5 GHz `/8` and `/9` fail (output period about 10 input periods;
0/16 async phases pass at 2.97 and 3.63 V). The same grid passed with ideal resistors. This is a failing 5.5 GHz corner,
not relaxed here. Not re-run: the divider corner records, the VCO-load (G2) and loop-power records, and the g1
bench; see the PR for the list.

**Architecture (issue #158, `spec/decision-records/DR-005-prescaler-p89-div23-first-stage.md`)**: `div89_dm`
puts the `cml_div23` /2/3 cell on the VCO (its input pair is the same `cml_ef` follower pair as the old /2, one
`npn13G2v` Nx = 1 base per side) and follows it with two `div2_cml_ls` /2 stages. `M = MC AND S1 AND S2` (two
`cml_and2` levels, `S1` through a `cml_ef`) is high for exactly one /2/3 output period in four, so MC high swallows
one VCO cycle per prescaler period: /8 with MC low, /9 with MC high. `S1`/`S2` are a ripple counter (S2 toggles on S1), so the states step 00, 01, 10, 11 with S1 falling before S2 changes: by
design `M` cannot see a spurious 11. The async-phase runs below check that, they do not prove it. The earlier /8-/10 build (`div2_cml` then
`div45_dm`) is kept in the tree but not instantiated. Simulated at `sim/prescaler-div89/`.

## Loop blocks (`loopfilter`, `divider`, `pll_top`)

Item-1 sources for the rest of the loop (issue #32). The schematics were emitted by a script and are
plain xschem; edit them in xschem and regenerate the netlists (`design/netlist.sh`).

**Loop filter.** `loopfilter` is `sim/loop-model/loop-filter.json` as devices: `VIN` -R1- node -C1- `VSS`
(zero), C2 `VIN` to `VSS`, then the unloaded pole `VIN` -R3- `VCTRL` -C3- `VSS`. R1 = R3 = 7035.6 ohm,
C1 = 90.48 pF, C2 = 6.032 pF, C3 = 2.828 pF (the JSON, not spec section 7's "R1 about 6.5 kohm": the spec
number is the older estimate and the JSON is the sizing source; `spec/` is not edited here). Devices:
`rppd` (260 ohm/sq, w = 2 um, l = 53.9 um) and `cap_cmim` (1.5 fF/um2; C1 is 12 x 70.9 um square because a
`cap_cmim` PCell is capped at 8 pF). Sizing is by square count and area density: the as-drawn values are
about 7.0 kohm, 90.48 / 6.03 / 2.83 pF (C2 and C3 are 0.05 % and 0.09 % low from the 5 nm grid). The `rppd`
end resistance, the MIM sidewall term and corner spread are not modelled here; they belong to the
filter's simulation (#34). Connected to a high-impedance VCO input, so the model's "unloaded R3-C3" holds
only as far as the varactor's DC load is negligible.

**Divider.** `divider` takes the prescaler's CML `OUTP`/`OUTN`, converts them to a CMOS clock (`cml2cmos`:
HV-NMOS pair, PMOS mirror, tail 4 x `IREF` from the prescaler reference node, two inverters), and runs a
pulse-swallow counter: `mcounter` counts `M` clocks (loads `M[3:0]` when Q = 0001), `acounter` holds `A`
(3 bits, A0..A2) and drives `MC` high for `A` clocks after each load. With the prescaler's P = 8 (`MC` low) or
9 (`MC` high), **N = 8 M + A, A in [0, 7]**, every integer N reachable provided M >= A (DR-005; spec row 3). N = 100
is M = 12 (1100), A = 4 (100); the stretch band's bounds are N = 90 (M = 11, A = 2) and N = 110 (M = 13, A = 6). The
counter needs M >= A, and M >= 3 for the registered terminal count. `FB` is the terminal-count pulse retimed by one
`CK` flop (one prescaler-output period wide). `M0..M3` and `A0..A2` are static code inputs; `pll_top` ties them for
N = 100. The code-to-N map of the netlist (tied code, reachability of 90-110, `acounter` holding MC high for exactly
A clocks) is checked from the committed netlist by `sim/prescaler-div89/test_divider_code.py`: a zero-delay logic
check, not a timing or corner result.

The counter cells are the pinned `sg13g2-pll` cells (`dff_tg_hv`, `xor2_hv`, `nand2_hv`, `nand3_hv`, `nor2_hv`,
`inv_hv`, `tgate_hv`; `reuse.lock.json`, fetched and sha256-verified): adopted, with the swallow logic designed
here, since the sibling `divider_chain` is a /2/3 cascade, not an M/A counter. Their sizing is the sibling's
first-pass sizing; speed at the prescaler output frequency (the prescaler divides 5.0 GHz by 8, so the
first counter stage sees 625 MHz) is **not claimed here**; it is graded by #34 / #39.

**Lock detector.** `lock_detector` is adopted by pin (`sg13g2-pll@e71ff61`, with `delaywin_hv`, `schmitt_hv`,
`xor2_hv` and their cells), instantiated unmodified in `pll_top` on `UP`/`DN`. Spec section 7 makes the
adoption conditional on a 50 MHz re-grade (gate G5). That re-grade is recorded in [`sim/lock-detector/`](../sim/lock-detector/README.md) (simulated; nominal and the C-grid, no layout): the delay window clears the 2.5 ns floor, but the lock thresholds sit at 25-50 % of T_ref and `LOCK` is active-low as netlisted, so the cell is adopted with that finding, not as a graded pass.

**Top.** `pll_top` wires `REF` -> `pfd` -> `cp` -> `loopfilter` -> `vco` -> `prescaler` -> `divider` -> `pfd`
(`FB`), with `lock_detector` on `UP`/`DN`. Ports: `REF`, `IREFCP` (charge pump, 20 uA), `IREFPS` (prescaler
and divider tails, 50 uA), `LOCK`, `VCTRL`, `FB`, `VDD`, `VDDV` (VCO supply branch, tie to `VDD` in a
testbench: the isolation network of spec section 5 is not designed here), `VSS`. The netlist is
self-contained except for the VCO.

**The VCO is a black box in the top, on purpose.** The pinned `sg13g2-vco` has no symbol and no `.subckt`:
its `design/vco.spice` is a flat bench (supply and control sources, a `.control` block, `@@` placeholder
tokens), so it cannot be instantiated as a block unmodified, and CLAUDE.md forbids forking it. `design/vco.sym`
is a `type=primitive` interface symbol (`VCTRL OUTP OUTN VDD VSS`, the nets of the pinned netlist) so the top
carries one `XVCO ... vco` instance line and no stub `.subckt`. A loop testbench must supply `vco` itself
(for example by wrapping the pinned file's device lines in a `.subckt vco VCTRL OUTP OUTN VDD VSS`, without
editing the pinned bytes). The gap is filed on `sg13g2-vco` (see the PR).

**Speed (issue #61).** The first-pass counters did not divide at the prescaler output rate (bisect: `sim/divider-elab/records/20261103-bisect-issue61.md`; the `mcounter` next-state logic, about eight gates deep, stopped between 520 and 550 MHz). Fixed by retiming, with the adopted cells unchanged: `mcounter` now registers its terminal count (`TC`/`TCN` are flop outputs, high exactly when Q = 0001) and per-bit borrow flags (`b1..b3`, lower bits of Q are zero), so every flop-to-flop path is at most three gates; `acounter` has a three-gate-deep next state (two-gate in the 2-bit version; 3 bits since PR #161) with a registered `MC`; the extra clock load on `cml2cmos` is isolated by a one-inverter-plus-three-parallel-`inv_hv` buffer (`CK` -> `CKL`) in `divider`. Requires **M >= 3** (the registered terminal count assumes Q = 0001 is not the loaded value). Verified by `scripts/run-divider-elab.sh`: FB divides N = 100 at 625 and 687.5 MHz through the real `cml2cmos` (simulated, nominal corner `hbt_typ`/`mos_tt`/`cap_typ`, 27 C, 3.3 V, not measured). A prototype of the counter alone divided by 12 at 800 MHz and failed at 900 MHz (nominal, ideal clock; scratch, not a committed record). A = 0 (N = 96) and A = 3 (N = 102) at M = 12 also divide at both rates through the real converter (separate deck `divider_speedA`, same script; simulated, nominal corner, not measured). Not done: any corner other than nominal (the C-grid is #39's `klt sim` envelope work).

**Checks.** `scripts/run-divider-elab.sh` elaborates the divider for five N codes (100, 90, 110, A = 0, A = 3) and counts
`FB` period and `MC`-high clocks for N = 100 and 90 at a relaxed 100 MHz clock, then runs the speed check (625 and 687.5 MHz, real chain and an ideal-clock bisect control, nominal corner), writing an append-only
record under `sim/divider-elab/records/`. It found two real defects while this was written (a DC-coupled level converter that
could not reach the inverter threshold, and a case-insensitive net-name collision between a port `A0` and a state bit `a0`);
SPICE names are case-insensitive, so keep port and internal net names distinct. Item-1 attestation:
`manifests/design-sources.inventory.json` -> `manifests/design-sources.attest.json` (`klt signoff --attest 1`).
