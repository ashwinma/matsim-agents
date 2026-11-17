"""Summarise wall time and run details of every pw.x calculation under an inputs dir."""
import csv, re, sys
from pathlib import Path

root = Path(sys.argv[1])

def wall_seconds(text):
    m = re.findall(r"PWSCF\s*:.*?CPU\s+(.*?)\s+WALL", text)
    if not m:
        return None
    parts = dict((u, float(v)) for v, u in re.findall(r"([\d.]+)\s*([dhms])", m[-1]))
    return parts.get("d", 0) * 86400 + parts.get("h", 0) * 3600 + parts.get("m", 0) * 60 + parts.get("s", 0)


def first(pattern, text, cast=str):
    m = re.search(pattern, text)
    return cast(m.group(1)) if m else ""

rows = []
for out in sorted(root.rglob("pw.out")):
    rel = out.relative_to(root).parts
    if rel[0] == "validation":
        kind, material, label = "validation", rel[1], rel[3]
    elif rel[0] == "elemental" and rel[1] == "cache":
        kind, material = "elemental-" + rel[3].rstrip("s"), rel[2]
        label = rel[-2]
    else:
        continue  # diagnostics/smoke/superseded are not part of the final set
    text = out.read_text(errors="replace")
    inp = out.with_name("pw.in")
    inp_text = inp.read_text() if inp.exists() else ""
    species = sorted(set(re.findall(r"^\s*([A-Z][a-z]?)\s+[\d.]+\s+\S+\.(?:UPF|upf)", inp_text, re.M)))
    rows.append({
        "kind": kind, "material": material, "label": label,
        "formula_species": "".join(species),
        "n_atoms": first(r"number of atoms/cell\s*=\s*(\d+)", text, int),
        "n_electrons": first(r"number of electrons\s*=\s*([\d.]+)", text, float),
        "n_kpoints": first(r"number of k points=\s*(\d+)", text, int),
        "nspin": 2 if "nspin" in inp_text and re.search(r"nspin\s*=\s*2", inp_text) else 1,
        "hubbard": "yes" if "HUBBARD" in inp_text else "no",
        "ecutwfc_ry": first(r"kinetic-energy cutoff\s*=\s*([\d.]+)", text, float),
        "ecutrho_ry": first(r"charge density cutoff\s*=\s*([\d.]+)", text, float),
        "mpi_ranks": first(r"Number of MPI processes:\s*(\d+)", text, int),
        "scf_iterations": first(r"convergence has been achieved in\s+(\d+)\s+iterations", text, int),
        "converged": "JOB DONE." in text and "convergence NOT achieved" not in text,
        "wall_s": wall_seconds(text) or "",
        "path": str(out.parent.relative_to(root)),
    })

fields = list(rows[0])
with open(root / "qe-timing.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(rows)

def fmt(s):
    return f"{s/3600:.2f} h" if s >= 3600 else f"{s/60:.1f} min"

lines = ["| Kind | Material | Runs | Converged | Atoms (min-max) | Median wall | Max wall | Total wall (rank-job time) |", "|---|---|---|---|---|---|---|---|"]
from itertools import groupby
from statistics import median
key = lambda r: (r["kind"], r["material"])
for (k, m), grp in groupby(sorted(rows, key=key), key):
    g = list(grp); w = [r["wall_s"] for r in g if r["wall_s"] != ""]
    a = [r["n_atoms"] for r in g if r["n_atoms"] != ""]
    lines.append(f"| {k} | {m} | {len(g)} | {sum(r['converged'] for r in g)} | {min(a, default='')}-{max(a, default='')} | {fmt(median(w)) if w else '-'} | {fmt(max(w)) if w else '-'} | {fmt(sum(w))} |")
total = sum(r["wall_s"] for r in rows if r["wall_s"] != "")
lines.append(f"\nTotal pw.x wall time over {len(rows)} runs: {fmt(total)} (sum of per-run wall; each run used 1 node, 8 ranks).")
(root / "qe-timing-summary.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
