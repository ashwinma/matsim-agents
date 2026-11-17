from __future__ import annotations

from pathlib import Path

from matsim_agents.active_learning.dft_protocol import scientific_dft_payload
from matsim_agents.backends.dft.config import DFTConfig


def _cfg(tmp_path: Path, **qe) -> DFTConfig:
    upf = tmp_path / "Fe.upf"
    upf.write_text("x")
    return DFTConfig.model_validate(
        {
            "backend": "qe",
            "qe": {
                "pw_bin": str(tmp_path / "pw.x"),
                "pw_wrapper": str(tmp_path / "w.sh"),
                "pseudo_dir": str(tmp_path),
                "pseudopotentials": {"Fe": "Fe.upf"},
                **qe,
            },
        }
    )


def test_hubbard_u_changes_scientific_payload(tmp_path: Path) -> None:
    plain = scientific_dft_payload(_cfg(tmp_path), {"Fe"})
    empty = scientific_dft_payload(_cfg(tmp_path, hubbard_u={}), {"Fe"})
    with_u = scientific_dft_payload(_cfg(tmp_path, hubbard_u={"Fe-3d": 5.3}), {"Fe"})
    other_u = scientific_dft_payload(_cfg(tmp_path, hubbard_u={"Fe-3d": 4.0}), {"Fe"})
    other_proj = scientific_dft_payload(
        _cfg(tmp_path, hubbard_u={"Fe-3d": 5.3}, hubbard_projector="ortho-atomic"), {"Fe"}
    )
    assert not plain["hubbard_u"] and not empty["hubbard_u"]
    assert with_u["hubbard_u"] == {"Fe-3d": 5.3}
    assert with_u != plain and with_u != other_u and with_u != other_proj
