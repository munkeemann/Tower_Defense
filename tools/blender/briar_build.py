"""Builds the Briar Thicket (footprint "line4": [0,0] front .. [0,3] back), a Verdant tower: an aura that scratches and
slows whatever walks past (GameData.STRIKES "erupt": each pulse shows as build_strike()'s thorn vines round the enemy).

    python tools/blender/build.py briar --out <preview dir>

One living wall snakes through all four hexes: a low drystone wall with a hedge riding it, and over both a weave of
thick thorny canes that root on one side, arch over and root again on the other, bound by long runners spiked with big
thorns. In each hex the wall bulges to one side and the briar throws a tongue of canes out to the other. Where the wall
crosses the middle on the slant stands the gate: two rune-carved standing stones, and from beside each a twisted trunk
of three canes climbing over to cross the other's at the top, where the Great Rose opens (the Muzzle, a glowing heart).
The roses are the team's color. Eight tall whip canes stand up out of the hedge: the rig (under the root: nothing turns).
Clips: idle (the whips sway, the Great Rose breathes and nods), fire (the whips lash out to both sides and the Great
Rose bursts open).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler
exec(open(os.path.join(REPO, "tools", "blender", "greatwood_common.py"), encoding="utf-8").read())

TID = "briar"
CELLS = [(0, 0), (0, 1), (0, 2), (0, 3)]
MID = footprint_mid(CELLS)
CS = [hex_to_world(0, i, MID) for i in range(4)]
TOP = 0.34
T = TOP + 0.05                  # the turf's top (plinth(turf=True))
GLOW = "glow:%s,%s,%s,0.9" % SPIRIT
THORN = "cream:0.1:0.55"
CANES = ("wood_dark:0.2:0.8", "taupe_dark:0.25:0.85")
CANE_RED = "wood_red:0.5:1.0"
HEDGE = ("teal:0.35:0.92", "grass:0.4:0.95")
PETAL = "team!:0.1:0.7"
HIPS = "orange:0.2:0.8"


class Line:
    """The wall's line as a smooth curve with a ruler along it."""

    def __init__(self, ctrl, sub=8):
        self.sub = sub
        self.pts = spline_pts([(x, y, 0.0) for x, y in ctrl], sub)
        self.acc = [0.0]
        for a, b in zip(self.pts, self.pts[1:]):
            self.acc.append(self.acc[-1] + (b - a).length)
        self.length = self.acc[-1]

    def at(self, s):
        """-> (the point s along the line, the line's direction there, its left side)."""
        s = min(max(s, 0.0), self.length)
        i = 0
        while i < len(self.pts) - 2 and self.acc[i + 1] < s:
            i += 1
        a, b = self.pts[i], self.pts[i + 1]
        d = (b - a).normalized()
        return a.lerp(b, (s - self.acc[i]) / max(self.acc[i + 1] - self.acc[i], 1e-9)), d, Vector((-d.y, d.x, 0.0))

    def s_ctrl(self, i):
        return self.acc[i * self.sub]

    def s_at_y(self, y):
        return self.acc[min(range(len(self.pts)), key=lambda j: abs(self.pts[j].y - y))]


# the wall's line from the back end to the front end: it bulges to one side in each hex, is back in the middle where two
# hexes meet (the footprint's narrow necks), and crosses the very middle on the slant, between the gate's two stones
LINE = [(0.2, -3.72), (0.42, -3.12), (0.3, -2.5), (0.0, -2.08), (-0.3, -1.6), (-0.45, -1.04), (-0.38, -0.5),
        (0.38, 0.5), (0.45, 1.04), (0.3, 1.6), (0.0, 2.08), (-0.3, 2.5), (-0.42, 3.12), (-0.2, 3.72)]
LN = Line(LINE)
S_A, S_B = LN.s_ctrl(6), LN.s_ctrl(7)
GA, GB = LN.pts[6 * 8].copy(), LN.pts[7 * 8].copy()
GE = (GB - GA).normalized()                 # along the gate
GN = Vector((GE.y, -GE.x, 0.0))             # through it (toward +x and the back: the side the game's camera sees)
RUNS = ((0.0, S_A - 0.26), (S_B + 0.26, LN.length))
ROSE_C = Vector((0.0, 0.0, T + 2.2)) + GN * 0.04
ROSE_UP = (Vector((0.0, -0.32, 1.0)) + GN * 0.12).normalized()
# the whips: (y along the footprint, side: 1 = the line's left)
LASH = [(-3.46, 1.0), (-2.72, -1.0), (-1.72, 1.0), (-1.02, -1.0), (1.02, 1.0), (1.72, -1.0), (2.72, 1.0), (3.46, -1.0)]


def on_ground(p, c):
    """p, pulled toward c until it stands on the footprint."""
    p, c = Vector((p.x, p.y, 0.0)), Vector((c.x, c.y, 0.0))
    for _ in range(12):
        if in_footprint(CELLS, p.x, p.y, 0.2):
            break
        p = p.lerp(c, 0.12)
    return p


def gate_pt(t, z, off=0.0):
    """A point of the gate: t along it from the middle, z above the turf, off through it."""
    return Vector((GE.x * t + GN.x * off, GE.y * t + GN.y * off, T + z))


def lash_shapes():
    """The eight whips' curves: [(points, the wall's direction there, the whip's outward side)]."""
    rnd = random.Random(14)
    out = []
    for y, side in LASH:
        p, d, nr = LN.at(LN.s_at_y(y))
        o = nr * side
        reach = 1.0 if o.x * p.x < 0.0 else 0.72          # (shorter where the hedge already bulges to the hex's edge)
        hk = rnd.uniform(0.9, 1.08)
        ctrl = [p + o * (lat * reach) + d * al + Vector((0, 0, T + 0.72 + (z - 0.72) * hk)) for lat, z, al in
                ((0.04, 0.72, 0.0), (0.1, 1.2, 0.05), (0.26, 1.62, 0.1), (0.55, 1.86, 0.08), (0.82, 1.74, 0.02), (0.97, 1.5, -0.03))]
        out.append((spline_pts(ctrl, 3), d, o))
    return out


def build_base():
    col = collection("Briar")
    root = empty("Briar", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP, turf=True)
    rnd = random.Random(27)
    k = Kit()
    # ---- the drystone wall, a big stone where it ends
    for s0, s1 in RUNS:
        bm_drystone(k["stone2:0.1:0.9"], rnd, [LN.at(s0 + (s1 - s0) * i / 16.0)[0] for i in range(17)], T - 0.02, h=0.56, th=0.52,
                    stone=0.36, courses=3)
    for s in (0.0, LN.length):
        p = LN.at(s)[0]
        bm_boulder(k["stone2:0.15:0.92"], rnd, (p.x, p.y, T - 0.03), 0.27, squash=(1.0, 1.0, 0.95), n=11)
    k.emit("Wall", col, root, vary=0.09, seed=3)
    # ---- the hedge riding the wall: a dark mass of leaves, lighter sprigs pushing out of it
    hb = 0
    for ri, (s0, s1) in enumerate(RUNS):
        s, end = s0 + (0.62, 0.5)[ri], s1 - (0.5, 0.62)[ri]
        while s < end:
            p, d, nr = LN.at(s)
            q = p + nr * rnd.uniform(-0.06, 0.06)
            tap = 0.78 + 0.22 * smooth(min(s - s0, s1 - s) / 1.0)           # (lower and slimmer toward the wall's ends)
            bm_blob(k[HEDGE[hb % 2]], rnd, (q.x, q.y, T + 0.5 + 0.28 * tap + rnd.uniform(-0.04, 0.05)), rnd.uniform(0.42, 0.47) * tap,
                    squash=(0.88, 1.2, 0.8), jitter=0.2, sub=2)
            if hb % 3 == 0:                             # ... spilling down the wall's side here and there
                sd = 1.0 if hb % 2 else -1.0
                f = on_ground(p + nr * (sd * 0.4) + d * 0.2, p)
                bm_blob(k[HEDGE[(hb + 1) % 2]], rnd, (f.x, f.y, T + 0.4), 0.27, squash=(1.0, 1.2, 1.0), jitter=0.22)
            s += rnd.uniform(0.44, 0.56)
            hb += 1
        for i in range(26):
            p, d, nr = LN.at(rnd.uniform(s0 + 0.3, s1 - 0.3))
            th = math.radians(rnd.uniform(15, 80))
            o = nr * (rnd.choice((-1.0, 1.0)) * math.cos(th)) + Vector((0, 0, math.sin(th)))
            q = p + Vector((o.x * 0.42, o.y * 0.42, T + 0.78 + o.z * 0.34))
            bm_sprig(k[LEAF_C if i % 3 else LEAF_A], rnd, q, o + d * rnd.uniform(-0.5, 0.5), n=3, size=0.25)
    # ---- the weave: thick thorny canes that root on one side of the wall, arch over it and root again on the other
    for ri, (s0, s1) in enumerate(RUNS):
        cnt = int(round((s1 - s0) / 0.34))
        for j in range(cnt):
            L = rnd.uniform(1.0, 1.35)
            a = s0 - 0.15 + (s1 - s0 + 0.3 - L) * j / (cnt - 1.0)
            side = 1.0 if (j + ri) % 2 else -1.0
            pts = []
            for f, lat, z in ((0.0, 0.46, -0.07), (0.13, 0.58, 0.52), (0.5, rnd.uniform(-0.1, 0.1), rnd.uniform(1.08, 1.3)), (0.87, -0.58, 0.52),
                              (1.0, -0.46, -0.07)):
                p, d, nr = LN.at(min(max(a + L * f, s0 + 0.03), s1 - 0.03))
                q = p + nr * (side * lat)
                if z < 0.0:
                    q = on_ground(q, p)
                pts.append(Vector((q.x, q.y, T + z)))
            bm_cane(k[CANES[j % 2]], k[THORN], rnd, pts, [0.095, 0.09, 0.078, 0.07, 0.055], n=5, sub=2, every=0.26, tl=0.17, tr=0.045)
        # two runners along the ridge, spiked with the biggest thorns
        m = max(3, int(round((s1 - s0) / 0.5)))
        for rn in range(2):
            ph = rnd.uniform(0, 6.283)
            pts = []
            for i in range(m + 1):
                p, d, nr = LN.at(s0 + (s1 - s0) * i / m)
                if i in (0, m):                         # (rooted beside the wall at both ends)
                    q, z = on_ground(p + nr * (0.36 if rn else -0.36), p), -0.06
                else:
                    q, z = p + nr * (0.24 * math.sin(i * 2.1 + ph + rn * 3.1)), 1.16 + 0.1 * math.cos(i * 1.7 + ph)
                pts.append(Vector((q.x, q.y, T + z)))
            bm_cane(k[CANE_RED], k[THORN], rnd, pts, 0.07, n=5, sub=2, every=0.28, tl=0.26, tr=0.06, hook=0.1)
    k.emit("Hedge", col, root, vary=0.07, seed=5)
    # ---- roses along the ridge, hips hanging at the flanks
    nth = 0
    for s0, s1 in RUNS:
        for f in (0.13, 0.38, 0.63, 0.88):
            p, d, nr = LN.at(s0 + (s1 - s0) * f + rnd.uniform(-0.08, 0.08))
            side = 1.0 if nth % 2 else -1.0
            up = (nr * (side * 0.5) + Vector((0, -0.22, 1.0))).normalized()
            bm_rose(k, rnd, p + nr * (side * 0.26) + Vector((0, 0, T + 1.24)), rnd.uniform(0.22, 0.28), up, petal=PETAL, heart="gold:0.1:0.6", leaf=LEAF_C)
            nth += 1
        for f in (0.26, 0.52, 0.78):
            p, d, nr = LN.at(s0 + (s1 - s0) * f)
            c = p + nr * ((1.0 if nth % 2 else -1.0) * 0.52) + Vector((0, 0, T + 0.7))
            nth += 1
            for b in range(3):
                bm_blob(k[HIPS], rnd, c + Vector((rnd.uniform(-0.07, 0.07), rnd.uniform(-0.07, 0.07), -0.085 * b)), 0.075, jitter=0.06)
    # ---- each hex's open side: a tongue of canes thrown out toward the hex's corner over a mound of leaves, a rose on it
    for i, c in enumerate(CS):
        p = LN.at(LN.s_at_y(c.y))[0]
        sb = -1.0 if p.x > 0 else 1.0
        for dy0, dy1, dy3, hh in ((-0.3, -0.36, -0.44, 0.9), (0.0, 0.04, 0.0, 1.02), (0.3, 0.38, 0.44, 0.86)):
            foot = on_ground(Vector((sb * 1.02, c.y + dy3, 0)), c)
            pts = [Vector((p.x + sb * 0.3, c.y + dy0, T + 0.8)), Vector((p.x + sb * 0.78, c.y + dy1, T + hh)),
                   Vector((foot.x - sb * 0.2, c.y + (dy1 + dy3) * 0.5, T + 0.5)), Vector((foot.x, foot.y, T - 0.06))]
            bm_cane(k[CANES[i % 2]], k[THORN], rnd, pts, [0.085, 0.078, 0.062, 0.045], n=5, sub=2, every=0.24, tl=0.17, tr=0.045)
            bm_sprig(k[LEAF_C], rnd, pts[1] + Vector((0, 0, 0.06)), Vector((sb * 0.4, dy1, 1.0)), n=3, size=0.24)
        # a carpet of creeping leaves under it, out to the hex's corner
        for dx, dy, r in ((0.3, 0.0, 0.46), (0.68, -0.28, 0.36), (0.7, 0.3, 0.36), (0.93, 0.0, 0.26), (0.36, -0.62, 0.28), (0.36, 0.62, 0.28)):
            f = on_ground(Vector((sb * dx, c.y + dy, 0)), c)
            bm_blob(k[HEDGE[(i + int(dx * 10)) % 2]], rnd, (f.x, f.y, T + 0.03), r, squash=(1.1, 1.1, 0.3), jitter=0.22)
        bm_rose(k, rnd, Vector((sb * 0.5, c.y + 0.03, T + 1.02)), 0.25, (sb * 0.45, -0.25, 1.0), petal=PETAL, heart="gold:0.1:0.6", leaf=LEAF_C)
        for b in range(3):
            bm_blob(k[HIPS], rnd, Vector((sb * 0.84 + rnd.uniform(-0.06, 0.06), c.y + 0.3 + rnd.uniform(-0.06, 0.06), T + 0.5 - 0.085 * b)), 0.075, jitter=0.06)
        for dy in (-0.66, 0.66):
            bm_fern(k["grass:0.1:0.75"], rnd, (sb * 0.52, c.y + dy, T), n=5, length=0.3, rise=0.2, w=0.1)
    k.emit("Blooms", col, root, vary=0.05, seed=7)
    # ---- the gate: two rune stones, and from beside each a twisted trunk of three canes that climbs over and crosses the other's
    yaw = math.degrees(math.atan2(-GN.x, GN.y))
    for sg, g, rune, lean in ((-1, GA, "fork", (2.0, 4.0)), (1, GB, "coil", (-2.0, -6.0))):
        face = bm_menhir(k, rnd, (g.x, g.y, T), 1.02, w=0.46, d=0.3, yaw=yaw, lean=lean)
        bm_rune(k[GLOW], rune, face, 0.4, size=0.36, w=0.045)
        ctrl = [(-0.98, -0.06, 0.34), (-1.0, 0.5, 0.3), (-0.92, 1.02, 0.14), (-0.66, 1.5, 0.08), (-0.3, 1.88, 0.07), (0.1, 2.12, 0.07), (0.36, 2.4, 0.1)]
        mid = spline_pts([gate_pt(-sg * t, z, -sg * off) for t, z, off in ctrl], 2)
        m = len(mid)
        for c in range(3):
            pts, rad = [], []
            for i, q in enumerate(mid):
                u = i / (m - 1.0)
                tan = (mid[min(i + 1, m - 1)] - mid[max(i - 1, 0)]).normalized()
                n1 = (GN - tan * GN.dot(tan)).normalized()
                n2 = tan.cross(n1)
                ang = 2 * math.pi * c / 3.0 + u * 2 * math.pi * 1.25 * sg
                hr = 0.105 * (1.0 - 0.25 * u) + 0.13 * smooth((u - 0.78) / 0.22)          # (the three splay at the top)
                pts.append(q + (n1 * math.cos(ang) + n2 * math.sin(ang)) * hr)
                rad.append(0.095 * (1.0 - 0.3 * u) * (1.0 - smooth((u - 0.8) / 0.2)))
            rad[-1] = 0.0
            bm_cane(k[CANE_RED], k[THORN], rnd, pts, rad, n=5, sub=1, every=0.24, tl=0.2, tr=0.05, skip_ends=0.06)
        for tt, z, off in ((0.95, 1.3, 0.24), (0.52, 1.82, -0.1)):
            bm_sprig(k[LEAF_C], rnd, gate_pt(sg * tt, z, -sg * off), GE * (sg * 0.6) + GN * (-sg * off * 3.0) + Vector((0, 0, 0.7)), n=3, size=0.22)
    k.emit("Gate", col, root, vary=0.06, seed=9)
    # ---- the ground: the path through the gate, stones fallen from the wall, petals
    def on_path(x, y):
        return abs(x * GE.x + y * GE.y) < 0.36 and abs(x * GN.x + y * GN.y) < 1.1 and in_footprint(CELLS, x, y, 0.2)
    bm_flagstones(k["stone:0.1:0.8"], rnd, on_path, (-1.1, -1.1, 1.1, 1.1), T - 0.005, size=0.27, gap=0.03, h=0.04)
    for (x, y, sz) in ((0.72, -3.5, 0.2), (-0.3, -3.2, 0.16), (-0.62, -0.62, 0.17), (0.62, 0.62, 0.17), (0.3, 3.2, 0.16), (-0.72, 3.5, 0.2),
                       (0.1, -1.75, 0.15), (-0.1, 1.75, 0.15)):
        if in_footprint(CELLS, x, y, 0.22):
            bm_stone(k["stone2:0.15:0.92"], rnd, (x, y, T - 0.02), (sz * 1.5, sz * 1.1, sz), yaw=rnd.uniform(0, 180), n=9, jit=0.18)
    for i in range(22):
        c = CS[i % 4]
        x, y = rnd.uniform(-0.95, 0.95), c.y + rnd.uniform(-0.9, 0.9)
        if in_footprint(CELLS, x, y, 0.24):
            d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0)).normalized()
            bm_leaf(k[PETAL], (x, y, T + 0.012), (x + d.x * 0.13, y + d.y * 0.13, T + 0.02), 0.09)
    k.emit("Ground", col, root, vary=0.08, seed=11)
    empty("Head", col, root, (0, 0, T), 0.5, "SINGLE_ARROW")
    return root


def build_head():
    col = collection("Briar")
    root = bpy.data.objects["Briar"]
    head = bpy.data.objects["Head"]
    shapes = lash_shapes()
    bones = {"root": ((0, 0, 0), (0, 0, 0.2), None), "rose": (tuple(ROSE_C), tuple(ROSE_C + ROSE_UP * 0.3), "root")}
    names = []
    for i, (pts, d, o) in enumerate(shapes):
        prev = "root"
        for j in range(3):
            bones["lash.%d.%d" % (i, j + 1)] = (tuple(pts[j * 5]), tuple(pts[j * 5 + 5]), prev)
            prev = "lash.%d.%d" % (i, j + 1)
            names.append(prev)
    rig = make_rig(col, root, bones)
    rnd = random.Random(3)
    k = Kit()
    for i, (pts, d, o) in enumerate(shapes):
        bm_cane(k[CANE_RED], k[THORN], rnd, pts, resample([0.105, 0.095, 0.08, 0.062, 0.042, 0.0], len(pts)), n=5, sub=1, every=0.2, tl=0.22,
                tr=0.05, skip_ends=0.1, hook=0.3)
        bm_sprig(k[LEAF_C], rnd, pts[3] + o * 0.08, o + Vector((0, 0, 0.6)), n=3, size=0.2)
        bm_sprig(k[LEAF_A], rnd, pts[7] - o * 0.06, Vector((0, 0, 1)) - o * 0.4, n=2, size=0.17)
    k.emit("Lash", col, rig=rig, bones=names, vary=0.06)
    bm_rose(k, rnd, ROSE_C, 0.42, ROSE_UP, petal=PETAL, heart="glow:%s,%s,%s,0.7" % SPIRIT, leaf=LEAF_C)
    k.emit("Rose", col, rig=rig, bone="rose")
    empty("Muzzle", col, head, (ROSE_C.x, ROSE_C.y, ROSE_C.z - T + 0.18), 0.2, "SPHERE")
    return rig


IDLE_LEN = 96
FIRE_LEN = 18


def pose(rig, ph=0.0, lash=None, bloom=1.0, nod=0.0):
    """ph: the sway's phase; lash: how far each whip is thrown out (0..1, below 0: drawn back); bloom: the Great Rose's size."""
    pb = rig.pose.bones
    rest_pose(rig)
    for i, (pts, d, o) in enumerate(lash_shapes()):
        a = lash[i] if lash else 0.0
        axis = (-o.y, o.x, 0.0)                     # a turn about this tips the whip out to its side (+)
        for j, (sw, out) in enumerate(((5.0, 52.0), (8.0, -8.0), (11.0, -34.0))):
            b = pb["lash.%d.%d" % (i, j + 1)]
            w = sw * math.sin(2 * ph + i * 1.7 - j * 0.7) + sw * 0.4 * math.sin(3 * ph + i * 2.9)
            b.rotation_quaternion = arm_space_quat(b, axis, w + out * a) @ arm_space_quat(b, tuple(o), sw * 0.6 * math.sin(ph + i * 2.3 - j * 0.5))
    r = pb["rose"]
    r.scale = (bloom, 1.0 + (bloom - 1.0) * 0.35, bloom)            # (the bone's own Y is the rose's axis)
    r.rotation_quaternion = arm_space_quat(r, tuple(GN), nod)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        ph = 2 * math.pi * f / IDLE_LEN
        pose(rig, ph=ph, bloom=1.0 + 0.05 * math.sin(2 * ph), nod=5.0 * math.sin(ph))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        # the whips draw back for a frame, crack out to their sides (thrown flat by frame 4) and swing back up
        lash = []
        for i in range(len(LASH)):
            g = f - (i % 3) * 0.6
            lash.append(smooth((g - 1.0) / 3.0) * (1.0 - smooth((g - 6.0) / 9.0)) - 0.3 * smooth(g / 1.0) * (1.0 - smooth((g - 1.0) / 2.0))
                        - 0.1 * math.sin(math.pi * min(max((g - 11.0) / 5.0, 0.0), 1.0)))
        pose(rig, lash=lash, bloom=1.0 + 0.4 * smooth(f / 3.0) * (1.0 - smooth((f - 5) / 10.0)))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 0.9), "dist": 14.0, "yaw": 150, "pitch": 22, "anim_target": (0, 0, 1.1), "anim_dist": 9.5,
           "frames": [("idle", 0), ("idle", 24), ("fire", 1), ("fire", 4), ("fire", 9)],
           "extra": [{"yaw": 40, "pitch": 16, "dist": 5.2, "target": (0, 0, 1.4)},
                     {"yaw": 0, "pitch": 50, "dist": 6.5, "target": (0, -2.3, 0.7)},
                     {"yaw": 150, "pitch": 30, "dist": 6.0, "target": (0, 2.4, 0.8)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
    tri_report(collection("Briar"))


# ================================================================================================ the strike
# What the game plays under every enemy the thicket scratches (Strike, GameData.STRIKES "erupt"; the damage is instant):
# thorn vines whip up out of the ground round the enemy and lash over it (down on it by frame 2), claw marks flash
# across it, leaves and thorns fly; the vines writhe, lash once more, and sink back. +Y points away from the tower.
STRIKE_LEN = 21
STRIKE_VINES = 5
STRIKE_BITS = 6


def build_strike():
    col = collection("Briar_strike")
    root = empty("Briar_strike", col, None, (0, 0, 0), 0.5, "ARROWS")
    rnd = random.Random(11)
    bones = {"root": ((0, 0, 0), (0, 0, 0.2), None), "dirt": ((0, 0, 0), (0, 0, 0.3), "root")}
    shapes = []
    for i in range(STRIKE_VINES):
        a = 2 * math.pi * (i + rnd.uniform(-0.12, 0.12)) / STRIKE_VINES
        d = Vector((math.cos(a), math.sin(a), 0))
        sd = Vector((-d.y, d.x, 0)) * (1.0 if i % 2 else -1.0)          # each whips round the enemy to one side
        h = rnd.uniform(1.0, 1.3)
        ctrl = [d * 0.6 + Vector((0, 0, -0.12)), d * 0.74 + Vector((0, 0, h * 0.4)), d * 0.52 + sd * 0.12 + Vector((0, 0, h * 0.8)),
                d * 0.08 + sd * 0.3 + Vector((0, 0, h)), d * -0.3 + sd * 0.34 + Vector((0, 0, h * 0.82)), d * -0.48 + sd * 0.1 + Vector((0, 0, h * 0.52))]
        pts = spline_pts(ctrl, 3)
        shapes.append((d, pts))
        prev = "root"
        for j in range(3):
            bones["v%d.%d" % (i, j + 1)] = (tuple(pts[j * 5]), tuple(pts[j * 5 + 5]), prev)
            prev = "v%d.%d" % (i, j + 1)
    mid = Vector((0, 0, 0.7))
    slashes = []
    for i, (az, tilt) in enumerate(((-70.0, 32.0), (110.0, -32.0))):        # two rakes of three claw marks, one on each side
        u = Vector((math.cos(math.radians(az)), math.sin(math.radians(az)), 0))
        w0 = Vector((-u.y, u.x, 0))
        v = (Vector((0, 0, 1)) * math.cos(math.radians(tilt)) + w0 * math.sin(math.radians(tilt))).normalized()
        slashes.append((u, v, u.cross(v)))
        bones["slash%d" % i] = (tuple(mid), tuple(mid + v * 0.3), "root")
    fly = []
    for i in range(STRIKE_BITS):
        a = 2 * math.pi * (i + 0.5 + rnd.uniform(-0.2, 0.2)) / STRIKE_BITS
        d = Vector((math.cos(a), math.sin(a), 0))
        fly.append((d, rnd.uniform(0.8, 1.25), rnd.uniform(1.4, 2.1)))
        bones["bit%d" % i] = (tuple(d * 0.3 + Vector((0, 0, 0.6))), tuple(d * 0.3 + Vector((0, 0, 0.8))), "root")
    rig = make_rig(col, root, bones)
    k = Kit()
    for i, (d, pts) in enumerate(shapes):
        bm_cane(k[CANE_RED], k[THORN], rnd, pts, resample([0.09, 0.085, 0.072, 0.056, 0.04, 0.0], len(pts)), n=5, sub=1, every=0.2, tl=0.18,
                tr=0.045, skip_ends=0.1, hook=0.3)
        bm_sprig(k[LEAF_A], rnd, pts[6] + d * 0.06, d + Vector((0, 0, 0.6)), n=2, size=0.2)
        k.emit("Vine%d" % i, col, rig=rig, bones=["v%d.%d" % (i, j) for j in (1, 2, 3)])
    for i, (u, v, w) in enumerate(slashes):
        for c in (-1, 0, 1):
            arc = []
            for q in range(9):
                a = math.radians(-58 + 116 * q / 8.0)
                arc.append(mid + w * (c * 0.19) + (u * math.cos(a) + v * math.sin(a)) * (0.66 - 0.03 * abs(c)))
            bm_tube(k["glow:0.92,1.0,0.8,0.9"], arc, [0.0, 0.03, 0.05, 0.062, 0.066, 0.062, 0.05, 0.03, 0.0], n=4, up=tuple(u), squash=0.3)
        k.emit("Slash%d" % i, col, rig=rig, bone="slash%d" % i)
    for i, (d, pts) in enumerate(shapes):                               # the turf torn open where each vine comes up
        bm_stone(k["wood_red:0.55:0.98" if i % 2 else "taupe_dark:0.3:0.9"], rnd, tuple(d * 0.66 + Vector((0, 0, -0.03))), (0.3, 0.22, 0.17),
                 yaw=math.degrees(math.atan2(d.y, d.x)) + 90, n=9, jit=0.2)
    k.emit("Heave", col, rig=rig, bone="dirt", vary=0.06)
    for i, (d, _, _) in enumerate(fly):
        p = d * 0.3 + Vector((0, 0, 0.6))
        if i % 2:
            bm_leaf(k[LEAF_C], p - d * 0.1, p + d * 0.12, 0.13, up=(0.3, 0.2, 1))
        else:
            bm_crystal(k[THORN], p - d * 0.08, p + d * 0.12, 0.04, n=3, shoulder=0.2)
        k.emit("Bit%d" % i, col, rig=rig, bone="bit%d" % i)
    new_action(rig, "strike", STRIKE_LEN)
    pb = rig.pose.bones
    for f in range(STRIKE_LEN + 1):
        rest_pose(rig)
        gone = smooth((f - 14) / 7.0)
        grow = smooth(f / 2.0) * (1.0 - gone)
        # thrown open as they come up, down on the enemy by frame 2 (a little too far, then easing), a second lash at 9-11
        opened = (1.0 - smooth(f / 2.4)) - 0.16 * math.sin(math.pi * min(max((f - 2) / 4.0, 0.0), 1.0)) \
            + 0.42 * math.sin(math.pi * min(max((f - 6) / 5.0, 0.0), 1.0)) ** 2 + 0.7 * gone
        for i, (d, pts) in enumerate(shapes):
            axis = (-d.y, d.x, 0)                   # a turn about this tips the vine outward (+) or inward (-)
            wob = 3.0 * math.sin(f * 1.5 + i * 2.0) * (1.0 if 3 < f < 15 else 0.0)
            b1 = pb["v%d.1" % i]
            b1.scale = (max(grow, 0.02),) * 3
            b1.location = arm_space_loc(b1, (0, 0, -0.5 * (1.0 - grow)))
            b1.rotation_quaternion = arm_space_quat(b1, axis, 30 * opened + wob)
            pb["v%d.2" % i].rotation_quaternion = arm_space_quat(pb["v%d.2" % i], axis, 40 * opened)
            pb["v%d.3" % i].rotation_quaternion = arm_space_quat(pb["v%d.3" % i], axis, 36 * opened - wob)
        for i, (u, v, w) in enumerate(slashes):     # the claw marks rake across as they flash, and are gone by frame 7
            b = pb["slash%d" % i]
            b.scale = (max(0.02, smooth(f / 1.6) * (1.0 - smooth((f - 3.5) / 3.5))),) * 3
            b.rotation_quaternion = arm_space_quat(b, tuple(w), -34 + 52 * smooth(f / 5.0))
        pb["dirt"].scale = (max(0.05, smooth(f / 1.5) * (1.0 - smooth((f - 15) / 6.0))),) * 3
        for i, (d, reach, vz) in enumerate(fly):    # leaves and thorns thrown out and up, tumbling
            t = min(max((f - 1 - (i % 2)) / 13.0, 0.0), 1.0)
            b = pb["bit%d" % i]
            b.location = arm_space_loc(b, tuple(d * (reach * t) + Vector((0, 0, vz * t * (1.0 - t) * 1.5))))
            b.rotation_quaternion = arm_space_quat(b, (d.y, -d.x, 0), -500 * t)
            b.scale = (max(0.02, smooth(t / 0.1) * (1.0 - smooth((t - 0.75) / 0.25))),) * 3
        key_pose(rig, f)
    bpy.context.scene.frame_set(0)


STRIKE_PREVIEW = {"frames": [1, 2, 3, 9, 17], "dist": 5.0, "target": (0, 0, 0.6)}
