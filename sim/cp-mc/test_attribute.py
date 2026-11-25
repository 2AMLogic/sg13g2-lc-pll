"""Check the charge-pump attribution schedule, device groups, and mismatch masks.

`attribute.py` is the single source of the campaign order (#477, #478). The tests use
the committed `design/netlist/cp.spice` and require only the standard library and pytest.
"""

from pathlib import Path

import pytest

import attribute

CP_SPICE = Path(__file__).resolve().parents[2] / "design" / "netlist" / "cp.spice"
MOS_COUNT = 23

ORDER = ("all bn_ref bn_xbn2 bn_xbns bn_casc bp_ref bp_copy bp_casc "
         "leg_p leg_n switches none").split()


def test_campaign_order():
    assert attribute.campaign() == ["all", *attribute.GROUPS, "none"]
    assert attribute.campaign() == ORDER


def test_groups_partition_netlist():
    assert attribute.check_partition(CP_SPICE.read_text()) == MOS_COUNT


@pytest.mark.parametrize("name", attribute.GROUPS)
def test_group_mask_count(name):
    netlist = attribute.write_netlist(name, CP_SPICE.read_text())
    assert netlist.count("mm_ok=0") == MOS_COUNT - len(attribute.GROUPS[name])


def test_all_leaves_netlist_unchanged():
    text = CP_SPICE.read_text()
    netlist = attribute.write_netlist("all", text)
    assert netlist == text
    assert netlist.count("mm_ok=0") == 0


def test_none_masks_every_device():
    netlist = attribute.write_netlist("none", CP_SPICE.read_text())
    assert netlist.count("mm_ok=0") == MOS_COUNT


@pytest.mark.parametrize("name", ["bn_typo", "", "ALL", "None", "all "])
def test_unknown_group_rejected(name):
    with pytest.raises(ValueError):
        attribute.write_netlist(name, CP_SPICE.read_text())
