"""Negative controls for the Vce grader: an out-of-rating Vce must FAIL, a non-converged corner is never a pass,
and an empty report is INCOMPLETE, never a PASS."""
import gzip
import json
import re

import vce_record as vr


def _scope_line(md):
    return next(l for l in md.splitlines() if l.startswith("- **Scope**"))


def _headline(md):
    return next(l for l in md.splitlines() if l.startswith("**Result"))


def _corner(vdd, vals, status="pass"):
    return {"corner_id": "TYP/27C/%s" % vdd, "process": "TYP", "temperature_c": 27, "params": {"vddv": vdd},
            "status": status, "diagnostics": [],
            "measurements": [{"name": "vce_x%d" % i, "value": v, "status": "pass"} for i, v in enumerate(vals)]}


def test_all_within_rating_passes():
    g = vr.grade({"corners": [_corner(2.97, [1.0, 2.1]), _corner(3.63, [1.2, 2.19])]})
    assert g["verdict"] == "PASS" and g["n_exceeding"] == 0


def test_out_of_rating_vce_fails():
    g = vr.grade({"corners": [_corner(2.97, [1.0, 2.2001])]})
    assert g["verdict"] == "FAIL" and g["rows"][0]["worst_device"] == "x1"


def test_non_converged_corner_is_not_a_pass():
    err = _corner(3.63, [], status="error")
    assert vr.grade({"corners": [_corner(2.97, [1.0]), err]})["verdict"] == "INCOMPLETE"


def test_failure_outranks_non_convergence():
    g = vr.grade({"corners": [_corner(2.97, [2.5]), _corner(3.63, [], status="error")]})
    assert g["verdict"] == "FAIL"


def test_mc_high_only_overstress_fails_and_is_labelled():
    lo, hi = _corner(3.63, [1.0, 2.0]), _corner(3.63, [1.0, 2.3])
    lo["params"]["mcv"], hi["params"]["mcv"] = 0, 1
    g = vr.grade({"corners": [lo, hi]})
    assert g["verdict"] == "FAIL" and [r["mc"] for r in g["rows"]] == [0.0, 1.0]
    assert [r["exceeds"] for r in g["rows"]] == [False, True]


def test_empty_report_grades_incomplete():
    g = vr.grade({"corners": []})
    assert g["verdict"] == "INCOMPLETE"
    assert g["rows"] == []
    assert (g["n_corners"], g["n_exceeding"], g["n_not_converged"]) == (0, 0, 0)


def test_empty_report_records_incomplete(tmp_path):
    rep = tmp_path / "empty.json"
    rep.write_text(json.dumps({"environment": {}, "corners": []}))
    out = tmp_path / "records"
    assert vr.main(["--report", str(rep), "--out-dir", str(out), "--id", "20990101-000000-empty", "--commit", "deadbeef"]) == 0
    archived = json.loads(gzip.decompress((out / "20990101-000000-empty-klt-report.json.gz").read_bytes()))
    assert archived == {"environment": {}, "corners": []}
    md = (out / "20990101-000000-empty-vce.md").read_text()
    assert "**INCOMPLETE**" in md
    assert "No corner was observed" in md
    assert re.search(r"0 of \d+ requested runs", md)
    assert re.search(r"\d+ runs requested, 0 observed", md)


# --- The record's corner count, grid fragment and supply rails are derived from the
# --- request, never typed (#397). ---

def _narrowed_request(tmp_path, vddv=(2.97, 2.97), res_section=None):
    """A prescaler request copy cut down to TYP/27C, both MC levels; the rail list and the
    TYP block's cornerRES section name are overridable."""
    req = json.loads((vr.HERE / "prescaler_vce.request.json").read_text())
    c = req["corners"]
    c["process"] = [p for p in c["process"] if p["name"] == "TYP"]
    c["temperature_c"] = [27]
    c["params"]["vddv"] = list(vddv)
    c["params"]["mcv"] = [0, 1]
    if res_section is not None:
        for s in c["process"][0]["sections"]:
            if "cornerRES" in s["lib"]:
                s["section"] = res_section
    narrowed = tmp_path / "narrowed.request.json"
    narrowed.write_text(json.dumps(req))
    return narrowed


def test_render_derives_the_count_and_grid_from_a_narrowed_request(tmp_path):
    mc0, mc1 = _corner(2.97, [1.0, 2.0]), _corner(2.97, [1.1, 2.1])
    mc0["params"]["mcv"], mc1["params"]["mcv"] = 0, 1
    rep = tmp_path / "one-subcorner.json"
    rep.write_text(json.dumps({"environment": {}, "corners": [mc0, mc1]}))
    out = tmp_path / "records"
    assert vr.main(["--report", str(rep), "--out-dir", str(out), "--id", "t",
                    "--request", str(_narrowed_request(tmp_path)), "--commit", "deadbeef"]) == 0
    md = (out / "t-vce.md").read_text()
    assert "the 1 supply sub-corners" in md
    assert "{2.970} V x {TYP} x {27} C" in md
    assert "2 requested: 1 sub-corners x MC low/high" in md
    assert "at every one of the 1 supply sub-corners (2 runs requested, 2 observed)" in md
    assert "18 sub-corners" not in md
    assert "the 18 supply sub-corners" not in md
    # The Scope line's legend and rails come from the grid too: TYP-only, 2.970 V-only.
    scope = _scope_line(md)
    assert set(re.findall(r"([A-Z]+) = hbt_", scope)) == {"TYP"}
    assert set(re.findall(r"(\d+\.\d{3})", scope.split("Not covered:")[0])) == {"2.970"}
    assert "SLOW" not in scope and "FAST" not in scope
    assert "hbt_wcs" not in scope and "hbt_bcs" not in scope
    assert "beyond the issue's" not in scope
    assert "3.630" not in md
    # The cornerRES half of the same sentence is derived too (#401): TYP-only shows res_typ only.
    assert "the cornerRES section res_typ is paired with each HBT corner" in scope
    assert "res_wcs" not in scope and "res_bcs" not in scope
    # The low rail was requested, so its summary is a complete sentence of its own.
    assert "At the minimum supply 2.970 V the worst converged corner is 2.100 V (TYP/27C/2.97, x1)." in _headline(md)


def test_render_derives_the_count_and_grid_from_a_widened_request(tmp_path):
    req = json.loads((vr.HERE / "prescaler_vce.request.json").read_text())
    req["corners"]["temperature_c"] = req["corners"]["temperature_c"] + [85]
    widened = tmp_path / "widened.request.json"
    widened.write_text(json.dumps(req))
    rep = tmp_path / "two-corners.json"
    rep.write_text(json.dumps({"environment": {}, "corners": [_corner(2.97, [1.0]), _corner(3.63, [1.1])]}))
    out = tmp_path / "records"
    assert vr.main(["--report", str(rep), "--out-dir", str(out), "--id", "t",
                    "--request", str(widened), "--commit", "deadbeef"]) == 0
    md = (out / "t-vce.md").read_text()
    assert "the 24 supply sub-corners" in md
    assert "{2.970, 3.630} V x {SLOW, TYP, FAST} x {-40, 27, 125, 85} C" in md
    assert "48 requested: 24 sub-corners x MC low/high" in md
    assert "at every one of the 24 supply sub-corners (48 runs requested, 2 observed)" in md
    assert "18 sub-corners" not in md
    # The legend and rail sentence are derived from the widened grid, not typed back in.
    scope = _scope_line(md)
    assert set(re.findall(r"([A-Z]+) = hbt_", scope)) == {"SLOW", "TYP", "FAST"}
    assert "SLOW = hbt_wcs, TYP = hbt_typ, FAST = hbt_bcs" in scope
    assert set(re.findall(r"(\d+\.\d{3})", scope.split("Not covered:")[0])) == {"2.970", "3.630"}
    assert "The 3.630 V half is beyond the issue's 2.970 V ask" in scope
    assert "the cornerRES section res_wcs/res_typ/res_bcs is paired with each HBT corner" in scope
    # Both rails requested: the two-rail headline wording survives.
    assert "At the minimum supply 2.970 V the worst converged corner is" in _headline(md)
    assert "; at 3.630 V it is" in _headline(md)


def test_render_process_legend_falls_back_to_names_without_a_cornerhbt_section(tmp_path):
    req = json.loads((vr.HERE / "prescaler_vce.request.json").read_text())
    for p in req["corners"]["process"]:
        p["sections"] = [s for s in p["sections"] if "cornerHBT" not in s["lib"]]
    stripped = tmp_path / "res-only.request.json"
    stripped.write_text(json.dumps(req))
    rep = tmp_path / "empty.json"
    rep.write_text(json.dumps({"environment": {}, "corners": []}))
    out = tmp_path / "records"
    assert vr.main(["--report", str(rep), "--out-dir", str(out), "--id", "t3",
                    "--request", str(stripped), "--commit", "deadbeef"]) == 0
    scope = _scope_line((out / "t3-vce.md").read_text())
    assert " = hbt_" not in scope
    assert "C, SLOW, TYP, FAST (the prescaler" in scope


def test_render_survives_a_request_without_a_corners_grid(tmp_path):
    bare = tmp_path / "bare.request.json"
    bare.write_text(json.dumps({"measurements": []}))
    rep = tmp_path / "empty.json"
    rep.write_text(json.dumps({"environment": {}, "corners": []}))
    out = tmp_path / "records"
    assert vr.main(["--report", str(rep), "--out-dir", str(out), "--id", "t2",
                    "--request", str(bare), "--commit", "deadbeef"]) == 0
    md = (out / "t2-vce.md").read_text()
    assert "No corner was observed" in md
    assert "0 of 0 requested runs (0 sub-corners)" in md
    assert "the 0 supply sub-corners" in md
    assert "18 sub-corners" not in md
    assert "the 18 supply sub-corners" not in md


# --- The headline names a rail only when the grid asked for it (#401): a 3.630 V-only
# --- request gets a complete high-rail sentence, no rail the grid never requested. ---

def test_render_high_rail_only_headline_is_a_complete_sentence(tmp_path):
    rep = tmp_path / "hi-only.json"
    rep.write_text(json.dumps({"environment": {}, "corners": [_corner(3.63, [1.0, 2.1])]}))
    out = tmp_path / "records"
    assert vr.main(["--report", str(rep), "--out-dir", str(out), "--id", "t4",
                    "--request", str(_narrowed_request(tmp_path, vddv=(3.63, 3.63))), "--commit", "deadbeef"]) == 0
    md = (out / "t4-vce.md").read_text()
    head = _headline(md)
    assert "At 3.630 V the worst converged corner is 2.100 V (TYP/27C/3.63, x1)." in head
    assert "minimum supply" not in head
    assert "2.970" not in head
    assert "0 of 1 observed runs (2 requested: 1 sub-corners x MC low/high)" in head
    # Scope is checked independently: it still names the issue's 2.970 V target in its own sentence.
    assert "The 3.630 V half is beyond the issue's 2.970 V ask" in _scope_line(md)


def test_render_neither_rail_headline_goes_straight_to_the_run_counts(tmp_path):
    for vddv in ([3.3, 3.3], []):
        out = tmp_path / ("records-%d" % len(vddv))
        rep = tmp_path / ("neither-%d.json" % len(vddv))
        rep.write_text(json.dumps({"environment": {}, "corners": [_corner(3.3, [1.0, 2.1])]}))
        assert vr.main(["--report", str(rep), "--out-dir", str(out), "--id", "t5",
                        "--request", str(_narrowed_request(tmp_path, vddv=vddv)), "--commit", "deadbeef"]) == 0
        head = _headline((out / "t5-vce.md").read_text())
        assert "worst converged corner" not in head
        assert "minimum supply" not in head
        assert "observed runs" in head


# --- The Scope line's cornerRES half is derived from the loaded blocks (#401): renamed
# --- sections follow the request, and no pairing is claimed for a block without one. ---

def test_render_res_clause_follows_a_renamed_res_section(tmp_path):
    rep = tmp_path / "lo-only.json"
    rep.write_text(json.dumps({"environment": {}, "corners": [_corner(2.97, [1.0, 2.1])]}))
    out = tmp_path / "records"
    assert vr.main(["--report", str(rep), "--out-dir", str(out), "--id", "t6",
                    "--request", str(_narrowed_request(tmp_path, res_section="res_typ_v2")),
                    "--commit", "deadbeef"]) == 0
    scope = _scope_line((out / "t6-vce.md").read_text())
    assert "the cornerRES section res_typ_v2 is paired with each HBT corner" in scope
    assert "res_wcs" not in scope and "res_bcs" not in scope


def test_render_res_clause_claims_pairing_only_for_blocks_that_carry_one(tmp_path):
    req = json.loads((vr.HERE / "prescaler_vce.request.json").read_text())
    for p in req["corners"]["process"]:
        if p["name"] == "TYP":
            p["sections"] = [s for s in p["sections"] if "cornerRES" not in s["lib"]]
    stripped = tmp_path / "no-typ-res.request.json"
    stripped.write_text(json.dumps(req))
    rep = tmp_path / "empty.json"
    rep.write_text(json.dumps({"environment": {}, "corners": []}))
    out = tmp_path / "records"
    assert vr.main(["--report", str(rep), "--out-dir", str(out), "--id", "t7",
                    "--request", str(stripped), "--commit", "deadbeef"]) == 0
    scope = _scope_line((out / "t7-vce.md").read_text())
    assert "the cornerRES section res_wcs/res_bcs is paired with the HBT corners that carry one" in scope
    assert "each HBT corner" not in scope
    assert "res_typ" not in scope


def test_render_res_clause_without_any_res_section(tmp_path):
    req = json.loads((vr.HERE / "prescaler_vce.request.json").read_text())
    for p in req["corners"]["process"]:
        p["sections"] = [s for s in p["sections"] if "cornerRES" not in s["lib"]]
    stripped = tmp_path / "no-res.request.json"
    stripped.write_text(json.dumps(req))
    rep = tmp_path / "empty.json"
    rep.write_text(json.dumps({"environment": {}, "corners": []}))
    out = tmp_path / "records"
    assert vr.main(["--report", str(rep), "--out-dir", str(out), "--id", "t8",
                    "--request", str(stripped), "--commit", "deadbeef"]) == 0
    scope = _scope_line((out / "t8-vce.md").read_text())
    assert "no cornerRES section is loaded" in scope
    assert "cornerRES section res" not in scope
    assert "paired with" not in scope
