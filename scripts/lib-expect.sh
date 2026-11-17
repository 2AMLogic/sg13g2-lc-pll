# shellcheck shell=bash
# Sourced by the test-*.sh scripts that score a command against an expectation: the one definition
# of expect() and its pass/bad tally, so the discriminating-negative-control rule below is stated
# once instead of per copy. Consumers: `git grep -ln 'source.*lib-expect.sh' -- scripts`.
# Expects T (a scratch directory it writes T/out into); needs no ROOT and no die(), unlike
# lib-record.sh / lib-pdk.sh. Sets: pass, bad. Unit test: scripts/test-lib-expect.sh.
#
# want: ok | refuse | refuse:<ERE>. Plain `refuse` passes on any non-zero exit, so it cannot tell
# a detected fault from a crash (a SyntaxError, a missing klayout); `refuse:<ERE>` also requires
# the checker's own refusal text in the output, which is what makes a negative control
# discriminating (#234). Use `refuse:<ERE>` for every case whose checker prints refusal text;
# bare `refuse` only where it prints none.

pass=0; bad=0

# expect <name> <ok|refuse|refuse:ERE> <cmd...>  -> one PASS/FAIL line, tally updated. An
# expectation string that is none of the three is reported as such, not scored as a case.
expect() {
  local name="$1" want="$2"; shift 2
  "$@" >"${T}/out" 2>&1; local rc=$?
  local ok=0
  case "${want}" in
    ok) [ "${rc}" = 0 ] && ok=1 ;;
    refuse) [ "${rc}" != 0 ] && ok=1 ;;
    refuse:*) [ "${rc}" != 0 ] && grep -qE "${want#refuse:}" "${T}/out" && ok=1 ;;
    *) echo "FAIL ${name}: unknown expectation '${want}'"; bad=$((bad+1)); return ;;
  esac
  if [ "${ok}" = 1 ]; then
    echo "PASS ${name} (rc=${rc})"; pass=$((pass+1))
  else echo "FAIL ${name} (rc=${rc})"; sed 's/^/    /' "${T}/out"; bad=$((bad+1)); fi
}

# expect_summary  -> print the tally; non-zero when any case failed. Call it as the caller's
# explicit verdict (`expect_summary || exit 1`), so a line appended after it cannot turn a
# failing run into exit 0 the way a trailing `[ "${bad}" = 0 ]` can.
expect_summary() {
  echo "${pass} passed, ${bad} failed"
  [ "${bad}" = 0 ]
}
