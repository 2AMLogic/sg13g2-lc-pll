#!/usr/bin/env bash
# PDK-free unit test for scripts/lib-expect.sh: the harness every layout and fetch negative
# control is scored by. Its own counters are tpass/tbad, so they cannot be confused with the
# pass/bad the library under test owns.
#   scripts/test-lib-expect.sh
set -uo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
T="$(mktemp -d)"; trap 'rm -rf "${T}"' EXIT
# shellcheck source=lib-expect.sh
source "${SRC}/scripts/lib-expect.sh"
tpass=0; tbad=0

# The three commands under test: a clean run, a checker that refuses with its own text, and a
# crash that says nothing about the fault being tested (#234's SyntaxError, in miniature).
clean()  { echo "ok  all good"; return 0; }
refuser() { echo "checker: sha256 mismatch; refusing" >&2; return 1; }
crasher() { echo "Traceback (most recent call last): SyntaxError: invalid syntax" >&2; return 1; }
noisy()  { echo "checker: sha256 mismatch; refusing"; return 0; }   # right text, exit 0

check() { # <desc> <PASS|FAIL|UNKNOWN> <expect args...>
  local desc="$1" exp="$2"; shift 2
  local p0="${pass}" b0="${bad}" got line
  expect "$@" >"${T}/verdict" 2>&1
  line="$(head -1 "${T}/verdict")"
  case "${line}" in
    *"unknown expectation"*) got=UNKNOWN ;;
    PASS\ *) got=PASS ;;
    FAIL\ *) got=FAIL ;;
    *) got="unrecognised" ;;
  esac
  local dp=$((pass - p0)) db=$((bad - b0)) wdp=0 wdb=1
  [ "${exp}" != PASS ] || { wdp=1; wdb=0; }
  if [ "${got}" = "${exp}" ] && [ "${dp}" = "${wdp}" ] && [ "${db}" = "${wdb}" ]; then
    echo "ok   ${desc}"; tpass=$((tpass+1))
  else
    echo "FAIL ${desc}: verdict '${got}' want '${exp}', pass+${dp} bad+${db} want pass+${wdp} bad+${wdb}"
    sed 's/^/    /' "${T}/verdict"; tbad=$((tbad+1))
  fi
}

check "ok + exit 0 passes"                    PASS    "c" ok clean
check "ok + non-zero fails"                   FAIL    "c" ok refuser
check "refuse + non-zero passes"              PASS    "c" refuse refuser
check "refuse + exit 0 fails"                 FAIL    "c" refuse clean

# The #234 contrast: the SAME crash must fail under refuse:<ERE> and pass under bare `refuse`.
# That pair is the regression test -- it is what makes refuse:<ERE> worth requiring.
check "refuse:<ERE> + matching refusal passes" PASS   "c" "refuse:sha256 mismatch; refusing" refuser
check "refuse:<ERE> + crash without it fails"  FAIL   "c" "refuse:sha256 mismatch; refusing" crasher
check "bare refuse scores that crash a pass"   PASS   "c" refuse crasher

# refuse:<ERE> needs BOTH halves: the text alone, on a clean exit, is not a refusal.
check "refuse:<ERE> + text but exit 0 fails"   FAIL   "c" "refuse:sha256 mismatch; refusing" noisy

# An expectation string that is none of the three is reported as such, not scored as a case.
check "unknown expectation reported"          UNKNOWN "c" refusal refuser
check "ok typo reported, not scored"          UNKNOWN "c" OK clean

# expect_summary: the printed tally and the verdict it returns. Run in a subshell so these
# synthetic counters do not disturb the ones check() is reading.
sum() { # <desc> <pass> <bad> <expected rc>
  local desc="$1" p="$2" b="$3" exp="$4" out rc
  out="$(pass="${p}" bad="${b}"; expect_summary)"; rc=$?
  if [ "${out}" = "${p} passed, ${b} failed" ] && [ "${rc}" = "${exp}" ]; then
    echo "ok   ${desc}"; tpass=$((tpass+1))
  else echo "FAIL ${desc}: '${out}' rc=${rc}, want '${p} passed, ${b} failed' rc=${exp}"; tbad=$((tbad+1)); fi
}
sum "summary: all passed -> rc 0"       3 0 0
sum "summary: a failure -> rc non-zero" 3 2 1
sum "summary: nothing ran -> rc 0"      0 0 0

echo "${tpass} passed, ${tbad} failed"
[ "${tbad}" = 0 ] || exit 1
