# Work Log

Chronological record of merged PRs and closed issues, maintained by the Guide triage agent.

### 2026-11-13

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
