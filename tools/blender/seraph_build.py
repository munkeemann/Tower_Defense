"""Builds the Seraph (footprint "arrow3": [0,0] front, [1,0] back-right, [-1,1] back-left), a creature tower.

    python tools/blender/build.py seraph --out <preview dir>

One sanctuary: an armored angel (KayKit's Paladin with helmet) hovers over a round, stepped marble dais on the front
cell. Rings of marble paving spread from the dais over all three hexes, and on the two back cells stand the two halves
of the broken colonnade that rings it: white columns on a stepped stylobate under a gilded entablature, team-colored
drapes swagged between them, a brazier burning behind each half. The angel is the Head: it turns toward targets and
throws (spears of light leave from the Muzzle at its hand).
idle: it hovers, the wings beat slowly, the halo turns. fire: the throw (from the pack's clip, its wind-up trimmed so
the spear leaves on the first frames), a hard wing beat, and the spear forms again in its hand.
"""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "angel_common.py"), encoding="utf-8").read())

TID = "seraph"
CELLS = [(0, 0), (1, 0), (-1, 1)]
MID = footprint_mid(CELLS)
FRONT = hex_to_world(0, 0, MID)
BR = hex_to_world(1, 0, MID)
BL = hex_to_world(-1, 1, MID)
TOP = 0.34
DAIS = TOP + 0.44             # the dais top (the Head)
CHAR = "Paladin_with_Helmet.glb"
HEIGHT = 1.5
HOVER = 0.5
GOLD = (1.0, 0.8, 0.35)
RC = 2.3                      # the colonnade's radius round the dais (clear of the wings' sweep)
COLS = (-44, -26, -8)         # its columns' angles (degrees) on the right half, mirrored on the left
COL_H = 1.35
STYLO = TOP + 0.2             # the stylobate's top


def fits(x, y, inset=0.12):
    return in_footprint(CELLS, x, y, inset)


def _angles(sx):
    return [a if sx > 0 else 180 - a for a in COLS]


def build_base():
    col = collection("Seraph")
    root = empty("Seraph", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    rnd = random.Random(7)
    k = Kit()
    F = FRONT
    c = (F.x, F.y)
    spans = []
    for sx in (1, -1):
        a = _angles(sx)
        spans.append((min(a) - 9, max(a) + 9))

    def under_stylobate(x, y):
        r = math.hypot(x - c[0], y - c[1])
        a = math.degrees(math.atan2(y - c[1], x - c[0]))
        a = a if a > -90 else a + 360
        return RC - 0.4 < r < RC + 0.4 and any(lo - 2 < a < hi + 2 for lo, hi in spans)

    # ---- the floor: one bed over all three hexes, rings of marble slabs laid on it round the dais
    prism(k["white:0.55:0.95"], outline(CELLS, 0.1), T - 0.02, T + 0.03)
    k.emit("Floor", col, root, tag="no_refine")
    ring_paving(k, rnd, c, 0.9, 1.98, T + 0.03, keep=lambda x, y: fits(x, y, 0.13) and not under_stylobate(x, y),
                h=0.04, width=0.36, block=0.52, swatches=("white:0.12:0.55", "white:0.12:0.55", "cream:0.15:0.6"))
    bm_flagstones(k["white:0.1:0.5"], rnd, lambda x, y: fits(x, y, 0.3) and math.hypot(x - c[0], y - c[1]) > 2.12 and not under_stylobate(x, y),
                  (-3.2, -1.6, 3.2, 1.9), T + 0.03, size=0.36, gap=0.04, h=0.035)
    k.emit("Paving", col, root, vary=0.08)
    # ---- the dais: three tiers of coursed marble with gilded nosings, a glowing sigil on top
    tiers = ((0.95, T, T + 0.16, 24), (0.77, T + 0.16, T + 0.31, 20), (0.58, T + 0.31, DAIS, 16))
    for i, (r, z0, z1, n) in enumerate(tiers):
        bm_block_course(k["white:0.05:0.45"], rnd, (c[0], c[1], 0), r, z0, z1 - z0, n, depth=0.22, phase=0.5 * i)
        ring(k["gold:0.1:0.5"], (c[0], c[1], 0), r + 0.012, r - 0.06, z1 - 0.03, z1 + 0.006, seg=20)
    bm_cyl(k["cream:0.4:0.9"], 0.76, 0.76, 0.3, (c[0], c[1], T + 0.15), seg=20)
    bm_cyl(k["white:0.05:0.35"], 0.4, 0.4, DAIS - T - 0.32, (c[0], c[1], (T + 0.3 + DAIS - 0.02) / 2), seg=16)
    k.emit("Dais", col, root, vary=0.07)
    ring(k["gold:0.05:0.4"], (c[0], c[1], 0), 0.37, 0.32, DAIS - 0.02, DAIS + 0.01, seg=24)
    for i in range(8):
        a = math.radians(45 * i + 22.5)
        p0 = Vector((c[0] + math.cos(a) * 0.1, c[1] + math.sin(a) * 0.1, DAIS - 0.01))
        p1 = Vector((c[0] + math.cos(a) * 0.31, c[1] + math.sin(a) * 0.31, DAIS - 0.01))
        bm_beam(k["team!:0.1:0.45"], p0, p1, 0.09 if i % 2 == 0 else 0.06, 0.03, w1=0.0, h1=0.03)
    bm_cyl(k["glow:1.0,0.85,0.45,0.9"], 0.09, 0.07, 0.03, (c[0], c[1], DAIS + 0.005), seg=10)
    k.emit("Dais_Sigil", col, root)
    # ---- two team runners from the top of the dais, down its steps and across the paving to the colonnade halves
    steps = [(0.38, DAIS), (0.58, T + 0.31), (0.77, T + 0.16), (0.95, T + 0.07)]
    for sx in (1, -1):
        a = math.radians(_angles(sx)[1])
        o = Vector((math.cos(a), math.sin(a), 0))
        C0 = Vector((c[0], c[1], 0))
        pts = [C0 + o * 0.38 + Vector((0, 0, DAIS + 0.012))]
        for (r0, z0), (r1, z1) in zip(steps, steps[1:]):
            pts += [C0 + o * (r1 + 0.02) + Vector((0, 0, z0 + 0.012)), C0 + o * (r1 + 0.02) + Vector((0, 0, z1 + 0.012))]
        pts.append(C0 + o * (RC - 0.42) + Vector((0, 0, T + 0.082)))
        for p, q in zip(pts, pts[1:]):
            if (q - p).length < 1e-4:
                continue
            vert = abs(q.z - p.z) > 1e-3
            bm_beam(k["team!:0.1:0.6"], p, q, 0.4, 0.024, up=tuple(o) if vert else (0, 0, 1))
        t = Vector((-o.y, o.x, 0))
        f0, f1 = C0 + o * 0.97 + Vector((0, 0, T + 0.088)), C0 + o * (RC - 0.42) + Vector((0, 0, T + 0.088))
        for s in (-1, 1):
            bm_beam(k["gold:0.05:0.4"], f0 + t * (s * 0.17), f1 + t * (s * 0.17), 0.035, 0.012)
        bm_beam(k["gold:0.05:0.4"], f1 - t * 0.21, f1 + t * 0.21, 0.05, 0.03)
    k.emit("Runner", col, root)
    # ---- the colonnade: two arcs of it on the back cells, ringing the dais
    for sx in (1, -1):
        angs = sorted(_angles(sx))
        lo, hi = angs[0] - 9, angs[-1] + 9
        ring_blocks(k["white:0.12:0.6"], rnd, c, RC + 0.4, 0.8, T, T + 0.1, lo - 5, hi + 5, block=0.5, keep=fits, fit=True)
        ring_blocks(k["white:0.08:0.5"], rnd, c, RC + 0.28, 0.56, T + 0.1, STYLO, lo - 1, hi + 1, block=0.5, phase=0.5, keep=fits, fit=True)
        for a in angs:
            ar = math.radians(a)
            column(k, rnd, (c[0] + RC * math.cos(ar), c[1] + RC * math.sin(ar)), STYLO, COL_H, 0.13, courses=3)
        z = STYLO + COL_H
        ring_blocks(k["white:0.05:0.4"], rnd, c, RC + 0.19, 0.38, z, z + 0.14, lo, hi, block=0.55)              # architrave
        ring_blocks(k["gold:0.1:0.5"], rnd, c, RC + 0.16, 0.32, z + 0.14, z + 0.25, lo + 0.5, hi - 0.5, block=0.3)   # frieze
        ring_blocks(k["white:0.03:0.35"], rnd, c, RC + 0.24, 0.44, z + 0.25, z + 0.33, lo - 1.5, hi + 1.5, block=0.5)  # cornice
        for r0 in (RC + 0.25, RC - 0.14):                                                                       # its gilded lips
            ring_blocks(k["gold:0.05:0.4"], rnd, c, r0, 0.06, z + 0.32, z + 0.36, lo - 1.5, hi + 1.5, block=0.45, gap=0.0, jit=0.0)
        for a0, a1 in zip(angs, angs[1:]):
            drape(k, c, RC + 0.21, a0 + 2, a1 - 2, z - 0.01, 0.12, 0.4)
        # the team's banner down the outer face, over the middle column: seen from behind
        am = math.radians(angs[1])
        o = Vector((math.cos(am), math.sin(am), 0))
        t = Vector((-o.y, o.x, 0))
        p = Vector((c[0], c[1], 0)) + o * (RC + 0.22)
        bm_beam(k["gold:0.05:0.4"], p - t * 0.24 + Vector((0, 0, z - 0.03)), p + t * 0.24 + Vector((0, 0, z - 0.03)), 0.05, 0.05)
        bm = k["team!:0.1:0.7"]
        pts = [(-0.19, 0.0), (0.19, 0.0), (0.19, -0.9), (0.0, -0.74), (-0.19, -0.9)]
        for off, flip in ((0.014, True), (0.0, False)):
            vs = [bm.verts.new(p + o * off + t * u + Vector((0, 0, z - 0.04 + v))) for u, v in pts]
            bm.faces.new(list(reversed(vs)) if flip else vs)
        bm_cyl(k["gold:0.05:0.4"], 0.07, 0.07, 0.02, tuple(p + o * 0.022 + Vector((0, 0, z - 0.36))), rot=rot_deg(o), seg=8)
        for a in (lo + 1.5, hi - 1.5):          # gilded acroteria at the ends of the cornice
            ar = math.radians(a)
            p = Vector((c[0] + (RC + 0.05) * math.cos(ar), c[1] + (RC + 0.05) * math.sin(ar), z + 0.35))
            bm_crystal(k["gold:0.05:0.4"], p, p + Vector((0, 0, 0.24)), 0.09, n=4, shoulder=0.4, foot=1.0)
        am = math.radians(angs[1])              # a holy flame over the middle column
        fire_bowl(k, rnd, (c[0] + (RC + 0.05) * math.cos(am), c[1] + (RC + 0.05) * math.sin(am)), z + 0.34)
    k.emit("Colonnade", col, root, vary=0.07)
    empty("Head", col, root, (F.x, F.y, DAIS), 0.5, "SINGLE_ARROW")
    return root


def build_head():
    col = collection("Seraph")
    return make_angel(CHAR, col, bpy.data.objects["Head"], HEIGHT, HOVER, span=1.05, halo_r=0.17, weapon=(0.45, 1.15),
                      blade=(0.17, 0.42), gold=GOLD)


def build_anims():
    # the throw's wind-up is trimmed, so the spear leaves on the first frames (the game fires as the clip starts)
    angel_anims(bpy.data.objects["Rig"], "Jump_Idle", "Throw", fire_start=0.32, fire_speed=0.68, hide=(3, 14, 22))


PREVIEW = {"target": (0, 0, 1.4), "dist": 9.0, "yaw": 160, "pitch": 18, "anim_target": (0, FRONT.y, 1.8), "anim_dist": 5.0,
           "frames": [("idle", 0), ("idle", 30), ("fire", 2), ("fire", 8), ("fire", 20)],
           "extra": [{"yaw": 15, "pitch": 40, "dist": 4.2, "target": (0, FRONT.y, 2.0)},
                     {"yaw": 120, "pitch": 22, "dist": 4.5, "target": (BR.x, BR.y, 1.3)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
