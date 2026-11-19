"""Login-node watcher for the E3-QE geometry handoff (see E3Sampler._handoff_geometry).

usage: SLURM_JOB_ID=<allocation> python scripts/e3_qe_geometry_watcher.py <run_out_dir> [--idle-exit-seconds N]

Runs on the login node (the only place the Lux LLM proxy accepts requests). For each
iteration_*/geometry-request.json without a geometry-handoff-done.json it runs the recorded
`benchmarks.e3.qe_active_learning geometry ...` command with this interpreter and writes the exit status.
"""
import argparse, json, os, subprocess, sys, time
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("out_dir", type=Path)
ap.add_argument("--idle-exit-seconds", type=float, default=7200)
args = ap.parse_args()
if not os.environ.get("SLURM_JOB_ID"):
    raise SystemExit("export SLURM_JOB_ID=<allocation id> first")
last = time.monotonic()
while time.monotonic() - last < args.idle_exit_seconds:
    for req in sorted(args.out_dir.glob("iteration_*/geometry-request.json")):
        done = req.with_name("geometry-handoff-done.json")
        if done.exists():
            continue
        command = [sys.executable, *json.loads(req.read_text())["command"]]
        print(f"[watcher] {time.ctime()} running {req.parent.name}", flush=True)
        rc = subprocess.run(command).returncode
        tmp = done.with_name(".done.tmp")
        tmp.write_text(json.dumps({"returncode": rc, "finished": time.ctime()}))
        os.replace(tmp, done)
        print(f"[watcher] {req.parent.name} rc={rc}", flush=True)
        last = time.monotonic()
    time.sleep(5)
