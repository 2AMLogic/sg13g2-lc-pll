#!/usr/bin/env bash
# Negative controls for scripts/run-prescaler-g1.sh. Two throwaway copies of the prescaler netlist, each
# deliberately wrong in one way, must be flagged by the bench:
#   A (slowed / mis-biased): the first-stage latch tail resistor 600 ohm -> 60 kohm, so the tail current collapses
#       to a few uA: the /2 must NOT toggle up to the 5.5 GHz band top (toggle verdict FAIL).
#   B (oversized input): the first-stage input emitter followers Nx = 1 -> 4: the differential input capacitance
#       must exceed the 2.1 fF budget (capacitance verdict EXCEEDS).
# The skewed netlists and their records live in a scratch dir; nothing is committed by this.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT
SRC="${ROOT}/design/netlist/prescaler.spice"
fail=0

# A: first-stage latch tail resistor (inside div2_latch_hs) 600 -> 60k
awk '/^\.subckt div2_latch_hs/ {p=1} /^\.ends/ {p=0} p && /^RT / { sub(/ 600 /, " 60k ") } {print}' "${SRC}" > "${T}/a.spice"
# B: first-stage input followers (inside div2_ef_hs) Nx=1 -> Nx=4
awk '/^\.subckt div2_ef_hs/ {p=1} /^\.ends/ {p=0} p && /^XQE[12] / { sub(/Nx=1 /, "Nx=4 ") } {print}' "${SRC}" > "${T}/b.spice"
for x in a b; do
  if diff -q "${SRC}" "${T}/${x}.spice" >/dev/null; then echo "FAIL: skew ${x} did not change the netlist"; exit 1; fi
  echo "skew ${x} applied:"; diff "${SRC}" "${T}/${x}.spice" | grep '^>'
done

echo; echo "== control A: starved first-stage latch tail =="
out="$(PRESC_NETLIST="${T}/a.spice" RECORD_DIR="${T}/reca" G1_FLIST="2e9 4e9 6e9 10e9" "${ROOT}/scripts/run-prescaler-g1.sh" 2>&1)"; rc=$?
echo "${out}"
if [ "${rc}" = 0 ] && grep -q 'required >= 5.5 GHz: FAIL' <<<"${out}"; then
  echo "PASS: the bench flags the starved stage (toggle verdict FAIL)"
else echo "FAIL: the bench did not flag the starved stage (rc=${rc})"; fail=1; fi

echo; echo "== control B: oversized input followers =="
out="$(PRESC_NETLIST="${T}/b.spice" RECORD_DIR="${T}/recb" G1_FLIST="6e9" "${ROOT}/scripts/run-prescaler-g1.sh" 2>&1)"; rc=$?
echo "${out}"
if [ "${rc}" = 0 ] && grep -q 'budget 2.1 fF: EXCEEDS' <<<"${out}"; then
  echo "PASS: the bench flags the oversized input (capacitance verdict EXCEEDS)"
else echo "FAIL: the bench did not flag the oversized input (rc=${rc})"; fail=1; fi
exit "${fail}"
