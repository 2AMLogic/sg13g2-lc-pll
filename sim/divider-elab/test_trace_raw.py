"""Time-window regression for the ngspice ASCII trace reader."""
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).with_name("trace_raw.py")


@pytest.mark.parametrize(("start", "stop", "edges", "summary"), [
    ("0.75", "1.75", "f1.500", ["3.300", "3.300", "0", "1", "1.500"]),
    ("0.5", "1.5", "r0.500 f1.500", ["3.300", "3.300", "1", "1", "1.500"]),
    ("0.25", "0.75", "r0.500", ["", "", "1", "0", "0.500"]),
])
def test_crossing_window(tmp_path, start, stop, edges, summary):
    raw = tmp_path / "waveform.raw"
    raw.write_text(
        "No. Variables: 2\nNo. Points: 3\nVariables:\n"
        "\t0\ttime\ttime\n\t1\tv(x)\tvoltage\nValues:\n"
        "0 0 0\n1 1e-9 3.3\n2 2e-9 0\n"
    )
    cmd = [sys.executable, str(SCRIPT), str(raw)]
    crossings = subprocess.check_output([*cmd, "--cross", start, stop, "v(x)"], text=True)
    assert crossings.rstrip() == f"v(x) {edges}"
    rows = subprocess.check_output([*cmd, "v(x)", "--t0", start, "--t1", stop], text=True)
    assert rows.splitlines()[1].split("\t") == ["v(x)", *summary]
