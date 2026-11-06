#!/usr/bin/env bash
# scratch: run the unsplit loop-power deck against a variant divider netlist; usage: runvar.sh NBUF TAG
set -euo pipefail
R=/home/ubuntu/GitHub/sg13g2-lc-pll/.loom/worktrees/issue-84
S=/tmp/issue84-scratch/$2; mkdir -p "$S"
ROOT=$R; die() { echo "err: $*" >&2; exit 1; }; source "$R/scripts/lib-pdk.sh" 2>/dev/null
python3 -I /tmp/issue84-scratch/mkvar.py "$R/design/netlist/divider.spice" "$S/divider_var.spice" "$1"
sed -e "s|@@MODELS_DIR@@|${MODELS}|g" -e "s|@@OSDI_PSP@@|${OSDI_PSP}|g" \
  -e "s|@@PRESC_NETLIST@@|$R/design/netlist/prescaler.spice|g" -e "s|@@DIV_NETLIST@@|$S/divider_var.spice|g" \
  -e "s|@@TSTOP@@|120n|g" -e "s|@@W0@@|40n|g" -e "s|@@OUT_DIR@@|$S|g" \
  "$R/sim/loop-power/loop_power.spice.tmpl" > "$S/deck.spice"
printf 'set ngbehavior=hsa\n' > "$S/.spiceinit"
cd "$S" && HOME="$S" "$NGSPICE" -b deck.spice > ng.log 2>&1
grep -E '^(ipavg|idavg)' ng.log
awk 'NR>1 && p<1.65 && $2>=1.65 { n++; te=$1; if (n>1) {s+=te-last;k++} last=te } {p=$2}  END {printf "FB edges %d mean period %.3g ns\n", n, (k?s/k*1e9:0)}' fb.data
