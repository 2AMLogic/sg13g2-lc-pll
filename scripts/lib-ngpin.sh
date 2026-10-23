# shellcheck shell=bash
# Sourced after NG_VER is set: compare it with sim/pins.json ngspice.version. A mismatch
# warns on stderr and is recorded; it never aborts (the host's only ngspice may differ from the pin).
# Expects PINS and NG_VER. Sets: NG_PIN_STATUS (the line the run scripts write into the record).
_ng_pin="$(jq -r '.ngspice.version // empty' "${PINS}")"
_ng_have="${NG_VER#ngspice-}"
if [ -n "${_ng_have}" ] && [ -n "${_ng_pin}" ] && { [ "${_ng_have}" = "${_ng_pin}" ] || [ "${_ng_have#"${_ng_pin}".}" != "${_ng_have}" ]; }; then
  NG_PIN_STATUS="matches pin (ngspice-${_ng_pin})"
else
  NG_PIN_STATUS="Pin check: ${NG_VER:-ngspice-unknown} != pinned ${_ng_pin:-unset} (mismatch)"
  echo "warning: ${NG_PIN_STATUS}" >&2
fi
unset _ng_pin _ng_have
