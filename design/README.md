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
  prescaler.sch/.sym        top: fixed /2 CML first stage + /4/5 dual-modulus, one IREF
  div2_cml.sch/.sym         /2 first stage at the VCO frequency (input emitter followers + 2 latches)
  div2_ef_hs, div2_latch_hs first-stage follower pair and latch (higher current)
  div45_dm.sch/.sym         /4/5: /2/3 cell + /2 toggle + modulus gating (MC high = /5)
  cml_div23, cml_dff, cml_latch, cml_ef, cml_and2, div2_cml_ls, mc_conv   /4/5 stage cells
  mos_latch.sch/.sym        G3 comparison only (HV-NMOS version of the CML latch); not in the prescaler
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
- **PFD**: **adopted by pin, not copied**. `reuse.lock.json` pins `2AMLogic/sg13g2-pll@83e59fe`
  `design/netlist/pfd.spice` plus the `pfd`, `edgedet`, `srlatch`, `nand2_hv`, `inv_hv`, `inv2x_hv`
  schematics and symbols (sha256-verified, fetched into the gitignored `.fetched/`):
  `scripts/fetch-pll.sh`, negative controls in `scripts/test-fetch-pll.sh`. Spec section 7 makes the
  adoption conditional on a 50 MHz re-grade; `sim/pfd/` is that re-grade and **the pinned PFD fails it**
  (see `sim/pfd/README.md`). No locally designed PFD is committed: spec section 7 requires a
  superseding decision record first.

## Prescaler (`prescaler`)

Designed here (spec row 4, section 7). Everything runs from the 3.3 V rail; the only bias input is
`IREF` (50 uA nominal): a diode-connected `npn13G2v` + 2.4 kohm reference at the top, every tail is
k x IREF (emitter-degenerated mirror). `INP`/`INN` are the tank-node inputs: the base of one
`npn13G2v` emitter follower each (Nx = 1), DC-coupled, common mode 3.3 V (the VCO tank returns to
VDD). `MC` is a CMOS-level (0/3.3 V) modulus control: low = /4, high = /5. `OUTP`/`OUTN` are CML
levels (not CMOS; the level converter belongs with the divider, #32). The schematics were emitted
by a script and are plain xschem; edit them in xschem and regenerate the netlist.

Derived from nothing in `sg13g2-pll` (spec section 7: no sibling block runs at the VCO frequency).
Resistors are ideal `res` (no PDK resistor model or parasitics yet). Sized at `hbt_typ`, 27 C, 3.3 V
only (`sim/prescaler-g1/`, `sim/prescaler-g3/`); no corner grid.

**Ratio caveat**: a fixed /2 followed by a /4/5 gives total /8 or /10, not the /8 or /9 that spec rows
3 and 4 state; see the issue filed against the spec. The cells implement /4/5 as the issue asks.

## Item-1 inventory entry

`design/netlist/prescaler.inventory.json` lists the prescaler netlist (path + sha256) for the item-1
`--inventory` file that #32 assembles. `scripts/check-prescaler-inventory.sh` fails if it is stale.
