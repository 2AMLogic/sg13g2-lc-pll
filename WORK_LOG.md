# Work Log

Chronological record of merged PRs and closed issues, maintained by the Guide triage agent.

### 2026-11-26

- **PR #420**: test(lvs): refuse unparseable envelopes in the freshness gate
- **Issue #419** (closed): scripts/test-layout-top.sh: lvs_fresh_check silently skips an LVS envelope whose JSON will not parse
- **Issue #487** (closed): Decouple lock-detector ramp timing from measurement-card generation
- **PR #490**: refactor: compute lock-detector ramp timing directly

### 2026-11-25

- **Issue #485** (closed): Simplify vco-prescaler-load and cp-dc make_requests.py: collapse 4 writer functions and guard module entry points
- **PR #486**: refactor(sim): build VCO and charge-pump corner requests in memory
- **PR #483**: test(sim): verify charge-pump device partition and mask counts
- **Issue #481** (closed): Strengthen the cp attribution guard: cover check_partition and assert what write_netlist actually masks
- **PR #480**: test(sim): guard cp-mc attribution schedule and group rejection
- **Issue #479** (closed): Wire sim/cp-mc into the pytest harness: assert the attribution campaign order and the unknown-group rejection
- **PR #478**: refactor(sim): derive cp attribution campaign list from attribute.py
- **Issue #477** (closed): Derive the charge-pump attribution run list from the device groups
- **PR #475**: test: add pytest coverage for the vco-prescaler-load record writer
- **Issue #474** (closed): Unit-test vco-prescaler-load make_record.py now that it imports cleanly
- **PR #473**: refactor(sim): decompose vco-prescaler-load make_record main() and guard entry point
- **PR #472**: refactor(scripts): extract layout-top negative-control fixtures into a tracked helper
- **Issue #469** (closed): Simplify sim/corner-verification/vco-prescaler-load/make_record.py: decompose 221-line main() and guard module entry point
- **Issue #468** (closed): Extract the last inline Python heredoc (111 lines) from scripts/test-layout-top.sh into a tracked helper
- **PR #437**: feat: report recorded vs running klt and PDK in gen_cells --check
- **Issue #433** (closed): layout: report the generator used for cell digest checks and document local harnesses
- **Issue #466** (closed): scripts/ld_tool.py klt sim request omits psp103_nqs.osdi (sibling of #451, not in its scope)
- **Issue #463** (closed): osdi-preload guard is file-scoped, so a multi-request generator can regress on one of its preload lists
- **Issue #451** (closed): klt sim request generators still missing psp103_nqs.osdi: cp-mc, cp-dc I_cp corners, loop-power ad-hoc requests
- **PR #465**: fix(sim): preload psp103_nqs.osdi in 42 loop-power diagnostic requests
- **PR #455**: docs: refresh top-level LVS envelope for native bipolar/MOS cards
- **Issue #456** (closed): lock-detector C-grid request generator (scripts/ld_tool.py) still preloads psp103.osdi without psp103_nqs.osdi
- **Issue #454** (closed): layout: regenerate cells and top.gds after klayout-tools#7531 so pfet arrays carry pSD (0 sg13_hv_pmos extracted in LVS)
- **Issue #452** (closed): loop-power corner-verification requests abort at parse: no cornerRES/r3_cmc loading for the netlists' rppd resistors
- **Issue #450** (closed): Extract 3 inline Python heredocs (235 lines) from scripts/test-layout-cells.sh into a tracked module
- **Issue #448** (closed): Simplify layout/gen_integrated.py: decompose 411-line main() and deduplicate collision check
- **PR #462**: fix(lock-detector): preload psp103_nqs.osdi and guard psp103-only generators
- **PR #460**: fix(layout): restore pSD implants in loop-block pFET arrays
- **PR #459**: fix(sim): load cornerRES/r3_cmc in the 42 #97 loop-power requests
- **PR #458**: refactor: extract test-layout-cells inline Python into a tracked helper
- **PR #457**: refactor(layout): decompose gen_integrated main() into Router and stage helpers
- **PR #453**: fix(sim): preload psp103_nqs.osdi in cp-mc generator, I_cp corners request, and flop-toggle request
- **PR #446**: fix(manifests): cite passing post-retune cp-dc envelopes for item 5

### 2026-11-24

- **Issue #443** (closed): layout/lvs/README.md header still says no klt lvs envelope exists / engines stop before a compare
- **Issue #432** (closed): fetch-vco.sh: --retry-all-errors retries HTTP 404, so a wrong pin fails slowly (~13s/file)
- **Issue #429** (closed): sim/pfd, cp-dc, loop-tran and loop-power decks never load psp103_nqs.osdi: NQS model cards silently ignored, and the PFD bench dies on the pinned ngspice-47
- **Issue #223** (closed): Drop vendored manifests/design-evidence-tiers.md: the pinned klt 0.8.0 bundles the identical doc
- **PR #447**: fix: load psp103_nqs in PFD/CP/loop decks and refuse runs with ignored model cards
- **PR #445**: docs: correct LVS README status to reflect mismatch envelope
- **PR #444**: chore: drop vendored tier checklist and --tiers-doc, pinned klt selects it
- **PR #438**: fix: fail fast on permanent 404 in fetch-vco.sh retry loop
- **Issue #418** (closed): Remove broken one-shot sim/loop-power/attempts/issue-84/ scripts (stale against current divider and loop_power template)
- **PR #442**: chore: remove broken issue-84 scratch scripts
- **PR #441**: docs: record top-level LVS re-run with subckt-call reference (mismatch)
- **Issue #416** (closed): layout: routed cells' stamped port labels are not read as pins by the PDK LVS runset (loop filter: layout pins 3 -> 0)
- **PR #424**: fix(layout): stamp cell port labels on SG13G2 metal text purpose /25
- **PR #431**: fix: bound-retry transient fetch failures in fetch-vco.sh
- **Issue #348** (closed): test flake: scripts/ci-harness.sh fetch-pll test fails on signoff when one locked blob is momentarily unreachable
- **PR #422**: fix: remove the stale reset-fix diagnostic mode from run-pfd-sweep.sh
- **Issue #250** (closed): Remove the PFD_VARIANT=reset-fix mode from run-pfd-sweep.sh: against the current pin it half-applies and would write a mislabeled record
- **PR #427**: refactor: share verdict, grid and append-only archive helpers across klt sim record writers
- **Issue #426** (closed): Share verdict, request-grid and append-only report-archive helpers across the four klt sim record writers

### 2026-11-23

- **Issue #219** (closed): Remove archived pre-DR-005 prescaler cells (div2_cml, div2_ef_hs, div2_latch_hs, div45_dm): uninstantiated
- **PR #421**: fix: derive the cornerRES clause, rail-gated Vce headline and div89 grid text from the request
- **Issue #401** (closed): Three remaining input-immutable spans in emitted record text: the cornerRES legend half, the head's minimum-supply clause, and div89_record's PDK legend
- **PR #417**: fix(layout): refuse colliding group ids in common.plan()
- **Issue #415** (closed): layout: split-off HBT group ids are not guaranteed unique in common.plan()
- **PR #414**: fix(layout): re-pin drifted LVS envelopes to the shipped stream and check them
- **Issue #413** (closed): layout/lvs: committed envelopes on main pin a superseded layout/top.gds (klt lvs --check reports drifted)
- **PR #412**: fix: match divider_corner_record.py docstring usage to the real --part CLI
- **Issue #411** (closed): divider_corner_record.py docstring documents a --report CLI that argparse rejects
- **PR #410**: fix: drop the fixed speed and count sweep prose from divider corner records
- **Issue #407** (closed): Remove the fixed speed and count sweep descriptions from divider corner records
- **PR #409**: test: track the four generated Python helpers from test-layout-top.sh in scripts/
- **Issue #408** (closed): test-layout-top.sh: four more generated Python helpers are still outside the tracked syntax check
- **PR #406**: test: extract the inductor clearance checker to scripts/indclear.py
- **Issue #402** (closed): Move the inductor clearance checker out of the layout harness heredoc
- **PR #403**: chore(sim): retire the local nominal G2 bench, point the README at batch stage 0
- **Issue #227** (closed): Retire the local nominal G2 bench (run-vco-prescaler-load.sh): superseded by the batch stage-0 request and cannot elaborate the current prescaler
- **PR #400**: fix: derive the prescaler Scope-line legend and cp-dc comment counts from the request
- **Issue #399** (closed): Residual input-immutable text in the prescaler-vce record Scope line and the remaining typed 18-corner comments
- **PR #357**: fix(layout): erase router net labels on routed cells so ports carry one label
- **Issue #349** (closed): layout: routed cells get two labels per subckt port, and test-layout-cells.sh set-dedupes so it cannot see it
- **PR #354**: docs(layout): record routing trials and per-cell LVS evidence for the four remaining cells
- **Issue #346** (closed): layout: route the remaining cells and LVS each against its own subcircuit (follow-up of #343)
- **PR #351**: feat(layout): split the prescaler input pair under the tank pins, cutting the tank routes to the geometric floor
- **Issue #345** (closed): layout: floorplan iteration to cut the tank route (850 um / 612 um) to the keep-out floor, and record the remaining shortfall against the 2.1 fF budget

- **PR #398**: fix: derive the loop-model and prescaler record corner counts from the request
- **Issue #397** (closed): Two more record writers hard-code the 18-corner count: sim/loop-model/envelope.py and sim/prescaler-g1/vce_record.py
- **PR #396**: fix: derive the cp-dc record's corner count and grid text from the request
- **Issue #395** (closed): cp-dc record writer hard-codes the corner count: "18 of 18 corners converged" is printed whatever cp_icp_corners.request.json contains
- **PR #394**: fix: drop the cp-dc record writer's --request override
- **Issue #392** (closed): Remove the charge-pump record writer’s alternate request option to prevent false 18-corner summaries

### 2026-11-22

- **PR #390**: fix: score an unset BASE_CLEAR as a failed out-of-tree control
- **Issue #378** (closed): test-layout-top.sh: BASE_CLEAR is unbound under set -u when the committed-stream clearance check fails
- **PR #388**: fix: grade each div89 report before combining so an empty report is INCOMPLETE
- **Issue #386** (closed): Use one verdict rule per report so an empty div89 async voltage sweep cannot pass
- **PR #387**: fix: grade an empty prescaler-g1 Vce report INCOMPLETE, not PASS
- **Issue #385** (closed): prescaler-g1 Vce grader also grades an empty corner report PASS
- **PR #384**: fix: grade an empty divider corner report INCOMPLETE, not PASS
- **Issue #376** (closed): Use one divider verdict rule so an empty corner report grades INCOMPLETE
- **PR #377**: test(layout): refuse nested VCO copies in the top-metal clearance checker
- **Issue #373** (closed): indclear.py's placement guard reads only DIRECT vco instances; a nested extra copy is still accepted
- **Issue #379** (closed): Share the GDS round-trip test for the top layout and block cells
- **PR #382**: test: share the GDS round-trip machinery between the layout harnesses
- **Issue #375** (closed): Remove the duplicate archive-conversion test in sim/loop-model/test_envelope.py
- **PR #380**: test: drop duplicated load_icp_points archive test definition
- **Issue #369** (closed): test(layout): require one VCO placement with an identity transform before checking top-metal clearance
- **PR #372**: test(layout): refuse unsupported VCO placements in the top-metal clearance checker
- **Issue #368** (closed): Share the I_cp report reader so incomplete corner grids cannot produce a row-5 pass
- **PR #371**: sim: enforce the I_cp corner grid through one shared report reader

### 2026-11-21

- **PR #370**: fix: ignore Loom daemon account-ranking runtime files in gitignore
- **Issue #366** (closed): gitignore: .loom/account-ranking.codex (daemon runtime state) is untracked dirt that fails check-main-clean.sh
- **PR #367**: test(layout): assert top-metal clearance to the VCO inductor exclusion markers
- **Issue #361** (closed): layout: no test asserts top-metal routes stay clear of the VCO inductor exclusion markers
- **PR #364**: docs: attribute erc.supply_short skip to the degenerate tap declaration, not the --pdk deck
- **Issue #362** (closed): layout/README.md: erc.supply_short's skip reason is misattributed to a missing --pdk deck
- **PR #359**: feat(layout): route supplies, external pins and divider tie-offs from labelled landings
- **Issue #344** (closed): layout: route VDD / VDDV / VSS, the REF, IREFCP and LOCK pins and the divider tie-offs in gen_integrated.py (ROADMAP Now 5; prerequisite for items 4 and 11)
- **Issue #353** (closed): Reuse the divider gate evaluator in the prescaler code test
- **PR #356**: refactor: reuse the divider gate evaluator in the prescaler code test
- **Issue #358** (closed): WORK_PLAN.md generated-region blurbs drift from render_plan_body()'s literals, defeating the #5890 debounce

### 2026-11-20

- **PR #347**: feat(layout): route loop-filter cell, add per-cell LVS envelopes (not matched)

### 2026-11-19

- **PR #340**: run-lock-detector: rebuild grid records from the saved artifacts alone
- **Issue #338** (closed): Remove simulation setup from lock-detector report replay

### 2026-11-18

- **PR #334**: ci: add merge_group trigger to harness and signoff workflows
- **Issue #332** (closed): Merge queue: add the merge_group trigger to the required-check workflow(s)

### 2026-11-17

- **PR #327**: chore(loom): resync installed Loom to v0.19.1306
- **Issue #197** (closed): Divider stops dividing at 125C after start-up (7 of 54 corner units): SLOW 625/687.5 MHz, TYP 687.5 MHz
- **Issue #82** (closed): spec decision: CP up/down mismatch (row 7) limit and yield target

### 2026-11-16

- **PR #322**: chore(loom): resync installed Loom to v0.19.1302

### 2026-11-15

- **Issue #304** (closed): Bump the klt pin from 0.8.0 to a release that accepts model-run (unblocks the row-5 item-5 citation)
- **PR #317**: bump the klt pin to 0.9.1 and cite the row-5 model-run record as item-5 evidence
- **Issue #308** (closed): Consolidate duplicated digest() and sha256() helpers in layout/: #263 had to be fixed in two copies, which have since diverged
- **PR #314**: layout: consolidate duplicated digest() and sha256() into cells/common.py
- **Issue #298** (closed): Consolidate the append-only record guard into lib-record.sh: 14 call sites, and run-lock-detector.sh:41 has already lost its message clause
- **PR #316**: refactor(record): assert_new_record in lib-record.sh; one append-only guard for all 14 sites
- **Issue #300** (closed): Row-5 item-5 citation: the remaining work the new gap text names has no issue, and ROADMAP 'Now' item 4 no longer fits that section's contract
- **PR #310**: docs: split ROADMAP Now item 4 into the model-run re-emission (#303); move the klt pin bump to Next (#304)
- **Issue #303** (closed): Re-emit the row-5 method-L envelope record in the klt model-run shape (so item 5 can cite it)
- **PR #312**: feat: emit row-5 envelope records in the klt model-run signoff shape
- **Issue #301** (closed): Docs say three klt signoff --attest envelopes (items 1, 9, 10); there are four — item 2's layout.attest.json is omitted repo-wide
- **PR #315**: docs: count item 2's attest envelope in the manifest evidence index
- **Issue #294** (closed): README's 'DRC clean' summary omits the deck-coverage qualifier that item 3 calls claimant-enforced
- **PR #302**: docs: qualify README's DRC-clean ladder sentence with curated-deck coverage pointer
- **Issue #297** (closed): design/README.md states the mcounter terminal-count decode as Q = 0001; the netlist decodes Q = 0010 (count 2)
- **PR #311**: docs: withdraw the false mcounter README discrepancy in the #278 record and disambiguate the decode phases
- **Issue #290** (closed): lib-pdk.sh: a missing model library or OSDI file dies with no message (set -e aborts before the die)
- **PR #309**: fix: keep the PDK pin check's missing-file die reachable under set -e
- **Issue #268** (closed): spec/README.md index omits DR-005 (prescaler P8/9 div-2/3 first stage)
- **PR #271**: test(spec): hold the decision-record index to the tree, index DR-005
- **Issue #291** (closed): Remove six never-read names in project Python: an uncalled nested helper, two silently-ignored parameters, three dead constants
- **PR #306**: Remove born-dead names: uncalled nested ext(), ignored params, dead constants
- **Issue #282** (closed): test-layout-vco.sh/-top.sh: five bare-refuse negative controls pass when their fixture generation silently fails
- **PR #305**: test: make layout negative controls discriminating and guard their fixture generation
- **Issue #273** (closed): run-jitter.sh: a NOISE_INPUTS file supplying no in-band term still promises a listing the record does not contain
- **PR #299**: fix: guard the jitter record's inputs parenthetical on the supplied term count
- **Issue #281** (closed): Define the record ID once in lib-record.sh: the same ID= line is repeated in 11 bench drivers
- **PR #288**: refactor(record): set the record ID and directory in lib-record.sh, not in each driver
- **Issue #275** (closed): A Guide docs-maintenance PR that edits README.md always red-lines item 10's attest gate
- **PR #293**: docs(manifests): record README.md ownership rule and item-10 recovery for Guide docs PRs
- **Issue #286** (closed): Remove three born-dead lines in layout/lvs/build_reference.py: two unused imports and a comment that claims the LVS reference strips device parameters when it does not
- **PR #292**: refactor: drop unused imports and false strip comment in LVS reference builder
- **Issue #280** (closed): Item 5, row 5: cite the method-L envelope or correct the declared gap now that klayout-tools#4859 is closed
- **PR #296**: manifests: row-5 gap names the klt 0.9.0 model-run gate instead of the closed #4859; regenerate record
- **Issue #285** (closed): Collapse the triplicated OSDI pin check in lib-pdk.sh, and fix what PDK_SKIP_PSP103 claims to gate
- **PR #289**: refactor(pdk): one guarded loop for the three OSDI pin checks, flag renamed
- **Issue #278** (closed): Enumerate the M/A counter state sequence for N = 90-110 (PDK-free), to say which terminal-count decodes are valid for #199
- **PR #295**: Enumerate M/A counter state sequences from the netlist; settle look-ahead decode validity

### 2026-11-14

- **Issue #263** (closed): gen_integrated.py digest() is layer-order sensitive, so it is not stable across a GDS round trip
- **PR #270**: fix(layout): hash digest layers in sorted (layer, datatype) order
- **Issue #279** (closed): Record what a sg13g2-vco pin bump would bring and what it would invalidate (pin 17e49a8 vs upstream main)
- **PR #287**: docs(sim): record the sg13g2-vco pin delta and what a bump would cost
- **PR #284**: docs: state README status and ladder from the signoff record; re-tense stale DRC claims
- **Issue #272** (closed): Consolidate the duplicated expect() test harness into one scripts/ library; test-fetch-vco.sh still carries the pre-#234 weak form
- **PR #283**: test: consolidate the duplicated expect() harness into scripts/lib-expect.sh
- **Issue #261** (closed): Compute the ngspice pin verdict in the klt sim record generators: five scripts print "pin 47: mismatch" as a literal
- **PR #265**: refactor(sim): compute the ngspice pin verdict in sim/ngpin.py, drop the five literals
- **PR #276**: docs: roadmap as of 2026-11-13
- **Issue #260** (closed): run-jitter.sh: a record made with NOISE_INPUTS carries only the file's path and sha256, not each term's table and source
- **PR #269**: feat(jitter): state each in-band noise input's summary and source in the record
- **Issue #245** (closed): Finish the Metal1 pad-trim guard in gen_integrated.py and remove its inert bindings and duplicate helpers
- **PR #256**: feat(layout): test trimmed Metal1 pads still cover their Via1, record the count

### 2026-11-13

- **Issue #257** (closed): gen_integrated.py --write churns the attested top.gds on an unchanged design (GDS timestamps)
- **PR #264**: fix(layout): keep the attested top.gds bytes when --write finds no geometry change
- **Issue #258** (closed): make_record.py: G2 closure line cannot see a 125 C unit missing from the reports
- **PR #266**: fix(sim): grade the G2 125 C closure line against the requested grid
- **Issue #247** (closed): Method-L jitter model: take the three in-band noise terms as inputs and report an unsupplied term as missing, never 0.0
- **PR #259**: feat: take the three in-band jitter terms as model inputs and report an unsupplied term as missing
- **Issue #239** (closed): Consolidate the spec corner-set table: seven request generators each re-encode the DR-004 SLOW/TYP/FAST bundles, and they have diverged
- **PR #255**: refactor: define the spec C-grid corner set once in sim/corner_set.py
- **Issue #243** (closed): Compute the verdict lines in the G2 C-grid record generator: make_record.py --dsubw prints one run's conclusions as literals
- **PR #254**: fix(sim): derive the G2 verdict, 27 C control and ngspice pin lines from the graded data
- **Issue #36** (closed): T1 item 3 (DRC clean): klt drc on the integrated layout with coverage disclosed
- **PR #248**: docs(drc): record clean curated+native DRC and grade T1 item 3 met
- **Issue #241** (closed): Nothing detects a stale testbenches.attest.json: signoff binds item 9 by the inventory hash, not the attest's per-file hashes
- **PR #244**: ci(signoff): check each attest envelope's per-file hashes, add restamp-attest.sh
- **Issue #236** (closed): Consolidate the three divider N-per-window counters; the local 100 MHz count check is never graded
- **PR #240**: refactor(sim): grade the divider 100 MHz count check with the speed grader
- **Issue #228** (closed): Remove the stale 'pinned VCO did not oscillate' reason from two record generators and seven other files
- **PR #238**: docs: retire the 'VCO did not oscillate' reason from two record generators and six doc sites
- **Issue #234** (closed): layout/gen_integrated.py is a SyntaxError on Python 3.10 (the CI-pinned version)
- **PR #235**: fix(layout): make gen_integrated parse on Python 3.10, add a compile gate
- **Issue #222** (closed): Run the divider corner grader's negative-control tests in CI; drop unused frange helper
- **PR #233**: test(ci): run divider corner grader negative controls, make two discriminating
- **Issue #230** (closed): Split the DRC run log out of layout/README.md into layout/drc/README.md (350 of 498 lines)
- **PR #232**: docs(layout): move the DRC run log into layout/drc/README.md
- **PR #226**: feat(drc): derive the IHP runset's declared rule set from the deck, native DRC coverage_unknown -> clean
- **Issue #202** (closed): layout: fix gen_cells.py findings from native DRC cross-check (pfet w5 cell, HBT spacing, LU.b tap ties)
- **PR #224**: layout: draw pSD substrate tap rings on every nfet group, native DRC 322 -> 0
- **PR #220**: docs(layout): commit first runset LVS envelope (mismatch)
- **PR #218**: docs(layout): record LVS re-run on klt dev879 and runset coverage crash

### 2026-11-12

- **PR #217**: Bump Repo Skills 0.25.10 -> 0.26.1
- **PR #216**: docs(layout): record blocked LVS attempt with reproducible reference and request
- **Issue #210** (closed): divider-elab and loop-power decks load no cornerRES.lib / r3_cmc OSDI although divider.spice has rppd/rhigh
- **PR #215**: fix(sim): load RES lib and r3 OSDI in divider-elab and loop-power decks
- **Issue #209** (closed): run-prescaler-g3: chain analysis still expects /8 and /10 after the prescaler was re-tied to /8/9
- **PR #214**: fix(sim): score prescaler-g3 chain bench against the ratified /8 and /9 ratios
- **Issue #212** (closed): Stop tracking 6 generated vco-prescaler-load decks (extends #106)
- **PR #213**: chore(sim): untrack six regenerable prescaler-load decks and ignore them
- **Issue #208** (closed): run-prescaler-g3 fails on a clean host: rppd is an unknown subckt (attest 9 cold start stops there)
- **Issue #196** (closed): Re-attest prescaler G1 bench with klt signoff --attest 9 (follow-on from PR #195)
- **PR #211**: fix(sim): load rppd resistor lib and r3_cmc OSDI in prescaler-g3 decks

### 2026-11-11

- **Issue #203** (closed): Remove archived pre-DR-005 first-stage cells (div2_cml, div45_dm, div2_ef_hs, div2_latch_hs)
- **Issue #47** (closed): spec row 1: stretch channel plan says 50 MHz steps, unreachable with even-N only (DR-002)

### 2026-11-10

- **Issue #165** (closed): Prescaler: x1.x89.xmc.xqt exceeds BVCEO 2.2 V at 3.63 V with MC high (9 of 36 Vce runs)
- **PR #170**: fix: clamp mc_conv bm with an input divider so the tail Vce stays under BVCEO
- **PR #205**: fix(layout): close pad notches and ring-contact gaps, native DRC 348 -> 322
- **PR #204**: fix(layout): move divider clear of prescaler, native DRC 1798 -> 348
- **PR #201**: docs(layout): record native-deck DRC cross-check of integrated top (1798 violations)
- **Issue #166** (closed): Divider corner record at d04a1a4: 16 of 54 runs ungraded (9 timestep_too_small, 7 no-toggle at 125C)
- **PR #198**: feat(sim): ramp divider corner bench start and add 54-unit graded record
- **Issue #171** (closed): Fix stale prescaler-g1 negative control; decide on 8 unused pre-DR-005 cell files
- **PR #195**: fix(sim): retarget prescaler G1 bench and negative controls at cml_div23
- **Issue #191** (closed): Fold gen_res_requests.py into gen_corner_requests.py: generator no longer reproduces committed divider requests
- **PR #194**: refactor(sim): fold divider resistor-corner patch into the request generator
- **Issue #186** (closed): Prescaler: close the 3 residual SLOW/125 C async failures left by the cml_dff_latch resize
- **PR #193**: fix(design): shorten cml_dff_latch load to 7.8u to close SLOW/125C async failures
- **Issue #187** (closed): Layout: regenerate cml_dff-containing cells after the cml_dff_latch resize
- **PR #192**: fix(layout): regenerate prescaler and integrated top for cml_dff_latch RL 8.0 um
- **Issue #175** (closed): Decide: keep or delete eight unused pre-DR-005 prescaler cell files (split from #171)
- **PR #181**: docs: mark pre-DR-005 divider cells archived in README and inventory
- **Issue #182** (closed): Resize or decide on cml_dff latch loads for 5.5 GHz SLOW/125 C prescaler
- **PR #189**: feat(prescaler): cml_dff-only latch with 8.0u load closes the 108-unit chain grid, 3 async units remain
- **Issue #188** (closed): Prescaler Vce bench: load the rppd resistor models so the 36-run grid runs on the current netlist
- **PR #190**: fix(sim): load cornerRES and r3_cmc in the prescaler Vce bench and re-grade
- **PR #185**: docs(layout): commit klt drc report of the integrated top (747 violations) as item 3 evidence
- **Issue #35** (closed): T1 item 2 (layout): integrated loop layout with the pinned sg13g2-vco stream placed unmodified
- **PR #184**: feat(layout): integrated top GDS with placed and routed loop blocks and item-2 attestation
- **Issue #168** (closed): prescaler /8-/9 fails at SLOW/125 C, 5.5 GHz with PDK rppd resistors
- **PR #183**: docs: record bisection of 5.5 GHz SLOW/125 C prescaler failure to cml_dff latch loads
- **Issue #151** (closed): Collapse 11 near-identical cp-mc probe netlists into base plus patches
- **Issue #154** (closed): Stop tracking generated sim/prescaler-g1/prescaler_vce.request.json (#106 rule)
- **Issue #58** (closed): T1 item 2 (layout) b/3: layout cells for prescaler, divider, PFD, CP, loop filter, lock detector
- **PR #180**: feat(layout): regenerate loop-block provenance with all devices drawn
- **Issue #164** (closed): Schematic: replace the 76 ideal R cards (prescaler 71, divider 5) with PDK resistors (rppd/rhigh W/L) and re-run affected sims (r7-q52)
- **PR #177**: feat: re-run divider and loop-power corner records with rppd/rhigh corner models
- **PR #176**: feat: grade VCO at 125 C with a labelled dsubw-TNOM approximation (loaded G2 stays open)
- **PR #174**: docs: record 125 C convergence probe for the loaded VCO
- **Issue #160** (closed): VCO swing and startup re-check with the P = 8/9 prescaler input load (1.84-1.95 fF)
- **PR #172**: feat: re-run loaded-VCO nominal and corner grid on batch against the rppd/rhigh prescaler

### 2026-11-09

- **Issue #43** (closed): spec rows 3/4: fixed /2 then /4/5 gives /8 or /10, not /8 or /9
- **PR #169**: feat: swap ideal resistors for rppd/rhigh instances; /8-/9 grid fails at SLOW 125C 5.5 GHz
- **PR #167**: fix: take vco-prescaler-load record's load figures from the Cin record
- **Issue #162** (closed): prescaler_vce.cir bench stale for div89_dm hierarchy (.ic nodes, MC modes)
- **Issue #158** (closed): Prescaler: ÷2/3 first stage (P = 8/9) to restore contiguous N 90-110 (r7-q31)
- **PR #161**: feat: P = 8/9 prescaler with ÷2/3 first stage and fixed ÷4, corner and async-modulus evidence

### 2026-11-08

- **Issue #3** (closed): Pin sg13g2-vco in reuse.lock.json and smoke-simulate the pinned netlist

### 2026-11-07

- **PR #163**: Bump Repo Skills 0.25.1 -> 0.25.10

### 2026-11-06

- **PR #159**: docs: record ÷2/3 P = 8/9 architecture, sibling reuse check and checked M/A table
- **Issue #155** (closed): sim: split the divider speed check into dividers-only and counters-only decks
- **PR #157**: sim: split divider speed deck by circuit role; ignore klt header in netlist check
- **Issue #153** (closed): Divider speed deck fails operating point (NaN at bias HBT) with current divider netlist
- **PR #156**: sim: record divider speed deck op-point bisect
- **PR #152**: sim: load psp103_nqs.osdi in the divider decks and pin its sha256
- **Issue #60** (closed): Consolidate run-script record-ID/placeholder boilerplate; divider-elab lacks -dirty marker
- **PR #148**: scripts: share record stamp, placeholder scan and .spiceinit via lib-record.sh
- **Issue #79** (closed): Dedupe charge-pump klt sim circuit body: cp_body.spice vs cp_icp.cir
- **PR #150**: sim: share cp_icp.cir as the CP body for corner-verification stage requests
- **PR #147**: sim: DT decode fed from replica q0/q1 flops leaves SLOW and TYP 125 C 2.97 V not dividing, trial reverted
- **PR #144**: sim: SLOW 125 C 2.97 V DT path is 1.07 ns clock-to-Q plus 0.78 ns decode against a 1.606 ns period
- **Issue #142** (closed): sim/loop-power/attempts/issue-84 scripts hard-code worktree and /tmp scratch paths, so the 21.14 mW attempt cannot be re-run from the repo
- **PR #145**: sim: make issue-84 scripts path-independent with mktemp scratch
- **PR #137**: sim: doubling the DT inverter in parallel leaves SLOW and TYP 125 C 2.97 V not dividing
- **Issue #84** (closed): Row 11 power: divider at speed puts loop-power sum at 23.01 mW vs 20 mW budget
- **PR #140**: sim: divider power attempt reaches 21.14 mW against 20 mW, DR-003 proposes the row 11 fallback
- **Issue #106** (closed): Remove 29 generated request-stage1-missing*.json files from sim/corner-verification/loop-power
- **PR #141**: chore: stop tracking 56 generated sim request JSONs, attest regeneration
- **Issue #66** (closed): Collapse five identical layout/cells block modules into one table
- **PR #139**: refactor: collapse five identical layout cell modules into a table
- **PR #136**: sim: DT driver split per flop leaves SLOW and TYP 125 C 2.97 V not dividing, trial reverted
- **PR #135**: sim: DT decode as NAND2 into NOR2 stops all four 125 C corners producing FB edges, trial reverted

### 2026-11-05

- **PR #134**: sim: FAST/TYP/SLOW 125 C 2.97 V DT pulse arrives 0.03/0.15/0.25 ns after the capture edge, only FAST divides
- **PR #133**: sim: SLOW 125 C 2.97 V counter D inputs settle 0.0-0.2 ns before the next clock edge
- **PR #132**: sim: SLOW 125 C 2.97 V probed forced-state trial, forcing reached target and DT falls between clock edges, cause not apportioned
- **PR #131**: sim: SLOW 125 C 2.97 V held in a valid counter state still never divides
- **PR #130**: sim: SLOW 125 C 2.97 V counter free-runs irregularly from the first clock and never presents terminal count
- **PR #129**: sim: TC flops fed from DTN plus inverters stops FAST 125 C 2.97 V dividing, trial reverted
- **PR #128**: sim: TC from TCN inverters stops four 125 C corners dividing, trial reverted
- **PR #127**: sim: TYP 125 C 2.97 V misses the terminal-count capture, SLOW 125 C 2.97 V never reaches terminal count
- **PR #126**: design: mcounter Q-bar tap and second TC flop, 17 of 18 stage-2 corners divide
- **PR #125**: sim: shortening both D2 routes at once makes two 125 C corners divide, two still fail
- **PR #124**: sim: only q2 misses its capture after the TC reload at FAST 125 C, two routes into D2 settle together
- **PR #123**: sim: a direct Q-bar tap on the q2 flop leaves the four 125 C corners unchanged, trial reverted

### 2026-11-04

- **PR #122**: sim: q2 miscapture at FAST 125 C is a setup violation on the clock-to-Q-to-D path
- **Issue #117** (closed): Dedupe .subckt parser/flattener: gen_prescaler_vce_request.py vs layout/cells/common.py
- **PR #121**: refactor: read the prescaler Vce stress list with the shared netlist parser
- **PR #120**: sim: edge-aligned trace shows q2 not falling after the 12-load at FAST 125 C, TC/TCN buffering does not close it
- **PR #119**: sim: a D-input delay on the counter flops moves the 125 C modulus but divides at no corner, trial reverted
- **PR #118**: sim: isolated dff_tg_hv toggles at 625 MHz at SLOW 125 C 2.97 V, flop cell alone is not the limit
- **PR #116**: sim: duplicating the TC/TCN flops in mcounter stops division at the four 125 C corners (trial reverted)
- **PR #115**: sim: doubling the divider clock-buffer drive leaves the 125 C modulus unchanged
- **PR #114**: sim: 125 C diagnosis of the four non-dividing corners, M counter reload and stuck state
- **PR #113**: sim: stage-2 18-corner grid after cml2cmos self-bias, 14 of 18 divide
- **Issue #70** (closed): Item 5 remainder (gated): C-grid envelopes for rows 1, 8, 9, 10, 11 and row 7 upper edge
- **PR #112**: sim: row 11 stage 1 complete at 135 of 135 corners, 24 divide, still fail
- **PR #111**: design: self-biased AC-coupled cml2cmos input inverter, one FAST 125 C corner divides, grid incomplete
- **PR #110**: sim: divider flop clock pulse too narrow to capture at two TYP corners
- **PR #109**: sim: divide ratio at TYP 27 C 3.63 V and 125 C 2.97 V, clock good, counter side fails
- **PR #108**: sim: row 11 stage-1 loop power, 57 more fleet corners (128 of 135)
- **Issue #102** (closed): Drop standalone mcounter/acounter/cml2cmos netlists: byte-identical subsets of divider.spice
- **PR #107**: chore: drop standalone mcounter/acounter/cml2cmos netlists contained in divider.spice

### 2026-11-03

- **PR #105**: sim: FB edge-time probe shows FB is not 50 MHz at two TYP corners
- **Issue #103** (closed): Stale test-fetch-pll.sh command lines in sim/pfd and sim/lock-detector READMEs
- **PR #104**: docs: point sim READMEs at test-fetch-vco.sh PFD-pin form
- **PR #100**: sim: divider non-division diagnostic, cml2cmos clock stuck high at TYP 125 C 3.63 V
- **Issue #99** (closed): Merge test-fetch-pll.sh into test-fetch-vco.sh: same negative controls run twice
- **PR #101**: test: fold PFD-pin fetch negative controls into test-fetch-vco.sh
- **PR #98**: sim: row 11 start-up comparison on the fleet and 21 more stage-1 corners
- **PR #96**: sim: loop-power start-up probe and stage-1 missing-unit attempt (partial)
- **Issue #87** (closed): G2: re-check pinned VCO swing and startup with the prescaler load
- **PR #95**: sim: G2 C-grid for the pinned VCO with the prescaler load on the batch fleet
- **PR #94**: sim: record row 11 stage 1 fleet retry (no new corners)
- **PR #92**: sim: row 11 loop-power C-grid requests, fleet stage 2 record, partial stage 1
- **Issue #90** (closed): run-vco-smoke.sh reads vco_tran_<v>.data; ngspice-46 wrdata writes no suffix (false non-oscillation)
- **PR #91**: fix(smoke): accept suffixless wrdata files in the VCO smoke bench
- **PR #89**: feat(sim): G2 bench of the pinned VCO with and without the prescaler load
- **Issue #61** (closed): Divider (cml2cmos + M/A counters) does not divide at the 625 MHz prescaler output
- **PR #85**: test(divider): count A=0 and A=3 at 625/687.5 MHz through the real converter
- **PR #83**: fix(design): retime divider counters to divide N=100 at 625/687.5 MHz
- **Issue #78** (closed): Row 7 CP up/down mismatch fails Monte Carlo yield at 1.65 V (0.718 vs 2 % target); sizing or spec decision needed
- **PR #81**: docs(cp-mc): per-group mismatch attribution and failed XBNS/XBPA resize probes (design unchanged)
- **PR #80**: feat(layout): draw prescaler/divider HBTs and lock-detector pull-down
- **Issue #40** (closed): T1 item 6 (Monte Carlo): klt yield on CP mismatch (row 7) and reference spur (row 9)
- **PR #77**: feat(sim): charge-pump mismatch Monte Carlo over the C-grid graded with klt yield
- **Issue #72** (closed): Prescaler HBT Vce exceeds BVCEO 2.2 V min at the 2.97 V sub-corners, and four 125 C corners do not converge
- **PR #76**: fix: bring prescaler HBT Vce under BVCEO at all 18 supply corners
- **Issue #67** (closed): CP up/down mismatch 2.19 % at FAST, 3.63 V, -40 C exceeds the 2 % row-7 bound
- **PR #75**: fix: widen CP PMOS cascode-bias diode to meet row 7 mismatch at FAST/3.63V/-40C
- **Issue #64** (closed): Remove superseded prescaler-only inventory stopgap (script + JSON)
- **PR #74**: chore: remove superseded prescaler-only inventory stopgap
- **Issue #55** (closed): sim: re-grade the adopted lock_detector at f_ref = 50 MHz (gate G5)
- **PR #71**: sim: 50 MHz re-grade of the pinned lock_detector (delay window passes; thresholds and polarity filed upstream)
- **Issue #68** (closed): Item 5 remainder: C-grid envelope for row 5 and prescaler Vce margin (gated rows in #70)
- **PR #73**: test: row 5 envelope over measured I_cp and prescaler HBT Vce over the supply sub-corners
- **PR #69**: feat(sim): C-grid envelopes for the charge pump, declare item 5 row gaps
- **PR #65**: test: add 625/687.5 MHz speed check to divider bench and record bisect
- **PR #63**: feat: generate loop-block cells with port labels and provenance
- **Issue #34** (closed): T1 item 9 (testbenches shipped): closed-loop lock, spur, jitter and power benches plus --attest 9 inventory
- **PR #62**: feat(sim): closed-loop lock/spur, jitter and loop-power benches; attest T1 item 9
- **Issue #57** (closed): T1 item 2 (layout) a/3: generator scaffold, pinned VCO placement, keep-out/guard ring/fill
- **PR #59**: feat: layout generator placing pinned VCO with keep-out, guard ring and fill
- **Issue #32** (closed): T1 item 1 (design sources): loop filter, M/A counter, lock detector and top-level loop schematic + attest 1
- **PR #56**: feat: capture loop filter, M/A divider and loop top; attest T1 item 1

### 2026-11-02

- **Issue #31** (closed): T1 item 1 (design sources): prescaler schematics (CML divide-by-2 + divide-by-4/5) and close gates G1/G3
- **PR #44**: feat: CML prescaler (/2 + /4/5) schematics with G1 load and G3 flavour evidence

### 2026-11-01

- **PR #54**: Bump Repo Skills 0.24.7 -> 0.25.1

### 2026-10-30

- **Issue #19** (closed): PFD + charge-pump schematic (SG13G2 HV MOS) with a DC compliance / up-down mismatch testbench for spec row 7
- **PR #53**: feat: re-pin sg13g2-pll PFD to reset-parity fix and re-grade at 50 MHz
- **PR #23**: docs: record upstream PFD reset-parity issue and re-pin path

### 2026-10-29

- **Issue #33** (closed): T1 item 10 (repo hygiene): README reproduction steps, harness tests in CI, klt signoff --attest 10
- **PR #42**: ci: add harness workflow, reproduce-records README and item 10 attestation

### 2026-10-28

- **PR #50**: docs(measurements): add characterization report skeleton and item 8 inventory

### 2026-10-24

- **PR #6**: ci: grade T1 tier state with klt signoff against a committed verdict
- **Issue #4** (closed): Commit a T1 block manifest and a klt signoff CI job (T1 item 10)

### 2026-10-23

- **PR #27**: refactor: source shared lib-pdk.sh in the VCO smoke bench
- **PR #25**: feat: warn and record when ngspice differs from the pinned version
- **Issue #26** (closed): Consolidate run-vco-smoke.sh PDK/pin check into lib-pdk.sh (copy has drifted: no thread cap)
- **Issue #22** (closed): sim/pins.json ngspice pin says 47; CP/PFD records ran on ngspice-46
- **PR #21**: feat: charge-pump design sources, CP/PFD benches, and the PFD pin with its failed 50 MHz re-grade
- **PR #20**: feat(sim): method-L loop model and loop-filter sizing over Kvco and I_cp
- **Issue #18** (closed): Linear phase-domain loop model: size the type-II 3rd-order loop filter and grade f_c / PM over the Kvco and I_cp range (spec rows 5, 6, 8 method L)

### 2026-10-21

- **PR #14**: Bump Repo Skills 0.24.3 -> 0.24.7

### 2026-10-20

- **PR #11**: fix: wire package.json gate scripts to fetch-vco negative controls
- **Issue #10** (closed): Replace always-green stub check scripts in package.json with the repo's real checks

### 2026-10-18

- **PR #9**: feat: pin sg13g2-vco with hash-verified fetch and a smoke bench

### 2026-10-17

- **PR #7**: docs(spec): ratify LC-PLL target spec, VCO interface table and DR-001
- **PR #1**: chore(loom): Install Loom 0.19.1181
- **Issue #2** (closed): Draft and ratify the target spec
