#!/usr/bin/env bash
# Negative control for scripts/run-jitter.sh: a throwaway copy of the loop filter with C2 = C1 (the shunt
# capacitor as large as the series one: the loop loses its phase margin) must make the record say
# "MODEL GATE FAILED" in its result line. Needs numpy (PYTHON). Records go to a scratch dir.
#   PYTHON=.venv/bin/python scripts/test-jitter-negative.sh
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT
jq '.c2_f = .c1_f' "${ROOT}/sim/loop-model/loop-filter.json" > "${T}/bad-filter.json"
LOOP_FILTER="${T}/bad-filter.json" RECORD_DIR="${T}/rec" "${ROOT}/scripts/run-jitter.sh" >"${T}/log" 2>&1; rc=$?
[ "${rc}" = 0 ] || { echo "FAIL: bench did not run (rc=${rc})"; cat "${T}/log"; exit 1; }
rec="$(ls "${T}"/rec/*.md | head -1)"
if sed -n 3p "${rec}" | grep -q 'MODEL GATE FAILED'; then
  echo "PASS: the bench flags a loop filter that breaks the row 5 gate (C2 = C1)"
else
  echo "FAIL: the bench did not flag the broken filter"; sed -n 3p "${rec}" | cut -c1-300; exit 1
fi
