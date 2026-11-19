"""Tight-reference SCF sweep for magnetic materials (LiFePO4 28-atom, FCC Cantor).

  python e3_qe_ref_sweep.py add  <material> <frame> <name> '<json edits>'   # create run dir (+manifest entry)
  python e3_qe_ref_sweep.py task <name-key>                                  # run one entry (1 node, GPU build)
  python e3_qe_ref_sweep.py summ                                             # print status table
Edits: {"SYSTEM": {key: val|null}, "ELECTRONS": {...}}; null deletes the key. Only these namelists differ from the pilot pw.in.
"""
from __future__ import annotations
import json, os, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path("/lustre/orion/ven136/proj-shared/ashwinaji/ai4science/matsim-eval")
INP = ROOT / "e3-qe-lux-inputs"
REF = INP / "qualification-ref"
PW_X = "/lustre/orion/ven136/proj-shared/qe/76omp-bf7acca2/bin/pw.x"
LAUNCHER = Path(__file__).resolve().parents[1] / "deployments/lux/launchers/_qe-step-lux.sh"
MAN = REF / "manifest.json"


def set_nml(text, nml, edits):
    lines = text.splitlines()
    s = next(i for i, l in enumerate(lines) if l.strip().upper().startswith("&" + nml))
    e = next(i for i in range(s + 1, len(lines)) if lines[i].strip() == "/")
    block = lines[s + 1:e]
    for k, v in edits.items():
        pat = re.compile(rf"^\s*{re.escape(k)}\s*=", re.I)
        block = [l for l in block if not pat.match(l)]
        if v is not None:
            block.append(f"  {k} = {v}")
    return "\n".join(lines[:s + 1] + block + lines[e:]) + "\n"


def add(material, frame, name, edits):
    d = REF / material / frame / name
    d.mkdir(parents=True, exist_ok=True)
    t = (INP / "validation" / material / "frames" / frame / "pw.in").read_text()
    for nml, ed in edits.items():
        t = set_nml(t, nml, ed)
    (d / "pw.in").write_text(t)
    man = json.load(open(MAN)) if MAN.exists() else {}
    man[f"{material}/{frame}/{name}"] = {"dir": str(d), "edits": edits}
    json.dump(man, open(MAN, "w"), indent=1)
    print(d)


def task(key):
    d = Path(json.load(open(MAN))[key]["dir"])
    env = dict(os.environ, MATSIM_DEVICES_PER_NODE="8", MATSIM_NODE_DEVICES="8")
    with open(d / "pw.out", "w") as log:
        subprocess.run(["bash", str(LAUNCHER), str(d), PW_X, str(d / "pw.in"), "1", "8", "16"],
                       stdout=log, stderr=subprocess.STDOUT, env=env, cwd=d)
    if os.environ.get("KEEP_TMP") != "1":
        shutil.rmtree(d / "tmp", ignore_errors=True)
    for c in d.glob("core.*"):
        c.unlink()


def summ():
    for k, v in json.load(open(MAN)).items():
        o = Path(v["dir"]) / "pw.out"
        t = o.read_text(errors="replace") if o.exists() else ""
        a = re.findall(r"estimated scf accuracy\s*<\s*([\d.eE+-]+)", t)
        m = re.findall(r"total magnetization\s*=\s*([-\d.]+)", t)
        am = re.findall(r"absolute magnetization\s*=\s*([-\d.]+)", t)
        conv = "CONV" if "convergence has been achieved" in t else ("NOCONV" if "convergence NOT" in t else "run")
        print(f"{k:50s} {conv:7s} it={len(a):3d} last={a[-1] if a else '-':>11} min={min(map(float,a)) if a else '-'} "
              f"mag={m[-1] if m else '-'}/{am[-1] if am else '-'}")


if __name__ == "__main__":
    c = sys.argv[1]
    if c == "add":
        add(sys.argv[2], sys.argv[3], sys.argv[4], json.loads(sys.argv[5]))
    elif c == "task":
        task(sys.argv[2])
    else:
        summ()
