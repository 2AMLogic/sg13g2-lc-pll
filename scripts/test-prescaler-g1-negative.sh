#!/usr/bin/env bash
# Negative controls for scripts/run-prescaler-g1.sh. Two throwaway copies of the prescaler netlist, each
# deliberately wrong in one way, must be flagged by the bench:
#   A (starved tail): the tail resistor XRT of cml_dff_latch (the latch inside cml_dff, i.e. the clocked flip-flops of
#       the /2-/3 first stage cml_div23) l=9.05u -> 905u, ~100x the resistance, so the tail current collapses:
#       the first stage must NOT toggle at f/2 up to the 5.5 GHz band top (toggle verdict FAIL). cml_and2 and
#       cml_latch have an identical XRT line and are deliberately not touched.
#   B (oversized input): the input emitter followers XQE1/XQE2 of cml_ef Nx = 1 -> 4. Only XCK (inside cml_div23)
#       loads INP/INN, so the differential input capacitance must exceed the 2.1 fF budget (capacitance verdict
#       EXCEEDS); the toggle verdict is not asserted for B.
# The skewed netlists and their records live in a scratch dir; nothing is committed by this.
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT
SRC="${ROOT}/design/netlist/prescaler.spice"
fail=0

# A: first-stage flip-flop latch tail resistor (inside cml_dff_latch) l=9.05u -> 905u
awk '/^\.subckt cml_dff_latch / {p=1} /^\.ends/ {p=0} p && /^XRT / { sub(/l=9\.05u/, "l=905u") } {print}' "${SRC}" > "${T}/a.spice"
# B: input emitter followers (inside cml_ef) Nx=1 -> Nx=4
awk '/^\.subckt cml_ef / {p=1} /^\.ends/ {p=0} p && /^XQE[12] / { sub(/Nx=1 /, "Nx=4 ") } {print}' "${SRC}" > "${T}/b.spice"
for x in a b; do
  if diff -q "${SRC}" "${T}/${x}.spice" >/dev/null; then echo "FAIL: skew ${x} did not change the netlist"; exit 1; fi
  echo "skew ${x} applied:"; diff "${SRC}" "${T}/${x}.spice" | grep '^>'
done

echo; echo "== control A: starved first-stage flip-flop tail =="
out="$(PRESC_NETLIST="${T}/a.spice" RECORD_DIR="${T}/reca" G1_FLIST="6e9" "${ROOT}/scripts/run-prescaler-g1.sh" 2>&1)"; rc=$?
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
