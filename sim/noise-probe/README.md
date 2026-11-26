# sim/noise-probe

The method-N feasibility probe behind
[DR-007](../../spec/decision-records/DR-007-reference-noise-and-method-n.md): does
ngspice-47's small-signal `.noise` return device noise for the model families this loop's
switching blocks use, and in what units?

**This is a probe, not a bench.** One operating point, one corner, no negative control, no
corner grid, no run script, and no entry in `sim/testbench-inventory.json`. It exists so
DR-007 can say "`.noise` returns device noise for these models" with evidence instead of
with an assumption. The method-N bench -- the `.noise` decks, the `klt sim` C-grid, the
negative control and the per-corner records that actually supply the method-L model's
PFD/CP term -- is **issue #253**, and nothing here is a method-N result.

`records/` is dated and append-only.

## Transient source check

Run `ngspice -n -b sim/noise-probe/trannoise.spice` from the repository root.
The deck places two identical 100 kΩ dividers on a 1 V DC rail at 27 °C under
`.option TRANNOISE=1`. Only the second has an explicit `trnoise(40p 1n 0 0)`
current source. It takes the peak-to-peak voltage of each midpoint over the same 2 µs.
The ngspice-47 run produced 0 V and 8.95 µV, respectively. The random span can
vary on replay. The check is zero span on the first midpoint and nonzero span on
the second. This tool check uses ideal components and an illustrative source
amplitude. The PFD and divider still need calibrated noise sources and timing
runs for method T. [Simulated output](records/20261126-083942-a8f665e-trannoise.txt)

## Reproduce the method-N probe

Needs an `ihp-sg13g2` install and `ngspice`. Substitute the placeholders by hand (there is
no driver script on purpose -- a driver would make this a bench):

```bash
PDK=<parent of ihp-sg13g2>/ihp-sg13g2
M="${PDK}/libs.tech/ngspice/models"
W="$(mktemp -d)"
sed -e "s|@@MODELS_DIR@@|${M}|g" \
    -e "s|@@CP_NETLIST@@|$PWD/design/netlist/cp.spice|g" \
    -e "s|@@OSDI_PSP@@|${PDK}/$(jq -r .psp103.osdi sim/pins.json)|g" \
    -e "s|@@OSDI_PSP_NQS@@|${PDK}/$(jq -r .psp103_nqs.osdi sim/pins.json)|g" \
    -e "s|@@DATA_OUT@@|${W}/cp_noise.data|g" \
    sim/noise-probe/method_n_probe.spice.tmpl > "${W}/method_n_probe.spice"
printf 'set ngbehavior=hsa\n' > "${W}/.spiceinit"
( cd "${W}" && HOME="${W}" OMP_NUM_THREADS=2 ngspice -b method_n_probe.spice )
```

Keep `OMP_NUM_THREADS` at 2: the host is shared.

## Finding (see the record)

`records/20261113-174218-8211fdd.md`, nominal corner, simulated, no spec row graded:

1. `onoise_spectrum` is an **amplitude** density in V/sqrt(Hz). A 1 kohm resistor reads
   4.071372e-09, against sqrt(4kTR) = 4.0714e-09 and 4kTR = 1.6576e-17.
2. The charge pump (`sg13_hv_nmos` / `sg13_hv_pmos`, PSP103 OSDI) returns non-zero device
   noise with a 1/f region over a near-white floor. `cp.spice` has no resistors, so all of
   it is device noise.
3. `npn13G2v` (VBIC) returns non-zero device noise, with the 1 MHz plateau at 83 % of full
   collector shot noise in amplitude.
4. At the probed operating point the pump's two legs are both live at the output:
   I_up = 196.273 uA, I_dn = 198.353 uA, difference -2.080 uA, which is the probed point's
   own residual. Measured by three single-leg copies in the same deck and run, so the
   record shows the balanced steering state instead of asserting it from another run.

What the probe does **not** settle -- the gating approximation for flicker noise, any other
corner, the PFD, the divider, and the charge pump's on-time in lock -- is listed in the
record and in DR-007 "Limits".
