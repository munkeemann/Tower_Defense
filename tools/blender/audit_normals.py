"""Finds inside-out geometry in tower sources: every closed piece (a connected, watertight island of faces) of every
mesh should enclose a positive volume; a negative one has its faces wound inward, so single-sided materials (the
game's) cull its near side and show its inside.

    blender -b --factory-startup --python tools/blender/audit_normals.py -- <id> [<id> ...]

Prints one line per mesh with inverted pieces and a summary; exits 1 if any were found.
"""
import bpy, bmesh, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(REPO, "assets", "towers", "src")


def islands(bm):
    seen, out = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack, isl = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop()
            isl.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        out.append(isl)
    return out


def audit(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    closed = bad = 0
    for isl in islands(bm):
        fs = set(isl)
        if any(sum(1 for h in e.link_faces if h in fs) != 2 for f in isl for e in f.edges):
            continue            # open (a plane, a membrane): no inside to speak of
        closed += 1
        vol = 0.0
        for f in isl:
            vs = [v.co for v in f.verts]
            for i in range(1, len(vs) - 1):
                vol += vs[0].dot(vs[i].cross(vs[i + 1])) / 6.0
        if vol < 0:
            bad += 1
    bm.free()
    return closed, bad


def main():
    ids = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    total = 0
    for tid in ids:
        bpy.ops.wm.open_mainfile(filepath=os.path.join(SRC, tid + ".blend"))
        for o in bpy.data.objects:
            if o.type != "MESH" or o.name.startswith("guide_hex"):
                continue
            closed, bad = audit(o)
            if bad:
                total += bad
                print("AUDIT %s %s: %d of %d closed pieces inside out" % (tid, o.name, bad, closed))
    print("AUDIT done: %d inside-out pieces in %d towers" % (total, len(ids)))
    sys.exit(1 if total else 0)


main()
