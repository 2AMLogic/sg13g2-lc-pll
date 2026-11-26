# Work Plan

Backlog snapshot from current GitHub label state, maintained by the Guide role.
Direction lives in the hand-written roadmap: [`ROADMAP.md`](ROADMAP.md).

The body below is a snapshot of GitHub label state as of the last merged docs-maintenance PR — it may lag live labels until the next one merges. The `_Generated:` stamp at the top of the generated region dates the snapshot; `git log -1 -- WORK_PLAN.md` finds the merge that wrote it.

<!-- Maintained automatically by the Guide triage agent. Manual edits are fine but may be overwritten. -->

<!-- guide:plan-body:start -->
_Generated: 2026-11-26T16:45:50Z (snapshot; compare against live labels)_
## Operator Attention: Merge-Risk-Hold Pileup

Judge-approved PRs under a hold (`loom:blocked` or `loom:operator`) — only a human merge decision is missing.

- **#200**: docs(sim): trace two missed terminal-count captures in the hot divider
- **#207**: docs(spec): add clock-output interface row 15 and DR-006, stated as not met
- **#262**: docs(spec): add DR-007 — reference noise mask, in-band split, method N narrowed to the charge pump

## Very Important

`loom:very-important` (one counts per workspace); every stage takes these first.

- **#149**: Divider speed decks use PSP RF models but never load psp103_nqs.osdi (attest 9 fails on a clean host) *(held)*

## Important

`loom:important`; taken before unlabelled work.

- **#37**: T1 item 4 (LVS clean): klt lvs of the integrated layout vs the top netlist (npn13G2v recognized) *(held)*
- **#38**: T1 item 11 (power delivery): klt erc supply spec for the section-5 supply branches *(held)*
- **#39**: T1 item 5 (corner verification): klt sim envelopes over C-grid for every target row *(held)*
- **#41**: T1 item 7 (post-layout): klt pex delta report for the integrated loop *(held)*
- **#48**: T1 item 8 (characterization): per-row characterization report over the DR-001 rows, attested with klt signoff --attest 8 *(held)*
- **#86**: Item 5 remainder (gated): C-grid envelopes for rows 1, 8, 9, 10 and row 7 upper edge *(held)*
- **#97**: Divider/prescaler stops dividing at 3.630 V and 125 C corners (row 11 C-grid) *(held)*
- **#199**: Divider M-counter terminal-count path fails setup at 125C (7 of 54 corner units) *(held)*
- **#350**: layout: nothing asserts the per-cell routing record, so a routed cell regressing to partial lands green (plus dead chain_links helper)

## Ready

Human-approved issues ready for implementation (`loom:issue`).

- **#350**: layout: nothing asserts the per-cell routing record, so a routed cell regressing to partial lands green (plus dead chain_links helper)

## In Progress

Issues currently being built (`loom:building`).

- **#88**: G6: measure transient-noise cost versus run length for method T
- **#206**: spec: state clock output swing and load for a downstream TX mux
- **#343**: layout: route the charge-pump and loop-filter cells and LVS each against its own subcircuit (first slice of intra-cell routing for item 4)

## PRs Awaiting Review

PRs waiting on Judge (`loom:review-requested`).

_None._

## Approved (Awaiting Merge)

PRs that passed review and are queued for Champion auto-merge (`loom:pr`).

- **#200**: docs(sim): trace two missed terminal-count captures in the hot divider
- **#207**: docs(spec): add clock-output interface row 15 and DR-006, stated as not met
- **#262**: docs(spec): add DR-007 — reference noise mask, in-band split, method N narrowed to the charge pump

## Proposed

Issues carrying `loom:curated`.

- **#37**: T1 item 4 (LVS clean): klt lvs of the integrated layout vs the top netlist (npn13G2v recognized) *(curated)* *(held)*
- **#39**: T1 item 5 (corner verification): klt sim envelopes over C-grid for every target row *(curated)* *(held)*
- **#48**: T1 item 8 (characterization): per-row characterization report over the DR-001 rows, attested with klt signoff --attest 8 *(curated)* *(held)*
- **#88**: G6: measure transient-noise cost versus run length for method T *(curated)*
- **#97**: Divider/prescaler stops dividing at 3.630 V and 125 C corners (row 11 C-grid) *(curated)* *(held)*
- **#149**: Divider speed decks use PSP RF models but never load psp103_nqs.osdi (attest 9 fails on a clean host) *(curated)* *(held)*
- **#178**: Stale sim/prescaler-g3: drives the old /4-/5 stage, not the merged /8-/9 prescaler *(curated)* *(held)*
- **#206**: spec: state clock output swing and load for a downstream TX mux *(curated)*
- **#237**: Retire the stale smoke-record clause in sim/testbench-inventory.json (needs a re-attestation #228 could not run locally) *(curated)* *(held)*
- **#252**: Spec section 4: state the reference phase-noise requirement and define method N for the switching blocks (decision record) *(curated)* *(held)*
- **#277**: README status line and ladder position contradict the signoff record (still says "Nothing is designed or simulated yet") *(curated)* *(held)*
- **#343**: layout: route the charge-pump and loop-filter cells and LVS each against its own subcircuit (first slice of intra-cell routing for item 4) *(curated)*
- **#461**: Re-stamp layout/provenance.json inputs.gen_integrated.sha256 on a PDK host *(curated)* *(held)*

## Proposed (Architect / Hermit)

- **#143**: Stop tracking 19 regenerable loop-power probe request JSONs (extends #106) *(hermit)* *(held)*
- **#146**: Consolidate crossing-probe boilerplate across 11 loop-power make_*_97 generators *(hermit)* *(held)*
- **#435**: Remove archived /4/5 prescaler cells (div45_dm, div2_cml and its two sub-cells): unused since DR-005 *(hermit)* *(held)*

## Epics

_None._

## Backlog Balance

| Bucket | Count |
|------|-------|
| Operator merge-risk holds | 3 |
| Very important | 1 |
| Important | 9 |
| Ready (`loom:issue`) | 1 |
| In Progress (`loom:building`) | 3 |
| PRs awaiting review | 0 |
| Approved PRs awaiting merge | 3 |
| Curated | 13 |
| Architect / Hermit proposals | 3 |
| Active epics | 0 |
<!-- guide:plan-body:end -->
