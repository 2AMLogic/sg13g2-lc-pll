#!/usr/bin/env bash
# scratch: split-rail power breakdown deck for the divider (cml2cmos vs counters/clock tree)
set -euo pipefail
R="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
S="$(mktemp -d)"; trap '[ -n "${KEEP_SCRATCH:-}" ] || rm -rf "$S"' EXIT
ROOT=$R; die() { echo "err: $*" >&2; exit 1; }; source "$R/scripts/lib-pdk.sh" 2>/dev/null
DIVNET="${1:-$R/design/netlist/divider.spice}"
sed -e "s|@@MODELS_DIR@@|${MODELS}|g" -e "s|@@OSDI_PSP@@|${OSDI_PSP}|g" \
  -e "s|@@PRESC_NETLIST@@|$R/design/netlist/prescaler.spice|g" -e "s|@@DIV_NETLIST@@|${DIVNET}|g" \
  -e "s|@@TSTOP@@|120n|g" -e "s|@@W0@@|40n|g" -e "s|@@OUT_DIR@@|$S|g" \
  "$R/sim/loop-power/loop_power.spice.tmpl" > "$S/base.spice"
python3 -I - <<EOF
t=open("$S/base.spice").read()
new="""XCV psp psn iref ck vcv 0 cml2cmos
XM ckl 0 0 vddd vddd tc tcn vddd 0 mcounter
XA ckl tc tcn 0 vddd mc vddd 0 acounter
XFB tc ckl fb vddd 0 dff_tg_hv
XBA ck ckb vddd 0 inv_hv
XBB ckb ckl vddd 0 inv_hv
XBC ckb ckl vddd 0 inv_hv
XBD ckb ckl vddd 0 inv_hv
VCV vcv 0 3.3"""
old="XDIV psp psn iref 0 0 vddd vddd 0 vddd mc fb vddd 0 divider"
assert old in t
t=t.replace(old,new)
t=t.replace("meas tran idavg avg i(vddd) from=40n to=120n","meas tran idavg avg i(vddd) from=40n to=120n\nmeas tran icv avg i(vcv) from=40n to=120n\nmeas tran ick avg i(vddd) from=40n to=120n")
t=t.replace(".save v(fb) v(mc) i(vddp) i(vddd)",".save v(fb) v(mc) i(vddp) i(vddd) i(vcv)")
open("$S/split.spice","w").write(t)
EOF
printf 'set ngbehavior=hsa\n' > "$S/.spiceinit"
cd "$S" && HOME="$S" "$NGSPICE" -b split.spice > split.log 2>&1
grep -E '^(ipavg|idavg|icv|OP_)' split.log
