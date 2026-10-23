#!/usr/bin/env bash
# Negative control for scripts/run-cp-dc.sh: simulate a throwaway copy of the cp netlist
# with the PMOS (up) leg mirror + cascode widened 3.8u -> 4.6u (~+20 % I_up) and require the
# bench to report mismatch > 2 % at mid-window (2.00 V) and no window around 1.65 V.
# The skewed netlist and its records live in a scratch dir; nothing is committed by this.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT
awk '/^\.subckt cp_leg_p/ {p=1} /^\.ends/ {p=0} p && /^XM[12] / { sub(/w=3\.8u/, "w=4.6u") } {print}' \
  "${ROOT}/design/netlist/cp.spice" > "${T}/cp_skewed.spice"
if diff -q "${ROOT}/design/netlist/cp.spice" "${T}/cp_skewed.spice" >/dev/null; then
  echo "FAIL: the skew did not change the netlist"; exit 1; fi
echo "skew applied:"; diff "${ROOT}/design/netlist/cp.spice" "${T}/cp_skewed.spice" | grep '^>'
out="$(CP_NETLIST="${T}/cp_skewed.spice" RECORD_DIR="${T}/rec" "${ROOT}/scripts/run-cp-dc.sh" 2>&1)"; rc=$?
echo "${out}"
[ "${rc}" = 0 ] || { echo "FAIL: bench did not run (rc=${rc})"; exit 1; }
rec="$(ls "${T}"/rec/*.md | head -1)"
m200="$(awk -F'|' '$2+0==2.00 {gsub(/ /,"",$5); print $5}' "${rec}")"
echo "mismatch at 2.00 V with the skewed up leg: ${m200} %"
if awk -v m="${m200}" 'BEGIN{exit !(m>2.0)}' && grep -q 'mismatch at 1.65 V exceeds' "${rec}"; then
  echo "PASS: the bench flags the skewed charge pump (mismatch > 2 %, no window around 1.65 V)"
else
  echo "FAIL: the bench did not flag the skewed charge pump"; exit 1
fi
