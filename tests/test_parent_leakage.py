from __future__ import annotations

import json
import tempfile
from pathlib import Path

from ase import Atoms

from matsim_agents.datasets.parent_leakage import check_parent_leakage


def _frame(sha: str | None) -> Atoms:
    a = Atoms("H")
    if sha:
        a.info["generation_json"] = json.dumps({"source_sha256": sha})
    return a


def test_parent_overlap_warns_and_fails() -> None:
    d = Path(tempfile.mkdtemp())
    val = d / "validation-x.extxyz"
    (d / "validation-x.parents.json").write_text(
        json.dumps({"frames": [{"parent_id": "aaa"}, {"parent_id": "bbb"}]})
    )
    train = [_frame("aaa"), _frame("aaa"), _frame("ccc"), _frame(None)]
    assert check_parent_leakage(train, val, mode="warn") == {"aaa": 2}
    assert check_parent_leakage(train, val, mode="off") == {}
    assert check_parent_leakage([_frame("ccc")], val, mode="fail") == {}
    try:
        check_parent_leakage(train, val, mode="fail")
    except ValueError:
        pass
    else:
        raise AssertionError("fail mode must raise")
    assert check_parent_leakage(train, d / "no-sidecar.extxyz", mode="fail") == {}


if __name__ == "__main__":
    test_parent_overlap_warns_and_fails()
    print("OK")
