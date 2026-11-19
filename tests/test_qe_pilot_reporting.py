"""Pilot reporting, magnetic-moment parsing, spin configurations, PBE/PBE+U tagging.

Runs under pytest or as plain python (no pytest in the Lux venv):
    python tests/test_qe_pilot_reporting.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ase.build import bulk  # noqa: E402

from matsim_agents.active_learning.dft_protocol import scientific_dft_payload  # noqa: E402
from matsim_agents.backends.dft.config import DFTConfig  # noqa: E402
from matsim_agents.backends.dft.qe import _parse_pw_out, parse_magnetization  # noqa: E402
from matsim_agents.backends.dft.qe_relax import QESettings, write_pw_input  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "e3_qe_pilot_report", ROOT / "scripts" / "e3_qe_pilot_report.py"
)
report = importlib.util.module_from_spec(_spec)
sys.modules["e3_qe_pilot_report"] = report
_spec.loader.exec_module(report)

SPIN_OUT = """\
     total magnetization       =     1.00 Bohr mag/cell
     absolute magnetization    =     2.00 Bohr mag/cell
     Magnetic moment per site:
     atom:    1    charge:   13.0000    magn:    0.5000    constr:    0.0000
     atom:    2    charge:   13.0000    magn:    0.5000    constr:    0.0000

     total magnetization       =     3.97 Bohr mag/cell
     absolute magnetization    =     4.12 Bohr mag/cell
     Magnetic moment per site:
     atom:    1    charge:   13.1000    magn:    2.1000    constr:    0.0000
     atom:    2    charge:   13.2000    magn:   -2.0500    constr:    0.0000

     convergence has been achieved in   9 iterations
     PWSCF        :     3m20.00s CPU     3m25.00s WALL
   JOB DONE.
"""


def _cfg(tmp: Path, **qe) -> DFTConfig:
    (tmp / "Fe.upf").write_text("x")
    return DFTConfig.model_validate(
        {
            "backend": "qe",
            "qe": {
                "pw_bin": str(tmp / "pw.x"),
                "pw_wrapper": str(tmp / "w.sh"),
                "pseudo_dir": str(tmp),
                "pseudopotentials": {"Fe": "Fe.upf"},
                **qe,
            },
        }
    )


def test_parse_magnetization_takes_last_values() -> None:
    mag = parse_magnetization(SPIN_OUT)["magnetization"]
    assert mag["total_magnetization"] == 3.97 and mag["absolute_magnetization"] == 4.12
    assert [s["magn"] for s in mag["per_site"]] == [2.1, -2.05]
    assert parse_magnetization("no spin here\n   JOB DONE.\n") is None


def test_parse_pw_out_without_ase_energy_keeps_extra_and_old_fields() -> None:
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "pw.out"
        out.write_text(SPIN_OUT)
        res = _parse_pw_out(str(out), d, 0, 1.0, "qe")
        assert res.extra["magnetization"]["total_magnetization"] == 3.97
        assert res.converged is False  # no energies parsed from the synthetic output
        out.write_text("plain nonspin\n")
        assert _parse_pw_out(str(out), d, 0, 1.0, "qe").extra is None


def test_default_input_and_signature_unchanged_without_spin_configuration() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        plain = scientific_dft_payload(_cfg(tmp), {"Fe"})
        assert "spin_configuration" not in plain
        afm = _cfg(
            tmp,
            spin_configuration={
                "name": "afm",
                "sites": [{"symbol": "Fe", "indices": [1], "starting_magnetization": -0.3}],
            },
        )
        assert scientific_dft_payload(afm, {"Fe"})["spin_configuration"]["name"] == "afm"
        atoms = bulk("Fe", cubic=True)  # 2 atoms
        s = QESettings(
            pseudo_dir=d,
            ecutwfc_ry=40,
            ecutrho_ry=320,
            occupations="smearing",
            kpts=(2, 2, 2),
            pseudopotentials={"Fe": "Fe.upf"},
            calculation="scf",
            extra_system={"nspin": 2, "starting_magnetization(1)": 0.3},
        )
        p0 = write_pw_input(atoms, s, str(tmp / "a.in"))
        assert "Fe1" not in Path(p0).read_text()
        again = write_pw_input(atoms, s, str(tmp / "b.in"))
        assert Path(p0).read_text() == Path(again).read_text()


def test_afm_split_species_and_hubbard() -> None:
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        atoms = bulk("Fe", cubic=True)
        s = QESettings(
            pseudo_dir=d,
            ecutwfc_ry=40,
            ecutrho_ry=320,
            occupations="smearing",
            kpts=(2, 2, 2),
            pseudopotentials={"Fe": "Fe.upf"},
            calculation="scf",
            hubbard_u={"Fe-3d": 5.3},
            extra_system={"nspin": 2, "starting_magnetization(1)": 0.3125},
            spin_configuration={
                "name": "afm",
                "sites": [{"symbol": "Fe", "indices": [1], "starting_magnetization": -0.3125}],
            },
        )
        text = Path(write_pw_input(atoms, s, str(tmp / "afm.in"))).read_text()
        assert "ntyp                      = 2" in text
        assert "starting_magnetization(1) = 3.12500000d-01" in text
        assert "starting_magnetization(2) = -3.12500000d-01" in text
        assert "  Fe  " in text and "  Fe1  " in text
        assert "U Fe-3d 5.3" in text and "U Fe1-3d 5.3" in text
        pos = text.split("ATOMIC_POSITIONS angstrom")[1].splitlines()[1:3]
        assert pos[0].split()[0] == "Fe" and pos[1].split()[0] == "Fe1"
        bad = {"sites": [{"symbol": "Fe", "indices": [5], "starting_magnetization": 0.1}]}
        s.spin_configuration = bad
        try:
            write_pw_input(atoms, s, str(tmp / "bad.in"))
        except ValueError:
            pass
        else:
            raise AssertionError("out-of-range indices must raise")


def test_template_and_spin_configuration_exclusive() -> None:
    with tempfile.TemporaryDirectory() as d:
        try:
            _cfg(
                Path(d),
                pw_template=str(Path(d) / "t"),
                spin_configuration={"species": {"Fe": 0.1}},
            )
        except ValueError:
            return
        raise AssertionError("pw_template + spin_configuration must be rejected")


def _make_label(root: Path, rnd: str, name: str, converged: bool, reason, wall, tag="pbe+u"):
    d = root / rnd / "dft" / name
    d.mkdir(parents=True)
    (d / "pw.in").write_text("x")
    (d / "pw.out").write_text(SPIN_OUT if converged else "partial\n")
    (d / "label-metadata.json").write_text(
        json.dumps(
            {
                "converged": converged,
                "failure_reason": reason,
                "wall_time_sec": wall,
                "dft_protocol_tag": tag,
                "magnetization": parse_magnetization(SPIN_OUT)["magnetization"]
                if converged
                else None,
            }
        )
    )


def test_pilot_report_counts_cost_and_tags() -> None:
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "e3-qe-policy.json").write_text(
            json.dumps(
                {
                    "material": "lifepo4",
                    "hubbard": {"u_eV": {"Fe-3d": 5.3}, "projector": "atomic"},
                    "dft_protocol": {
                        "tag": "pbe+u",
                        "hubbard_projector": "atomic",
                        "hubbard_u_eV": {"Fe-3d": 5.3},
                    },
                    "al_config": {
                        "dft": {"qe": {"extra_electrons": {"conv_thr": 2e-3}, "kpts": [2, 4, 8]}},
                        "resources": {"pools": {"dft": {"nodes_per_job": 2}}},
                    },
                }
            )
        )
        _make_label(root, "iteration_0000", "a", True, None, 3600.0)
        _make_label(root, "iteration_0000", "b", False, "scf_not_converged", 1800.0)
        _make_label(root, "iteration_0000", "c", False, "timeout", 7200.0)
        run = report.summarise_run(root)
        r = run["rounds"][0]
        assert (r["attempted"], r["successful"], r["failed"]) == (3, 1, 2)
        assert r["failure_reasons"] == {"scf_not_converged": 1, "timeout": 1}
        assert abs(r["node_hours"] - (3600 + 1800 + 7200) * 2 / 3600) < 1e-9
        assert r["total_magnetization"]["mean"] == 3.97
        assert run["policy"]["dft_protocol_tag"] == "pbe+u"
        assert run["policy"]["hubbard_projector"] == "atomic"
        assert any("loose SCF" in w for w in run["warnings"])
        md = report.render_markdown([run])
        assert "pbe+u" in md and "scf_not_converged: 1" in md
        _make_label(root, "iteration_0001", "d", True, None, 10.0, tag="pbe")
        assert any("MIXED" in w for w in report.summarise_run(root)["warnings"])


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except Exception as exc:  # noqa: BLE001
                failed += 1
                print(f"FAIL {name}: {exc!r}")
    sys.exit(1 if failed else 0)
