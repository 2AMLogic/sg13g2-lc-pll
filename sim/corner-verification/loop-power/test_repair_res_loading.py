#!/usr/bin/env python3
"""The issue #452 repair script's rewrite rules.

These guard the three edits repair_res_loading.py makes to each #97 loop-power request
(the res corner section, the r3_cmc preload, the hsa ngspice_init plus the #452 comment
line), their SLOW/TYP/FAST mapping, and the two promised behaviors: idempotence, and a
loud refusal on a process name that is not a DR-004 bundle.
"""
import importlib.util
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))


def _load_module():
    spec = importlib.util.spec_from_file_location("lp_repair_res", os.path.join(HERE, "repair_res_loading.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


rr = _load_module()

RES_LIB = "libs.tech/ngspice/models/cornerRES.lib"


def _sections(name):
    """The three families every #97 request loads; only the res section is under test."""
    return [{"lib": "libs.tech/ngspice/models/cornerMOShv.lib", "section": "mos_tt"},
            {"lib": "libs.tech/ngspice/models/cornerCAP.lib", "section": "cap_typ"},
            {"lib": "libs.tech/ngspice/models/cornerHBT.lib", "section": "hbt_typ"}]


def _request(path, names=("TYP",), res=False, osdi=("psp103",), init=None):
    d = {"_comment": ["a #97 diagnostic request"],
         "netlist": "loop_power_body.spice", "engine": "ngspice",
         "corners": {"process": [{"name": n, "sections": _sections(n)} for n in names],
                     "temperature_c": [125], "params": {"vddv": [2.97]}},
         "options": {"timeout_s": 600,
                     "osdi_preload": ["$PDK_ROOT/ihp-sg13g2/libs.tech/ngspice/osdi/%s.osdi" % p for p in osdi]}}
    if res:
        for p in d["corners"]["process"]:
            p["sections"].append({"lib": RES_LIB, "section": "res_" + {"SLOW": "wcs", "TYP": "typ", "FAST": "bcs"}[p["name"]]})
    if init is not None:
        d["options"]["ngspice_init"] = list(init)
    path.write_text(json.dumps(d, indent=1) + "\n")
    return str(path)


def test_adds_res_section_preload_init_and_comment(tmp_path):
    p = _request(tmp_path / "request-x.json")
    assert rr.repair(p) is True
    d = json.load(open(p))
    assert d["corners"]["process"][0]["sections"][-1] == {"lib": RES_LIB, "section": "res_typ"}
    assert d["options"]["osdi_preload"] == ["$PDK_ROOT/ihp-sg13g2/libs.tech/ngspice/osdi/psp103.osdi",
                                            rr.R3_CMC]
    assert d["options"]["ngspice_init"] == ["set ngbehavior=hsa"]
    assert sum("#452" in c for c in d["_comment"]) == 1
    assert open(p).read().endswith("}\n")


@pytest.mark.parametrize("name,section", [("SLOW", "res_wcs"), ("TYP", "res_typ"), ("FAST", "res_bcs")])
def test_bundle_names_map_to_res_sections(tmp_path, name, section):
    p = _request(tmp_path / "request-x.json", names=(name,))
    rr.repair(p)
    assert json.load(open(p))["corners"]["process"][0]["sections"][-1] == {"lib": RES_LIB, "section": section}


def test_second_run_rewrites_nothing(tmp_path):
    p = _request(tmp_path / "request-x.json")
    rr.repair(p)
    before = open(p).read()
    assert rr.repair(p) is False
    assert open(p).read() == before


def test_every_process_entry_gets_its_own_res_corner(tmp_path):
    """request-stage2-97-fix1.json shape: SLOW, TYP and FAST entries in one request."""
    p = _request(tmp_path / "request-x.json", names=("SLOW", "TYP", "FAST"))
    rr.repair(p)
    want = {"SLOW": "res_wcs", "TYP": "res_typ", "FAST": "res_bcs"}
    for proc in json.load(open(p))["corners"]["process"]:
        res = [s for s in proc["sections"] if s["lib"] == RES_LIB]
        assert res == [{"lib": RES_LIB, "section": want[proc["name"]]}]


def test_existing_res_section_is_not_duplicated(tmp_path):
    p = _request(tmp_path / "request-x.json", res=True)
    assert rr.repair(p) is True  # the preload/init/comment are still missing
    d = json.load(open(p))
    assert sum(s["lib"] == RES_LIB for s in d["corners"]["process"][0]["sections"]) == 1
    assert rr.R3_CMC in d["options"]["osdi_preload"]
    assert rr.repair(p) is False


def test_non_bundle_process_name_fails_loudly(tmp_path):
    p = _request(tmp_path / "request-x.json", names=("mos_tt/cap_typ/hbt_typ",))
    with pytest.raises(SystemExit) as e:
        rr.repair(p)
    assert "request-x.json" in str(e.value)
    assert "mos_tt/cap_typ/hbt_typ" in str(e.value)
