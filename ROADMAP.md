# Roadmap

An integer-N LC PLL on IHP SG13G2 that closes a loop around the pinned `sg13g2-vco`; this file says
where the block stands against its ratified targets and the T1 checklist, and what comes next.

**Status as of 2026-11-13, `main` @ `22168ca`.** Every number below is simulated, never measured.
`WORK_PLAN.md` is the label-state queue and `WORK_LOG.md` the merge history; this file is the plan
they do not carry. The verdict of record is `manifests/sg13g2-lc-pll.signoff.json`.

## Where it stands

**Not-T1: 5 of 11 T1 items met** (`klt signoff`, `klayout-tools==0.8.0`).

| T1 item | Status | Evidence / what is missing |
|---|---|---|
| 1 Design sources | met | `manifests/design-sources.attest.json` |
| 2 Layout | met | `layout/top.gds`, `manifests/layout.attest.json` (placement-level routing, supplies not routed) |
| 3 DRC clean | met | `layout/drc/top.drc.json`, clean for the layers the deck covers (PR #248) |
| 4 LVS clean | unmet | first envelope is `mismatch` (`layout/lvs/top.lvs.json`): the hierarchical reference does not pair with the flat extraction; #37 |
| 5 Corner verification | unmet | row 6 stage 1 passes, stage 2 fails; rows 1, 5, 7, 8, 9, 10, 11 are declared gaps; #39, #86 |
| 6 Monte Carlo | unmet | charge-pump campaign fails the row 7 mismatch target (`sim/cp-mc/records/`); #82 |
| 7 Post-layout | unmet | no `klt pex` run; #41 |
| 8 Characterization | unmet | `measurements/characterization.md` is a skeleton, 0 of 14 rows over the C-grid; #48 |
| 9 Testbenches | met | `manifests/testbenches.attest.json`; the cold start was carried, not re-run (#149, #242) |
| 10 Repo hygiene | met | `manifests/repo-hygiene.attest.json` |
| 11 Power delivery | unmet | no `klt erc` supply spec; #38 |

Spec gates (`spec/target-spec.md` §Gates):

- **G1** device-level input load recorded: 1.837 fF differential at 5.0 GHz against the 2.1 fF
  budget, routing excluded (`sim/prescaler-div89/records/`). **G3** closed by DR-002. **G8** recorded
  in `layout/README.md`; `klayout-tools#3849` is closed.
- **G2 open, and it is the largest finding in the repo.** With the pinned VCO (`sg13g2-vco@17e49a8`)
  the C-grid records in `sim/corner-verification/vco-prescaler-load/records/` show 0 corners inside
  the 4.5-5.5 GHz band, loaded or unloaded (3.67-4.32 GHz in the 2026-11-10 records), and 125 C units that abort or fall below
  the 0.40 Vpp swing floor. Row 1 (5.0 GHz) cannot close on this pin.
- **G4 open upstream** (`sg13g2-vco#50`, `#53`): no graded f(Vctrl), so V_hi,req and local Kvco are unknown.
- **G5** lock detector re-graded at 50 MHz, nominal and C-grid (`sim/lock-detector/records/`); the PFD
  record at 50 MHz is nominal only.
- **G6 open** (#88; PR #93 held). **G7 not started**: no supply-isolation simulation and no issue.

Design findings that are open:

- The divider stops dividing at 125 C; traced to the M-counter terminal-count path (#197, #199, #97).
- Tank-node routing in the current floorplan is estimated at 73 fF / 53 fF against 2.1 fF
  (`layout/provenance.json` `tank_node_estimate`; geometric, not extracted).
- Three keep-out violations, all the VCTRL pin-access stack; the upstream change (`sg13g2-vco#314`)
  and the tool gap (`klayout-tools#5198`) are both closed, but the pin here predates them.

## In flight (claimed; not available)

PRs #269 (#260), #270 (#263), #271 (#268), #265 (#261) are in review; #262 (DR-007, #252) is approved.

## Now

Unblocked, one PR each, none needs the PDK. None has an issue yet; drafts exist for the first four.

1. **Bring `README.md` status in line with the verdict of record.** The README still says "Nothing is
   designed or simulated yet" and places the block at "spec ratified". Done when the status line and
   ladder position match `manifests/sg13g2-lc-pll.signoff.json`, `layout/lvs/README.md` no longer says
   DRC is `violations`, and item 10 is re-stamped (`scripts/restamp-attest.sh 10`).
2. **Enumerate the M/A counter state sequence for N = 90-110.** The last note on #97 names this as the
   step before any look-ahead or registered terminal-count decode. Done when a PDK-free script and
   test under `sim/divider-elab/` print, per N, the state sequence and whether the state before the
   terminal count is always visited, and a record states which decode options that leaves valid for #199.
3. **Record the delta between the VCO pin and `sg13g2-vco` main.** Done when a dated record lists, per
   file in `reuse.lock.json`, whether its sha256 differs at upstream `main`, whether the VCTRL top-metal
   pin of `sg13g2-vco#314` is present, and which records and attestations here a pin bump would invalidate.
4. **Settle the row 5 item-5 citation.** `manifests/sg13g2-lc-pll.json` declares row 5 a gap because a
   method-L record could not be cited (`klayout-tools#4859`, now closed). Done when either the manifest
   cites `sim/loop-model/records/*row5-envelope*` and the verdict is regenerated, or the gap text names
   the `klt` version that is needed and why the pin cannot move yet.
5. **Route the supply nets in `gen_integrated.py`** (VDD, VDDV, VSS; `layout/README.md` lists them as not
   routed). Done when the nets are routed, `scripts/test-layout-top.sh` passes and DRC is re-run and
   still `clean`. Needs a PDK host and a re-stamp of items 2 and 3, so it wants a Curator pass to size it.

## Next

- **Divider fix at 125 C** (#199): needs Now 2 and the hold on PR #200 lifted. Done when the 54-unit
  corner grid of `sim/divider-elab/` grades every unit as dividing.
- **Row 11 C-grid envelope** (#97, part of #39): after #199.
- **Method-N bench for the in-band noise terms** (#253): after #252 merges through PR #262. Done when
  `run-jitter.sh` runs with all three in-band terms supplied and reports no missing term.
- **G6 transient-noise cost record** (#88, PR #93): after #149.
- **Real item-9 cold start enforced in CI** (#242) and the inventory clause (#237): after #149.
- **VCO pin bump**: after Now 3, if the delta shows a usable change. Done when `reuse.lock.json` moves,
  `scripts/run-vco-smoke.sh` writes a new record, and the keep-out record in `layout/README.md` is re-run.
- **LVS match** (#37): needs `klayout-tools#5406` (open) for a hierarchical subcircuit-call reference,
  and Now 5 so the supplies exist in the layout.
- **ERC supply spec** (#38) and **PEX delta** (#41): after #37.
- **Rows 1, 9, 10 with the real VCO, prescaler and counters** (#86): after G4 upstream, G2 and #199.

## Later

- **Close row 1 at 5.0 GHz.** Question first: does the band shortfall get fixed in `sg13g2-vco` (a tank
  retarget, request R-VCO-1 of DR-001) or by a superseding record here? No upstream issue was found
  open for it on 2026-11-13.
- **Tank-node floorplan.** Question first: can the prescaler input sit within tens of micrometres of
  the tank pins without breaking the 20 um keep-out, or does the loop need the buffer of spec §6 Q1?
- **G7 supply isolation.** Question first: what quantity and limit grade the VCO branch against VCO
  row 9, given that the pinned VCO does not yet run in band.
- **Row 11 completeness.** Reference and clock buffering are not in the design
  (`sim/testbench-inventory.md`); question first: are they in this block or the wrapper's.
- **Characterization report** (#48): after items 5, 6 and 7 have envelopes to cite.
- **Shuttle seat, measured silicon**: the last two rungs of the README ladder; nothing scheduled.

## Blocked and waiting

- **Decisions pending on the tracker:** #173 (how to treat the loaded 125 C units that abort), #149
  (PSP NQS model in the divider speed decks; blocks #88, #242, #237), #82 with PR #138 (row 7 mismatch
  limit and yield), PR #207 (DR-006, clock-output row), PR #200 (125 C trace record), PR #179 (#178),
  and the removal proposals #219, #223, #227, #250.
- **Upstream:** `sg13g2-vco#50` and `#53` (G4); `klayout-tools#5406` (LVS reference form).
- **Tracker hygiene:** the checklist in #5 still reads as of 2026-10-17 with every box open; the
  record in `manifests/` supersedes it.

The tracker has no ready, unclaimed issue today: every open issue is in progress, blocked, held for
a decision, or an unapproved proposal (#272, #143, #146). The Now list above is the available work.

## Not planned

- Redesigning, resizing or forking the VCO: it is consumed by pinned reference; changes are raised on `sg13g2-vco`.
- Fractional-N, and the full 4.5-5.5 GHz band before the single 5.0 GHz channel closes.
- Relaxing a ratified row to make a result pass; a row changes only by a superseding decision record.
- A hand-flattened LVS reference: it would be a second, unreviewed netlist (`layout/lvs/README.md`).
