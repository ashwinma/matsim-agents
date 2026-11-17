"""Write validation-<material>.parents.json next to each delivered validation extxyz."""
import json
import sys
from pathlib import Path

from ase.io import read

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from benchmarks.e3.structure_generation import _source  # noqa: E402

root = Path(sys.argv[1])
S4 = REPO / "research/paper/e4/aurora-dft-scaling/stage1-inputs-v2"
SEEDS = REPO / "examples/paper_cases/seeds"


def sha(path):
    return _source(path)[1]


def bases(material):
    """Ordered like scripts/e3_qe_reference_inputs.py::_base_structures."""
    if material == "bcc_refractory":
        return [(p, p, "E4 stage-1 POSCAR") for p in sorted((S4 / "bcc_refractory").glob("*/POSCAR"))]
    if material == "fcc_cantor":
        return [(p, p, "E4 stage-1 POSCAR") for p in sorted((S4 / "fcc_hea").glob("*/POSCAR"))]
    if material == "nb_ta_o":
        return [(p, p, "Nb-Ta-O pilot POSCAR") for p in sorted((REPO / "research/nb-ta-o/pilot/poscars").glob("*.POSCAR"))]
    if material == "lifepo4":
        seed = SEEDS / "lifepo4_olivine.extxyz"
        out = [(p, seed, "2x2x1 supercell of the olivine seed, Li-Fe antisite pairs (verified by site matching)")
               for p in sorted((S4 / "lifepo4").glob("*/POSCAR"))]
        return out + [(seed, seed, "olivine seed itself")]
    if material == "phosphorene":
        b, u = SEEDS / "phosphorene_black_P.extxyz", SEEDS / "phosphorene_blue_P.extxyz"
        return [(b, b, "seed"), (u, u, "seed"), (b, b, "2x2x1 supercell of seed"), (u, u, "3x2x1 supercell of seed")]
    if material == "zn_formate_mof":
        c = SEEDS / "zn_formate_cod_7205949.cif"
        return [(c, c, "seed")]


for material in ("phosphorene", "nb_ta_o", "zn_formate_mof", "bcc_refractory", "fcc_cantor", "lifepo4"):
    frames = read(root / f"validation-{material}.extxyz", index=":")
    table = bases(material)
    rows = []
    for i, f in enumerate(frames):
        src, parent, how = table[int(f.info["validation_base_index"])]
        rows.append({
            "frame": i,
            "validation_base_index": int(f.info["validation_base_index"]),
            "variant": int(f.info["validation_variant"]),
            "parent_id": sha(parent),
            "parent_file": str(parent.relative_to(REPO)),
            "derived_from": str(src.relative_to(REPO)),
            "derivation": how,
        })
    (root / f"validation-{material}.parents.json").write_text(
        json.dumps({"material": material, "n_frames": len(rows), "frames": rows}, indent=1))
    print(material, len(rows), "parents:", len({r["parent_id"] for r in rows}))
