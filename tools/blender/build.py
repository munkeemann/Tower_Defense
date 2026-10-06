"""Builds towers with a background Blender at low priority (so it never disturbs an open Blender, or a game):

    python tools/blender/build.py <tower id> [more ids...] [--out <preview dir>] [--jobs N] [--script other.py]

For each id it runs tools/blender/build_tower.py (see there), writes the log to <preview dir>/<id>.log, and prints one
line: "OK <id> tris=<n> glb=<bytes>" or "FAIL <id>" with the end of the log. A background Blender exits 0 even when its
script throws, so the check is the "BUILD saved" line. Exit code 1 if any tower failed.

--script runs another script under tools/blender instead of build_tower.py (its arguments: the id, then the preview
dir), e.g. --script render_tower.py to render an already-built tower again.
The Blender to use: the BLENDER environment variable, else the portable install on E:.
"""
import os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
BLENDER = os.environ.get("BLENDER", r"E:\Blender\blender-5.2.2-windows-x64\blender.exe")
LOW = getattr(subprocess, "BELOW_NORMAL_PRIORITY_CLASS", 0)


def build(tid, out, script):
    os.makedirs(out, exist_ok=True)
    log = os.path.join(out, tid + ".log")
    with open(log, "w", encoding="utf-8", errors="replace") as f:
        subprocess.run([BLENDER, "-b", "--factory-startup", "--python", os.path.join(HERE, script), "--", tid, out],
                       stdout=f, stderr=subprocess.STDOUT, cwd=REPO, creationflags=LOW)
    text = open(log, encoding="utf-8", errors="replace").read()
    done = [l for l in text.splitlines() if l.startswith(("BUILD saved", "RENDER done"))]
    if done and "Traceback" not in text:
        tris = done[0].rsplit("tris", 1)[1].strip() if "tris" in done[0] else "?"
        glb = os.path.join(REPO, "assets", "towers", tid + ".glb")
        return True, "OK %s tris=%s glb=%d" % (tid, tris, os.path.getsize(glb) if os.path.exists(glb) else 0)
    tail = text[text.rfind("Traceback"):] if "Traceback" in text else "\n".join(text.splitlines()[-15:])
    return False, "FAIL %s (log: %s)\n%s" % (tid, log, tail.strip())


def main():
    args = sys.argv[1:]
    out = os.path.join(REPO, ".preview")
    jobs, script, ids = 1, "build_tower.py", []
    while args:
        a = args.pop(0)
        if a == "--out":
            out = os.path.abspath(args.pop(0))
        elif a == "--jobs":
            jobs = int(args.pop(0))
        elif a == "--script":
            script = args.pop(0)
        else:
            ids.append(a)
    if not ids:
        print(__doc__)
        return 2
    ok = True
    with ThreadPoolExecutor(max_workers=max(1, jobs)) as ex:
        for good, line in ex.map(lambda t: build(t, out, script), ids):
            print(line, flush=True)
            ok = ok and good
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
