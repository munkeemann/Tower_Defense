"""Builds the Wasp Hive (footprint "pair": [0,0] front, [0,1] back), a Verdant tower: a swarm of stingers, five a second.

    python tools/blender/build.py hive --out <preview dir>

One gnarled old tree owns both cells: it stands on the back cell, thick roots running forward across the front one,
and its trunk crooks up, round and over, to hold a giant paper hive over the front cell: layer on layer of scalloped
paper, a spout of an entrance glowing amber, the team's sash round its neck. The hive is the Head (it turns its
entrance toward its target), so it hangs free of the trunk, round its own axis. Honey drips off its tip into the
beekeeper's crock on the roots below; comb hangs under the crook and fills the hollow at the trunk's foot, honey
running down the bark. Tucked in the roots: a straw skep and honey pots on a rug in the team's color; the team's
ribbons hang from the boughs.
Big striped wasps circle on bones: a low ring round the entrance, a high one over the crook (where the camera sees it).
Clips: idle (wasps circle, wings a blur; the hive sways; honey drips; the entrance's glow breathes), fire (five frames:
the hive throbs, the glow flares, every wasp darts out and back; it plays five times a second).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "megabeast_common.py"), encoding="utf-8").read())

TID = "hive"
CELLS = [(0, 0), (0, 1)]
MID = footprint_mid(CELLS)
FRONT = hex_to_world(0, 0, MID)        # (0, 1.04)
BACK = hex_to_world(0, 1, MID)         # (0, -1.04)
TOP = 0.34
AX, AY = 0.3, 0.9                      # the hive's axis: the Head
HONEY = "glow:1.0,0.58,0.08,0.7"
AMBER = "glow:1.0,0.72,0.2,1.0"
BARK, BARK2 = "wood_dark:0.2:0.9", "wood_dark:0.5:0.98"
# the trunk's middle line: (x, y, height above the ground, radius): up from the back cell, round and over the hive
# (it keeps to the left, so that from behind, where the game's camera is, the hive hangs clear of it)
TRUNK = [(-0.5, -1.0, -0.05, 0.56), (-0.6, -0.94, 0.5, 0.45), (-0.74, -0.76, 1.1, 0.38), (-0.82, -0.4, 1.7, 0.33),
         (-0.8, 0.12, 2.25, 0.28), (-0.46, 0.62, 2.58, 0.23), (AX, AY, 2.62, 0.19), (0.72, 1.0, 2.5, 0.13), (1.02, 1.04, 2.26, 0.06)]
# the hive's outline, top to tip: (height above the Head, radius)
PROF = [(2.74, 0.165), (2.57, 0.3), (2.39, 0.4), (2.19, 0.495), (1.99, 0.595), (1.79, 0.67), (1.59, 0.7), (1.41, 0.64),
        (1.25, 0.505), (1.11, 0.33), (1.0, 0.11)]
MOUTH = Vector((0, 0.73, 1.34))        # the entrance, in the Head's space
WS = 0.8                               # wasp scale
# wasps: (orbit radius, height, start angle, turns per loop (+ counterclockwise), bob)
WASPS = [(0.92, 1.26, 80, 1, 0.06), (1.0, 1.1, 215, -1, 0.05), (0.82, 1.4, 330, 2, 0.05),
         (0.62, 3.12, 20, -1, 0.08), (0.95, 3.26, 150, 1, 0.07), (0.5, 3.42, 265, 2, 0.05)]
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "hive": ((0, 0, 2.62), (0, 0, 1.9), "root"),
    "glow": (tuple(MOUTH - Vector((0, 0.06, 0))), tuple(MOUTH + Vector((0, 0.1, 0))), "hive"),
    "drop.1": ((0, 0, 0.9), (0, 0, 0.72), "root"),
    "drop.2": ((0, 0, 0.9), (0, 0, 0.72), "root"),
}
for _i, (_r, _z, _a, _n, _b) in enumerate(WASPS):
    _d = 1 if _n > 0 else -1
    BONES["orbit.%d" % _i] = ((0, 0, _z), (0, 0, _z + 0.2), "root")
    BONES["wasp.%d" % _i] = ((_r, 0, _z), (_r, 0.3 * _d, _z), "orbit.%d" % _i)
    BONES["wing.%d" % _i] = ((_r, 0.04 * _d, _z + 0.03), (_r, 0.04 * _d, _z + 0.23), "wasp.%d" % _i)


def _trunk_at(t):
    """A point `t` (0..1) of the way up the trunk's middle line (by index, not by length), and its radius there."""
    x = t * (len(TRUNK) - 1)
    i = min(int(x), len(TRUNK) - 2)
    a, b = TRUNK[i], TRUNK[i + 1]
    f = x - i
    return Vector((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f)), a[3] + (b[3] - a[3]) * f


def _comb(k, c, across, w, h, th=0.07, cells=True):
    """A plate of honeycomb hanging from c: `w` wide along `across`, `h` deep, rounded below, cells on both faces."""
    ax = Vector(across).normalized()
    nrm = ax.cross(Vector((0, 0, 1))).normalized()
    c = Vector(c)
    pts = [c + Vector((0, 0, 0.03)), c - Vector((0, 0, h * 0.35)), c - Vector((0, 0, h * 0.75)), c - Vector((0, 0, h))]
    bm_tube(k["gold:0.1:0.7"], pts, [w * 0.42, w * 0.5, w * 0.4, 0.0], n=8, squash=th / w, up=ax)
    if cells:
        for row in range(3):
            for i in range(-2, 3):
                x = (i + (0.5 if row % 2 else 0.0)) * 0.105
                z = -0.12 - row * 0.1
                if abs(x) > w * (0.4 - 0.08 * row) or -z > h * 0.8:
                    continue
                for side in (1, -1):
                    p = c + ax * x + Vector((0, 0, z)) + nrm * (side * th * 0.5)
                    bm_tube(k["gold:0.62:0.98"], [p - nrm * (side * 0.012), p + nrm * (side * 0.012)], 0.04, n=6, up=(0, 0, 1))


def build_base():
    col = collection("Hive")
    root = empty("Hive", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP, turf=True)
    rnd = random.Random(9)
    k = Kit()
    Z = Vector((0, 0, T))
    # ---- the old tree: a crooked trunk, lumpy and ridged, burls, broken stubs
    pts = [Vector((x, y, T + z)) for x, y, z, r in TRUNK]
    rings = bm_tube(k[BARK], pts, [r for x, y, z, r in TRUNK], n=9)
    for i, vring in enumerate(rings):
        c = sum((v.co for v in vring), Vector()) / len(vring)
        for v in vring:
            v.co = c + (v.co - c) * (1.0 + rnd.uniform(-0.1, 0.14) * (0.5 if i >= 5 else 1.0))
    for a0, tw in ((0.5, 1.1), (2.4, 0.8), (4.0, 1.3), (5.3, 0.9)):               # bark ridges winding up it
        rp = []
        for j in range(9):
            t = 0.02 + 0.62 * j / 8
            c, r = _trunk_at(t)
            c2, _ = _trunk_at(t + 0.02)
            tan = (c2 - c).normalized()
            u = Vector((0, 0, 1)).cross(tan)
            u = u.normalized() if u.length > 1e-3 else Vector((1, 0, 0))
            w = tan.cross(u)
            a = a0 + tw * t * 2.0
            rp.append(c + Z + (u * math.cos(a) + w * math.sin(a)) * (r * 0.97))
        bm_tube(k[BARK2], rp, [0.085, 0.08, 0.075, 0.07, 0.065, 0.06, 0.055, 0.045, 0.03], n=4)
    for t, a, r in ((0.16, 2.6, 0.2), (0.33, 0.4, 0.17), (0.45, 3.6, 0.15)):       # burls
        c, tr = _trunk_at(t)
        d = Vector((math.cos(a), math.sin(a), 0.1))
        bm_boulder(k[BARK], rnd, c + Z + d * (tr * 0.8) - Vector((0, 0, r * 0.5)), r, n=11, sink=0.0)
    stubs = [(0.3, Vector((-0.3, -0.9, 0.45)), 0.34, 0.09), (0.52, Vector((-0.3, 0.8, 0.5)), 0.3, 0.075), (0.2, Vector((0.2, -1.0, 0.45)), 0.26, 0.085)]
    for t, d, ln, r in stubs:
        c, tr = _trunk_at(t)
        d = d.normalized()
        bm_tube(k[BARK], [c + Z + d * (tr * 0.5), c + Z + d * (tr + ln)], [r * 1.25, r], n=6)
        bm_tube(k["sand:0.2:0.7"], [c + Z + d * (tr + ln - 0.01), c + Z + d * (tr + ln + 0.012)], r * 0.72, n=6)
    # one living bough, back and to the right over the skep (low and behind: it hides nothing of the hive)
    boughs = [([(-0.74, -0.76, 1.1), (-0.42, -1.12, 1.5), (-0.05, -1.38, 1.84), (0.28, -1.5, 2.1)], [0.18, 0.14, 0.1, 0.045]),
              ([(-0.05, -1.38, 1.84), (0.3, -1.2, 2.0), (0.56, -1.12, 2.14)], [0.07, 0.055, 0.03])]
    for bp, br in boughs:
        bm_tube(k[BARK], [Vector(p) + Z for p in bp], br, n=6)
    # roots: thick ones forward through the neck between the cells and round the crock, shorter ones behind
    B0 = Vector((-0.55, -1.0, 0))
    roots = [[(-0.3, -0.72), (-0.22, -0.3), (-0.32, 0.12), (-0.62, 0.5), (-0.84, 0.95), (-0.66, 1.46)],
             [(-0.18, -0.9), (0.12, -0.5), (0.34, -0.05), (0.56, 0.3), (0.9, 0.62), (0.94, 1.08)],
             [(-0.35, -0.62), (-0.05, -0.15), (0.02, 0.2), (-0.16, 0.5), (-0.28, 0.95), (-0.05, 1.5), (0.3, 1.72)],
             [(-0.4, -1.32), (-0.2, -1.66), (0.1, -1.86)], [(-0.72, -1.4), (-0.7, -1.62)],
             [(-0.95, -1.12), (-1.0, -1.32)], [(-0.95, -0.8), (-1.02, -0.52)]]
    for i, rp in enumerate(roots):
        n = len(rp)
        path = [B0 + (Vector((rp[0][0], rp[0][1], 0)) - B0) * 0.35 + Vector((0, 0, T + 0.34))]
        for j, (x, y) in enumerate(rp):
            u = j / max(n - 1, 1)
            path.append(Vector((x, y, T + 0.2 * (1 - u) ** 1.5 + (0.05 * math.sin(j * 2.1 + i) if 0 < j < n - 1 else 0.0) - 0.04 * u)))
        r0 = 0.3 if n > 4 else (0.23 if n > 2 else 0.17)
        bm_tube(k[BARK], path, [r0 * (1 - 0.72 * j / n) for j in range(n + 1)], n=6)
    for rp, r0 in (([(-0.6, 0.48), (-0.46, 0.84), (-0.56, 1.14)], 0.14), ([(0.54, 0.28), (0.5, -0.02), (0.62, -0.3)], 0.13),
                   ([(-0.2, -1.64), (-0.5, -1.84)], 0.1)):                        # forks
        bm_tube(k[BARK], [Vector((x, y, T + 0.07 - 0.03 * j)) for j, (x, y) in enumerate(rp)], [r0 * (1 - 0.3 * j) for j in range(len(rp))], n=5)
    for t, a, r in ((0.44, 0.0, 0.2), (0.53, 0.3, 0.2), (0.62, 0.2, 0.17), (0.36, -0.4, 0.17)):    # moss on its back, where the light falls
        c, tr = _trunk_at(t)
        bm_blob(k["grass:0.2:0.8"], rnd, c + Z + Vector((a * tr * 0.5, 0, tr * 0.86)), r, squash=(1.0, 1.25, 0.34), jitter=0.12)
    tree = k.emit("Tree", col, root)
    # ---- the hollow at its foot (it faces the camera): dark, lipped, full of comb with a glow behind it
    hc, hr = _trunk_at(0.11)
    hd = Vector((0.72, -0.69, 0)).normalized()
    hs = Vector((-hd.y, hd.x, 0))
    hp = hc + Z + hd * (hr * 0.97)
    bm_ellipsoid(k["black:0.3:0.7"], hp, (0.2, 0.14, 0.31), (0, 0, math.degrees(math.atan2(hd.y, hd.x)) - 90), u=8, v=6)
    lip = []
    for i in range(9):
        a = 2 * math.pi * i / 8
        lip.append(hp + hd * 0.07 + hs * (math.cos(a) * 0.24) + Vector((0, 0, math.sin(a) * 0.36)))
    bm_tube(k[BARK], lip, 0.07, n=5, cap=False)
    k.emit("Hollow", col, root)
    for dx, w, h in ((-0.09, 0.2, 0.3), (0.06, 0.24, 0.4)):
        _comb(k, hp + hd * 0.1 + hs * dx + Vector((0, 0, 0.16)), hs, w, h)
    bm_ellipsoid(k[AMBER], hp + hd * 0.04 + Vector((0, 0, -0.04)), (0.13, 0.05, 0.2), (0, 0, math.degrees(math.atan2(hd.y, hd.x)) - 90), u=6, v=4)
    # ---- comb hanging under the crook, honey running down the bark and off the comb
    for t, w, h in ((0.36, 0.3, 0.3), (0.42, 0.38, 0.4), (0.48, 0.32, 0.34)):   # (on the side away from the hive: it turns)
        c, r = _trunk_at(t)
        c2, _ = _trunk_at(t + 0.03)
        tan = (c2 - c)
        tan.z = 0
        tan.normalize()
        away = Vector((c.x - AX, c.y - AY, 0)).normalized()
        top = c + Z + away * (r * 0.25) - Vector((0, 0, r * 0.84))
        _comb(k, top, tan, w, h)
        bm_crystal(k[HONEY], top - Vector((0, 0, h * 0.9)), top - Vector((0, 0, h + 0.13)), 0.035, n=5, shoulder=0.3)
    run = []
    for j in range(7):
        t = 0.5 - 0.42 * j / 6
        c, r = _trunk_at(t)
        d = Vector((0.75, 0.55 - 0.9 * j / 6, 0)).normalized()
        run.append(c + Z + d * (r * 0.96) + Vector((0, 0, -0.06)))
    bm_tube(k[HONEY], run, [0.07, 0.085, 0.065, 0.08, 0.06, 0.075, 0.05], n=5, squash=1.6, up=(0, 0, 1))
    for j in (1, 3, 5):
        bm_crystal(k[HONEY], run[j] + Vector((0, 0, -0.02)), run[j] + Vector((0.02, 0, -0.22)), 0.045, n=5, shoulder=0.3)
    k.emit("Comb", col, root)
    # ---- leaves on the boughs, and the team's ribbons hanging from them and from the crook
    for (x, y, z, r, sw) in ((0.26, -1.5, 2.26, 0.4, "grass:0.1:0.75"), (-0.1, -1.4, 2.04, 0.27, "teal:0.25:0.8"), (0.6, -1.14, 2.24, 0.27, "teal:0.25:0.8"),
                             (0.14, -1.22, 2.44, 0.25, "grass:0.05:0.7"), (0.56, -1.44, 2.06, 0.22, "grass:0.2:0.8")):
        bm_blob(k[sw], rnd, (x, y, T + z), r, squash=(1.0, 1.0, 0.72), jitter=0.14, sub=2 if r > 0.3 else 1)
    k.emit("Leaves", col, root)
    for (x, y, z, ln, wd, rz) in ((-0.24, -1.25, 1.58, 0.6, 0.16, 25), (-0.9, -1.16, 1.54, 0.5, 0.15, -30), (0.62, -1.1, 1.92, 0.46, 0.14, 10)):
        p = Vector((x, y, T + z))
        ax = Vector((math.cos(math.radians(rz)), math.sin(math.radians(rz)), 0))
        nr = Vector((-ax.y, ax.x, 0))
        bm_beam(k["team!:0.1:0.75"], p + Vector((0, 0, 0.05)), p - Vector((0, 0, ln)), wd, 0.02, up=nr)
        for s in (-1, 1):                                                       # a forked end
            bm_beam(k["team!:0.3:0.8"], p + ax * (s * wd * 0.25) - Vector((0, 0, ln - 0.01)), p + ax * (s * wd * 0.36) - Vector((0, 0, ln + 0.16)),
                    wd * 0.48, 0.02, w1=0.02, up=nr)
        bm_beam(k["gold:0.1:0.5"], p - ax * (wd * 0.56) + Vector((0, 0, 0.03)), p + ax * (wd * 0.56) + Vector((0, 0, 0.03)), 0.06, 0.07)   # the knot
    c, r = _trunk_at(0.305)                                                     # ... and a band of it bound round the trunk
    c2, _ = _trunk_at(0.33)
    tan = (c2 - c).normalized()
    u = Vector((0, 0, 1)).cross(tan).normalized()
    w = tan.cross(u)
    for sw, half, grow in (("team!:0.1:0.7", 0.11, 0.035), ("gold:0.1:0.5", 0.14, 0.02)):
        bm_loft(k[sw], [[c + Z + tan * dz + (u * math.cos(a) + w * math.sin(a)) * (r * 1.06 + grow) for a in [2 * math.pi * i / 10 for i in range(10)]]
                        for dz in (-half, half)])
    k.emit("Ribbons", col, root)
    # ---- the ground under it: a bed of moss from cell to cell, drifts of meadow flowers the wasps work
    keep = lambda x, y: in_footprint(CELLS, x, y, 0.17)
    for cx, cy, r, sq in ((-0.2, -1.05, 0.95, 0.95), (0.0, -0.05, 0.56, 1.25), (0.15, 1.0, 0.98, 0.92)):
        bm_patch(k["grass:0.3:0.8"], rnd, (cx, cy), r, T - 0.01, T + 0.035, n=12, squash=sq, keep=keep)
    k.emit("Moss", col, root)
    for cx, cy, n, sw in ((-0.7, 1.5, 5, "white:0.0:0.3"), (0.72, 0.2, 4, "salmon:0.1:0.5"), (0.75, -1.72, 4, "white:0.0:0.3"),
                          (-0.75, -1.72, 3, "salmon:0.1:0.5"), (0.2, 1.84, 3, "salmon:0.1:0.5")):
        for i in range(n):
            a, d = rnd.uniform(0, 6.283), rnd.uniform(0.05, 0.24)
            x, y, h = cx + math.cos(a) * d, cy + math.sin(a) * d, rnd.uniform(0.1, 0.2)
            if not in_footprint(CELLS, x, y, 0.14):
                continue
            bm_box(k["grass:0.5:0.95"], (0.022, 0.022, h), (x, y, T + h / 2))
            bm_cyl(k[sw], 0.07, 0.035, 0.03, (x, y, T + h + 0.005), rot=(rnd.uniform(-14, 14), rnd.uniform(-14, 14), rnd.uniform(0, 60)), seg=5)
            bm_cyl(k["gold:0.05:0.4"], 0.028, 0.02, 0.03, (x, y, T + h + 0.03), seg=5)
    k.emit("Flowers", col, root)
    # ---- the beekeeper's crock under the drip, honey to its brim and down its side, a pool on the roots
    C = Vector((AX, AY, 0))
    bm_tube(k["roof:0.15:0.85"], [(C.x, C.y, T - 0.02), (C.x, C.y, T + 0.1), (C.x, C.y, T + 0.3), (C.x, C.y, T + 0.44), (C.x, C.y, T + 0.5)],
            [0.2, 0.3, 0.33, 0.25, 0.28], n=10)
    ring(k["roof:0.05:0.5"], (C.x, C.y, 0), 0.3, 0.2, T + 0.47, T + 0.53, seg=10)
    k.emit("Crock", col, root)
    bm_cyl(k[HONEY], 0.215, 0.215, 0.03, (C.x, C.y, T + 0.5), seg=10)
    bm_tube(k[HONEY], [(C.x + 0.2, C.y + 0.12, T + 0.52), (C.x + 0.3, C.y + 0.18, T + 0.42), (C.x + 0.37, C.y + 0.21, T + 0.2), (C.x + 0.36, C.y + 0.22, T + 0.03)],
            [0.045, 0.05, 0.04, 0.06], n=5)
    bm_patch(k[HONEY], rnd, (C.x + 0.44, C.y + 0.34), 0.36, T + 0.02, T + 0.05, n=10, jitter=0.2, keep=lambda x, y: in_footprint(CELLS, x, y, 0.2))
    bm_patch(k[HONEY], rnd, (-0.22, -1.42), 0.2, T + 0.02, T + 0.05, n=8, jitter=0.2)            # ... and one under the hollow
    k.emit("Honey", col, root)
    # ---- tucked in the roots behind: a straw skep on its board, honey pots on a rug in the team's color
    R = Vector((0.38, -1.2, 0))
    rz = math.radians(-24)
    ax, ay = Vector((math.cos(rz), math.sin(rz), 0)), Vector((-math.sin(rz), math.cos(rz), 0))
    bm_beam(k["team!:0.15:0.6"], R - ax * 0.46 + Vector((0, 0, T + 0.012)), R + ax * 0.46 + Vector((0, 0, T + 0.012)), 0.6, 0.024)
    for s in (-1, 1):
        bm_beam(k["gold:0.1:0.55"], R + ax * (s * 0.44) - ay * 0.3 + Vector((0, 0, T + 0.016)), R + ax * (s * 0.44) + ay * 0.3 + Vector((0, 0, T + 0.016)), 0.07, 0.028)
        for i in range(5):                                                      # the fringe
            p = R + ax * (s * 0.49) + ay * ((i - 2) * 0.125) + Vector((0, 0, T + 0.012))
            bm_beam(k["cream:0.1:0.6"], p, p + ax * (s * 0.09), 0.04, 0.016)
    k.emit("Rug", col, root)
    S0 = R + ax * 0.16 + ay * 0.02
    bm_cyl(k["wood:0.3:0.8"], 0.3, 0.3, 0.05, (S0.x, S0.y, T + 0.05), seg=8)
    for i, (z, r, h) in enumerate(((0.07, 0.25, 0.1), (0.16, 0.255, 0.1), (0.25, 0.23, 0.1), (0.34, 0.19, 0.09), (0.42, 0.13, 0.08), (0.49, 0.06, 0.06))):
        bm_cyl(k["gold:0.2:0.85"], r, r * 0.9, h, (S0.x, S0.y, T + z + h / 2), seg=10)
    k.emit("Skep", col, root, vary=0.09)
    bm_ellipsoid(k["black:0.3:0.6"], (S0.x - ay.x * 0.24, S0.y - ay.y * 0.24, T + 0.13), (0.07, 0.05, 0.06), (0, 0, math.degrees(rz)), u=6, v=4)
    bm_crystal(k["gold:0.4:0.9"], (S0.x, S0.y, T + 0.52), (S0.x, S0.y, T + 0.62), 0.03, n=4)
    k.emit("Skep_Door", col, root)
    for dx, dy, r in ((-0.3, -0.12, 0.13), (-0.14, 0.2, 0.1), (-0.34, 0.14, 0.085)):
        p = R + ax * dx + ay * dy
        bm_tube(k["roof:0.15:0.85"], [(p.x, p.y, T + 0.02), (p.x, p.y, T + r * 0.6), (p.x, p.y, T + r * 1.5), (p.x, p.y, T + r * 1.95)],
                [r * 0.7, r, r * 0.92, r * 0.6], n=8)
        bm_ellipsoid(k["team!:0.1:0.6"], (p.x, p.y, T + r * 1.98), (r * 0.74, r * 0.74, r * 0.3), u=8, v=4)                # a cloth lid
        ring(k["sand:0.3:0.7"], (p.x, p.y, 0), r * 0.7, r * 0.5, T + r * 1.82, T + r * 1.9, seg=8)
    k.emit("Pots", col, root)
    kk = [("forest/Grass_2_A_Color1", (0.9, 0.5, 0), 0.45), ("forest/Grass_1_B_Color1", (-0.92, 0.7, 0), 0.45),
          ("forest/Bush_1_C_Color1", (0.5, 1.7, 0), 0.26), ("forest/Grass_1_A_Color1", (-0.4, 1.78, 0), 0.5),
          ("forest/Bush_2_B_Color1", (0.9, -0.66, 0), 0.22), ("props/Mushroom", (0.2, -1.8, 0), 0.5)]
    for i, (rel, loc, sc) in enumerate(kk):
        if not in_footprint(CELLS, loc[0], loc[1], 0.12):
            continue
        kk_import(rel, col, root, (loc[0], loc[1], T - 0.02), rnd.uniform(0, 360), sc, name="Prop_KK_%d" % i)
    empty("Head", col, root, (AX, AY, T), 0.5, "SINGLE_ARROW")
    return root


def _band(bm, rnd, z0, r0, z1, r1, n=12, scallop=0.02):
    """One layer of the hive's paper: a closed cone from (z0, r0) down to a scalloped hem at (z1, r1)."""
    top = [Vector((math.cos(2 * math.pi * i / n) * r0, math.sin(2 * math.pi * i / n) * r0, z0)) for i in range(n)]
    hem = []
    for i in range(n):
        a = 2 * math.pi * (i + 0.5) / n
        rr = r1 + (scallop if i % 2 else -scallop * 0.4) + rnd.uniform(-0.008, 0.008)
        hem.append(Vector((math.cos(a) * rr, math.sin(a) * rr, z1 + (-scallop if i % 2 else scallop * 0.8))))
    return bm_loft(bm, [top, hem])


def _wasp(kb, kw, p, f):
    """A wasp at p flying along f (flat): black head and thorax, a striped abdomen with a sting, two pairs of wings
    (in their own kit: they flutter), trailing legs."""
    p, f = Vector(p), Vector(f).normalized()
    z = Vector((0, 0, 1))
    s = f.cross(z)
    S = WS
    bm_tube(kb["black:0.2:0.7"], [p + f * 0.13 * S, p + f * 0.19 * S, p + f * 0.24 * S], [0.045 * S, 0.06 * S, 0.035 * S], n=6)       # head
    bm_tube(kb["black:0.3:0.8"], [p - f * 0.03 * S, p + f * 0.05 * S, p + f * 0.14 * S], [0.045 * S, 0.08 * S, 0.05 * S], n=6)       # thorax
    for sx in (-1, 1):
        e = p + f * 0.2 * S + s * (sx * 0.045 * S) + z * 0.02 * S
        bm_ellipsoid(kb["gold:0.05:0.4"], e, (0.022 * S, 0.03 * S, 0.03 * S), u=5, v=3)                                       # eyes
        bm_beam(kb["black:0.3:0.8"], p + f * 0.22 * S + s * (sx * 0.02 * S) + z * 0.04 * S, p + f * 0.33 * S + s * (sx * 0.07 * S) + z * 0.1 * S, 0.012, 0.012)
        bm_beam(kb["black:0.3:0.8"], p - f * 0.0 * S + s * (sx * 0.04 * S) - z * 0.04 * S, p - f * 0.14 * S + s * (sx * 0.08 * S) - z * 0.17 * S, 0.014, 0.014)
    ts = [0.0, 0.07, 0.15, 0.23, 0.31, 0.37, 0.44]
    rs = [0.035, 0.078, 0.092, 0.084, 0.06, 0.03, 0.0]
    q = [p - f * (0.03 + t) * S - z * (0.5 * t * t) * S for t in ts]
    for i, sw in enumerate(("black:0.3:0.8", "gold:0.05:0.5", "black:0.3:0.8", "gold:0.05:0.5")):
        bm_tube(kb[sw], [q[i], q[i + 1]], [rs[i] * S, rs[i + 1] * S], n=6)
    bm_tube(kb["black:0.3:0.8"], [q[4], q[5], q[6]], [rs[4] * S, rs[5] * S, 0.0], n=6)                                         # the sting
    for sx in (-1, 1):
        b = p + f * 0.06 * S + s * (sx * 0.03 * S) + z * 0.065 * S
        bm_beam(kw["white:0.0:0.3"], b, b - f * 0.26 * S + s * (sx * 0.27 * S) + z * 0.16 * S, 0.1 * S, 0.01, w1=0.06 * S, up=z)
        bm_beam(kw["sky:0.0:0.3"], b - f * 0.03 * S, b - f * 0.25 * S + s * (sx * 0.14 * S) + z * 0.06 * S, 0.07 * S, 0.01, w1=0.04 * S, up=z)


def build_head():
    col = collection("Hive")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    rnd = random.Random(3)
    k = Kit()
    # ---- the hive: a dark core, layers of paper lapping over each other down to the tip, a knob round the bough
    bm_tube(k["wood_dark:0.4:0.95"], [(0, 0, z) for z, r in PROF], [max(r - 0.05, 0.03) for z, r in PROF], n=12)
    k.emit("Head_Core", col, rig=rig, bone="hive")
    cols = ("gold:0.06:0.6", "tan:0.15:0.8", "gold:0.12:0.7", "cream:0.25:0.85")
    for i in range(len(PROF) - 1):
        (z0, r0), (z1, r1) = PROF[i], PROF[i + 1]
        _band(k[cols[i % len(cols)]], rnd, z0 + 0.05, max(r0 - 0.035, 0.05), z1, r1 + 0.03)
    bm_blob(k["tan:0.15:0.8"], rnd, (0, 0, 2.66), 0.34, squash=(1.0, 1.0, 0.72), jitter=0.08, sub=2)
    # the entrance: a paper spout, a rim, darkness inside
    y0 = 0.46
    bm_tube(k["tan:0.2:0.85"], [(0, y0, MOUTH.z + 0.04), (0, MOUTH.y - 0.06, MOUTH.z + 0.01), (0, MOUTH.y, MOUTH.z)], [0.26, 0.23, 0.235], n=10)
    ring(k["gold:0.05:0.5"], (0, 0, MOUTH.z), 0.265, 0.17, MOUTH.y - 0.03, MOUTH.y + 0.035, seg=10, axis="Y")
    bm_cyl(k["black:0.4:0.8"], 0.18, 0.18, 0.02, (0, MOUTH.y + 0.012, MOUTH.z), rot=(90, 0, 0), seg=10)
    k.emit("Head_Hive", col, rig=rig, bone="hive", vary=0.05)
    # the team's sash round its neck, tails hanging; honey gathering at the tip
    ring(k["team!:0.1:0.6"], (0, 0, 0), 0.5, 0.32, 2.28, 2.44, seg=12)
    ring(k["gold:0.1:0.5"], (0, 0, 0), 0.515, 0.32, 2.44, 2.475, seg=12)
    ring(k["gold:0.1:0.5"], (0, 0, 0), 0.515, 0.32, 2.245, 2.28, seg=12)
    for a, ln in ((205, 0.5), (232, 0.38)):
        d = Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0))
        bm_beam(k["team!:0.2:0.8"], d * 0.51 + Vector((0, 0, 2.34)), d * 0.74 + Vector((0, 0, 2.34 - ln)), 0.17, 0.02, w1=0.11, up=d)
    bm_boulder(k["gold:0.1:0.5"], rnd, (math.cos(math.radians(218)) * 0.52, math.sin(math.radians(218)) * 0.52, 2.3), 0.07, n=8, sink=0.0)
    k.emit("Head_Sash", col, rig=rig, bone="hive")
    bm_crystal(k[HONEY], (0, 0, 1.04), (0, 0, 0.86), 0.06, n=6, shoulder=0.3)
    bm_tube(k[HONEY], [(0.5, 0.23, 1.25), (0.36, 0.17, 1.12), (0.06, 0.03, 1.02)], [0.05, 0.05, 0.055], n=5)
    k.emit("Head_HoneyTip", col, rig=rig, bone="hive")
    bm_cyl(k[AMBER], 0.14, 0.14, 0.02, (0, MOUTH.y + 0.026, MOUTH.z), rot=(90, 0, 0), seg=10)
    k.emit("Head_Glow", col, rig=rig, bone="glow")
    for i in (1, 2):                                                           # drops of honey on their way to the crock
        bm_tube(k[HONEY], [(0, 0, 0.93), (0, 0, 0.885), (0, 0, 0.845), (0, 0, 0.8)], [0.0, 0.03, 0.042, 0.0], n=6)
        k.emit("Head_Drop%d" % i, col, rig=rig, bone="drop.%d" % i)
    # ---- the wasps, each on its orbit
    kw = Kit()
    for i, (r, z, a, n, b) in enumerate(WASPS):
        _wasp(k, kw, (r, 0, z), (0, 1 if n > 0 else -1, 0))
        k.emit("Head_Wasp%d" % i, col, rig=rig, bone="wasp.%d" % i)
        kw.emit("Head_Wings%d" % i, col, rig=rig, bone="wing.%d" % i)
    empty("Muzzle", col, head, tuple(MOUTH), 0.2, "SPHERE")
    return rig


IDLE_LEN = 60
FIRE_LEN = 5


def pose(rig, t=0.0, f=0, sway=0.0, throb=0.0, flare=0.0, dart=0.0):
    """t: where the idle loop is (0..1): the wasps' places on their orbits, the honey drops; f: the frame (the wings
    beat every other one); dart: the wasps' lunge when the hive shoots."""
    pb = rig.pose.bones
    rest_pose(rig)
    ph = 2 * math.pi * t
    turn(pb, "hive", x=sway * math.sin(ph), y=sway * 0.8 * math.cos(ph))
    pb["hive"].scale = (1 + throb, 1 - throb * 0.5, 1 + throb)                 # (it hangs: the bone's own Y is its height)
    g = 1.0 + 0.12 * math.sin(ph * 2) + flare
    pb["glow"].scale = (g, 1.0, g)
    for i, (r, z, a, n, b) in enumerate(WASPS):
        ang = a + 360.0 * n * t
        turn(pb, "orbit.%d" % i, z=ang)
        w = math.radians(ang) * 2 + i
        d = 1 if n > 0 else -1
        # bobbing and weaving on its way round; darting out along its path when the hive shoots
        shift(pb, "wasp.%d" % i, (0.06 * math.sin(w * 1.5 + 1.0) + dart * 0.1, d * dart * 0.16, b * math.sin(w) + dart * 0.04))
        turn(pb, "wasp.%d" % i, y=d * (10 * math.cos(w) + 14 * dart), x=-d * 9 * math.cos(w))
        up = (f + i) % 2 == 0
        pb["wing.%d" % i].scale = (1.0, 1.0 if up else 0.12, 1.0)
        turn(pb, "wing.%d" % i, y=0.0 if up else 4.0)
    for j, off in ((1, 0.0), (2, 0.5)):
        u = (t + off) % 1.0
        # it swells at the tip, falls into the crock, is gone there, and (too small to see) goes back up
        fall = min(max((u - 0.34) / 0.16, 0.0), 1.0)
        s = max(0.02, smooth(u / 0.3) * (1.0 - smooth((u - 0.5) / 0.06)))
        pb["drop.%d" % j].scale = (s, s * (1.0 + 0.6 * math.sin(math.pi * fall)), s)
        shift(pb, "drop.%d" % j, (0, 0, -0.42 * fall ** 2 * (1.0 - smooth((u - 0.6) / 0.3))))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(IDLE_LEN + 1):
        pose(rig, t=f / IDLE_LEN, f=f if f < IDLE_LEN else 0, sway=1.6)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        kk = math.sin(math.pi * f / FIRE_LEN) if 0 < f < FIRE_LEN else 0.0
        pose(rig, t=0.0, f=f if f < FIRE_LEN else 0, sway=1.6, throb=0.05 * kk, flare=0.55 * kk, dart=kk)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.1, 1.75), "dist": 9.2, "yaw": 150, "pitch": 16, "anim_target": (AX, AY, 2.2), "anim_dist": 6.2,
           "frames": [("idle", 0), ("idle", 14), ("idle", 31), ("fire", 2), ("fire", 3)],
           "extra": [{"yaw": 165, "pitch": 8, "dist": 3.6, "target": (AX, AY + 0.2, 1.9)},
                     {"yaw": 20, "pitch": 30, "dist": 4.6, "target": (0.0, -0.9, 0.9)},
                     {"yaw": 0, "pitch": 57, "dist": 6.4, "target": (0, 0, 1.4)},
                     {"yaw": 100, "pitch": 12, "dist": 6.6, "target": (0, 0, 1.7)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
