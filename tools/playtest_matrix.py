"""Runs the playtest bots (scripts/playtest.gd) over every skill x faction x difficulty, several seeds each, in parallel
headless Godot processes, and collects each run's PLAYTEST line into <out>/results.jsonl.

    python tools/playtest_matrix.py <out dir> [--seeds 1,2] [--jobs 6] [--skills low,mid,high]
                                    [--factions crown,verdant,forge,tide,grave] [--difficulties 0,1,2] [--maxwave 30]

Every run uses a fresh profile (--fresh: no War Council upgrades) and never touches the player's save. Then
`python tools/playtest_report.py <out dir>` summarizes balance and pacing.
"""
import argparse, json, os, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

GODOT = os.environ.get("GODOT", r"C:\Users\maxja\OneDrive\Documents\Godot\Godot_v4.7.1-stable_win64_console.exe")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_one(out, skill, faction, diff, seed, maxwave):
    name = f"{skill}_{faction}_{diff}_{seed}"
    path = os.path.join(out, name + ".log")
    if os.path.exists(path) and "PLAYTEST {" in open(path, encoding="utf-8", errors="replace").read():
        return name, "cached", 0.0
    t0 = time.time()
    cmd = [GODOT, "--headless", "--path", REPO, "--", f"--autotest={faction}", f"--difficulty={diff}", f"--skill={skill}",
           f"--seed={seed}", f"--maxwave={maxwave}", "--fresh"]
    with open(path, "w", encoding="utf-8") as fh:
        try:
            subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT, timeout=1500)
            status = "ok"
        except subprocess.TimeoutExpired:
            status = "timeout"
    return name, status, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--seeds", default="1,2")
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--skills", default="low,mid,high")
    ap.add_argument("--factions", default="crown,verdant,forge,tide,grave")
    ap.add_argument("--difficulties", default="0,1,2")
    ap.add_argument("--maxwave", type=int, default=30)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    jobs = [(s, f, int(d), int(seed)) for seed in a.seeds.split(",") for d in a.difficulties.split(",")
            for f in a.factions.split(",") for s in a.skills.split(",")]
    print(f"{len(jobs)} runs, {a.jobs} at a time", flush=True)
    done = 0
    with ThreadPoolExecutor(a.jobs) as ex:
        futs = [ex.submit(run_one, a.out, s, f, d, seed, a.maxwave) for s, f, d, seed in jobs]
        for fu in futs:
            name, status, secs = fu.result()
            done += 1
            print(f"[{done}/{len(jobs)}] {name} {status} {secs:.0f}s", flush=True)
    with open(os.path.join(a.out, "results.jsonl"), "w", encoding="utf-8") as res:
        for fn in sorted(os.listdir(a.out)):
            if not fn.endswith(".log"):
                continue
            for line in open(os.path.join(a.out, fn), encoding="utf-8", errors="replace"):
                if line.startswith("PLAYTEST {"):
                    d = json.loads(line[len("PLAYTEST "):])
                    d["seed"] = int(fn[:-4].split("_")[-1])
                    res.write(json.dumps(d) + "\n")
    print("results in", os.path.join(a.out, "results.jsonl"))


if __name__ == "__main__":
    main()
