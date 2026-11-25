"""PDK-free checks for the VCO/prescaler and charge-pump corner request generators."""
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest


BENCHES = Path(__file__).resolve().parents[1]


@pytest.fixture
def load_generator(tmp_path, monkeypatch):
    benches = tmp_path / "sim" / "corner-verification"
    benches.mkdir(parents=True)
    shutil.copy(BENCHES.parent / "corner_set.py", benches.parent)
    monkeypatch.setenv("PDK_ROOT", str(tmp_path / "missing-pdk"))
    monkeypatch.setattr(sys, "dont_write_bytecode", True)

    def load(name):
        directory = benches / name
        directory.mkdir()
        script = Path(shutil.copy(BENCHES / name / "make_requests.py", directory))
        spec = importlib.util.spec_from_file_location("make_requests", script)
        module = importlib.util.module_from_spec(spec)
        search_path = sys.path.copy()
        spec.loader.exec_module(module)
        assert sys.path == search_path
        return module, directory

    return load


def test_cp_requests_match_tracked_bytes(load_generator):
    generator, directory = load_generator("cp-dc")
    requests = generator.build_requests()
    assert list(directory.iterdir()) == [directory / "make_requests.py"]
    assert set(requests) == {"request-stage1.json", "request-stage2.json"}

    generator.main()
    for name, request in requests.items():
        expected = (BENCHES / "cp-dc" / name).read_bytes()
        assert (json.dumps(request, indent=1) + "\n").encode() == expected
        assert (directory / name).read_bytes() == expected


def test_vco_request_inventory(load_generator):
    generator, directory = load_generator("vco-prescaler-load")
    requests = generator.build_requests()
    assert list(directory.iterdir()) == [directory / "make_requests.py"]

    expected = {"request-loaded-stage1.json"}
    for mos in ("tt", "ss", "ff", "sf", "fs"):
        expected.add(f"request-loaded-stage1-{mos}.json")
        name = f"request-loaded-stage1-dsubw-{mos}.json"
        expected.add(name)
        assert requests[name]["corners"]["temperature_c"] == ([27, 125] if mos == "tt" else [125])
    for tag in ("loaded", "unloaded"):
        expected.update(f"request-{tag}-{suffix}.json" for suffix in ("nominal", "stage2", "stage2-125C"))
        for corner in ("SLOW", "TYP", "FAST"):
            expected.add(f"request-{tag}-stage2-{corner}.json")
            name = f"request-{tag}-stage2-dsubw-{corner}.json"
            expected.add(name)
            assert requests[name]["corners"]["temperature_c"] == [27, 125]
    assert set(requests) == expected


@pytest.mark.parametrize("loaded", [False, True])
def test_vco_body_from_lines(load_generator, loaded):
    generator, _ = load_generator("vco-prescaler-load")
    lines = ["* input header", ".lib a b", ".include old.spice", "VSUP original", "VCT original",
             "  Xvar a b sg13_hv_svaricap w=1", ".ic original", ".control", "run"]
    body = generator.body(loaded, lines)
    elements = body.split(".param vddv=3.3 vctrl=1.65\n")[1]
    expected = ("VSUP VDD 0 dc {vddv}\nVCT VCTRL 0 dc {vctrl}\n  Xvar a b sg13_hv_svaricap w=1\n"
                ".ic v(OUTP)={vddv+0.005} v(OUTN)={vddv-0.005}\nBD vd 0 V=v(outp)-v(outn)\n"
                ".include sg13g2_inductor_em.spice\n")
    assert elements == expected + (generator.LOAD if loaded else "")
    assert generator.dsubw_body(loaded, lines) == (
        body.replace(" sg13_hv_svaricap ", " svar_loc ") + ".include svar_dsubw125.spice\n"
    )


def test_varactor_subcircuit_from_pinned_bytes(load_generator):
    generator, _ = load_generator("vco-prescaler-load")
    raw = (b"* preamble\r\n.subckt sg13_hv_svaricap a b\r\n.model sg13_hv_svaricap mosvar\r\n"
           b".model dsubw d is=1e-15\r\n.model other d is=2e-15\r\n.ends sg13_hv_svaricap\r\n* tail\r\n")
    pin = hashlib.sha256(raw).hexdigest()
    deck = generator.dsubw_svar(raw, pin)
    assert f"sha256 {pin}, lines 2-6" in deck
    assert deck.splitlines(keepends=True)[3:] == [
        ".subckt svar_loc a b\n", ".model svar_loc_mod mosvar\n", ".model dsubw d tnom = 125 is=1e-15\n",
        ".model other d is=2e-15\n", ".ends svar_loc\n",
    ]
    with pytest.raises(SystemExit, match="not the pinned PDK file"):
        generator.dsubw_svar(raw + b" ", pin)
