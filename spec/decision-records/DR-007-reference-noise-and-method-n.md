# DR-007: The reference phase-noise requirement, the in-band split, and what method N means for the switching blocks

- **Status**: proposed (ratified by the record PR's Judge review plus Champion/operator merge, as DR-001)
- **Date**: 2026-11-13
- **Decided by**: Builder agent (issue #252, split out of #247)
- **Numbering**: DR-004 is proposed in PR #46 (closed unmerged, still cited on `main`) and DR-006 in open PR
  #207. DR-007 was free on 2026-11-13: a forge search for "DR-007" returned only issue #252, and
  `git grep DR-007` on `3706968` returned nothing. This record edits no earlier record.

## Context

Spec section 4 names two method-L inputs that nothing in the repository states precisely enough to compute.

1. **The reference-source phase noise**, "as a stated requirement" (`spec/target-spec.md:136`). No number is
   stated. The nearest text is DR-001 "Row 8": the in-band share of 5e-4 rad^2 gives "-138 dBc/Hz at the PFD
   input, a requirement on the reference and the PFD/CP" -- one figure for the sum of the in-band
   contributors, not a requirement on the reference alone.
2. **What method N means for the switching blocks.** `spec/target-spec.md:134` takes "CP, PFD and prescaler
   noise from ngspice small-signal `.noise` at the locked operating point (N)". `.noise` linearises about a
   DC operating point; the PFD/CP and the divider/prescaler are switching circuits. Which operating point,
   which small-signal quantity, and how that quantity maps to the model's input is unstated.

Until both are stated, the method-N bench (#253) has no testable acceptance and the reference term of the
method-L model (#247) has no input, so the row 8 result stays a floor of two terms out of five.

(Line references as of `3706968`.)

## Decision

### 1. The reference phase-noise requirement (R-REF-1)

**R-REF-1.** At 50 MHz (row 2), the external source shall satisfy **L_ref(f) <= L_ref,max** (single-sideband
phase noise at the PFD reference input) over **10 kHz to 10 MHz**, at every C-grid temperature. Qualify the
source against the loop as designed across row 5's f_c range of 0.5-2.0 MHz. For the committed filter over
its full 25-point design sweep the mask is **-148.0 dBc/Hz**.
To obtain the mask for a design, compute the method-L bandwidth at each graded C-grid point across the
section 3 Kvco range, including the operating charge-pump current at that corner. With G the open-loop gain,

    B_eff = integral from 10 kHz to 10 MHz of |G(f) / (1 + G(f))|^2 df
    L_ref,max [dBc/Hz] = 10 log10(2.0e-4 / max_grid(2 N^2 B_eff))

Round the resulting limit toward more negative dBc/Hz when quoting tenths.
Section 2 gives the design-point and sweep values. Recalculate when the filter or graded operating range
changes. This bounds the loop-weighted variance of any source meeting the mask by the reference's
2.0e-4 rad^2 share. Row 8 sets the integration band.

The source carrier and the PFD reference input are both at 50 MHz. Enter the mask directly in the model's
`reference_x_N2` input for a worst-case calculation, or enter the source's documented spectrum for its
contribution. Both take the on-chip reference buffer as noiseless (see "Not decided here").

**Catalog comparison.** At 50 MHz and 3.3 V the Statek CXOXLPN lists typical phase noise of -159 dBc/Hz at
10 kHz offset and -162 dBc/Hz at 100 kHz, 1 MHz and 5 MHz. These datasheet points sit 11 to 14 dB below
the design-sweep mask. Qualification requires a bound over the full offset band and all specified
temperatures. [Statek CXOXLPN datasheet, rev. F](https://statek.com/wp-content/uploads/2020/07/CXOXLPN-10226_REV-F.pdf)

### 2. The in-band split

DR-001's in-band share of **5e-4 rad^2** is split three ways. At N = 100 and f_c = 1 MHz, a *flat* L at the
PFD input integrates to an output-referred variance through DR-001 "Row 8"'s own arithmetic -- the equivalent
brick-wall noise bandwidth BW_n = (pi/2) x f_c = 1.5708 MHz and the 20 log10(N) = 40 dB of division:

    sigma_phi,out^2 = 2 x N^2 x L_in x BW_n = 3.1416e10 x L_in       [rad^2]
    L_in            = sigma_phi,out^2 / 3.1416e10                    [1/Hz]

and the equivalent rms time jitter at the 5.0 GHz output is sigma_t = sqrt(sigma_phi,out^2) / (2 pi x 5 GHz).

| Share of the in-band 5e-4 rad^2 | rad^2 (output-referred) | DR-001 brick-wall flat equivalent at N = 100, f_c = 1 MHz (PFD input) | Output rms at 5 GHz |
|---|---|---|---|
| Reference (external source) | <= 2.0e-4 | 6.366e-15 = **-142.0** dBc/Hz (-141.96 unrounded) | 450 fs |
| PFD/CP | <= 2.0e-4 | 6.366e-15 = **-142.0** dBc/Hz (-141.96 unrounded) | 450 fs |
| Divider/prescaler | <= 1.0e-4 | 3.183e-15 = **-145.0** dBc/Hz (-144.97 unrounded) | 318 fs |
| **Sum (unchanged from DR-001)** | **5.0e-4** | 1.592e-14 = **-138.0** dBc/Hz | 712 fs |

**Method-L acceptance (#253 / #86).** At **every graded C-grid point across the section 3 Kvco range**,
integrate each term's PFD-input spectrum over 10 kHz to 10 MHz with the local gain
`2 N^2 |G/(1+G)|^2`. Compare the three output variances with 2.0e-4, 2.0e-4 and 1.0e-4 rad^2 respectively.
For the middle term, the pump and PFD edge contributions together must fit 2.0e-4. Report the worst point
for each term. Check row 5's bandwidth and phase margin independently.

For example, with the committed `loop-filter.json`, enter one constant point per term (-142 / -142 /
-145 dBc/Hz at 10 kHz) in `sim/loop-model/loop_model.py --noise-inputs`. At 200 uA, 480 MHz/V,
f_c = 1.000 MHz, the model gives 2.967e-4 / 2.967e-4 / 1.487e-4 rad^2 by trapezoidal integration on
its 30-points/decade log grid. Here B_eff = 2.3513 MHz, so the flat limits rounded down to tenths are
-143.8 / -143.8 / -146.8 dBc/Hz. At -142 dBc/Hz the reference variance spans 1.444e-4 to 7.805e-4 rad^2
over the full 100-400 uA by 381-606 MHz/V design sweep. Its largest B_eff is 6.1848 MHz at 400 uA,
606 MHz/V (f_c = 2.172 MHz, PM = 39.7 degrees), giving -147.913 dBc/Hz before rounding. Including that
row-5 failure gives a conservative mask. At -148.0 dBc/Hz the largest reference variance over the 25
points is 1.9604e-4 rad^2. C-grid qualification uses the realized corner inputs.

**This table is an allocation, not a derivation.** No method-N or method-T number exists for any of the three
terms, so nothing here is evidence that any of them is attainable. The three rad^2 figures sum to exactly
5.0e-4, the ratified in-band share; the three *rounded* dBc/Hz figures sum to 1.578e-14 = -138.02 dBc/Hz,
marginally inside the -137.98 dBc/Hz that 5.0e-4 rad^2 gives on the same brick-wall basis.

**Why this split.** DR-001 wrote one -138 dBc/Hz figure as "a requirement on the reference and the PFD/CP"
and named the divider in the row without quantifying it. Absent any evidence that one of those two is cheaper
than the other, equal halves is the neutral split; the divider takes the remainder. The illustration below is
the only datum pointing either way, and it puts the charge pump inside 2.0e-4 for a reset overlap under about
390 ps, which is the range a 50 MHz PFD reset chain is designed in. A superseding record moves the split once
method-N and method-T numbers exist.

**Row 8's limit, the 5 / 2 / 2.9 e-4 allocation and the -138 dBc/Hz total are unchanged.** This record splits
the in-band share; it does not relax it. DR-001 is not edited (records are append-only, `spec/README.md`).

**Bandwidth and division-ratio sensitivity.** At N = 100, all brick-wall dBc/Hz equivalents shift by
-10 log10(f_c / 1 MHz) through row 5's 0.5-2.0 MHz band. The 2.0e-4 share reads -139.0, -142.0 and
-145.0 dBc/Hz at 0.5, 1.0 and 2.0 MHz, respectively (nearest tenth). The rad^2 shares and their 5 GHz
output-time equivalents stay fixed. R-REF-1 uses the actual B_eff, which also depends on loop shape.
Over the stretch band N = 90-110 the rad^2 shares are unchanged
and only the dBc/Hz column moves: holding f_c at 1 MHz it moves as -20 log10(N/100) (+0.92 dB at N = 90,
-0.83 dB at N = 110); letting f_c track N through row 5's design equation f_c = I_cp x R1 x Kvco / (2 pi N) at
fixed I_cp x R1 x Kvco, N^2 x BW_n is proportional to N and it moves as -10 log10(N/100) (+0.46 dB at N = 90,
-0.41 dB at N = 110). Both are under 1 dB. A stretch-band grade restates the column.

### 3. Method N for the PFD/CP

**Operating point.** The `.op` solution of `design/netlist/cp.spice` with **UP and DN both asserted** -- the
UP/DN reset-overlap state the pump is in during t_on in lock -- with its output held at the lock control
voltage V_ctrl by an ideal voltage source and its bias at the corner's IREF.

The pump is **current-steering**: `design/cp_leg_p.sch` and `design/cp_leg_n.sch` keep both tails conducting
at all times and switch them between VOUT and VDUMP. During overlap both legs steer to VOUT. During a
single-leg interval only the asserted leg steers to VOUT. With both switches released the tails steer to
VDUMP. The overlap state has a DC solution because neither leg is bistable. The nominal probe simulates
I_up = 196.273 uA and I_dn = 198.353 uA on the same netlist, giving I_up - I_dn = -2.080 uA.

V_ctrl in lock is per corner and comes from the VCO's graded f(V_ctrl) grid (**gate G4**). Until G4 closes, a
method-N number states the V_ctrl it used and is **not** a C-grid grade.

**Quantity read.** The charge pump's **short-circuit output current noise** S_i(f) [A^2/Hz] at VOUT, over
10 kHz to 10 MHz. ngspice's `.noise` reports a *voltage* amplitude density, so the current is read through a
0 V sense source plus a 1 V/A CCVS -- both noiseless -- after which `v(sense)` equals i_n in A/sqrt(Hz) and
S_i = i_n^2. The units are not assumed: the probe below calibrates `onoise_spectrum` against a 1 kohm
resistor, and a method-N record states the units it read and the calibration that fixed them.

**The loop filter is not in the deck.** The method-L model applies the loop shaping, and R1's thermal noise is
already a separate model term (`r1_thermal`); including the filter here would double-count it.

**Formula.** With d = t_on / T_ref the fraction of each reference period the leg's switch is on
(T_ref = 1/f_ref = 20 ns at row 2's 50 MHz), the time-averaged PSD of a white process gated on for a fraction
d of each period is d times the ungated PSD, and the pump's gain from phase error at the PFD input to average
output current is I_cp / (2 pi) A/rad. So

    S_phi,in(f) = S_i(f) x (t_on / T_ref) x (2 pi / I_cp)^2      [rad^2/Hz]
    L_in(f)     = S_phi,in(f) / 2                                [1/Hz, single sideband]
    L_in,dBc    = 10 log10(L_in(f))                              [dBc/Hz at the PFD input]

The both-on spectrum includes the correlation between the sourcing and sinking legs through their shared
bias. For unequal pulses, read their **actual overlap** and their UP-only and DN-only durations from the
same charge-balanced waveform. For each occupied state s, let d_s be its duration divided by T_ref.
Probe the **net VOUT current** in that state at the same forced V_ctrl and bias. In the first-order formula
replace `d S_i` with

    d_both S_both + d_up_only S_up_only + d_dn_only S_dn_only + d_off S_off .

Each duration counts once. Use the joint both-on spectrum throughout overlap, even when the pulses have
different widths. A sum of independent leg PSDs there loses the cross term. The simple overlap formula
assumes negligible both-dumped output noise. Record that state's spectrum or bound its contribution before
omitting it. The duration weighting applies directly to white noise. For slow flicker, the baseband PSD
depends on correlations between states. Within the stationary flicker approximation in Limits,
`(sum_s d_s sqrt(S_s,flicker))^2` bounds it for arbitrary correlation and is at most
`sum_s d_s S_s,flicker` (Cauchy-Schwarz). The equal-window 1/d factor below applies to one active state.

**The on-time is an input with a named source, not a constant.** t_on is the UP (and DN) pulse width taken at
**charge balance**, not at aligned edges: the REF-FB phase offset tau_0 at which the pump's average output
charge per reference cycle is zero at the corner's lock V_ctrl. In lock the loop sits at tau_0, not at zero
delay -- the `sim/pfd` sweep varies the physical REF-FB delay and its "Linear region" lines
(`sim/pfd/records/20261124-174920-c7e5a6b-dirty.md`, `20261030-183414-a9600e7.md`) show a non-zero charge per
cycle at zero delay (-162.5 / -160.7 fC nominal) and an interpolated zero-charge crossing near +945 / +926 ps.
A per-corner tau_0 is therefore read from that sweep (or its successor) at the chosen V_ctrl, and the UP and DN
widths and overlap are extracted **at tau_0** for the state weighting above. The existing PFD transient
`sim/pfd/pfd_sweep.spice.tmpl` instantiates the pinned `sg13g2-pll` PFD driving `design/cp.sch` at 50 MHz. Neither
`spec/target-spec.md` nor `design/netlist/cp.spice` states a reset delay or an on-time today, and that deck
saves only `i(VO)`, so the width is in no record yet -- adding it to the bench's outputs belongs to #253.
A method-N number states **the t_on it used, the record it came from, and the corner**: the reset chain's
delay is a gate delay and tracks the MOS corner and the temperature, so t_on is a per-corner input.

**The PFD's own noise is not a method-N term.** The PFD is sequential CMOS logic. Its `.op` solution is a
static latched state, not the state in which its output edges are formed, so a small-signal noise voltage at
one of its nodes does not map to the UP/DN edge timing the charge pump converts into charge. The PFD's
contribution is edge jitter on UP/DN, but **the observable is not the jitter of either pulse width alone**:
UP and DN share a reset, so their widths can fluctuate together, and a common extension of both pulses adds no
net charge (for ideal matched legs, +10 ps on both at 200 uA nets zero; the same +10 ps on UP alone nets
2 fC). Delta_t per reference cycle is therefore defined from the **net-charge-producing** part only, by either

- the fluctuation in the signed pulse-width difference (t_UP - t_DN) for matched legs, or
- the fluctuation in net charge per cycle dQ divided by the local charge-versus-input-delay slope dQ/dtau
  (C/s) at tau_0, i.e. Delta_t = dQ / (dQ/dtau),

and S_dt(f) is the PSD of that per-cycle series, taken jointly so the UP/DN correlation is preserved (never
the sum of two independent per-pulse PSDs). Then Delta_t is a phase error 2 pi x Delta_t / T_ref at the
PFD input:

    S_phi,in,pfd(f) = (2 pi f_ref)^2 x S_dt(f)

and is supplied by **method T** on the PFD alone, with section 4's transient-noise method fields (not yet run; see section 4, method T-div). A
`pfd_cp_x_N2` input that carries only the charge-pump part is a **floor** and says so. For grading,
combine the pump and PFD input spectra in linear power (include their cross spectrum if correlated).
The remaining allowance for PFD noise is the shared 2.0e-4 rad^2 less the loop-weighted pump contribution
when the two noise sources are independent.

### 4. The divider/prescaler: method N is withdrawn

A divider has **no DC operating point that represents its switching edge**. The `.op` solution of a CML or
CMOS divider chain is a latched state (or a converged metastable one), and `.noise` about it returns the
small-signal noise of a circuit sitting still. There is no path from that noise to the timing of an output
edge, because the edge is formed by a large-signal regenerative transition that the linearisation deletes.
Method N is therefore **not** retained for this block; `spec/target-spec.md:134`'s "CP, PFD and prescaler
noise ... (N)" is narrowed to the charge pump by the section 4 edit this record carries.

**Replacement -- method T-div.** A stand-alone transient-noise run on the prescaler plus counter chain,
clocked by an ideal 5.0 GHz source, reading the time-interval error x(t) of the /N output -- the edge the
PFD's feedback input actually sees. With S_x(f) its one-sided PSD [s^2/Hz], the conversion to the same plane
as every other term is

    S_phi,in(f) = (2 pi f_ref)^2 x S_x(f),   L_in(f) = S_phi,in(f) / 2

Its method fields are section 4's **method T** fields (window >= 100 us, >= 8 non-overlapping windows,
estimator named), not method N's.

**Method T has no model-derived device noise on the pinned ngspice-47.** The `.option TRANNOISE` switch
is accepted silently and injects nothing: a reviewer's probe of a 100 kOhm / 100 kOhm divider under
`.tran 1n 2u` returned a peak-to-peak of exactly zero over 2008 rows, whereas an explicitly instantiated
`trnoise()` current source on the same deck produced 8.8 uV p-p (reviewer-measured on this host, nominal,
a tool-capability probe; recorded in the PR #262 review, **not committed under `sim/`, method T not run
in this repository**). Transient noise exists in ngspice-47 only through `trnoise()` sources the author
instantiates by hand, so a method-T run needs one such source per noise-contributing device, with its
density named and sourced (e.g. from the `.noise` probe). Until a probe settles it, method T is a *named
but unexercised* method.

**Acceptance against the allocation.** At each graded corner #253 and #88 feed the /N-edge spectrum above
through the local method-L transfer (section 2). The target is <= 1.0e-4 rad^2 at the 5 GHz output,
equivalent to 318 fs rms **after loop weighting**. Raw band-integrated /N-edge jitter depends on the
spectrum and the corner bandwidth. Grading awaits the method-T source model and run described above.

Whether ngspice's transient noise is affordable on the divider chain alone is **not** settled here. The chain
takes 5 GHz in and puts 50 MHz out, far cheaper than the full-loop run behind gate G6, but it is still owed a
cost check (#253, #88).

### 5. The method fields a method-N number must carry

Next to the number, per CLAUDE.md "Noise needs its method". A number missing any of these is not a result.

1. **Block**, and the netlist file with its sha256, plus the repository commit.
2. **Corner**: MOS / MIM / HBT model corner, temperature, and supply.
3. **Operating point**: which inputs are asserted, every forced node voltage -- at minimum V_ctrl and the bias
   current -- and **the per-leg DC currents beside the residual**: I_up with UP asserted alone, I_dn with DN
   asserted alone, both at the same netlist, corner and forced nodes, so the record *shows*
   residual = I_up - I_dn rather than asserting it. The residual on its own does not establish the balanced
   steering state: with both switches dumping, the probe behind this record reads 4 fA, which also passes
   "small against a leg", and a deck with UP/DN polarity reversed would pass it too. Figures from another
   netlist revision do not substitute; cite the run that produced them and its netlist hash.
4. **Analysis** and its frequency range and point density (`.noise`, 10 kHz-10 MHz, points per decade).
5. **The quantity read**, its node, and **its units**, with the calibration that fixed the units.
6. **The conversion formula with the numeric value of every input**: I_cp, T_ref (= 1/f_ref), N and
   the durations and VOUT spectra (or bounds) for the occupied steering states.
7. **The source of the durations**: the record, corner, charge-balance offset and UP/DN overlap.
8. **What is excluded**: the PFD's edge-jitter term, the loop filter, and anything else not in the deck.
9. **Simulator version and the PDK / OSDI pins.**
10. The words **"simulated, not measured"**.

## Evidence

`sim/noise-probe/records/20261113-174218-8211fdd.md` -- ONE local `ngspice -b`, nominal corner
(`mos_tt` / `hbt_typ`), 27 C, nominal 3.3 V, one operating point. Simulated, no spec row graded. It settles
three things this record relies on and nothing else:

1. **Units.** `onoise_spectrum` is an amplitude density in V/sqrt(Hz), not a power density in V^2/Hz: a
   1 kohm resistor reads 4.071372e-09 against sqrt(4kTR) = 4.0714e-09 and 4kTR = 1.6576e-17.
2. **`.noise` returns device noise for the charge pump's models.** `sg13_hv_nmos` / `sg13_hv_pmos` through
   the pinned PSP103 OSDI give a non-zero spectrum with a 1/f region over a near-white floor
   (1.273e-10 A/sqrt(Hz) at 10 kHz, 1.793e-11 at 1 MHz, 1.338e-11 at 10 MHz). `cp.spice` instantiates no
   resistors, so all of it is device noise.
3. **`.noise` returns device noise for `npn13G2v`** (VBIC): the 1 MHz plateau is 1.591e-11 A/sqrt(Hz), 83 %
   in amplitude of full collector shot noise at the probed I_C = 1.160 mA.

Point 3 is recorded because the prescaler is HBT, even though this record takes the divider *out* of method N:
it removes "the models return no noise" as a reason, so the withdrawal in section 4 above rests on the
operating-point argument alone.

## Illustration (not a grade, and not a method-N number)

With the f_c = 1 MHz brick-wall allocation and the probe's integral of S_i df from 10 kHz to
BW_n = 1.5708 MHz = 1.0424e-15 A^2, I_cp = 200 uA
(row 6 typical), T_ref = 20 ns and N = 100, the formula in section 3 gives:

| t_on | d = t_on/T_ref | sigma_phi,out^2 (rad^2) | flat-equivalent L_in (dBc/Hz) |
|---|---|---|---|
| 200 ps | 0.010 | 1.03e-4 | -144.8 |
| 300 ps | 0.015 | 1.54e-4 | -143.1 |
| 400 ps | 0.020 | 2.06e-4 | -141.8 |
| 500 ps | 0.025 | 2.57e-4 | -140.9 |
| 1000 ps | 0.050 | 5.14e-4 | -137.9 |

At t_on = 389 ps the pump alone consumes the entire **joint PFD/CP** share of 2.0e-4 rad^2 in this
illustration, leaving zero allowance for independent PFD edge noise. At 972 ps it consumes the whole
5.0e-4 in-band share.

**Why this is not a grade**: one corner; a probe operating point at V_ctrl = 2.0 V rather than a per-corner
lock point; the PFD's own term excluded; an assumed t_on rather than a measured one; and -- the weakest step
-- the gating factor d applied to a spectrum that is flicker-dominated below about 300 kHz. It is here for one
reason: to show that t_on is the input this term turns on, which is why section 3 requires it be named with
its source.

## Limits

- **The gating model d x S_i is a first-order duty-cycle approximation, and for the flicker portion it is a
  conservative upper bound.** Gating a stationary current noise by a periodic window with duty d and
  Fourier coefficients c_k gives S_g(f) = sum_k |c_k|^2 S_i(f - k f_ref). The k = 0 term is d^2 S_i(f) -- the
  only term that reaches baseband for slowly varying noise, since flicker has no energy near k f_ref; the
  k != 0 terms fold in the white floor, (d - d^2) S_white. So S_g(f) ~ d^2 S_flicker(f) + d S_white, and
  d x S_i(total) over-estimates the flicker part by 1/d while being exact for the white part. This pump is
  current-steering (section 3): the tails conduct continuously and the switches route the current, a
  stationary flicker current only routed, which is the c_0 = d case. On the probe's integral (a K/f + W fit
  splits it roughly 70-75 % flicker / 25-30 % white, d = 0.01945 at t_on = 389 ps) the two-term form gives
  t_on of about 1.23 ns for the pump alone to fill the joint PFD/CP share and about 2.6 ns for the whole 5.0e-4, against
  389 ps and 972 ps under d x S_i: the table above is **pessimistic by roughly 3x**, not unbiased. This is
  re-derivation plus arithmetic on the committed probe log, not a simulation, and the split is a fit
  (+4.6 % on the measured integral), so treat the ratios as approximate. ngspice has no periodic-noise
  analysis to do better (`spec/target-spec.md:119`). A method-N number is a **first-order estimate whose
  flicker part is an upper bound**, and must say so.
- **The genuinely unknown-sign terms** are the next bullet's switching transients: they are not bounded by
  the duty-cycle argument, and no cross-check in this record bounds them while method T is unexercised.
- `.noise` about the overlap point ignores the switching transients at the edges of the window -- charge
  injection, clock feedthrough, the finite rise of the steering switch -- all of which are large-signal.
- The evidence is **one corner and one operating point**. Nothing here is a C-grid grade.
- Until gate G4 closes, no method-N number is at the real per-corner lock V_ctrl.
- The split in section 2 is an **allocation**. No evidence exists that any of its three terms is attainable.

## Alternatives considered

- **Exclude external source quality.** The sibling GF180 PLL assigns reference-source quality to the
  integrator. Here row 2 explicitly includes source noise in the budget and row 8 grades its transferred
  variance, so method L needs a bounded reference input. [GF180 PLL DR-019](https://github.com/2AMLogic/gf180-pll/blob/0221efb98ed5803ba36472a3dd51efa7df1ec6f7/spec/decision-records/DR-019-reference-input-contract-owner-and-source-quality-exclusion.md)
- **Keep one combined figure for reference plus PFD/CP.** Rejected: that is what DR-001 already has, and
  splitting it is what this record exists to do.
- **Write the method into the bench issue (#253) instead of `spec/`.** Rejected: CLAUDE.md requires a spec
  change to go through a decision record, and `spec/target-spec.md:134` is the text that is wrong.
- **Keep method N for the divider via `.noise` at a frozen mid-transition bias, divided by the edge slew
  rate.** Rejected: the frozen bias is not a solution of the circuit (it has to be forced into place), the
  slew rate is a large-signal quantity the linearisation does not produce, and the result would have no
  falsifier -- a number with an invented operating point and no way of being wrong. Section 4 already has a
  method for timing noise, with stated run-length and estimator rules.
- **Leave the PFD's own noise inside method N.** Rejected for the same operating-point reason as the divider.
- **Give the reference a 1/f-cornered mask instead of a flat floor.** Rejected for now: row 8's band starts at
  10 kHz, where a 50 MHz crystal source is already near its floor, so the flat form costs nothing and is
  simpler to check. A superseding record can add a corner if a chosen source needs one.
- **Split the in-band share unevenly in the charge pump's favour** (for example 1.5 / 2.5 / 1.0 e-4).
  Rejected: the only datum is the illustration above, which is not a grade, and sizing a ratified budget
  against a non-grade would read as evidence where there is none.

## Not decided here

- Any change to row 8's limit, to the 5 / 2 / 2.9 e-4 allocation, or to the -138 dBc/Hz total. DR-001 is not
  edited.
- **The value of t_on.** This record names it an input and names its source; it does not measure it.
- The bench, its decks, its `klt sim` C-grid and its negative control (#253), and the model's input interface
  (#247).
- Whether any of the three allocated shares is attainable. No method-N or method-T number exists yet.
- The split of R-REF-1 between the external source and the on-chip reference buffering: the model takes the
  buffer as noiseless and records that assumption. A buffer noise budget is owed when the buffer is designed
  (row 11 allocates it 4 mW together with the clock buffering).
- Choosing or qualifying a reference oscillator part.
- Whether transient noise is affordable, for the loop (gate G6) or for the divider chain alone (#253, #88).
- Qualification of the stretch band N = 90-110: section 2 gives the brick-wall sensitivity about the
  nominal N = 100, f_c = 1 MHz point. A stretch design recalculates its loop-weighted mask and grade.
