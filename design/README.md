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
  `scripts/fetch-pll.sh`, negative controls in `scripts/test-fetch-pll.sh`. Spec section 7 makes the
  adoption conditional on a 50 MHz re-grade; `sim/pfd/` is that re-grade. The first pin (`83e59fe`)
  failed it (reset-chain parity); the re-pin to `e71ff61` (upstream fix `sg13g2-pll#284`) passes it
  (see `sim/pfd/README.md` and its newest record). No locally designed PFD is committed.
