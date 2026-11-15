#!/usr/bin/env bash
# Negative controls for scripts/run-jitter.sh. Needs numpy (PYTHON). Records go to a scratch dir, never to
# sim/jitter/records, and no input file is committed.
#   PYTHON=.venv/bin/python scripts/test-jitter-negative.sh
#
# Case 1 (broken filter): a throwaway copy of the loop filter with C2 = C1 (the shunt capacitor as large as
#   the series one: the loop loses its phase margin) must make the record say "MODEL GATE FAILED" in its
#   result line. With NOISE_INPUTS unset it must also write no <id>-noise-inputs.json.
# Case 2 (in-band inputs stated, partial): with NOISE_INPUTS set to a scratch file outside the record dir,
#   supplying two of the three in-band terms, the record must name each supplied term, print its `source`
#   string and summary, state the file's sha256, and link a copy of the file written next to it; the third
#   term must still read as missing. This is the check that fails if a source is dropped from the record.
# Case 3 (in-band inputs stated, all three): the full-coverage branch must carry all three sources and must
#   not point at a "method block above" that the record does not contain.
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
if [ -z "$(ls "${T}"/rec/*-noise-inputs.json 2>/dev/null)" ]; then
  echo "PASS: with NOISE_INPUTS unset the run writes no -noise-inputs.json"
else
  echo "FAIL: a -noise-inputs.json was written for a run with no NOISE_INPUTS"; ls "${T}"/rec; exit 1
fi

# Cases 2 and 3 share these checks: `check <what> <literal that must be in the record under test>`.
fails=0
check() { grep -qF -- "$2" "${REC_UT}" || { echo "FAIL: $1 is not in the record"; fails=$((fails + 1)); }; }
refute() { grep -qF -- "$2" "${REC_UT}" && { echo "FAIL: $1 is still in the record"; fails=$((fails + 1)); }; }
copy_check() {  # the inputs file must sit next to the record, byte for byte
  [ -f "$2" ] && cmp -s "$1" "$2" && return 0
  echo "FAIL: the inputs file was not copied next to the record, or the copy differs"; fails=$((fails + 1))
}

# Case 2: two of the three in-band terms, from a file outside the record dir (the partial branch).
SRC_REF='scratch negative-control value, not a measurement: flat reference floor'
SRC_CP='scratch negative-control value, not a measurement: two-point PFD/CP table'
SRC_DIV='scratch negative-control value, not a measurement: flat divider/prescaler floor'
jq -n --arg sref "${SRC_REF}" --arg scp "${SRC_CP}" '{
  reference_x_N2: {ssb_dbc_per_hz: [[1000, -150.0]], source: $sref},
  pfd_cp_x_N2:    {ssb_dbc_per_hz: [[1000, -140.0], [10000000, -148.0]], source: $scp}
}' > "${T}/ni-partial.json"
NOISE_INPUTS="${T}/ni-partial.json" RECORD_DIR="${T}/rec2" "${ROOT}/scripts/run-jitter.sh" >"${T}/log2" 2>&1; rc=$?
[ "${rc}" = 0 ] || { echo "FAIL: bench did not run with a partial NOISE_INPUTS (rc=${rc})"; cat "${T}/log2"; exit 1; }
REC_UT="$(ls "${T}"/rec2/*.md | head -1)"
ID2="$(basename "${REC_UT}" .md)"
check "the supplied term reference_x_N2" 'reference_x_N2'
check "the supplied term pfd_cp_x_N2" 'pfd_cp_x_N2'
check "reference_x_N2's source string" "${SRC_REF}"
check "pfd_cp_x_N2's source string" "${SRC_CP}"
check "the summary of the flat reference input" 'flat floor at -150.0 dBc/Hz'
check "the summary of the two-point PFD/CP input" '2-point table over 1000-1e+07 Hz'
check "the sha256 of the inputs file" "$(sha256sum "${T}/ni-partial.json" | cut -d' ' -f1)"
check "a link to the copied inputs file" "(${ID2}-noise-inputs.json)"
check "the unsupplied divider_prescaler term, still named as missing" 'no input supplied: divider_prescaler'
copy_check "${T}/ni-partial.json" "${T}/rec2/${ID2}-noise-inputs.json"
if [ "${fails}" = 0 ]; then
  echo "PASS: a partial NOISE_INPUTS record states each supplied term with its source, and still names the missing one"
else
  echo "FAIL: ${fails} check(s) failed in case 2; record was:"; cat "${REC_UT}"; exit 1
fi

# Case 3: all three in-band terms, the branch whose result line claims full coverage.
jq -n --arg sref "${SRC_REF}" --arg scp "${SRC_CP}" --arg sdiv "${SRC_DIV}" '{
  reference_x_N2:    {ssb_dbc_per_hz: [[1000, -150.0]], source: $sref},
  pfd_cp_x_N2:       {ssb_dbc_per_hz: [[1000, -140.0], [10000000, -148.0]], source: $scp},
  divider_prescaler: {ssb_dbc_per_hz: [[1000, -145.0]], source: $sdiv}
}' > "${T}/ni-full.json"
NOISE_INPUTS="${T}/ni-full.json" RECORD_DIR="${T}/rec3" "${ROOT}/scripts/run-jitter.sh" >"${T}/log3" 2>&1; rc=$?
[ "${rc}" = 0 ] || { echo "FAIL: bench did not run with a full NOISE_INPUTS (rc=${rc})"; cat "${T}/log3"; exit 1; }
REC_UT="$(ls "${T}"/rec3/*.md | head -1)"
ID3="$(basename "${REC_UT}" .md)"
check "the full-coverage result line" 'All five spec section 4 terms have an input'
check "reference_x_N2's source string" "${SRC_REF}"
check "pfd_cp_x_N2's source string" "${SRC_CP}"
check "divider_prescaler's source string" "${SRC_DIV}"
check "the sha256 of the inputs file" "$(sha256sum "${T}/ni-full.json" | cut -d' ' -f1)"
check "a link to the copied inputs file" "(${ID3}-noise-inputs.json)"
refute "the dangling pointer at a method block the record does not contain" 'method block above'
copy_check "${T}/ni-full.json" "${T}/rec3/${ID3}-noise-inputs.json"
if [ "${fails}" = 0 ]; then
  echo "PASS: a full NOISE_INPUTS record states all three sources and points only at what it contains"
else
  echo "FAIL: ${fails} check(s) failed in case 3; record was:"; cat "${REC_UT}"; exit 1
fi
