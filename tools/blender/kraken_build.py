"""Builds the Kraken (footprint "fan5": [0,0] the hub, with [-1,0], [0,-1], [1,-1], [1,0] fanned round its front and
right), the Tide's tier-3 creature: tentacles seize and crush up to 3 enemies at once (GameData.STRIKES "erupt").

    python tools/blender/build.py kraken --out <preview dir>

One great dark sinkhole pool covers the footprint, rimmed with broken rock, and the kraken rises from it at the hub: a
bulbous crimson mantle with a war-paint band in the team's color, ice-glowing eyes under heavy brows and a hooked beak
(the Head: it turns to watch its prey). Its six arms break the water round it: three arch out over the pool and lie
across the rim of an outer hex each, two rear up in hooks between them, and one is coiled round the mast of the ship it
dragged down, whose bow lies aground on the far hex under a torn sail in the team's color.
Clips: idle (the body heaves in the water, the arms slither and curl, the sail flaps, flotsam bobs), fire (the arms rear
up and whip down, the mast is wrenched). build_strike(): what the game plays under each enemy it seizes: an arm bursts
out of the ground in a ring of spray, arches over and crushes it (the blow lands 0.25 s in), squeezes, and slides back.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "tide_beasts_common.py"), encoding="utf-8").read())

TID = "kraken"
CELLS = [(0, 0), (-1, 0), (0, -1), (1, -1), (1, 0)]
MID = footprint_mid(CELLS)
H = hex_to_world(0, 0, MID)
TOP = 0.34
W = TOP + 0.05                  # the pool's surface
ZB = TOP + 0.13                 # the top of the bank round it
K = Vector((H.x + 0.1, H.y + 0.18, 0.0))        # where the kraken rises: the hub, a step toward the pool's middle
BODY = "red:0.25:0.95"
PALE = "salmon"
SUCKER = "cream:0.1:0.7"
ICE = "glow:0.2,0.85,1.0,0.65"
EYE = "glow:0.3,0.95,1.0,1.0"
MANTLE_RED = "red:0.42:1.0"


def _margin(a):
    return 0.38 if 172.0 <= a <= 308.0 else 0.5


RAW = tb_star_pool(CELLS, K, _margin, 5.0)


def RP(a):
    """How far the pool reaches from the kraken toward angle a (degrees)."""
    a = a % 360.0
    i = int(a // 5.0)
    f = (a - i * 5.0) / 5.0
    r0, r1 = (RAW[i] - K).length, (RAW[(i + 1) % len(RAW)] - K).length
    return r0 + (r1 - r0) * f


def pol(a, r, z=0.0):
    return Vector((K.x + math.cos(math.radians(a)) * r, K.y + math.sin(math.radians(a)) * r, z))


# ---- the wreck's bow on the far hex, and its mast
HULL = dict(length=3.0, beam=0.52, depth=0.5)
HULL_M = tb_place((-0.5, 1.42, W - 0.14), yaw=-14, pitch=18, roll=12, origin=(0, 2.1, 0))
F0 = HULL_M @ Vector((0, 1.75, 0.06))
MD = Vector((0.07, -0.15, 1.0)).normalized()
MAST_LEN = 2.5
F1 = F0 + MD * MAST_LEN
YARD_AT = 2.05
YD = Vector((1.0, 0.12, -0.13)).normalized()


# ---- the arms: their shapes at rest, and the shapes they move between
def _drape(a, side, h, rb=1.05, lift=0.0, squash=1.0):
    R = RP(a)
    hh = h * squash
    tip = [pol(a + side * 5, R + 0.2, ZB + 0.15), pol(a + side * 10, R + 0.16, ZB + 0.1), pol(a + side * 13, R - 0.06, ZB + 0.1),
           pol(a + side * 11, R - 0.2, ZB + 0.12)]
    if lift > 0.0:
        tip = [pol(a + side * 5, R + 0.18, ZB + 0.15 + 0.2 * lift), pol(a + side * 9, R + 0.14, ZB + 0.1 + 0.45 * lift),
               pol(a + side * 10, R - 0.06, ZB + 0.1 + 0.5 * lift), pol(a + side * 8, R - 0.16, ZB + 0.12 + 0.3 * lift)]
    return [pol(a, rb, W - 0.4), pol(a, rb + 0.03, W + 0.38), pol(a - side * 1, rb + 0.26, W + hh * 0.8),
            pol(a - side * 2, (rb + R) * 0.5 + 0.08 + (1 - squash) * 0.5, W + hh), pol(a - side * 1, R - 0.45, W + hh * 0.74),
            pol(a, R, ZB + 0.36)] + tip


def _drape_rear(a, rb=1.05):
    return [pol(a, rb, W - 0.4), pol(a, rb + 0.05, W + 0.7), pol(a, rb + 0.14, W + 1.5), pol(a, rb + 0.12, W + 2.2), pol(a, rb - 0.12, W + 2.75),
            pol(a, rb - 0.5, W + 2.95), pol(a, rb - 0.72, W + 2.62), pol(a, rb - 0.6, W + 2.3)]


def _hook(a, h, rb=1.2, twist=0.0, open_=0.0):
    pts = [pol(a, rb, W - 0.4), pol(a, rb + 0.02, W + 0.42), pol(a + twist * 0.3, rb + 0.12, W + h * 0.52), pol(a + twist * 0.6, rb + 0.3, W + h * 0.82),
           pol(a + twist, rb + 0.56, W + h)]
    if open_ > 0.0:
        return pts + [pol(a + twist * 1.2, rb + 0.95, W + h * 1.0), pol(a + twist * 1.3, rb + 1.22, W + h * 0.88), pol(a + twist * 1.3, rb + 1.36, W + h * 0.7),
                      pol(a + twist * 1.3, rb + 1.36, W + h * 0.55)]
    return pts + [pol(a + twist * 1.3, rb + 0.84, W + h * 0.95), pol(a + twist * 1.5, rb + 0.92, W + h * 0.78), pol(a + twist * 1.5, rb + 0.76, W + h * 0.69),
                  pol(a + twist * 1.4, rb + 0.62, W + h * 0.75)]


def _hook_rear(a, rb=1.2):
    return [pol(a, rb, W - 0.4), pol(a, rb, W + 0.6), pol(a, rb - 0.02, W + 1.4), pol(a, rb - 0.12, W + 2.1), pol(a, rb - 0.4, W + 2.7),
            pol(a, rb - 0.75, W + 2.92), pol(a, rb - 0.95, W + 2.7)]


def _hook_slam(a, rb=1.2):
    return [pol(a, rb, W - 0.4), pol(a, rb + 0.1, W + 0.5), pol(a, rb + 0.42, W + 1.0), pol(a, rb + 0.86, W + 0.9), pol(a, rb + 1.08, W + 0.52),
            pol(a + 6, rb + 1.2, W + 0.42), pol(a + 14, rb + 1.12, W + 0.5), pol(a + 16, rb + 0.95, W + 0.62), pol(a + 12, rb + 0.9, W + 0.8)]


def _mast_arm():
    """The arm that holds the mast: up out of the pool, then coiled round it."""
    u = K - F0
    u = (u - MD * u.dot(MD)).normalized()
    v = MD.cross(u)
    pts = [pol(110, 1.12, W - 0.4), pol(109, 1.14, W + 0.32)]
    n = 15
    for i in range(-1, n + 1):
        t = i / float(n)
        th = math.radians(270.0 - 630.0 * t)
        h = 0.72 + 0.86 * t
        rr = 0.085 + (0.18 - 0.12 * max(t, 0.0)) * 0.95 + (0.12 if i < 0 else 0.0)
        pts.append(F0 + MD * h + (u * math.cos(th) + v * math.sin(th)) * rr)
    pts += [pts[-1] + MD * 0.1 - v * 0.14 + u * 0.05, pts[-1] + MD * 0.24 - v * 0.2 + u * 0.14]
    return pts


TENT = [dict(name="t0", kind="drape", a=155.0, side=1, h=1.4, r0=0.27, r1=0.05, nb=9),
        dict(name="t1", kind="mast", a=110.0, r0=0.24, r1=0.045, nb=10),
        dict(name="t2", kind="drape", a=25.0, side=-1, h=1.3, r0=0.27, r1=0.05, nb=9),
        dict(name="t3", kind="drape", a=325.0, side=-1, h=1.12, r0=0.26, r1=0.05, nb=9),
        dict(name="t4", kind="hook", a=122.0, h=1.9, twist=8.0, r0=0.23, r1=0.045, nb=8),
        dict(name="t5", kind="hook", a=58.0, h=1.58, twist=-10.0, r0=0.22, r1=0.045, nb=8)]
for _t in TENT:
    if _t["kind"] == "drape":
        _t["ctrl"] = _drape(_t["a"], _t["side"], _t["h"])
    elif _t["kind"] == "hook":
        _t["ctrl"] = _hook(_t["a"], _t["h"], twist=_t["twist"])
    else:
        _t["ctrl"] = _mast_arm()


def _shape(ctrl, nb):
    return tb_even(tb_curve(ctrl, 60), nb + 1)


def build_base():
    col = collection("Kraken")
    root = empty("Kraken", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    rnd = random.Random(97)
    k = Kit()
    # ---- the sinkhole: a bank of wet sand over the whole footprint, the pool cut out of it, the water darker toward the deep
    flat = tb_shore(CELLS, 0.2, rnd, step=0.3, jitter=0.03, rounds=2)
    pool = tb_wobble(tb_smooth(tb_resample(RAW, 0.25), 2), rnd, 0.02)
    bm = bmesh.new()
    tb_plate(bm, flat, [pool], ZB, z_skirt=T - 0.02, flare=0.07, z_hole=T, hole_flare=0.08)
    tb_shore_obj("Bank", bm, col, root, top=0.55)

    def ring_in(d, lo, hi=99.0):
        out = []
        for p in pool:
            v = p - K
            out.append(K + v.normalized() * min(max(v.length - d, lo), hi))
        return out
    tb_water("Pool", col, root, [tb_offset(pool, 0.05), ring_in(0.3, 0.6), ring_in(0.78, 0.45, 1.7)], W, [0.52, 0.72, 0.92])
    # ---- its broken rim: boulders all the way round (small ones behind the kraken, where the bank is narrow), tall shards
    hull_mid = HULL_M @ Vector((0, 2.2, 0))

    def ang(q):
        return math.degrees(math.atan2(q.y - K.y, q.x - K.x)) % 360.0

    def in_hull(q):
        return (Vector((q.x, q.y, 0)) - Vector((hull_mid.x, hull_mid.y, 0))).length < 0.62
    back = lambda q: 176.0 <= ang(q) <= 304.0
    tb_rim(k["stone2:0.15:0.9"], rnd, pool, ZB - 0.05, r=(0.15, 0.27), gap=0.36, out=0.13, skip=lambda q: back(q) or in_hull(q), n=11)
    tb_rim(k["stone2:0.2:0.95"], rnd, pool, ZB - 0.04, r=(0.1, 0.15), gap=0.25, out=0.07, skip=lambda q: not back(q), n=9)
    for a, dr, n in ((60, 0.34, 3), (120, 0.34, 3), (2, 0.26, 2), (174, 0.5, 2), (305, 0.3, 2)):
        c = pol(a, RP(a) + dr)
        for j in range(n):
            p = c + Vector((rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.2), 0))
            out = (p - K).normalized()
            hgt = rnd.uniform(0.45, 0.95) * (1.0 if j == 0 else 0.7)
            bm_crystal(k["stone2:0.1:0.85"], (p.x, p.y, ZB - 0.05), (p.x + out.x * hgt * 0.3, p.y + out.y * hgt * 0.3, ZB + hgt), rnd.uniform(0.15, 0.22),
                       n=5, shoulder=0.55, foot=1.0)
    k.emit("Rim", col, root, vary=0.09, seed=4)
    # corals and weed on the headlands between the lobes, barnacles on the rocks
    for a, dr, key, h in ((64, 0.5, "salmon:0.05:0.75", 0.62), (116, 0.52, "orange:0.05:0.7", 0.56), (171, 0.75, "salmon:0.05:0.75", 0.5),
                          (356, 0.42, "orange:0.05:0.7", 0.46)):
        p = pol(a, RP(a) + dr, ZB - 0.03)
        tb_coral(k[key], rnd, p, h=h, r=0.065, depth=2)
    tb_tube_coral(k, rnd, pol(128, RP(128) + 0.3, ZB - 0.02), n=4, key="orange:0.1:0.7")
    tb_tube_coral(k, rnd, pol(50, RP(50) + 0.3, ZB - 0.02), n=3, key="salmon:0.1:0.7")
    for a, dr in ((70, 0.22), (110, 0.25), (168, 0.5), (300, 0.3), (345, 0.3)):
        tb_weed(k["teal:0.2:0.9"], rnd, pol(a, RP(a) + dr, ZB - 0.02), h=0.45, n=3)
    tb_starfish(k["orange:0.15:0.7"], pol(182, RP(182) + 0.42, ZB + 0.005), r=0.15, yaw=25, h=0.04)
    for a in (200, 236, 262, 290, 14, 140):
        tb_barnacle(k, pol(a, RP(a) + 0.12, ZB + 0.12), 0.045)
    k.emit("Rim_Life", col, root)
    # ---- the wreck: the bow of the ship it dragged down, aground on the far hex; a piece of her side on the right
    part = Kit()
    tb_hull(part, rnd, t0=0.45, t1=1.0, **HULL)
    tb_merge(k, part, HULL_M)
    tb_hull(part, rnd, t0=0.08, t1=0.4, ribs=(0.16, 0.26, 0.34), deck=None, **HULL)
    c = pol(353, RP(353) + 0.1, W - 0.02)
    tb_merge(k, part, tb_place(c, yaw=62, pitch=-6, roll=64, origin=(0, 0.72, 0.1)))
    k.emit("Wreck", col, root, vary=0.08, seed=7)
    empty("Head", col, root, (K.x, K.y, W), 0.5, "SINGLE_ARROW")
    return root


# ---- the mantle, in the head's space (+Y forward, the water's surface at z = 0)
MANTLE = [  # y, z, half width, half depth, tilt (degrees) of each section along its spine, from under the water to the crown
    (0.00, -0.3, 0.48, 0.46, 0), (0.02, 0.08, 0.55, 0.51, 0), (0.03, 0.40, 0.60, 0.55, 0), (0.00, 0.68, 0.64, 0.61, 8),
    (-0.07, 0.98, 0.77, 0.75, 16), (-0.18, 1.30, 0.83, 0.81, 24), (-0.33, 1.60, 0.74, 0.72, 32), (-0.48, 1.84, 0.53, 0.52, 40),
    (-0.58, 1.97, 0.27, 0.27, 46)]
CROWN = (0, -0.64, 2.04)


def _mrow(u):
    i = min(int(u), len(MANTLE) - 2)
    f = u - i
    return tuple(MANTLE[i][q] + (MANTLE[i + 1][q] - MANTLE[i][q]) * f for q in range(5))


def _mring(row, grow=0.0, n=12):
    y, z, rx, ry, tilt = row
    t = math.radians(tilt)
    return oval((0, y, z), (1, 0, 0), (0, math.cos(t), math.sin(t)), rx + grow, ry + grow, n, power=2.2, phase=0.5)


def _mpoint(u, a, lift=0.0):
    """A point on the mantle: u along its spine (section numbers), a round it (degrees: 90 the front, 270 the back)."""
    y, z, rx, ry, tilt = _mrow(u)
    t, ar = math.radians(tilt), math.radians(a)
    ca, sa = math.cos(ar), math.sin(ar)
    e = 2.0 / 2.2
    px, py = math.copysign(abs(ca) ** e, ca) * (rx + lift), math.copysign(abs(sa) ** e, sa) * (ry + lift)
    return Vector((px, y + py * math.cos(t), z + py * math.sin(t)))


def _mnormal(u, a):
    y, z, rx, ry, tilt = _mrow(u)
    return (_mpoint(u, a) - Vector((0, y, z))).normalized()


def _rot_to(nrm):
    return tuple(math.degrees(x) for x in Vector((0, 0, 1)).rotation_difference(Vector(nrm).normalized()).to_euler())


def build_head():
    col = collection("Kraken")
    root = bpy.data.objects["Kraken"]
    head = bpy.data.objects["Head"]
    rnd = random.Random(3)
    k = Kit()
    # ---- the mantle: one loft leaning back; a pale mask round the beak, the war-paint band between cream lines
    bm_loft(k[MANTLE_RED], [_mring(r) for r in MANTLE], tip1=CROWN)
    mantle = k.emit("Head_Mantle", col, head)[0]
    c5, c6 = Vector((0, MANTLE[5][0], MANTLE[5][1])), Vector((0, MANTLE[6][0], MANTLE[6][1]))
    ax = c6 - c5
    paint_faces(mantle, "team", lambda c, n: 0.0 < (c - c5).dot(ax) / ax.length_squared < 1.0, team=True, lo=0.1, hi=0.6)
    paint_faces(mantle, PALE, lambda c, n: c.z < 0.42 and n.y > 0.3, lo=0.25, hi=0.85)
    c7, c8 = Vector((0, MANTLE[7][0], MANTLE[7][1])), Vector((0, MANTLE[8][0], MANTLE[8][1]))
    paint_faces(mantle, "red", lambda c, n: (c - c7).dot(c8 - c7) > 0.0, lo=0.75, hi=1.0)
    # a fin on either side of the crown
    for sx, a in ((1, 338), (-1, 202)):
        b0, b1 = _mpoint(5.45, a, -0.03), _mpoint(7.05, a, -0.03)
        out = _mnormal(6.2, a)
        tips = []
        for j, ln in enumerate((0.26, 0.42, 0.43, 0.28)):
            t = 0.08 + 0.84 * j / 3.0
            tips.append(b0.lerp(b1, t) + out * ln + Vector((0, -0.1 - 0.1 * j, 0.06 * j)))
        tb_fin(k["salmon:0.1:0.8"], b0, b1, tips, th=0.035, notch=0.6)
    for u in (5.0, 6.0):
        bm_loft(k["cream:0.05:0.5"], [_mring(_mrow(u + d), 0.014) for d in (-0.07, 0.0, 0.07)], cap0=False, cap1=False)
    # warts, and spots that glow like the deep
    for u, a, r in ((6.7, 250, 0.16), (6.9, 320, 0.13), (7.3, 200, 0.11), (4.4, 215, 0.15), (4.3, 300, 0.17), (4.5, 255, 0.12), (4.2, 350, 0.13),
                    (4.2, 190, 0.12), (3.6, 20, 0.1), (3.6, 160, 0.1)):
        nz = _mnormal(u, a)
        bm_ellipsoid(k["salmon:0.35:0.95"], tuple(_mpoint(u, a, -0.02)), (r, r * 0.8, r * 0.34), rot=_rot_to(nz), u=6, v=4)
    for u, a, r in ((6.45, 232, 0.055), (6.45, 270, 0.07), (6.45, 308, 0.055), (7.4, 270, 0.06), (7.15, 245, 0.045), (7.15, 295, 0.045),
                    (6.6, 180, 0.05), (6.6, 0, 0.05), (4.6, 235, 0.05), (4.6, 270, 0.06), (4.6, 305, 0.05)):
        nz = _mnormal(u, a)
        bm_ellipsoid(k[ICE], tuple(_mpoint(u, a, 0.004)), (r, r, r * 0.3), rot=_rot_to(nz), u=6, v=3)
    # ---- the face: deep sockets, glowing eyes with slit pupils, heavy brows drawn down in the middle, a hooked beak
    for sx in (-1, 1):
        a = 90 - sx * 43
        c = _mpoint(2.42, a, -0.05)
        yaw = math.degrees(math.atan2(c.y, c.x)) - 90.0
        out = Vector((c.x, c.y, 0)).normalized()
        bm_ellipsoid(k["black:0.3:0.8"], tuple(c), (0.2, 0.1, 0.17), rot=(0, 0, yaw), u=8, v=5)
        bm_ellipsoid(k[EYE], tuple(c + out * 0.05), (0.145, 0.075, 0.115), rot=(0, 0, yaw), u=8, v=5)
        bm_box(k["black:0.2:0.5"], (0.034, 0.03, 0.17), tuple(c + out * 0.118), (0, 0, yaw))
        bm_tube(k["red:0.45:1.0"], [_mpoint(2.72, 90 - sx * 13, 0.03), _mpoint(3.02, 90 - sx * 30, 0.07), _mpoint(3.22, 90 - sx * 52, 0.08),
                                    _mpoint(3.05, 90 - sx * 76, 0.03)], [0.07, 0.1, 0.095, 0.05], n=6)
    bm_tube(k["sand:0.3:1.0"], [(0, 0.36, 0.31), (0, 0.6, 0.35), (0, 0.8, 0.28), (0, 0.9, 0.13)], [0.2, 0.17, 0.115, 0.06], n=7, squash=0.72)
    bm_tube(k["black:0.3:0.75"], [(0, 0.885, 0.17), (0, 0.905, 0.08), (0, 0.86, -0.05)], [0.07, 0.05, 0.0], n=7, squash=0.72)
    bm_tube(k["sand:0.5:1.0"], [(0, 0.36, 0.03), (0, 0.58, -0.03), (0, 0.72, 0.0), (0, 0.79, 0.1)], [0.17, 0.14, 0.08, 0.0], n=7, squash=0.75)
    bm_ellipsoid(k["black:0.3:0.7"], (0, 0.52, 0.15), (0.12, 0.14, 0.07), u=6, v=4)
    k.emit("Head_Face", col, head)
    empty("Muzzle", col, head, (0, 0.85, 0.2), 0.25, "SPHERE")

    # ---- the rig (under the root: the arms do not turn with the head)
    bones = {"root": ((0, 0, 0), (0, 0, 0.2), None),
             "swell": ((K.x, K.y, W - 0.42), (K.x, K.y, W - 0.1), "root"),
             "rip.1": ((K.x, K.y, W), (K.x, K.y, W + 0.2), "root"), "rip.2": ((K.x, K.y, W), (K.x, K.y, W + 0.2), "root"),
             "mast": (tuple(F0), tuple(F1), "root")}
    yard0 = F0 + MD * YARD_AT - YD * 0.64
    flag_bones(bones, "sail", yard0, YD, 1.28, segs=3, parent="mast")
    BOB = [pol(20, 1.86, W), pol(147, 1.95, W)]
    for i, p in enumerate(BOB):
        bones["bob.%d" % (i + 1)] = (tuple(p), tuple(p + Vector((0, 0, 0.2))), "root")
    parts = []
    for t in TENT:
        d = pol(t["a"], 1.0) - K
        if t["kind"] == "mast":
            bpts, frames = tb_tentacle(k, t["ctrl"], t["r0"], t["r1"], bones=t["nb"], rings=36, up=tuple(-d), body=BODY, sucker=SUCKER, discs=(1, 9))
            names = tb_chain(bones, t["name"], bpts[:4]) + ["mast"]
        else:
            bpts, frames = tb_tentacle(k, t["ctrl"], t["r0"], t["r1"], bones=t["nb"], up=tuple(-d), body=BODY, sucker=SUCKER)
            names = tb_chain(bones, t["name"], bpts)
        t["bpts"] = bpts
        parts.append((t, k.parts, names, frames))
        k.parts = {}
    rig = make_rig(col, root, bones)
    for t, geo, names, frames in parts:
        k.parts = geo
        objs = k.emit("Arm_" + t["name"], col, rig=rig, bones=names)
        body = objs[0]
        if t["kind"] == "mast":
            def pale(c, n):
                q = F0 + MD * (c - F0).dot(MD)
                v = q - c
                return v.length < 0.52 and (c - F0).dot(MD) > 0.6 and n.dot(v.normalized()) > 0.35
            paint_faces(body, PALE, pale, lo=0.15, hi=0.75)
            tb_paint_span(body, frames, PALE, (0, 10), lo=0.15, hi=0.75, side=-1.0, cos_min=0.5)
        else:
            m = len(frames) - 1
            b0 = int(m * 0.36)
            tb_paint_span(body, frames, "team", (b0, b0 + 1), team=True, lo=0.1, hi=0.6)
            tb_paint_side(body, frames, PALE, side=-1.0, cos_min=0.5, lo=0.15, hi=0.75)
    # the arms' roots, just breaking the water round the mantle: they heave as it breathes
    for t in TENT:
        rb = (t["ctrl"][0] - K).length
        bm_tube(k[BODY], [pol(t["a"], 0.36, W - 0.14), pol(t["a"], (0.36 + rb) * 0.5, W - 0.13), pol(t["a"], rb, W - 0.22)],
                [0.3, 0.29, t["r0"] * 1.02], n=8, phase=0.5)
    k.emit("Arm_Roots", col, rig=rig, bone="swell")
    # foam: rings spreading from the body (two sets, one after the other), streaks where each arm breaks the surface
    for i, arcs in enumerate((((8, 50, 1.42), (66, 112, 1.5), (128, 162, 1.4), (-30, -6, 1.46)), ((20, 62, 1.62), (80, 124, 1.56), (136, 168, 1.64), (-36, -12, 1.6)))):
        for a0, a1, r in arcs:
            tb_foam(k["white:0.0:0.25"], (K.x, K.y, 0), r, a0, a1, w=0.07, z=W + 0.012)
        k.emit("Foam_Ring%d" % (i + 1), col, rig=rig, bone="rip.%d" % (i + 1))
    for t in TENT:
        p = t["ctrl"][0]
        for a0 in (20, 150, 260):
            tb_foam(k["white:0.0:0.25"], (p.x, p.y, 0), t["r0"] + 0.1, a0 + t["a"], a0 + t["a"] + 80, w=0.06, z=W + 0.012)
    for a0, a1 in ((200, 262), (278, 340), (30, 80), (110, 160)):
        tb_foam(k["white:0.0:0.25"], (K.x, K.y, 0), 0.66, a0, a1, w=0.06, z=W + 0.012)
    k.emit("Foam", col, root)
    # ---- the mast it holds, the yard and what is left of the sail; flotsam bobbing in the pool
    tb_spar(k, rnd, F0 - MD * 0.1, F1, r0=0.095, r1=0.07)
    ym = F0 + MD * YARD_AT
    bm_tube(k["wood_dark:0.3:0.9"], [ym - YD * 0.68, ym, ym + YD * 0.68], [0.045, 0.055, 0.045], n=6)
    bm_tube(k["sand:0.3:0.7"], [ym - MD * 0.07, ym + MD * 0.07], 0.105, n=7)
    k.emit("Mast", col, rig=rig, bone="mast")
    tb_rag(k["team!:0.1:0.75"], yard0, yard0 + YD * 1.28, (0.78, 0.92, 0.34, 0.22, 0.3, 0.84, 0.62), rows=4, billow=(0.02, -0.13, 0))
    k.emit("Sail", col, rig=rig, bones=["sail.1", "sail.2", "sail.3"])
    for i, p in enumerate(BOB):
        rk = random.Random(20 + i)
        a = rk.uniform(0, 3.14)
        tb_keg(k, (p.x, p.y, W + 0.03), (math.cos(a), math.sin(a), 0.12))
        for j in range(3):
            b = rk.uniform(0, 3.14)
            q = p + Vector((rk.uniform(-0.45, 0.45), rk.uniform(-0.4, 0.4), 0))
            bm_box(k["wood:0.3:0.85"], (rk.uniform(0.4, 0.62), 0.11, 0.035), (q.x, q.y, W + 0.012), (rk.uniform(-4, 4), rk.uniform(-4, 4), math.degrees(b)))
        k.emit("Flotsam%d" % (i + 1), col, rig=rig, bone="bob.%d" % (i + 1), vary=0.06)
    return rig


IDLE_LEN = 96
FIRE_LEN = 24
_SHAPES = {}


def _targets():
    """Each arm's other shapes, as turns from its rest shape: (curl, rear, slam)."""
    if _SHAPES:
        return _SHAPES
    for t in TENT:
        nb, rest = t["nb"], t.get("bpts")
        if t["kind"] == "drape":
            sh = (_drape(t["a"], t["side"], t["h"], lift=1.0), _drape_rear(t["a"]), _drape(t["a"], t["side"], t["h"], squash=0.72))
        elif t["kind"] == "hook":
            sh = (_hook(t["a"], t["h"], twist=t["twist"], open_=1.0), _hook_rear(t["a"]), _hook_slam(t["a"]))
        else:
            continue
        _SHAPES[t["name"]] = tuple(tb_turns(rest, _shape(s, nb)) for s in sh)
    return _SHAPES


def pose(rig, ph=0.0, f=None):
    """ph: where the idle is in its loop (0 .. 2 pi); f: the frame of the fire clip (None while idling)."""
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    sh = _targets()
    fire = f is not None
    br = math.sin(ph * 2)
    hit = 0.0
    for i, t in enumerate(TENT):
        name, nb = t["name"], t["nb"]
        d = (pol(t["a"], 1.0) - K).normalized()
        side = Vector((-d.y, d.x, 0))
        if t["kind"] == "mast":
            wr = 0.0
            if fire:
                wr = math.sin(f * 1.25) * smooth(f / 3.0) * (1 - smooth((f - 14) / 8.0))
            sway = 1.2 * math.sin(ph) + 6.0 * wr
            pb["mast"].rotation_quaternion = q(pb["mast"], (0, 1, 0), sway) @ q(pb["mast"], (1, 0, 0), 0.8 * math.sin(ph * 2 + 1.0) - 3.0 * abs(wr))
            for j in range(3):
                pb["%s.%d" % (name, j + 1)].rotation_quaternion = q(pb["%s.%d" % (name, j + 1)], (0, 1, 0), (0.6 * math.sin(ph * 2 + j) + 2.0 * wr) * (j + 1) / 3.0)
            continue
        curl, rear, slam = sh[name]
        g = f - (i % 3) * 1.2 if fire else 0.0
        w_rear = smooth(g / 5.0) * (1 - smooth((g - 5.5) / 2.5)) if fire else 0.0
        w_slam = smooth((g - 5.5) / 2.5) * (1 - smooth((g - 10) / 9.0)) if fire else 0.0
        hit = max(hit, w_slam)
        if t["kind"] == "drape":
            w_curl = 0.5 - 0.5 * math.cos(ph + i * 1.3)
            wave = tb_wave(nb, (0, 0, 1), 2.6, ph * 2 + i * 2.1, step=0.65, grow=2.6)
        else:
            w_curl = 0.32 - 0.32 * math.cos(ph + i * 2.0)
            wave = tb_wave(nb, tuple(side), 3.2, ph * 2 + i * 1.7, step=0.6, grow=2.2)
        turns = tb_mix(None, curl, w_curl * (1 - w_rear) * (1 - w_slam))
        turns = tb_mix(turns, rear, w_rear)
        turns = tb_mix(turns, slam, w_slam)
        tb_pose_chain(rig, name, turns, extra=wave)
    s = 0.5 + 0.5 * br
    pb["swell"].scale = (1.0 + 0.03 * s + 0.05 * hit, 1.0 + 0.03 * s + 0.05 * hit, 1.0 + 0.3 * s + 0.5 * hit)
    for i in (1, 2):
        p = (ph / (2 * math.pi) * 2 + 0.5 * (i - 1)) % 1.0
        b = pb["rip.%d" % i]
        sc = 0.84 + 0.42 * p
        b.scale = (sc, sc, 1.0)
        b.location = arm_space_loc(b, (0, 0, -0.05 * (1 - smooth(p / 0.12)) - 0.05 * smooth((p - 0.72) / 0.2)))
    wave_flag(rig, "sail", ph / (2 * math.pi) * 2, amp=0.55 + (0.5 * hit if fire else 0.0), segs=3, axis=tuple(YD))
    for i in (1, 2):
        b = pb["bob.%d" % i]
        b.location = arm_space_loc(b, (0, 0, 0.022 * math.sin(ph * 2 + i * 2.0) + 0.03 * hit))
        b.rotation_quaternion = q(b, (1, 0, 0), 4 * math.sin(ph * 2 + i)) @ q(b, (0, 1, 0), 3 * math.sin(ph + i * 2))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(rig, ph=2 * math.pi * f / IDLE_LEN)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        pose(rig, ph=0.0, f=f)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.1, 0.9), "dist": 11.5, "yaw": 160, "pitch": 24, "anim_target": (0, 0.2, 1.2), "anim_dist": 8.2,
           "frames": [("idle", 0), ("idle", 24), ("fire", 5), ("fire", 8), ("fire", 12)],
           "extra": [{"yaw": 165, "pitch": 4, "dist": 2.3, "target": (K.x, K.y + 0.25, 0.95)},
                     {"yaw": 0, "pitch": 58, "dist": 8.5, "target": (0, 0.1, 0.6)},
                     {"yaw": 222, "pitch": 22, "dist": 5.6, "target": (-0.5, 1.3, 1.3)},
                     {"yaw": 128, "pitch": 26, "dist": 6.0, "target": (1.3, -0.6, 0.8)}]}


def build_all():
    build_base()
    build_head()
    build_anims()


# ================================================================================================ the strike
# What the game plays under an enemy the kraken seizes (Strike, GameData.STRIKES "erupt"): the ground bursts in a ring
# of spray beside it, an arm shoots up, arches over and comes down round the enemy (the blow: 0.25 s in), squeezes, and
# slides back into the hole. The model stands on the enemy's spot on the road; +Y points away from the tower.
STRIKE_LEN = 36
S_BASE = Vector((-0.85, -0.1, 0.0))
S_NB = 9


def _s_pts(kind):
    e = Vector((-S_BASE.x, -S_BASE.y, 0)).normalized()        # from the hole toward the enemy
    s = Vector((-e.y, e.x, 0))
    B = S_BASE
    up = Vector((0, 0, 1))
    if kind == "crush":       # arched over the enemy, the end hooked down round its far side
        return [B - up * 0.6, B + up * 0.55 - e * 0.05, B + up * 1.3 + e * 0.02, B + up * 1.85 + e * 0.4, B + up * 2.0 + e * 0.95,
                B + up * 1.72 + e * 1.42, B + up * 1.2 + e * 1.6, B + up * 0.7 + e * 1.5, B + up * 0.42 + e * 1.22 + s * 0.12, B + up * 0.5 + e * 0.98 + s * 0.2]
    if kind == "tight":       # the squeeze: the hook drawn in and down
        return [B - up * 0.6, B + up * 0.5 - e * 0.02, B + up * 1.15 + e * 0.1, B + up * 1.6 + e * 0.48, B + up * 1.68 + e * 0.98,
                B + up * 1.4 + e * 1.36, B + up * 0.95 + e * 1.44, B + up * 0.55 + e * 1.26, B + up * 0.4 + e * 0.98 + s * 0.14, B + up * 0.55 + e * 0.8 + s * 0.22]
    # "up": shot straight out of the ground, the end curled back away from the enemy
    return [B - up * 0.6, B + up * 0.6, B + up * 1.3, B + up * 1.9 - e * 0.02, B + up * 2.4 - e * 0.3, B + up * 2.55 - e * 0.8, B + up * 2.3 - e * 1.2,
            B + up * 1.9 - e * 1.25, B + up * 1.65 - e * 0.95, B + up * 1.8 - e * 0.68, B + up * 2.05 - e * 0.7]


def build_strike():
    col = collection("Kraken_strike")
    root = empty("Kraken_strike", col, None, (0, 0, 0), 0.5, "ARROWS")
    rnd = random.Random(11)
    e = Vector((-S_BASE.x, -S_BASE.y, 0)).normalized()
    bones = {"root": ((0, 0, 0), (0, 0, 0.2), None),
             "pool": (tuple(S_BASE), tuple(S_BASE + Vector((0, 0, 0.2))), "root"),
             "spray": (tuple(S_BASE), tuple(S_BASE + Vector((0, 0, 0.3))), "root")}
    k = Kit()
    bpts, frames = tb_tentacle(k, _s_pts("crush"), 0.3, 0.06, bones=S_NB, n=8, up=tuple(-e), body=BODY, sucker=SUCKER)
    names = tb_chain(bones, "arm", bpts)
    geo = k.parts
    k.parts = {}
    fly = []
    for i in range(7):
        a = 2 * math.pi * (i + rnd.uniform(-0.2, 0.2)) / 7
        d = Vector((math.cos(a), math.sin(a), 0))
        fly.append((d, rnd.uniform(0.7, 1.15), rnd.uniform(1.6, 2.5), rnd.uniform(0.07, 0.11)))
        bones["drop%d" % i] = (tuple(S_BASE + d * 0.3 + Vector((0, 0, 0.1))), tuple(S_BASE + d * 0.3 + Vector((0, 0, 0.3))), "root")
    rig = make_rig(col, root, bones)
    k.parts = geo
    body = k.emit("Arm", col, rig=rig, bones=names)[0]
    tb_paint_side(body, frames, PALE, side=-1.0, cos_min=0.5, lo=0.15, hi=0.75)
    # the hole it bursts from: a dark pool, foam round it, broken ground tipped up at its edge
    bm_cyl(k["blue:0.55:0.95"], 0.5, 0.56, 0.03, (S_BASE.x, S_BASE.y, 0.012), seg=12)
    for a0 in (10, 130, 250):
        tb_foam(k["white:0.0:0.25"], (S_BASE.x, S_BASE.y, 0), 0.46, a0, a0 + 95, w=0.09, z=0.03)
    for i in range(8):
        a = 2 * math.pi * i / 8 + rnd.uniform(-0.15, 0.15)
        p = S_BASE + Vector((math.cos(a), math.sin(a), 0)) * rnd.uniform(0.56, 0.64)
        bm_boulder(k["stone2:0.2:0.9"], rnd, (p.x, p.y, -0.02), rnd.uniform(0.1, 0.16), squash=(1.2, 0.9, 0.7), n=8)
    k.emit("Pool", col, rig=rig, bone="pool", vary=0.07)
    # the ring of spray: sheets of water thrown up and outward round the hole
    for i in range(10):
        a = 2 * math.pi * i / 10 + rnd.uniform(-0.1, 0.1)
        d = Vector((math.cos(a), math.sin(a), 0))
        p = S_BASE + d * 0.36
        hgt = rnd.uniform(0.6, 1.0)
        bm_crystal(k["sky:0.0:0.55" if i % 2 else "white:0.0:0.3"], (p.x, p.y, 0.0), tuple(p + d * (hgt * 0.5) + Vector((0, 0, hgt))), rnd.uniform(0.1, 0.15),
                   n=4, shoulder=0.35, foot=1.0)
    k.emit("Spray", col, rig=rig, bone="spray")
    for i, (d, reach, vz, r) in enumerate(fly):
        bm_blob(k["sky:0.0:0.5"], rnd, tuple(S_BASE + d * 0.3 + Vector((0, 0, 0.1))), r, jitter=0.1)
        k.emit("Drop%d" % i, col, rig=rig, bone="drop%d" % i)
    up_t = tb_turns(bpts, _shape(_s_pts("up"), S_NB))
    tight_t = tb_turns(bpts, _shape(_s_pts("tight"), S_NB))
    new_action(rig, "strike", STRIKE_LEN)
    pb = rig.pose.bones
    for f in range(STRIKE_LEN + 1):
        rest_pose(rig)
        # out of the ground by frame 4, over and down by 7.5 (the blow), squeezing to 24, then back down the hole
        grow = smooth(f / 4.0) * (1.0 - smooth((f - 26) / 9.0))
        down = smooth((f - 4.5) / 3.0)
        over = 0.22 * math.sin(math.pi * min(max((f - 7.5) / 4.0, 0.0), 1.0))
        squeeze = (0.55 + 0.45 * math.sin((f - 9) * 0.9)) * smooth((f - 9) / 3.0) * (1 - smooth((f - 23) / 4.0))
        leave = smooth((f - 24) / 8.0)
        turns = tb_mix(up_t, None, down)
        turns = tb_mix(turns, tight_t, min(1.0, over + squeeze * 0.9))
        turns = tb_mix(turns, up_t, 0.55 * leave)
        tb_pose_chain(rig, "arm", turns, extra=tb_wave(S_NB, tuple(e), 2.0 * (1 - leave), f * 0.9, step=0.8, grow=2.0))
        b1 = pb["arm.1"]
        b1.scale = (max(grow, 0.02),) * 3
        b1.location = arm_space_loc(b1, (0, 0, -2.2 * (1.0 - grow)))
        pl = pb["pool"]
        s = smooth(f / 2.5) * (1.0 - smooth((f - 30) / 6.0))
        pl.scale = (max(0.02, s * (1.0 + 0.12 * math.sin(math.pi * min(f / 6.0, 1.0)))),) * 2 + (max(0.02, s),)
        sp = pb["spray"]
        t = min(max(f / 9.0, 0.0), 1.0)
        sp.scale = (max(0.02, (0.7 + 0.8 * t) * (1 - smooth((t - 0.75) / 0.25)) * smooth(f / 1.5)),) * 2 + (max(0.02, math.sin(math.pi * t) ** 0.7 * 1.25),)
        for i, (d, reach, vz, r) in enumerate(fly):                  # drops thrown out and up, gone as they land
            t = min(max((f - (i % 3)) / 14.0, 0.0), 1.0)
            b = pb["drop%d" % i]
            b.location = arm_space_loc(b, tuple(d * (reach * t) + Vector((0, 0, vz * t * (1.0 - t) * 1.6))))
            b.scale = (max(0.02, smooth(t / 0.12) * (1.0 - smooth((t - 0.78) / 0.22))),) * 3
        key_pose(rig, f)
    bpy.context.scene.frame_set(0)


STRIKE_PREVIEW = {"frames": [2, 4, 8, 16, 30], "dist": 7.0, "target": (0, 0, 1.0), "yaw": 168, "pitch": 16}
