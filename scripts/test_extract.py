import tempfile
from pathlib import Path

import extract
from extract import summarize

run = {
    "configuration": {"STARTTIME": "20260924011659", "LAYERS": {"meta": {"commit": "abc"}}},
    "result": {
        "ping.PingTest.test_ping": {"duration": 0.024741, "status": "PASSED"},
        "ptest.PtestRunnerTest.x": {"duration": 1.0, "status": "SKIPPED"},
        "ptestresult.coreutils.foo": {"status": "PASSED"},
        "ptestresult.sections": {"coreutils": {"duration": "1637"}},
        "nostatus": {"log": "oeselftest entries can lack status"},
    },
}
assert summarize(run) == {
    "start": "20260924011659",
    "commit": "abc",
    "durations": {"ping.PingTest.test_ping": 0.025, "ptest.PtestRunnerTest.x": 1.0},
    "sections": {"coreutils": 1637.0},
    "status": {"PASSED": 2, "SKIPPED": 1},
}

with tempfile.TemporaryDirectory() as tmp:
    extract.DATA = Path(tmp)
    runs = {i: {"id": i, "start": s} for i, s in [("a", "20251231235959"), ("b", "20260101000000")]}
    extract.save("x/y/testresults.json", runs)
    assert sorted(f.name for f in (extract.DATA / "x/y").iterdir()) == ["2025.json", "2026.json"]
    assert extract.load("x/y/testresults.json") == runs
print("ok")
