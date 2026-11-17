from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from ase import Atoms

from matsim_agents.active_learning.dft_protocol import scientific_dft_payload
from matsim_agents.backends.dft.config import DFTConfig
from matsim_agents.backends.dft.qe_relax import kmesh_from_spacing


def _spacing_from(cell, mesh):
    b = np.linalg.norm(np.asarray(cell.reciprocal()), axis=1)
    return [2 * math.pi * x / n for x, n in zip(b, mesh)]


def test_reference_cell_reproduces_its_mesh() -> None:
    cell = Atoms(cell=[14.304, 14.304, 7.152], pbc=True).cell
    s = _spacing_from(cell, (2, 2, 2))
    assert kmesh_from_spacing(cell, s) == (2, 2, 2)


def test_doubling_a_vector_halves_that_axis() -> None:
    ref = Atoms(cell=[10.0, 6.0, 5.0], pbc=True).cell
    s = _spacing_from(ref, (4, 6, 8))
    big = Atoms(cell=[20.0, 6.0, 5.0], pbc=True).cell
    assert kmesh_from_spacing(big, s) == (2, 6, 8)


def test_nonpositive_spacing_is_gamma_only() -> None:
    cell = Atoms(cell=[3.3, 4.6, 20.0], pbc=True).cell
    assert kmesh_from_spacing(cell, [0.9, 0.9, 0.0])[2] == 1
    assert kmesh_from_spacing(Atoms(cell=[3.3, 4.6, 5.0], pbc=True).cell, [0.9, 0.9, 0.0])[2] == 1


def test_nonorthogonal_nb_ta_o_cell_reproduces_4_8_9() -> None:
    cell = Atoms(cell=[[12.73, 0, 0], [-1.44372, 5.36929, 0], [0, 0, 4.88]], pbc=True).cell
    assert kmesh_from_spacing(cell, _spacing_from(cell, (4, 8, 9))) == (4, 8, 9)


def test_small_strain_does_not_change_mesh() -> None:
    cell = Atoms(cell=[13.367] * 3, pbc=True).cell
    s = _spacing_from(cell, (2, 2, 2))
    for f in (0.99, 1.0, 1.01):
        assert kmesh_from_spacing(Atoms(cell=[13.367 * f] * 3, pbc=True).cell, s) == (2, 2, 2)


def _cfg(tmp_path: Path, **qe) -> DFTConfig:
    (tmp_path / "Fe.upf").write_text("x")
    return DFTConfig.model_validate({"backend": "qe", "qe": {
        "pw_bin": str(tmp_path / "pw.x"), "pw_wrapper": str(tmp_path / "w.sh"),
        "pseudo_dir": str(tmp_path), "pseudopotentials": {"Fe": "Fe.upf"}, **qe}})


def test_exclusive_with_kpts_and_in_signature(tmp_path: Path) -> None:
    try:
        _cfg(tmp_path, kpts=[2, 2, 2], kpoint_spacing_inv_A=[0.2, 0.2, 0.2])
    except ValueError as exc:
        assert "mutually exclusive" in str(exc)
    else:
        raise AssertionError("expected ValueError")
    fixed = scientific_dft_payload(_cfg(tmp_path, kpts=[2, 2, 2]), {"Fe"})
    dens = scientific_dft_payload(_cfg(tmp_path, kpoint_spacing_inv_A=[0.2, 0.2, 0.2]), {"Fe"})
    assert "kpoint_spacing_inv_A" not in fixed and dens["kpoint_spacing_inv_A"] == [0.2, 0.2, 0.2]
