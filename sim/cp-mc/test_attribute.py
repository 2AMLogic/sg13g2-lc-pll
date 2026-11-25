"""The charge-pump attribution schedule and its unknown-group rejection (#479).

`attribute.py` is the single source of the campaign order (#477, #478). This guards the
twelve-name order, that `write_netlist` accepts every campaign name against the committed
`design/netlist/cp.spice`, and that it rejects anything else. Stdlib + pytest only: no PDK,
ngspice or fleet submission.
"""
from pathlib import Path

import pytest

import attribute

CP_SPICE = Path(__file__).resolve().parents[2] / "design" / "netlist" / "cp.spice"

ORDER = ("all bn_ref bn_xbn2 bn_xbns bn_casc bp_ref bp_copy bp_casc "
         "leg_p leg_n switches none").split()


def test_campaign_order():
    assert attribute.campaign() == ["all", *attribute.GROUPS, "none"]
    assert attribute.campaign() == ORDER


@pytest.mark.parametrize("name", ORDER)
def test_every_campaign_name_accepted(name):
    assert attribute.write_netlist(name, CP_SPICE.read_text())


@pytest.mark.parametrize("name", ["bn_typo", "", "ALL", "None", "all "])
def test_unknown_group_rejected(name):
    with pytest.raises(ValueError):
        attribute.write_netlist(name, CP_SPICE.read_text())
