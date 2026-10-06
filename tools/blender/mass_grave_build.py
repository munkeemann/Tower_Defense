"""Builds the Mass Grave (footprint "line4": [0,0] at the front .. [0,3] at the back, in a line), a Bone Legion aura
tower: an open grave the length of four hexes, and the dead in it claw at whatever walks past and drag at its legs
(GameData.STRIKES "erupt": every second the arms lunge, and more burst out of the road under each walker).

    python tools/blender/build.py mass_grave --out <preview dir>

One trench runs the whole footprint, dug along the cemetery's wall: the wall and its iron fence zigzag down the left
side from a tall, banner-hung end at the far hex to broken stubs at the near one, old headstones in a row at its foot;
the spoil is heaped down the right side, stuck with crooked crosses and the gravedigger's shovels. At the trench's head
his cart is tipping a coffin in; another waits on planks across the trench, a third on the spoil (their palls are the
team's color), and one lies open in the trench, its lid knocked ajar from inside. Green soul-mist lies along the
bottom, and out of it reach fourteen skeletal arms; at the near end one of the dead is hauling itself out, skull up
(all on bones: Rig is under the root, the tower never turns).
Clips: idle (the arms sway and grope, the mist creeps, the lid rattles, the banner stirs, the climber heaves, looks
about and gnashes), fire (every arm lunges out and snatches shut, the climber rears and snaps).
build_strike(): three arms burst out of the ground round a walker and clutch its legs.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "grave_big_common.py"), encoding="utf-8").read())

TID = "mass_grave"
CELLS = [(0, 0), (0, 1), (0, 2), (0, 3)]
MID = footprint_mid(CELLS)
CS = [hex_to_world(0, s, MID) for s in range(4)]        # the cells' middles: [0] the far (front) end .. [3] the near end
TOP = 0.34
FLOOR = 0.05                                            # the trench's floor
TEAM = "team!:0.1:0.75"
NECKS = [(CS[i].y + CS[i + 1].y) * 0.5 for i in range(3)]       # where the footprint narrows between two cells
YA, YB = CS[3].y - 0.3, CS[0].y - 0.15                  # the middles of the trench's round ends
MIST_LO, MIST_HI = glow((0.05, 0.3, 0.1), 0.4), glow((0.3, 0.92, 0.3), 0.5)
DIRT, DIRT_LT, DIRT_DK = "taupe_dark:0.3:0.95", "wood_dark:0.25:0.85", "taupe_dark:0.75:0.98"
COURSE = 0.18                                           # the wall's courses


def tr_c(y):
    """The trench's middle line."""
    return 0.07 + 0.025 * math.sin(1.1 * y + 0.5)


def tr_w(y):
    """Its half width: narrow where the footprint is, and toward its ends."""
    d = min(abs(y - n) for n in NECKS)
    return (0.27 + 0.11 * smooth(d / 0.7)) * (0.8 + 0.2 * smooth(min(y - YA, YB - y) / 0.5))


def tr_dist(x, y):
    """How far outside the trench's edge (x, y) is (negative inside)."""
    yy = min(max(y, YA), YB)
    if YA <= y <= YB:
        return abs(x - tr_c(y)) - tr_w(y)
    return math.hypot(x - tr_c(yy), y - yy) - tr_w(yy)


def _trench_loop(step=0.24):
    n = int(round((YB - YA) / step))
    ys = [YA + (YB - YA) * i / n for i in range(n + 1)]
    caps = [math.radians(t) for t in (30, 60, 90, 120, 150)]
    pts = [(tr_c(y) + tr_w(y), y) for y in ys]
    pts += [(tr_c(YB) + tr_w(YB) * math.cos(a), YB + tr_w(YB) * math.sin(a)) for a in caps]
    pts += [(tr_c(y) - tr_w(y), y) for y in reversed(ys)]
    pts += [(tr_c(YA) - tr_w(YA) * math.cos(a), YA - tr_w(YA) * math.sin(a)) for a in caps]
    return [Vector((x, y, 0)) for x, y in pts]


TRENCH = _trench_loop()
OUT = outline(CELLS, 0.17)                              # where the dug earth ends
# spoil heaps: (x, y, radius across, radius along, height)
MOUNDS = [(0.78, CS[0].y - 0.25, 0.42, 0.6, 0.27), (0.74, CS[1].y - 0.05, 0.46, 0.74, 0.42), (0.74, CS[2].y - 0.05, 0.44, 0.7, 0.3),
          (0.72, CS[3].y + 0.05, 0.44, 0.66, 0.36), (-0.52, CS[0].y - 0.1, 0.24, 0.4, 0.1), (-0.52, CS[1].y, 0.24, 0.42, 0.13),
          (-0.52, CS[2].y, 0.24, 0.42, 0.11), (-0.5, CS[3].y, 0.24, 0.4, 0.12), (0.07, YB + 0.42, 0.34, 0.2, 0.1)]


def earth_h(x, y):
    """The dug ground's height above the plinth's top: tucked under at the footprint's rim, a lip along the trench,
    the spoil heaps."""
    d_out = loop_dist(OUT, x, y)
    h = min(0.05, d_out * 0.45) - 0.02
    h += 0.075 * math.exp(-(max(tr_dist(x, y), 0.0) / 0.16) ** 2)
    for cx, cy, rx, ry, mh in MOUNDS:
        q = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
        if q < 1.0:
            h += mh * (1.0 - q) ** 1.3 * min(1.0, d_out / 0.12)
    return h + 0.014 * math.sin(7.3 * x + 1.7 * y) * math.sin(5.1 * y - 2.2 * x) * min(1.0, d_out / 0.1)


def gz(x, y):
    return TOP + earth_h(x, y)


# the wall's line down the left side: a pier at each cell's corner, a post at each neck and each end
PIER = [Vector((-0.8, c.y, 0)) for c in CS]
NECKP = [Vector((-0.335, y, 0)) for y in NECKS]
ENDP = [Vector((-0.42, CS[0].y + 0.75, 0)), Vector((-0.42, CS[3].y - 0.75, 0))]
BANNER_Z = TOP + 0.95
_wax = (PIER[0] - ENDP[0]).normalized()
BAN_AX = (_wax.x, _wax.y, 0.0)                         # along the far wall (the banner swings about it)
# the open coffin in the trench (its lid is on a bone), the coffin on planks, the cart
COFFIN_M = xf((0.0, CS[2].y - 0.2, FLOOR + 0.03), (9, -5, -6))
COFFIN = dict(l=0.8, w=0.36, h=0.2)
LID_OPEN = 24.0
PLANK_Y = CS[1].y
CART = Vector((0.07, YB + 0.62, 0))
# the arms: (x, y, lean (dx, dy), length, hand size, what it reaches for (dx, dy, dz), wrist bend)
ARMS = [
    (0.22, CS[3].y + 0.5, (0.40, 0.00), 0.95, 0.41, (1.0, 0.0, 0), 0.35),
    (0.03, NECKS[2] - 0.02, (0.00, -0.10), 1.12, 0.46, (0.2, -1.0, 0), 0.3),
    (0.20, CS[2].y - 0.72, (0.36, -0.10), 0.78, 0.33, (1.0, -0.2, 0), 0.35),
    (-0.14, CS[2].y - 0.44, (-0.38, 0.05), 0.90, 0.38, (-1.0, 0.0, 0), 0.35),
    (0.10, CS[2].y + 0.32, (0.16, 0.10), 0.74, 0.36, (0.8, 0.5, 0), 0.4),          # out of the open coffin
    (0.07, NECKS[1] + 0.02, (0.05, -0.06), 1.25, 0.54, (0.3, -1.0, 0), 0.3),        # the tallest, in the middle
    (-0.16, CS[1].y - 0.56, (-0.36, -0.10), 0.86, 0.36, (-1.0, -0.2, 0), 0.35),
    (0.33, CS[1].y - 0.64, (0.42, 0.00), 0.84, 0.35, (1.0, 0.0, 0), 0.35),
    (0.38, CS[1].y + 0.06, (0.10, 0.00), 0.70, 0.33, (-1.0, 0.0, -0.45), 0.8),      # clawing at the coffin on the planks
    (-0.20, CS[1].y + 0.64, (-0.34, 0.10), 0.92, 0.39, (-1.0, 0.2, 0), 0.35),
    (0.26, CS[1].y + 0.76, (0.10, -0.26), 0.98, 0.41, (0.0, -1.0, -0.2), 0.45),
    (0.07, NECKS[0] + 0.04, (0.05, 0.05), 1.04, 0.44, (0.4, -0.9, 0), 0.3),
    (0.30, CS[0].y - 0.5, (0.42, 0.05), 0.80, 0.35, (1.0, 0.0, 0), 0.35),
    (-0.12, CS[0].y - 0.26, (-0.25, 0.22), 0.84, 0.36, (-0.5, 0.85, 0), 0.35),
]
MIST_Y = [YA + 0.25 + (YB - YA - 0.5) * i / 6.0 for i in range(7)]
# the one hauling itself out at the near end (it faces -Y, up at the camera): where its parts are
CL_X = tr_c(YA)
CL = {"pelvis": Vector((CL_X, YA + 0.3, 0.02)), "neck": Vector((CL_X, YA + 0.04, 0.62))}
CL_U = (CL["neck"] - CL["pelvis"]).normalized()         # up its spine
CL_F = Vector((0, -CL_U.z, CL_U.y))                     # out of its chest
CL_S = 0.36
CL_SKULL_M = xf((CL_X, YA - 0.1, 0.85), (20, 0, 180))
CL_JAW_AX = (CL_SKULL_M.to_3x3() @ Vector((1, 0, 0))).normalized()
CL_SH = {sd: Vector((CL_X + sd * 0.25, YA + 0.04, 0.6)) for sd in (-1, 1)}
CL_EL = {sd: Vector((CL_X + sd * 0.42, YA - 0.13, 0.68)) for sd in (-1, 1)}
CL_WR = {sd: Vector((CL_X + sd * 0.27, YA - 0.31, gz(CL_X + sd * 0.27, YA - 0.31) + 0.06)) for sd in (-1, 1)}
CL_HAND = Vector((0, -1, -0.1)).normalized() * 0.2


def _lvl(*steps):
    """A wall's top: steps of (up to t, courses) and, between two different numbers, a broken slope."""
    def top(t):
        t0, c0 = 0.0, steps[0][1]
        for t1, c1 in steps:
            if t <= t1:
                c = c1 if isinstance(c1, (int, float)) else c1[0] + (c1[1] - c1[0]) * (t - t0) / max(t1 - t0, 1e-6)
                return c * COURSE + 0.02
            t0 = t1
        return COURSE
    top.coped = [(a, b, c) for a, (b, c) in zip([0.0] + [x[0] for x in steps], steps) if isinstance(c, int) and c >= 3]
    return top


def _wall_line():
    """The wall's stretches from the far end to the near one: (from, to, what). A slope (a, b) is broken wall."""
    return [(ENDP[0], PIER[0], "wall", _lvl((0.2, (3.6, 4.4)), (1.0, 6))),
            (PIER[0], NECKP[0], "wall", _lvl((0.42, 6), (1.0, (5.2, 2.2)))),
            (NECKP[0], PIER[1], "fence", "halloween/fence_seperate"),
            (PIER[1], NECKP[1], "wall", _lvl((0.34, 5), (1.0, (4.2, 0.4)))),
            (NECKP[1], PIER[2], "fence", "halloween/fence_seperate_broken"),
            (PIER[2], NECKP[2], "wall", _lvl((0.5, 4), (0.74, 3), (1.0, (2.6, 1.6)))),
            (NECKP[2], PIER[3], "wall", _lvl((1.0, (1.8, 3.0)))),
            (PIER[3], ENDP[1], "wall", _lvl((1.0, (2.2, 0.7))))]


def _shovel(k, M):
    """A gravedigger's shovel standing along +Z (its blade below the origin, in the earth)."""
    t = Kit()
    bm_beam(t["sand:0.3:0.9"], (0, 0, 0.08), (0, 0, 0.84), 0.04, 0.04)
    bm_beam(t["sand:0.3:0.9"], (-0.08, 0, 0.86), (0.08, 0, 0.86), 0.04, 0.05)
    bm_beam(t[IRON], (0, 0, 0.14), (0, 0, -0.12), 0.18, 0.022, w1=0.13, up=(0, 1, 0))
    return stamp(k, t, M)


def _cart(k, rnd, M):
    """The gravedigger's handcart, its axle's middle on the ground at the origin, its shafts toward +Y: tipped up,
    a pall-draped coffin sliding off its tail."""
    t = Kit()
    wood, dark = "wood:0.25:0.85", "wood_dark:0.2:0.8"
    tilt = Matrix.Translation((0, 0, 0.21)) @ Matrix.Rotation(math.radians(13), 4, "X") @ Matrix.Translation((0, 0, -0.21))
    b = Kit()
    for sx in (-1, 1):
        bm_beam(b[dark], (sx * 0.25, -0.44, 0.3), (sx * 0.25, 0.6, 0.3), 0.05, 0.06)                 # the shafts
        bm_beam(b[dark], (sx * 0.26, -0.42, 0.4), (sx * 0.26, 0.4, 0.4), 0.03, 0.11)                 # side boards
    bm_planks(b[wood], rnd, (-0.25, -0.44, 0.345), (0, 0.86, 0), (0.5, 0, 0), 4, th=0.035)
    bm_beam(b[dark], (-0.26, 0.41, 0.41), (0.26, 0.41, 0.41), 0.03, 0.13)
    bm_beam(b[dark], (-0.25, 0.6, 0.3), (0.25, 0.6, 0.3), 0.045, 0.045)                               # the grip
    coffin(b, xf((0, -0.62, 0.36), (0, 0, 3)), l=0.84, w=0.36, h=0.19, pall=TEAM)
    stamp(t, b, tilt)
    bm_beam(t[dark], (-0.42, 0, 0.21), (0.42, 0, 0.21), 0.05, 0.05)                                   # the axle
    w = bmesh.new()
    for sx in (-1, 1):
        ring(w, (sx * 0.36, 0, 0.21), 0.21, 0.155, -0.028, 0.028, seg=8, axis="X")
        bm_cyl(w, 0.05, 0.05, 0.09, (sx * 0.36, 0, 0.21), rot=(0, 90, 0), seg=6)
        for a in (0, 90):
            d = Vector((0, math.cos(math.radians(a + 20)), math.sin(math.radians(a + 20)))) * 0.16
            bm_beam(w, Vector((sx * 0.36, 0, 0.21)) - d, Vector((sx * 0.36, 0, 0.21)) + d, 0.03, 0.035, up=(1, 0, 0))
    bm_merge(t[wood], w)
    return stamp(k, t, M)


def build_base():
    col = collection("Mass_grave")
    root = empty("Mass_grave", col, None, (0, 0, 0), 0.6, "ARROWS")
    rnd = random.Random(31)
    plinth_cut(CELLS, col, root, TOP, holes=[TRENCH], grid=0.42)
    k = Kit()
    # ---- the dug ground: one sheet from the footprint's rim to the trench's edge, heaped with spoil
    tmp = bmesh.new()
    fine = []
    for i, p in enumerate(OUT):
        q = OUT[(i + 1) % len(OUT)]
        fine.extend(p.lerp(q, j / 3.0) for j in range(3))
    _cdt_fill(tmp, [fine], 0.0, holes=[TRENCH], grid=0.2)
    for f in tmp.faces:
        pts = [Vector((v.co.x, v.co.y, gz(v.co.x, v.co.y))) for v in f.verts]
        c = (pts[0] + pts[1] + pts[2]) / 3.0
        bm = k[DIRT_LT if c.z - TOP > 0.17 else DIRT]
        bm.faces.new([bm.verts.new(p) for p in pts])
    tmp.free()
    k.emit("Earth", col, root, vary=0.1, seed=2)
    # ---- the trench: earth sides down to an uneven floor
    n = len(TRENCH)
    mid, foot = inset_loop(TRENCH, 0.035), inset_loop(TRENCH, 0.085)
    wb = bmesh.new()
    rows = [[], [], []]
    for i in range(n):
        zr = gz(TRENCH[i].x, TRENCH[i].y)
        rows[0].append(wb.verts.new((TRENCH[i].x, TRENCH[i].y, zr)))
        rows[1].append(wb.verts.new((mid[i].x + rnd.uniform(-0.02, 0.02), mid[i].y + rnd.uniform(-0.02, 0.02),
                                     FLOOR + (zr - FLOOR) * 0.5 + rnd.uniform(-0.03, 0.03))))
        rows[2].append(wb.verts.new((foot[i].x, foot[i].y, FLOOR)))
    for a, b in zip(rows, rows[1:]):
        for i in range(n):
            j = (i + 1) % n
            wb.faces.new((a[i], a[j], b[j], b[i]))
    bm_merge(k["taupe_dark:0.45:0.98"], facet(wb))
    _cdt_fill(k[DIRT_DK], [[(p.x, p.y) for p in foot]], FLOOR, grid=0.3, lump=0.012, rnd=rnd)
    k.emit("Trench", col, root, vary=0.07, seed=4)
    # ---- the cemetery's wall and fence down the left side
    z0 = TOP - 0.03
    for i, (p0, p1, kind, what) in enumerate(_wall_line()):
        ax = (p1 - p0).normalized()
        if kind == "wall":
            a, b = p0 + ax * 0.1, p1 - ax * 0.1
            ruin_wall(k, rnd, a, b, z0, what, th=0.2, course=COURSE, block=0.34)
            for t0, t1, c in what.coped:                    # coping stones along its level stretches
                n = max(1, int(round((t1 - t0) * (b - a).length / 0.3)))
                for j in range(n):
                    if rnd.random() < 0.14:
                        continue
                    q0, q1 = a.lerp(b, t0 + (t1 - t0) * j / n), a.lerp(b, t0 + (t1 - t0) * (j + 1) / n)
                    zc = z0 + c * COURSE + 0.028 + rnd.uniform(0, 0.012)
                    bm_beam(k[STONE_LT], Vector((q0.x, q0.y, zc)) + ax * 0.008, Vector((q1.x, q1.y, zc)) - ax * 0.008, 0.28, 0.06)
        else:
            a, b = p0 + ax * 0.08, p1 - ax * 0.14
            m = (a + b) * 0.5
            kk_import(what, col, root, (m.x, m.y, gz(m.x, m.y) - 0.04), math.degrees(math.atan2(ax.y, ax.x)), (b - a).length / 4.0,
                      name="Fence_%d" % i)
    k.emit("Wall", col, root, vary=0.09, seed=5)
    for c, w, h, cap in ((PIER[0], 0.3, 1.4, "point"), (PIER[1], 0.28, 1.04, "flat"), (PIER[2], 0.28, 0.94, "point"), (PIER[3], 0.28, 0.6, None),
                         (NECKP[0], 0.17, 0.66, "flat"), (NECKP[1], 0.17, 0.34, None), (NECKP[2], 0.17, 0.6, "flat"),
                         (ENDP[0], 0.22, 0.86, "flat"), (ENDP[1], 0.2, 0.3, None)):
        pier(k, rnd, c, w, z0, h, cap=cap, course=0.2)
    gravestone(k, xf((PIER[0].x, PIER[0].y, z0 + 1.4 + 0.15)), "cross", w=0.3, h=0.44, th=0.08, base=False)
    k.emit("Piers", col, root, vary=0.09, seed=7)
    lz = z0 + 1.04 + 0.07                                    # a soul-lantern on the second pier
    for sx in (-1, 1):
        for sy in (-1, 1):
            bm_box(k[IRON], (0.022, 0.022, 0.2), (PIER[1].x + sx * 0.065, PIER[1].y + sy * 0.065, lz + 0.11))
    bm_box(k[IRON], (0.18, 0.18, 0.025), (PIER[1].x, PIER[1].y, lz + 0.012))
    bm_cyl(k[IRON], 0.14, 0.02, 0.1, (PIER[1].x, PIER[1].y, lz + 0.26), rot=(0, 0, 45), seg=4)
    bm_box(k[glow(SOULFIRE, 0.8)], (0.11, 0.11, 0.17), (PIER[1].x, PIER[1].y, lz + 0.115))
    k.emit("Lantern", col, root)
    bm_rubble(k[STONE], rnd, (NECKP[1].x - 0.1, NECKP[1].y + 0.34), n=4, r=0.16, size=0.13, z=TOP + 0.04)
    bm_rubble(k[STONE_LT], rnd, (ENDP[1].x - 0.05, ENDP[1].y + 0.3), n=3, r=0.14, size=0.12, z=TOP + 0.03)
    k.emit("Rubble", col, root, vary=0.1, seed=9)
    # ---- old headstones in a row at the wall's foot; crooked crosses on the spoil
    for (x, y), kind, rot, w, h in (((-0.5, CS[0].y - 0.12), "round", (-7, 0, 96), 0.3, 0.46), ((-0.5, CS[1].y + 0.02), "point", (6, 0, 82), 0.3, 0.5),
                                    ((-0.5, CS[2].y - 0.02), "round", (-11, 4, 100), 0.32, 0.44), ((-0.49, CS[3].y), "broken", (4, 0, 88), 0.32, 0.5),
                                    ((0.74, CS[1].y + 0.3), "cross", (7, 12, 14), 0.38, 0.66)):
        gravestone(k, xf((x, y, gz(x, y) - 0.04), rot), kind, w=w, h=h, base=kind != "cross")
    for (x, y), rot, h, rag in (((0.8, CS[0].y - 0.34), (5, -11, 18), 0.66, TEAM), ((0.7, CS[1].y - 0.5), (-8, 9, -14), 0.6, None),
                                ((0.8, CS[3].y + 0.24), (-6, -10, 10), 0.7, TEAM), ((0.66, CS[2].y - 0.56), (9, 7, -24), 0.5, None)):
        wood_cross(k, xf((x, y, gz(x, y) - 0.05), rot), h=h * 1.3, w=h * 0.78, th=0.08, rag=rag)
    k.emit("Graves", col, root, vary=0.08, seed=11)
    # ---- the coffins: one open in the trench, one on planks across it, one waiting on the spoil; the cart; shovels
    coffin(k, COFFIN_M, open_=True, **COFFIN)
    cx = tr_c(PLANK_Y)
    for dy in (-0.26, 0.26):
        za = gz(cx - 0.5, PLANK_Y + dy) + 0.03
        bm_beam(k["wood_dark:0.15:0.7"], (cx - 0.66, PLANK_Y + dy, za), (cx + 0.66, PLANK_Y + dy + 0.03, za + 0.02), 0.12, 0.05)
    pz = gz(cx - 0.4, PLANK_Y) + 0.075
    coffin(k, xf((cx, PLANK_Y - 0.42, pz), (0, 0, 2)), l=0.84, w=0.38, h=0.2, pall=TEAM)
    for dy in (-0.26, 0.26):                                # the ropes it will be lowered by
        bm_box(k["sand:0.3:0.8"], (0.42, 0.035, 0.035), (cx, PLANK_Y + dy, pz + 0.215))
        for sx in (-1, 1):
            bm_box(k["sand:0.3:0.8"], (0.03, 0.035, 0.2), (cx + sx * 0.205, PLANK_Y + dy, pz + 0.11))
    x, y = 0.72, CS[2].y + 0.02
    coffin(k, xf((x + 0.03, y - 0.36, gz(x, y) - 0.03), (4, -9, 4)), l=0.74, w=0.32, h=0.18, pall=TEAM)
    _cart(k, rnd, xf((CART.x, CART.y, gz(CART.x, CART.y) - 0.01)))
    for (x, y), rot in (((0.6, CS[3].y - 0.3), (14, 10, 30)), ((0.92, CS[3].y - 0.06), (-10, 16, 100)), ((0.62, CS[1].y + 0.36), (12, -9, -60))):
        _shovel(k, xf((x, y, gz(x, y) + 0.06), rot))
    k.emit("Props", col, root, vary=0.07, seed=13)
    # ---- bones and skulls in the trench and on the spoil
    def pick():
        y = rnd.uniform(YA + 0.1, YB - 0.1)
        return tr_c(y) + rnd.uniform(-0.75, 0.75) * (tr_w(y) - 0.09), y
    strew_bones(k, rnd, 9, pick, lambda x, y: FLOOR + 0.02, size=(0.24, 0.4), skulls=4, ribs=1, skull_s=0.19)
    for (x, y), yaw in (((0.62, CS[1].y - 0.2), 200), ((0.66, CS[3].y + 0.5), 160), ((0.6, CS[0].y - 0.66), 215)):
        skull(k, xf((x, y, gz(x, y) + 0.07), (-18, 8, yaw)), s=0.2, bone=BONE_OLD, detail=1, jaw=False, eyes=glow(SOULFIRE, 0.8))
    k.emit("Bones", col, root, vary=0.08, seed=15)
    head = empty("Head", col, root, (0, 0, TOP), 0.5, "SINGLE_ARROW")
    empty("Muzzle", col, head, (0, 0, 0.4), 0.2, "SPHERE")
    return root


def build_head():
    col = collection("Mass_grave")
    root = bpy.data.objects["Mass_grave"]
    rnd = random.Random(17)
    bones = {"root": ((0, 0, 0), (0, 0, 0.2), None)}
    arms, kits = [], []
    for i, (x, y, lean, L, s, out, flex) in enumerate(ARMS):
        base = Vector((x, y, FLOOR - 0.06))
        wrist = base + Vector((lean[0], lean[1], 1.0)).normalized() * L
        kk = Kit()
        a = reach_arm(kk[BONE if i % 3 else BONE_OLD], base, wrist, out, s=s, side=1 if i % 2 else -1, curl=0.22, flex=flex,
                      segs=3 if s >= 0.38 else 2, lite=s < 0.38, rnd=rnd, elbow=0.1 if L > 0.82 and flex < 0.6 else 0.0)
        arm_bones(bones, "arm.%d" % i, a)
        arms.append(a)
        kits.append(kk)
    for i, y in enumerate(MIST_Y):
        bones["mist.%d" % i] = ((tr_c(y), y, FLOOR), (tr_c(y), y, FLOOR + 0.25), "root")
    hp0, hp1 = COFFIN_M @ Vector((-0.5 * COFFIN["w"], 0.08, COFFIN["h"])), COFFIN_M @ Vector((-0.5 * COFFIN["w"], COFFIN["l"] - 0.08, COFFIN["h"]))
    bones["lid"] = (tuple(hp0), tuple(hp1), "root")
    w0, w1 = ENDP[0], PIER[0]
    wax = (w1 - w0).normalized()
    wn = Vector((-wax.y, wax.x, 0))                          # the banner's side of the far wall (toward the trench)
    bm0 = w0.lerp(w1, 0.56) + wn * 0.135
    flag_bones(bones, "flag", (bm0.x, bm0.y, BANNER_Z), (0, 0, -1), 0.62, segs=2)
    sc = CL_SKULL_M @ Vector((0, 0, 0))
    bones["climb"] = (tuple(CL["pelvis"]), tuple(CL["neck"]), "root")
    bones["climb.skull"] = (tuple(CL["neck"]), tuple(sc), "climb")
    bones["climb.jaw"] = (tuple(CL_SKULL_M @ (Vector((0, -0.04, -0.1)) * CL_S)), tuple(CL_SKULL_M @ (Vector((0, 0.33, -0.42)) * CL_S)), "climb.skull")
    for nm, sd in (("L", -1), ("R", 1)):
        bones["climb.%s.1" % nm] = (tuple(CL_SH[sd]), tuple(CL_EL[sd]), "climb")
        bones["climb.%s.2" % nm] = (tuple(CL_EL[sd]), tuple(CL_WR[sd]), "climb.%s.1" % nm)
        bones["climb.%s.h" % nm] = (tuple(CL_WR[sd]), tuple(CL_WR[sd] + CL_HAND), "climb.%s.2" % nm)
    rig = make_rig(col, root, bones)
    for i, kk in enumerate(kits):
        kk.emit("Arm%d" % i, col, rig=rig, bones=["arm.%d" % i, "arm.%d.h" % i, "arm.%d.g" % i])
    k = Kit()
    # ---- the soul-mist lying in the trench: a glowing sheet over the floor, puffs drifting on it, a few wisps rising
    _cdt_fill(k[MIST_LO], [[(q.x, q.y) for q in inset_loop(TRENCH, 0.13)]], FLOOR + 0.035, grid=0.34)
    k.emit("Mist_Floor", col, root)
    for i in range(13):
        y = YA + 0.2 + (YB - YA - 0.4) * i / 12.0 + rnd.uniform(-0.1, 0.1)
        r = (tr_w(y) - 0.1) * rnd.uniform(0.5, 0.8)
        x = tr_c(y) + rnd.uniform(-0.1, 0.1)
        bm_blob(k[MIST_HI], rnd, (x, y, FLOOR + 0.05), r, squash=(1.0, rnd.uniform(1.2, 1.7), 0.15), jitter=0.12)
        if i % 3 == 1:
            bm_flame(k[MIST_HI], rnd, (x, y, FLOOR + 0.05), h=rnd.uniform(0.26, 0.36), r=0.075, n=2, sides=4)
    k.emit("Mist", col, rig=rig, bones=["mist.%d" % i for i in range(len(MIST_Y))])
    # ---- the open coffin's lid, on its hinge
    lk = Kit()
    w = COFFIN["w"]
    lid_M = Matrix.Translation((-0.5 * w, 0, COFFIN["h"])) @ Matrix.Rotation(math.radians(-LID_OPEN), 4, "Y") @ Matrix.Translation((0.5 * w, 0, 0))
    scrap = Kit()
    coffin(scrap, COFFIN_M, lid_M=lid_M, lid_k=lk, **COFFIN)
    for bm in scrap.parts.values():
        bm.free()
    lk.emit("Lid", col, rig=rig, bone="lid")
    # ---- the banner on the far wall: the team's colors, a pale skull sewn on
    a, b = bm0 - wax * 0.27, bm0 + wax * 0.27
    bm_cloth(k[TEAM], (a.x, a.y, BANNER_Z), (b.x, b.y, BANNER_Z), 0.66, cols=4, rows=4, wave=0.03, tatter=0.3, rnd=rnd, th=0.014)
    k.emit("Banner", col, rig=rig, bones=["flag.1", "flag.2"])
    bm_beam(k["wood_dark:0.2:0.7"], (a.x - wax.x * 0.06, a.y - wax.y * 0.06, BANNER_Z + 0.02), (b.x + wax.x * 0.06, b.y + wax.y * 0.06, BANNER_Z + 0.02), 0.045, 0.045)
    k.emit("Banner_Rod", col, root)
    skull(k, frame((bm0.x + wn.x * 0.03, bm0.y + wn.y * 0.03, BANNER_Z - 0.26), wn), s=0.2, bone=BONE, detail=1, jaw=False)
    k.emit("Banner_Skull", col, rig=rig, bone="flag.1")
    # ---- the one climbing out at the near end: spine and ribs, a skull that looks about, arms braced on the rim
    ck = Kit()
    T = frame(CL["pelvis"].lerp(CL["neck"], 0.68), CL_F, up=CL_U)
    bm_tube(ck["taupe_dark:0.3:0.9"], [T @ Vector(q) for q in ((0, -0.13, -0.44), (0, -0.15, -0.1), (0, -0.14, 0.12), (0, -0.07, 0.24))], 0.04, n=5)
    for q in ((0, -0.15, -0.22), (0, -0.16, -0.06), (0, -0.15, 0.1), (0, -0.09, 0.23)):
        bm_lump(ck[BONE], rnd, T @ Vector(q), 0.062, squash=(1.3, 1.0, 0.8), n=8)
    for jr, (rx, ry) in enumerate(((0.19, 0.16), (0.215, 0.18), (0.2, 0.17))):
        zc = 0.15 - 0.115 * jr
        for sx in (-1, 1):
            pts = [T @ Vector((sx * rx * math.sin(math.radians(a)), 0.02 - ry * math.cos(math.radians(a)), zc - 0.075 * (a / 160.0) ** 1.3))
                   for a in (18, 55, 95, 130, 160)]
            bm_tube(ck[BONE], pts, [0.03, 0.032, 0.03, 0.027, 0.022], n=4)
    bm_beam(ck[BONE_OLD], T @ Vector((0, 0.2, 0.17)), T @ Vector((0, 0.2, -0.08)), 0.09, 0.035, w1=0.05, up=CL_F)
    for sd in (-1, 1):
        bm_bone(ck[BONE], T @ Vector((sd * 0.03, 0.19, 0.18)), CL_SH[sd], 0.026, n=4, lite=True)
        bm_lump(ck[BONE_OLD], rnd, CL_SH[sd], 0.07, n=8)
    ck.emit("Climber", col, rig=rig, bone="climb", vary=0.04)
    sk, sj = Kit(), Kit()
    skull(sk, CL_SKULL_M, s=CL_S, bone=BONE, detail=1, jaw=True, eyes=glow(SOULFIRE, 0.8), jaw_k=sj)
    sk.emit("Climber_Skull", col, rig=rig, bone="climb.skull")
    stamp(ck, sj, CL_SKULL_M @ Matrix.Diagonal((CL_S, CL_S, CL_S, 1.0)))
    ck.emit("Climber_Jaw", col, rig=rig, bone="climb.jaw")
    for nm, sd in (("L", -1), ("R", 1)):
        bm = ck[BONE]
        bm_bone(bm, CL_SH[sd], CL_EL[sd], 0.042, n=4, lite=True)
        bm_lump(bm, rnd, CL_EL[sd], 0.065, n=8)
        bm_forearm(bm, CL_EL[sd], CL_WR[sd], r=0.03, spread=0.04, side=(1, 0, 0), knob=False, lite=True)
        t = bmesh.new()
        hand_parts(t, t, s=0.34, curl=0.5, side=sd, segs=2)
        bm_merge(bm, t, frame(CL_WR[sd], CL_HAND, up=(0, 0, 1)))
        ck.emit("Climber_Arm" + nm, col, rig=rig, bones=["climb.%s.1" % nm, "climb.%s.2" % nm, "climb.%s.h" % nm])
    return rig, arms


IDLE_LEN = 96
FIRE_LEN = 16
_ph = random.Random(5)
PHASE = [(_ph.uniform(0, 6.283), _ph.uniform(0, 6.283), _ph.choice((1, 1, 2))) for _ in ARMS]


def _idle_arm(i, f):
    """Arm i in the idle at frame f: it sways, sinks and rises, gropes."""
    p, q, m = PHASE[i]
    ph = 2 * math.pi * f / IDLE_LEN
    return dict(lean=9.0 * math.sin(m * ph + p), side=7.0 * math.sin(ph + q), rise=-0.05 + 0.05 * math.sin(ph + p + q),
                flex=6.0 + 13.0 * math.sin(2 * ph + q), grip=16.0 + 24.0 * math.sin(2 * ph + p * 1.3))


def pose(fk, arms, f, thrust=0.0, clutch=0.0, calm=1.0, t=None):
    """f: where the idle's motion is; thrust / clutch: the lunge on top of it (calm: how much of the idle's own
    groping is left); t: the lid's rattle and the banner's phase (default: from f)."""
    fk.clear()
    pb = fk.pb
    ph = 2 * math.pi * f / IDLE_LEN
    for i, a in enumerate(arms):
        d = _idle_arm(i, f)
        k = 0.8 + 0.4 * ((i * 7) % 5) / 4.0
        pose_arm(fk, "arm.%d" % i, a, lean=d["lean"] * calm + (26.0 * thrust - 8.0 * clutch) * k, side=d["side"] * calm,
                 rise=d["rise"] * calm + (0.22 * thrust - 0.05 * clutch) * k, flex=d["flex"] * calm - 22.0 * thrust + 34.0 * clutch,
                 grip=d["grip"] * calm - 38.0 * thrust + 66.0 * clutch)
    for i in range(len(MIST_Y)):
        b = pb["mist.%d" % i]
        b.location = arm_space_loc(b, (0, 0.1 * math.sin(ph + i * 0.9), 0))
        wide = 1.0 + 0.07 * math.sin(2 * ph + i * 1.7) + 0.1 * thrust
        b.scale = (wide, 1.0 + 0.3 * math.sin(2 * ph + i * 1.3 + 1.0) + 1.1 * thrust + 0.4 * clutch, wide)
    rattle = max(0.0, math.sin(3 * ph + 0.6)) ** 3 * (0.6 + 0.4 * math.sin(ph))
    hinge = (Vector(fk.rest["lid"][2]) - Vector(fk.rest["lid"][1])).normalized()
    fk.put("lid", Quaternion(hinge, math.radians(-(9.0 * rattle * calm + 40.0 * thrust + 14.0 * clutch))))
    # the climber heaves at the rim, looks about, works its jaw; with the arms' lunge it rears and snaps
    R = Fk.rot
    chat = max(0.0, math.sin(4 * ph)) ** 2 * (0.5 + 0.5 * math.sin(ph + 2.0))
    fk.put("climb", R((0, 0, 1), 5.0 * math.sin(ph) * calm) @ R((1, 0, 0), 4.0 * math.sin(ph + 0.5) * calm + 12.0 * thrust - 3.0 * clutch),
           loc=(0, -0.1 * thrust + 0.02 * clutch, 0.04 * (0.5 + 0.5 * math.sin(2 * ph + 1.0)) * calm + 0.09 * thrust))
    fk.put("climb.skull", R((0, 0, 1), 26.0 * math.sin(ph + 2.0) * calm) @ R((1, 0, 0), 5.0 * math.sin(2 * ph) * calm - 16.0 * thrust + 12.0 * clutch))
    fk.put("climb.jaw", Quaternion(CL_JAW_AX, math.radians(-(5.0 + 12.0 * chat * calm + 34.0 * thrust - 5.0 * clutch))))
    for nm, sd in (("L", -1), ("R", 1)):
        fk.ik("climb.%s.1" % nm, "climb.%s.2" % nm, CL_WR[sd])
        fk.aim("climb.%s.h" % nm, fk.head("climb.%s.h" % nm) + CL_HAND, side=(1, 0, 0), side0=(1, 0, 0))
    wave_flag(fk.rig, "flag", f / IDLE_LEN * 2.0, amp=0.55 + 0.8 * thrust, segs=2, axis=BAN_AX)


def build_anims(arms):
    rig = bpy.data.objects["Rig"]
    fk = Fk(rig)
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(fk, arms, f)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        # 0-3: every arm lunges up and out, fingers spread; 3-5: they snatch shut; then they sink back to groping
        thrust = pulse(f, 0, 3, 7)
        clutch = smooth((f - 2.5) / 2.0) * (1.0 - smooth((f - 7) / 8.0))
        pose(fk, arms, 0, thrust=thrust, clutch=clutch, calm=1.0 - min(1.0, thrust + clutch))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 0.5), "dist": 13.5, "yaw": 150, "pitch": 24, "anim_target": (0, CS[1].y * 0.4, 0.6), "anim_dist": 8.0,
           "frames": [("idle", 0), ("idle", 24), ("fire", 3), ("fire", 5), ("fire", 9)],
           "extra": [{"yaw": 0, "pitch": 50, "dist": 5.0, "target": (0, CS[3].y + 0.1, 0.5)},
                     {"yaw": 0, "pitch": 50, "dist": 6.5, "target": (0, CS[1].y + 0.3, 0.5)},
                     {"yaw": 115, "pitch": 16, "dist": 5.0, "target": (0, 0, 0.7)},
                     {"yaw": 200, "pitch": 22, "dist": 6.0, "target": (0, CS[0].y - 0.4, 0.7)}]}


def build_all():
    build_base()
    rig, arms = build_head()
    build_anims(arms)


# ================================================================================================ the strike
# What the game plays under each walker the grave claws (GameData.STRIKES "erupt", the damage at once): three
# skeletal arms burst out of the road round it, already snatching at its legs by the third frame, hold and drag, and
# are gone again inside 0.8 s, while clods fly. The model stands on the walker's spot; +Y points away from the tower.
STRIKE_LEN = 24
STRIKE_ARMS = ((80, 0.84, 0.45), (205, 0.72, 0.4), (322, 0.78, 0.43))      # where round the walker, length, hand size
STRIKE_CLODS = 6


def build_strike():
    col = collection("Mass_grave_strike")
    root = empty("Mass_grave_strike", col, None, (0, 0, 0), 0.5, "ARROWS")
    rnd = random.Random(23)
    bones = {"root": ((0, 0, 0), (0, 0, 0.2), None), "dirt": ((0, 0, 0), (0, 0, 0.3), "root")}
    arms, kits = [], []
    for i, (ang, L, s) in enumerate(STRIKE_ARMS):
        dv = Vector((math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0))
        base = dv * 0.5 + Vector((0, 0, -0.14))
        kk = Kit()
        a = reach_arm(kk[BONE], base, base + (Vector((0, 0, 1)) - dv * 0.12).normalized() * L, -dv + Vector((0, 0, -0.3)), s=s,
                      side=1 if i % 2 else -1, curl=0.2, flex=0.8, rnd=rnd, elbow=0.1, thick=1.22)
        a["dv"] = dv
        arm_bones(bones, "arm%d" % i, a)
        arms.append(a)
        kits.append(kk)
    fly = []
    for i in range(STRIKE_CLODS):
        a = 2 * math.pi * (i + 0.5 + rnd.uniform(-0.2, 0.2)) / STRIKE_CLODS
        d = Vector((math.cos(a), math.sin(a), 0))
        fly.append((d, rnd.uniform(0.7, 1.1), rnd.uniform(1.3, 2.0), rnd.uniform(0.07, 0.11)))
        bones["clod%d" % i] = (tuple(d * 0.45 + Vector((0, 0, 0.1))), tuple(d * 0.45 + Vector((0, 0, 0.3))), "root")
    rig = make_rig(col, root, bones)
    for i, kk in enumerate(kits):
        kk.emit("Arm%d" % i, col, rig=rig, bones=["arm%d" % i, "arm%d.h" % i, "arm%d.g" % i])
    k = Kit()
    for i, a in enumerate(arms):                            # the road broken open round each arm
        for j in range(4):
            an = math.radians(STRIKE_ARMS[i][0]) + 2 * math.pi * (j + 0.5) / 4.0
            p = a["dv"] * 0.5 + Vector((math.cos(an), math.sin(an), 0)) * 0.17
            bm_lump(k[DIRT if j % 2 else DIRT_LT], rnd, (p.x, p.y, 0.035), 0.12, squash=(1.2, 0.9, 0.6), rot=(rnd.uniform(-25, 25), rnd.uniform(-25, 25), math.degrees(an)), n=8)
    k.emit("Heave", col, rig=rig, bone="dirt", vary=0.08)
    for i, (d, _, _, r) in enumerate(fly):
        bm_lump(k[DIRT], rnd, tuple(d * 0.45 + Vector((0, 0, 0.1))), r, squash=(1.2, 1.0, 0.8), n=8)
        k.emit("Clod%d" % i, col, rig=rig, bone="clod%d" % i)
    fk = Fk(rig)
    new_action(rig, "strike", STRIKE_LEN)
    pb = rig.pose.bones
    for f in range(STRIKE_LEN + 1):
        fk.clear()
        up = smooth(f / 2.0)                                # out of the ground by frame 2
        sink = smooth((f - 16) / 7.0)                       # and back into it from frame 16
        shut = smooth((f - 1.2) / 2.2)                      # the hands snatch shut over frames 1-3
        over = math.sin(math.pi * min(max((f - 3) / 4.0, 0.0), 1.0))
        drag = smooth((f - 5) / 4.0) * (1.0 - sink)
        for i, a in enumerate(arms):
            wob = 2.5 * math.sin(f * 1.5 + i * 2.1) * drag
            pose_arm(fk, "arm%d" % i, a, lean=-16.0 * (1.0 - shut) + 9.0 * shut + 5.0 * over + wob - 12.0 * sink, side=wob * 0.6,
                     rise=-0.95 * (1.0 - up) - 0.07 * drag - 1.0 * sink, flex=-24.0 * (1.0 - shut) + 22.0 * shut,
                     grip=-34.0 * (1.0 - shut) + 52.0 * shut + 8.0 * over - 30.0 * sink,
                     scale=max(0.02, min(1.0, f / 1.0) * (1.0 - smooth((f - 20) / 4.0))))
        b = pb["dirt"]
        b.scale = (0.75 + 0.3 * smooth(f / 3.0), max(0.03, smooth(f / 1.5) * (1.0 - smooth((f - 18) / 6.0))), 0.75 + 0.3 * smooth(f / 3.0))
        b.location = arm_space_loc(b, (0, 0, 0.07 * math.sin(math.pi * min(f / 7.0, 1.0)) - 0.02))
        for i, (d, reach, vz, r) in enumerate(fly):         # clods thrown out and up, tumbling, gone as they land
            t = min(max((f - (i % 2)) / 12.0, 0.0), 1.0)
            b = pb["clod%d" % i]
            b.location = arm_space_loc(b, tuple(d * (reach * t) + Vector((0, 0, vz * t * (1.0 - t) * 1.7))))
            b.rotation_quaternion = arm_space_quat(b, (d.y, -d.x, 0), -400 * t)
            b.scale = (max(0.02, smooth(t / 0.1) * (1.0 - smooth((t - 0.78) / 0.22))),) * 3
        key_pose(rig, f)
    bpy.context.scene.frame_set(0)


STRIKE_PREVIEW = {"frames": [1, 2, 4, 12, 20], "dist": 4.6, "target": (0, 0, 0.55)}
