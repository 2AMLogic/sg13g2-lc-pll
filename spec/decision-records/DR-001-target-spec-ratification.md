# DR-001: Target-spec ratification (LC PLL, targets only)

- **Status**: ratified
- **Date**: 2026-10-17
- **Decided by**: Builder agent (issue #2), ratified by the record PR's Judge
  review plus Champion/operator merge. This repo has no `ratification/` tree,
  so the two-key mechanism is the one `sg13g2-vco` uses (DR-003, DR-004).

## Context

`spec/` was empty and the README's target table was an unratified draft, so nothing
downstream (prescaler, loop, layout, signoff) had a graded bound. Issue #2
asks for the spec and this record. Inputs: `sg13g2-vco` @ `17e49a8` (12
ratified-as-target rows, none measured) and `sg13g2-pll` @ `83e59fe` (draft
spec, SG13CMOS5L). `reuse.lock.json` does not exist yet (#3), so both are
cited by SHA.

**Rule followed**: every bound is a cited ratified row or arithmetic written
below. Where a bound needs simulation it is left to a named gate (G1-G8 in
the spec). Nothing here is measured.

## Decision

Ratify `spec/target-spec.md` as a set of **targets**, binding and not met.
The VCO interface table cites each `sg13g2-vco` row with its record. The
arithmetic behind each derived number follows. Constants: f_out = 5.0 GHz,
f_ref = 50 MHz.

### Row 3: divide ratio

N = 5.0 GHz / 50 MHz = **100**. Stretch band 4.5-5.5 GHz: N = 4.5 GHz/50 MHz
= 90 to 5.5 GHz/50 MHz = 110, so **90-110**. Dual-modulus pulse-swallow
N = P·M + A with P = 8: N = 100 → M = 12, A = 4 (8·12 + 4); N = 90 → M = 11,
A = 2; N = 110 → M = 13, A = 6. Every integer in 90-110 is reachable
(A ∈ [0, 7], M ≥ 7).

### Row 4: prescaler ratio

The `sg13g2-pll` divider's recorded one-edge closing bound is 825 MHz at
`mos_tt`/−40 °C (866 at 27 °C, 1277 at `mos_ff`/27 °C). A fixed ÷4 gives
5.5/4 = 1.375 GHz > 825 MHz; ÷8 gives 5.5/8 = **687.5 MHz**, 1.2× under 825.
A fixed ÷8 cannot make N = 100 (100/8 = 12.5), so P = 8/9: a fixed ÷2 CML at
the VCO frequency, then a dual-modulus ÷4/5 at 2.5-2.75 GHz. The `mos_ss`/125
°C bound is not recorded in `sg13g2-pll`, so the 1.2× is a margin at the
worst *recorded* corner only (gate G5).

### Section 3: Kvco range

VCO row 3 gives a floor, 381 MHz/V, and no ceiling. VCO row 1 bounds the
tuning curve to 4.5-5.5 GHz, so span ≤ 1.0 GHz and mean Kvco over W
(1.65 V) ≤ 1.0 GHz / 1.65 V = **606 MHz/V**. Design mid:
√(381 × 606) = 480.5 → **480 MHz/V**. This rests on reading row 1 as "the curve
stays inside the band"; the request below asks the VCO to ratify a ceiling.

### Row 5/6: loop bandwidth and charge-pump current

Open-loop gain between the zero and the third pole is
(I_cp/2π)·R1·(2π·K_vco[Hz/V])/(N·2π f) ⇒ unity gain at
f_c = I_cp·R1·K_vco[Hz/V] / (2π·N). Solving for the product:
I_cp·R1 = 2π·100·1 MHz / 480 MHz/V = **1.31 V**. At I_cp = 200 µA,
R1 = 6.5 kΩ. With the Kvco range 381-606 and the product fixed, f_c =
0.79 MHz at 381 and 1.26 MHz at 606, inside the ratified f_c ∈ [0.5, 2.0] MHz.
f_c ≤ 2.0 MHz is 2.5× under f_ref/10 = 5 MHz.

Why I_cp is large: unfiltered R1 thermal noise is 4kT·R1; at R1 = 16.4 kΩ
(I_cp = 80 µA) it is 16.5 nV/√Hz, times Kvco 480 MHz/V is 7.9 Hz/√Hz, i.e.
L = 7.9²/(2·(1 MHz)²) = 3.1·10⁻¹¹ = **−105 dBc/Hz at 1 MHz** — equal to the
VCO's own target, before C2 filtering. At R1 = 6.5 kΩ it is ~−109 dBc/Hz.
The design range 100-400 µA is 0.5×-2× typ, an **allowance**.

### Row 7: charge-pump mismatch

See Row 9 below for the ripple budget V_r ≤ 0.52 mV. Mismatch ΔI produces a
net pulse of width t_off = (ΔI/I_cp)·t_rst at amplitude I_cp, so a ripple of
first-harmonic amplitude ≈ 2·I_cp·R1·(ΔI/I_cp)·(t_rst/T_ref)·a, with a the
filter attenuation at f_ref. Assuming (**stated allowances, not derived**)
t_rst = 0.1·T_ref and a = 0.1 (−20 dB at 50 MHz from the third pole), V_r =
2·1.31 V·δ·0.1·0.1 = 26 mV·δ; V_r ≤ 0.52 mV gives δ ≤ **2 %**. At −40 dBc
(3.16× looser) δ ≤ 6.3 %, stated as 6 %. Both assumptions are replaced by
simulated values at the loop-closed pass.

The compliance question: the VCO window runs to 3.30 V, but a charge pump
on the 3.3 V rail has 2.97 V at −10 %, and cannot source to 3.30 V.
So the compliance request is stated against **V_hi,req** (highest `Vctrl`
the 5.0 GHz channel needs at any corner), a number the VCO's graded
f(Vctrl) grid will give (gate G4). This is a conditional row, not a relaxed
one: if V_hi,req exceeds what the CP rail allows, the response is a request
on `sg13g2-vco` or a superseding record, not a silent edit.

### Row 8: jitter and the noise budget

σ_t = σ_φ/(2π f_out); 1 ps · 2π · 5.0 GHz = 0.0314 rad, σ_φ² =
9.87·10⁻⁴ rad² = −30.1 dBc. Free-running VCO: 1/f² line L(f) = L₁(f₁/f)²,
L₁ = 10^(−10.5) = 3.16·10⁻¹¹ at f₁ = 1 MHz. Out-of-band (above f_c) share
= 2·L₁·f₁²·(1/f_c − 1/10 MHz). Without a loop (f_c = 10 kHz): 2 × 3.16·10⁻¹¹
× 10¹² × (10⁻⁴ − 10⁻⁷) = 6.3·10⁻³ rad² = 79 mrad = **2.5 ps**, so the free
oscillator misses 1 ps by 2.5×. For the VCO share ≤ 2·10⁻⁴ rad²:
1/f_c ≤ 2·10⁻⁴/(6.32·10⁻²) + 10⁻⁷ = 3.26·10⁻³ s ⇒ f_c ≥ **0.31 MHz**
(0.32 MHz stated); 0.5 MHz is the ratified floor, 1.6× margin.
In-band share ≤ 5·10⁻⁴ rad² over a noise bandwidth (π/2)·f_c = 1.57 MHz:
L_out ≤ 5·10⁻⁴/(2·1.57·10⁶) = 1.6·10⁻¹⁰ = −98 dBc/Hz; minus 20·log₁₀(100) =
40 dB gives **−138 dBc/Hz** at the PFD input, a requirement on the reference
and the PFD/CP. The split 5 / 2 / 2.9 ·10⁻⁴ is an **allocation**.
The rest of the budget (2.9·10⁻⁴) is the remainder.

### Row 9: reference spur

−50 dBc = 20·log₁₀(β/2) ⇒ β/2 = 3.16·10⁻³ ⇒ β = Δf/f_ref = 6.3·10⁻³ ⇒
Δf ≤ 316 kHz. With Kvco at the ceiling 606 MHz/V, V_r ≤ 316 kHz/606 MHz/V
= **0.52 mV** peak at f_ref. This uses the mean Kvco ceiling, not a local
slope, and says so in the spec.

### Row 11: power

20 mW target (README). The split (prescaler ≤ 10, CP + PFD + bias ≤ 2, counters
+ lock detector ≤ 4, reference/clock buffering ≤ 4 mW) is an **allocation**;
I_cp = 200 µA from 3.3 V is 0.66 mW, a small share.

## Alternatives considered

- **Ratify the README table verbatim.** No method or corner set; fails the
  acceptance.
- **Pick a hard Kvco ceiling by fiat.** An invented number; the ceiling is
  derived from row 1 and a request is made instead.
- **Fixed ÷8 and N = 96 or 104.** Moves f_ref off 50 MHz or f_out off 5.0 GHz;
  one channel at 5.0 GHz from 50 MHz is the target.
- **Adopt `sg13g2-pll`'s `divider_chain`, `cp`, `loop_filter` as is.** Their
  recorded ranges (N 64-127, I_cp ≤ 80 µA, R1 ≈ 344 kΩ, f_ref ≤ 24.4 MHz) do
  not contain this loop's values; see the spec §7.
- **Resize or buffer the VCO here.** Out of scope; asks go to `sg13g2-vco`.

## Consequences

- Downstream issues (prescaler, loop, layout) have bounds to design and grade
  against. None is met until a graded pass exists.
- **Requests to raise on `2AMLogic/sg13g2-vco`** (stated here, not filed by
  this record; the PR description lists them for the Champion/operator):
  - **R-VCO-1**: ratify a mean-|Kvco| ceiling and a local-slope bound (this
    spec derived 606 MHz/V from row 1).
  - **R-VCO-2**: row 7 says a 3 % change in `C_tot` ≈ 2.1 fF, but 3 % of
    88.51 fF = 2.66 fF; and the 1.5 % shift is described as margin under the
    ceiling although added capacitance lowers f0. Clarify direction and
    value.
  - **R-VCO-3**: if the first stage cannot fit in the load budget, a buffer
    supersedes row 7 and re-grades rows 1 and 2.
- The 2.1 fF budget is tight; it may be unachievable with an `npn13G2v` input,
  which would force the buffer. That is the highest risk this spec records.
- Bad consequence: several numbers (t_rst, filter attenuation, allocations,
  ±2× I_cp window, 1.2× divider margin) are stated allowances. The graded pass
  may move them, and doing so needs a superseding record, not an edit.
- `klt` has no inductor keep-out/fill check as of `0.7.1.dev1754`; a friction
  issue is filed as `2AMLogic/klayout-tools#3849`.
