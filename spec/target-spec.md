# LC-PLL target specification

- **Status: RATIFIED (targets) by DR-001** (`spec/decision-records/DR-001-target-spec-ratification.md`,
  issue #2). Every row is a **target**: a binding bound derived from a cited
  ratified row or from arithmetic written out in DR-001. **No row is
  measured.** Nothing in `sim/` grades any of them yet; a simulated number
  is never called measured. A row whose bound needs simulation is closed
  only by naming its gate, never by a guessed value.
- **Date**: 2026-10-17
- **Written by**: Builder agent, issue #2
- **Changing a row** requires a superseding decision record. Agents do not
  relax a ratified row to make results pass.
- **Cited upstreams (by commit; `reuse.lock.json` does not exist yet, #3 creates it, after which the pinned ref replaces these SHAs):**
  - `2AMLogic/sg13g2-vco` @ `17e49a8f9aa4f858cff804ff33c3c484ed826095`:
    `spec/target-spec.md` (12 rows, 0-11, RATIFIED as targets, "binding, not
    met") via DR-003 (rows 1, 2, 4, 5, 6, 8, 9, 10, 11) and DR-004 (rows 0,
    3, 7).
  - `2AMLogic/sg13g2-pll` @ `83e59fe81db0b09dbefcff35a55965bea0c2a76f`:
    `spec/target-spec.md`, which is itself an unratified draft and
    targets SG13CMOS5L. Everything cited from it is a draft number.

## How to read this file

Every row states min/typ/max (target / fallback / stretch as in the README),
the **condition** that grades it, the **method**, the **corner set**, and a
**status**. Status is always `RATIFIED (target) per DR-001 — not met`
unless a row says it carries a gate. The corner set is defined once in
§Corner set; rows refer to it as **C-grid**.

## 1. VCO interface table

Each row cites the `sg13g2-vco` row **and** its ratifying record, at VCO
commit `17e49a8`. All are VCO **targets, not measurements**.

| # | Interface item | `sg13g2-vco` row (record) | Value quoted | What the loop owes / may assume |
|---|---|---|---|---|
| I1 | Band | row 1 (DR-003) | 4.5 / 5.0 / 5.5 GHz | Divide ratio covers the band from the chosen reference (§2 rows 1-3) |
| I2 | Tuning range | row 2 (DR-003) | f_max/f_min ≥ 1.15 (stretch ≥ 1.20) over 0.0-3.3 V | none; the loop uses the window only |
| I3 | Control window | row 3 (DR-004) | `Vctrl` window W = [1.65, 3.30] V; \|Kvco\|_mean ≥ 381 MHz/V over W; chord nonlinearity ≤ 30 % of span (≤ 20 % stretch); **no \|Kvco\| ceiling ratified** | Charge-pump compliance over W (§2 row 7) and a loop designed over the Kvco range of §3 |
| I4 | Core supply | row 0 (DR-004) | single 3.3 V rail, 2.97-3.63 V; `npn13G2v` cross-coupled pair; HV MOS corner family | A separate branch for the VCO core (§5) |
| I5 | Phase noise | row 4 (DR-003) | ≤ −105 dBc/Hz @ 1 MHz (target), ≤ −115 (stretch); companion ≤ −125 @ 10 MHz (target); **method open there** | Loop bandwidth that suppresses VCO noise inside f_c (§4); the loop inherits the open method (§4) |
| I6 | Tank-node load | row 7 (DR-004) | no output buffer in v1; tank `L_diff` 11.4478 nH, `C_tot` 88.51 fF, `R_p,diff` 3.418 kΩ @ 5.0 GHz (2.936 / 3.937 kΩ at band edges); "an added 3 % of `C_tot` (≈ 2.1 fF) shifts f0 by 1.5 %"; swing ≥ 0.40 Vpp differential, current-limited, 204.1 µA tail | Load budget below |
| I7 | Startup margin | row 6 (DR-003) | g_m ≥ 3.0 × tank loss conductance at every bound corner | Re-checked with the prescaler load attached (later sim issue; gate G2) |
| I8 | Corner set | row 10 (DR-003), crossing per DR-004 | 135-point model grid at 3.300 V + 18 supply sub-corners | Same grid (§Corner set) |
| I9 | Temperature | row 11 (DR-003) | −40 to +125 °C | same |
| I10 | Core power | row 8 (DR-003) | ≤ 10 mW (target) | Loop power is stated separately (§2 row 10) |
| I11 | Supply pushing | row 9 (DR-003) | ≤ 50 MHz/V (target) | Isolation requirement (§5) |

### Tank-node load budget (the number the prescaler is graded against)

**Budget: total differential capacitance added to the tank nodes OUTP/OUTN
by the first stage that connects to them (buffer or prescaler input, plus
the routing between the tank node and that input) ≤ 2.1 fF**, graded at the
5.0 GHz band centre over C-grid. This is `sg13g2-vco` row 7's own figure.
Two cautions are recorded rather than resolved here (DR-001 §Consequences):

1. Row 7 says 3 % of `C_tot` = "≈ 2.1 fF", but 3 % of 88.51 fF is 2.66 fF.
   The smaller number is used (conservative). Clarification is requested
   on `sg13g2-vco` (DR-001 request R-VCO-2).
2. Row 7 frames the 1.5 % shift as the margin under the 5.5 GHz ceiling,
   but added capacitance lowers f0, so it also erodes the low end and the
   tuning ratio (row 2's fixed-C budget F ≤ 0.92·V). The loop therefore
   treats 2.1 fF as a ceiling on **both** ends and re-grades rows 1 and 2
   with the load attached (gate G2).

Load presented to the tank is stated as capacitance (fF, differential) and
as the equivalent shunt conductance at 5.0 GHz; both are reported with the
prescaler-loaded VCO re-check. Neither is claimed attainable by this spec:
a `npn13G2v` base input is plausibly larger than 2.1 fF, which is why the
buffer question (§6 Q1) is a named gate and not an assumption.

## 2. Target rows

Corner set **C-grid** = §Corner set. Method codes: **A** = arithmetic in
DR-001; **L** = linear phase-domain model (§4); **T** = ngspice transient
(§4); **N** = ngspice `.noise`/small-signal.

| # | Parameter | Min / Target | Typ | Max / Fallback / Stretch | Condition | Method | Corner set | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | Output frequency / channel plan | f_out = **5.0 GHz**, one channel | 5.0 GHz | fallback: one fixed channel; stretch: 4.5-5.5 GHz in 50 MHz steps (N = 90-110) | Inside VCO row 1 band; locked, at every C-grid corner | T (lock) at the loop-closed pass; A for the plan | C-grid | target, not met |
| 2 | Reference frequency | 50 MHz | 50 MHz | fallback 100 MHz; stretch 25 MHz | Square or sine into the PFD input; the reference source's own phase noise is a budget input (§4) | A | C-grid for the PFD | target, not met. **Gate G5**: `sg13g2-pll`'s recorded reference range is 3.5-24.4 MHz (its row 2, draft); 50 MHz is outside it |
| 3 | Division ratio | N = **100** (5.0 GHz / 50 MHz) | 100 | stretch: integer N = **90-110** (4.5-5.5 GHz at 50 MHz); fallback fixed N; fractional-N out of scope (stretch of a stretch) | `N = P·M + A`, P = 8 (see row 4), A ∈ [0, 7], M ≥ 7. N = 100: M = 12, A = 4; N = 90: M = 11, A = 2; N = 110: M = 13, A = 6. All integers in 90-110 are reachable | A | n/a | target, not met |
| 4 | Prescaler architecture | first stage: fixed **÷2** CML, SiGe HBT `npn13G2v`, at the VCO frequency; second stage: **÷4/5** (dual-modulus), so P = 8/9 and the prescaler output at 5.5 GHz is ≤ 687.5 MHz | | MOS-only CML first stage is the fallback; a different ratio needs a superseding record | Prescaler supply: the 3.3 V rail, own branch (§5). Input load: ≤ 2.1 fF (§1) | A for ratios; **sim owed** for load and speed | C-grid | target, not met. **Gate G1**: first-stage input capacitance and max toggle frequency are unsimulated. **Gate G3**: second-stage device flavor (HBT vs HV MOS CML at 2.5-2.75 GHz) chosen at design time |
| 5 | Loop bandwidth, phase margin, loop-filter order | f_c typ **1 MHz** | 1 MHz | f_c ∈ [**0.5**, **2.0**] MHz at every C-grid corner and across the Kvco range of §3; **PM ≥ 45°** (stretch ≥ 60°); loop filter: **type-II, third order** (series R1-C1 shunt, C2 shunt, plus one RC pole) | f_c is the open-loop unity-gain frequency of the linearized loop; PM at f_c. Bounds: f_c ≥ 0.5 MHz from the VCO budget (§4: ≥ 0.32 MHz needed, 1.6× margin); f_c ≤ 2 MHz leaves ≥ 2.5× below the `f_ref/10` = 5 MHz sampling rule | A (design equation: f_c = I_cp·R1·K_vco[Hz/V]/(2π·N)); L for graded value | C-grid, with Kvco range §3 | target, not met |
| 6 | Charge-pump current | I_cp typ **200 µA** (R1 ≈ 6.5 kΩ) | 200 µA | design range **100-400 µA** (trimmable) | Set by I_cp·R1 = 2π·N·f_c/Kvco = **1.31 V** at N = 100, f_c = 1 MHz, Kvco = 480 MHz/V (the geometric mid of §3). Larger I_cp / smaller R1 lowers loop-filter R1 noise (§4). The ±2× is an **allowance** for R and CP process spread, to be replaced by the graded spread | A | C-grid | target, not met |
| 7 | Charge-pump compliance and mismatch | output compliance from **1.65 V** up to V_hi,req | | up/down mismatch **≤ 2 %** of I_cp (fallback ≤ 6 %) across [1.65 V, V_hi,req], including both edges | V_hi,req ≡ the highest `Vctrl` at which any C-grid corner needs the VCO to reach 5.0 GHz, read off the VCO's graded f(Vctrl) grid. The VCO window top is 3.30 V, but a CP on the same 3.3 V rail (2.97 V at −10 %) cannot source current to 3.30 V; so the compliance request is **conditional on V_hi,req**, not a silent relaxation. Mismatch bound: arithmetic in DR-001 §Row 7 (spur −50 dBc ⇒ \|Vr\| ≤ 0.52 mV at f_ref) | A; N/T for graded | C-grid | target, not met. **Gate G4**: V_hi,req is owed by the VCO graded corner grid (`sg13g2-vco` #50, #53); if V_hi,req exceeds what the CP rail allows, the tank retarget goes to `sg13g2-vco` (R-VCO-1) or a superseding record here |
| 8 | Integrated rms jitter | ≤ **1.0 ps** | | fallback ≤ 2 ps; stretch ≤ 0.5 ps | Output at 5.0 GHz, locked, integrated **10 kHz-10 MHz** of the single-sideband phase noise (σ_φ = √(2∫L df), σ_t = σ_φ/(2π f_out)). 1 ps at 5.0 GHz = 31.4 mrad = −30.1 dBc integrated | **L primary; T cross-check**, §4 | C-grid | target, not met; **no jitter number is reported without its §4 method fields** |
| 9 | Reference spur | ≤ **−50 dBc** | | fallback ≤ −40; stretch ≤ −60 | First reference harmonic (offset = f_ref = 50 MHz) at the 5.0 GHz carrier, locked | T: locked transient, ≥ 40 reference periods after lock, FFT of v(Vctrl) at f_ref, mapped to dBc by Δf = Kvco_local·V_r, spur = 20·log10(Δf/(2·f_ref)) (small-index FM); cross-check on the VCO output spectrum where the run length allows | C-grid | target, not met. Derived ripple budget: V_r ≤ 0.52 mV peak at −50 dBc (DR-001 §Row 9) |
| 10 | Lock time | ≤ **20 µs** | | fallback ≤ 50 µs; stretch ≤ 10 µs | From enable with the initial `Vctrl` at the window edge farthest from lock, to the last instant the output frequency error exceeds ±1 MHz (±0.02 %) **and** the static phase error exceeds 5 % of T_ref (the 5 % criterion `sg13g2-pll` also uses) | T: transient with the real PFD/CP/filter/divider; no cycle-slip count claimed without the waveform | C-grid | target, not met |
| 11 | Loop power (excluding VCO core) | ≤ **20 mW** | | fallback ≤ 30; stretch ≤ 10 | Nominal rail, 5.0 GHz locked, 27 °C; includes prescaler, PFD, CP, filter bias, divider, lock detector, reference/clock buffering; excludes the VCO core (VCO row 8). Allocation (not derived): prescaler ≤ 10, CP + PFD + bias ≤ 2, post-prescaler counters + lock detector ≤ 4, reference and clock buffering ≤ 4 mW | A for allocation; T/DC op for graded | nominal, then C-grid | target, not met |
| 12 | Supply plan | see §5 | | | | review | C-grid | target, not met |
| 13 | PVT corner set | see §Corner set | | | | | | target |
| 14 | Signoff | DRC + LVS clean with the VCO in place; post-layout re-verified | | | `klt drc`, `klt lvs`, `klt extract` on the integrated layout | tool | n/a | target, not met |

## 3. Kvco range the loop is designed and graded over

`sg13g2-vco` row 3 ratifies a floor (\|Kvco\|_mean ≥ 381 MHz/V over W) and
**no ceiling**. Loop bandwidth and phase margin need both, so this spec
derives one from ratified rows and also records a request.

- **Floor**: 381 MHz/V (VCO row 3, mean over W).
- **Derived ceiling**: VCO row 1 ratifies the band 4.5-5.5 GHz and grades
  it at the corners row 10 settles. If the whole tuning curve over W lies in
  the band, the window span f(1.65) − f(3.30) ≤ 1.0 GHz, so
  \|Kvco\|_mean ≤ 1.0 GHz / 1.65 V = **606 MHz/V**.
- **Design range** (mean Kvco over W, every C-grid corner): **381-606
  MHz/V** (ratio 1.59). The loop is designed at the geometric mid,
  **480 MHz/V** (√(381·606)).
- **Local slope**: VCO row 3 allows chord nonlinearity ≤ 30 % of span, so
  segment Kvco departs from the mean. No local-slope bound is ratified. The
  loop is graded for PM ≥ 45° on the VCO's **graded f(Vctrl) curve** once it
  exists (gate G4's input), not on an assumed multiplier.
- **Caveat on the ceiling**: it assumes row 1 means "the tuning curve stays
  inside 4.5-5.5 GHz", which row 1's text does not state in those words.
  Request R-VCO-1 asks `sg13g2-vco` to ratify a ceiling explicitly.

## 4. Noise methods and the phase-noise budget

ngspice has no periodic-noise analysis. Every phase-noise, jitter and spur
number in this repo states, next to the number: the method (L or T), run
length, window, estimator, and the linear model's inputs.

### Primary: linear phase-domain model (method **L**)

- **Model**: single-sided phase noise referred to the output; transfer
  functions of a type-II third-order charge-pump PLL with divide ratio N,
  open-loop gain from §2 row 5. Contributions: reference × N², PFD/CP
  input-referred noise × N², R1 thermal noise through Kvco, divider/prescaler
  jitter, and the VCO's L(f) high-passed by the loop. First-order: it
  ignores in-loop peaking, sampling-time effects and charge-pump nonlinearity.
- **Inputs, each with its source**: VCO L(f) from `sg13g2-vco` row 4's
  measurement (**the method of that row is open there**; until it closes,
  the free-running input is the 1/f² line through −105 dBc/Hz @ 1 MHz, a
  target, and every L result says so); CP, PFD and prescaler noise from
  ngspice small-signal `.noise` at the locked operating point (N), reported
  per C-grid corner; R1 from 4kT·R1; the reference-source phase noise as a
  stated requirement.
- **Estimator**: integrate L(f) over 10 kHz-10 MHz on a log grid, ≥ 10
  points per decade, trapezoid on log-f, σ_φ² = 2∫L df.
- **Variance and limits**: deterministic given its inputs; its error is
  the inputs' error. It does not capture supply or substrate coupling
  into the tank: those are graded post-layout with the VCO in place.

### Cross-check: transient noise (method **T**)

- ngspice transient noise on the loop with noise sources enabled; **window
  ≥ 100 µs** (one period of the 10 kHz lower integration edge), **≥ 8
  non-overlapping windows** averaged (Welch-style) for variance;
  time-interval-error from the output (or the ÷N output) zero crossings.
  Whether a full 5 GHz transient noise run of this length is affordable is
  **gate G6**; if not, the cross-check runs on the divided-down output with
  the VCO as its measured L(f) behavioural noise source, and says so.
- Every grid is submitted as a `klt sim` request (corners/Monte Carlo), not
  hand-launched.

### Budget (an allocation, not a derivation; arithmetic in DR-001 §Row 8)

| Share | rad² (of 9.87·10⁻⁴ = 1 ps at 5 GHz) | Basis |
|---|---|---|
| In-band (reference, PFD/CP, divider) | ≤ 5·10⁻⁴ | ⇒ ≤ −98 dBc/Hz at the output in-band ⇒ ≤ −138 dBc/Hz referred to the PFD input |
| VCO outside f_c | ≤ 2·10⁻⁴ | 1/f² line at −105 dBc/Hz @ 1 MHz needs f_c ≥ 0.32 MHz |
| R1, CP shaping, supply/substrate coupling, spur-related | ≤ 2.9·10⁻⁴ (remainder) | allocation |

A free-running VCO at the same L(f) integrates to ≈ 2.5 ps over 10 kHz-10
MHz (6.3·10⁻³ rad²), so the loop is required, not optional.

## 5. Supply plan

- **Rails**: one external 3.3 V nominal rail (2.97-3.63 V), matching VCO row
  0. No other rail is assumed; the 1.2 V core digital rail of the program's
  chip-level wrapper is not used inside this block.
- **Device flavors**: VCO — `npn13G2v` pair, HV MOS varactor (VCO row 0).
  Prescaler first stage — `npn13G2v` CML. PFD, charge pump, loop filter,
  lock detector, counters — 3.3 V thick-oxide MOS (`sg13_hv_nmos/pmos`), the
  flavor `sg13g2-pll` draft DR-002 uses. Loop-filter capacitors and resistors
  — PDK MIM and poly resistor.
- **VCO core isolation (requirement, no value yet)**: the VCO core is fed
  from its own branch off the rail with a dedicated bondpad/pin or an
  on-chip RC/LC filter separating it from the prescaler, charge pump and
  digital branches; the loop-filter ground and the VCO tank ground are not
  shared with digital return currents. Graded by VCO row 9 (pushing ≤ 50
  MHz/V) with the loop's supply ripple as the stimulus; the quantity and
  limit are set when the isolation is simulated (gate G7). No isolation
  figure (dB, ohms) is claimed here.
- **Loop power** (row 11) is accounted separately from VCO row 8.

## 6. Open questions: answers or named gates

| Q | Answer | Gate |
|---|---|---|
| Q1 Output buffer? | **Decision: if one is needed it is designed here** (README scope), not folded into the VCO. Because its input loads the tank nodes, it still **supersedes VCO row 7's "no output buffer" load statement** and re-grades VCO rows 1 and 2, so a record on `sg13g2-vco` is required either way (R-VCO-3). Whether one is needed is decided by the first-stage input capacitance versus the 2.1 fF budget | G1, G2 |
| Q2 Swing/startup with prescaler load? | Not claimed. Load budget is stated (§1). The re-check of VCO rows 1, 2, 6, 7 with the load attached is a later simulation issue | G2 |
| Q3 Adopt-or-keep of `sg13g2-pll` blocks | §7 | G5 |
| Q4 Closed-loop phase-noise estimation | §4: linear model with simulated component noise, cross-checked by transient noise | G6 |
| Q5 Inductor keep-out, guard ring, fill; does `klt` check it? | Requirement: the inductor's keep-out (no active devices, no metal fill, no substrate taps inside the exclusion region), the surrounding guard ring, and the fill rules around the thick top metals are drawn at layout time from the PDK's rules and the EM study in `sg13g2-vco`. As of `klt 0.7.1.dev1754+g81ac4d3915c1` the command list (`klt --help`; `klt precheck` checks) has `drc`, `ring-check` (closed annulus), `tap-distance` and `precheck`, and no command that checks an inductor exclusion region or fill-around-inductor; it is therefore a tool gap, filed generically as `2AMLogic/klayout-tools#3849` | G8 |

## 7. Adopt-or-keep: `sg13g2-pll` sub-blocks

All cite `sg13g2-pll` @ `83e59fe` and its unratified draft target spec. That repo's
flavor is SG13CMOS5L, 3.3 V thick-oxide CMOS; this repo is SG13G2 BiCMOS.
Its VCO is a ring oscillator, so none of its loop numbers (f_ref 3.5-24.4
MHz, N 64-127, I_cp ladder 2.5-80 µA, R1 ≈ 344 kΩ) carry over.

| Block | Decision | Reason |
|---|---|---|
| `pfd` | **Adopt, conditional** on a re-grade at 50 MHz (G5) | Same 3.3 V HV MOS flavor and rail. Its recorded reference range stops at 24.4 MHz; 50 MHz is outside it |
| `cp` | **Keep (design here), reusing its topology as a starting point** | Its recorded I_cp ladder tops at 80 µA; this loop needs 100-400 µA (row 6). Compliance must reach V_hi,req (row 7) rather than the ring VCO's 0.3-2.7 V |
| `loop_filter` | **Keep (re-size)** | Its R1 ≈ 344 kΩ is sized for a ring VCO and µA currents; row 6 gives R1 ≈ 6.5 kΩ, and MOM/MIM capacitor values follow from f_c = 1 MHz |
| `divider_chain` | **Keep (rework the counter), maybe reuse retiming cells** | Recorded programmable range is N = 64-127; the post-prescaler counts here are M ≈ 7-13 (row 3). Its recorded one-edge closing bound is 825 MHz at `mos_tt`/−40 °C, 866 at 27 °C, 1277 at `mos_ff`/27 °C against a 687.5 MHz prescaler output (1.2× margin at the worst recorded corner; the `mos_ss`/125 °C bound is not recorded there) |
| `lock_detector` | **Adopt, conditional** | Analog block on the same flavor. Its assert window (≥ 2.5 ns) is f_ref-dependent per its DR-006; it must be re-graded at 50 MHz (G5) |
| Prescaler | **New, designed here** | No sibling block runs at the VCO frequency |

## Corner set (VCO row 10, DR-004 crossing)

The loop is graded on the **same grid** as the VCO so the two are comparable.

- **Stage 1 — 135 model-grid points at 3.300 V**: MOS {tt, ss, ff, sf, fs}
  × MIM {cap_typ, cap_bcs, cap_wcs} × HBT {hbt_typ, hbt_bcs, hbt_wcs} × T
  {−40, +27, +125} °C. (The HBT family joins because the VCO and the
  prescaler first stage use `npn13G2v`.)
- **Stage 2 — 18 supply sub-corners**: {2.970, 3.630} V × {SLOW, TYP, FAST}
  × {−40, +27, +125} °C, with SLOW = ss + hbt_wcs + cap_wcs, TYP = tt +
  hbt_typ + cap_typ, FAST = ff + hbt_bcs + cap_bcs (DR-004).
- **Loop-side crossing**: the loop's own devices use the same MOS and MIM
  and poly-resistor corner of the grid point they are on; they carry no
  corner axis the VCO lacks. Loop numbers (f_c, PM, jitter, spur, lock
  time, power) are reported **per grid point** and the spec bound applies
  at the worst point. The VCO's Kvco and V_hi,req come from the VCO's graded
  grid at the same point (gate G4). Stage 3 (the full 3-way cross, 405
  points) follows DR-004's falsifier: required if the supply sub-corners
  move any loop row by more than the margin stage 1 left on it.
- **Temperature**: −40 to +125 °C (VCO row 11).
- Statistical rows (jitter, spur) are not Monte Carlo here: no Monte Carlo
  record exists on either sibling, and this spec claims corner-bounded
  numbers only.

## Gates (consolidated)

| Gate | What closes it |
|---|---|
| G1 | Prescaler first-stage input capacitance and max toggle frequency simulated |
| G2 | VCO rows 1, 2, 6, 7 re-checked with the prescaler load (later sim issue) |
| G3 | Second-stage device flavor chosen |
| G4 | VCO graded f(Vctrl) over the 135 + 18 grid (`sg13g2-vco` #50, #53): gives V_hi,req and local Kvco |
| G5 | `sg13g2-pll` blocks re-graded at 50 MHz (PFD, lock detector) |
| G6 | Transient-noise cost versus run length |
| G7 | VCO-rail isolation simulated against row 9 |
| G8 | Inductor keep-out check available in `klt` or recorded as a tool gap |
