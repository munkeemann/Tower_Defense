"""Builds the Soul Obelisk (footprint "pair": [0,0] front, [0,1] back), a Bone Legion tower: it rips out a share of a
target's current health with a slow soul-orb every 1.8 s.

    python tools/blender/build.py soul_obelisk --out <preview dir>

One monument. A stepped dais of dark coursed stone spans both cells: its lowest tier covers the pair, a hexagonal
tier rises on the front cell, and on a last square step stands a tall black obelisk, chamfered, its four faces cut with
columns of violet runes, an iron collar at its shoulders and a gilded capstone. Four heavy chains run from the collar
down to skull-topped posts at the hexagonal tier's corners (each hung with a torn team banner), a violet rune circle
is inlaid round its foot, and a team-coloured runner climbs the dais from the back. On the back cell a stone mourner
kneels on the runner facing it, between two urns of soul-fire. Above the tip a soul crystal floats and turns
(Muzzle), shards circling it; three captured soul-wisps orbit the shaft.
The Head (on the obelisk's axis) carries everything that moves, all of it round about the axis: the crystal, the
wisps and five rings of violet light that ripple up the shaft. Clips: idle (the crystal turns and bobs, the wisps
orbit, a faint ripple climbs the runes), fire (the rings flare from bottom to top, the crystal kicks up, flares and
spins a third of a turn, the wisps are dragged round once).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "grave_shrines_common.py"), encoding="utf-8").read())

TID = "soul_obelisk"
CELLS = [(0, 0), (0, 1)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)          # front: the obelisk
B = hex_to_world(0, 1, MID)          # back: the mourner
TOP = 0.34
T = TOP
Z1 = T + 0.14                        # the tiers' tops: both cells, the front hexagon, the obelisk's square step
Z2 = Z1 + 0.14
Z3 = Z2 + 0.14
SB, ST = Z3 + 0.24, Z3 + 1.86        # the shaft's foot and top
HW0, HW1 = 0.23, 0.155               # its half width there
CH = 0.035                           # the corners' chamfer
TIP = ST + 0.3                       # the pyramidion's point: the Head
CRY = 0.34                           # the crystal floats this far over the tip
T2R = 1.2 - 0.3 / 0.866              # the front tier's corner radius (inset 0.3 from the cell)
POSTS = [F + Vector((math.cos(math.radians(a)), math.sin(math.radians(a)), 0)) * 0.75 for a in (60, 120, 240, 300)]
POST_TOP = Z2 + 0.5
COLLAR = ST - 0.17                   # the iron collar's middle
RINGS = [SB + 0.24 + 0.24 * i for i in range(5)]       # the rune rows' heights (and the light rings')
WISPS = ((0.92, 1.5, 1.0), (0.86, 2.0, -1.0), (0.98, 2.5, 1.0))   # (orbit radius, height, direction)
MOURN = Vector((0.0, -0.62, Z1))
RUN_W = 0.42
VIO = (0.5, 0.18, 1.0)              # the runes' and the crystal's violet
PALE = (0.72, 0.5, 1.0)             # wisps, shards, candle flames


def hw(z):
    return HW0 + (HW1 - HW0) * (z - SB) / (ST - SB)


def _yaw_to(dx, dy):
    return math.degrees(math.atan2(-dx, dy))


def _shaft_ring(z, grow=0.0):
    h = hw(z) + grow
    c = CH + grow * 0.4
    pts = [(h, -(h - c)), (h, h - c), (h - c, h), (-(h - c), h), (-h, h - c), (-h, -(h - c)), (-(h - c), -h), (h - c, -h)]
    return [Vector((F.x + x, F.y + y, z)) for x, y in pts]


# rune glyphs: strokes in a box u -0.5..0.5 (across), v 0..1 (up)
GLYPHS = [[((0, 0), (0, 1)), ((0, 0.55), (-0.45, 1)), ((0, 0.55), (0.45, 1))],
          [((0, 0), (0, 1)), ((0, 1), (-0.45, 0.62)), ((0, 1), (0.45, 0.62))],
          [((-0.3, 0), (-0.3, 1)), ((0.3, 0), (0.3, 1)), ((-0.3, 0.68), (0.3, 0.32))],
          [((0, 0), (0.42, 0.5)), ((0.42, 0.5), (0, 1)), ((0, 1), (-0.42, 0.5)), ((-0.42, 0.5), (0, 0))],
          [((-0.25, 0), (-0.25, 1)), ((-0.25, 0.78), (0.32, 0.5)), ((0.32, 0.5), (-0.25, 0.22))],
          [((-0.35, 0), (-0.35, 1)), ((0.35, 0), (0.35, 1)), ((-0.35, 1), (0.35, 0.45)), ((0.35, 1), (-0.35, 0.45))]]


def _runner(bm, pts, w, th):
    """A cloth strip w wide (along X) lying along the (y, z) polyline pts."""
    for (y0, z0), (y1, z1) in zip(pts, pts[1:]):
        d = Vector((0, y1 - y0, z1 - z0))
        n = Vector((0, -d.z, d.y)).normalized()
        bm_beam(bm, (0, y0, z0), (0, y1, z1), w, th, up=tuple(n))


def build_base():
    col = collection("Soul_obelisk")
    root = empty("Soul_obelisk", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(23)
    k = Kit()
    # ---- the dais: a tier over both cells, a hexagonal tier on the front cell, the obelisk's square step
    t1 = outline(CELLS, 0.2)
    t2 = [F + Vector((math.cos(math.radians(60 * i)), math.sin(math.radians(60 * i)), 0)) * T2R for i in range(6)]
    t3 = gs_rect(F.x, F.y, 0.46, 0.46)
    gs_step(k, rnd, t1, T, Z1, stone="stone_dark:0.25:0.85", core="stone_dark:0.5:0.95", block=0.4, th=0.2)
    gs_step(k, rnd, t2, Z1 - 0.02, Z2, stone="stone_dark:0.15:0.75", core="stone_dark:0.5:0.95", block=0.38, th=0.2)
    gs_step(k, rnd, t3, Z2 - 0.02, Z3, stone="stone_dark:0.05:0.6", core="black:0.3:0.7", block=0.32, th=0.18)
    k.emit("Dais", col, root, bevel=0.012, vary=0.08)
    t1_in = outline(CELLS, 0.36)

    def flags1(x, y):
        if not inside(t1_in, x, y) or abs(x) < RUN_W / 2 + 0.03:
            return False
        return not inside(t2, x, y)
    bm_flagstones(k["stone:0.4:0.9"], rnd, flags1, (-1.3, -2.2, 1.3, 2.2), Z1 - 0.012, size=0.26, gap=0.035, keep=0.97)
    t2_in = [F + (p - F) * ((T2R - 0.2) / T2R) for p in t2]
    bm_flagstones(k["stone:0.3:0.8"], rnd, lambda x, y: inside(t2_in, x, y) and not (abs(x - F.x) < 0.5 and abs(y - F.y) < 0.5) and
                  not (abs(x) < RUN_W / 2 + 0.03 and y < F.y), (-1.3, -0.2, 1.3, 2.2), Z2 - 0.012, size=0.24, gap=0.035, keep=0.95)
    k.emit("Paving", col, root, vary=0.1)
    # the rune circle inlaid round the obelisk's step, ticks across it
    sg = k[glow(VIO, 0.75)]
    R = 0.6
    for i in range(24):
        a0, a1 = 2 * math.pi * i / 24 + 0.01, 2 * math.pi * (i + 1) / 24 - 0.01
        p0 = F + Vector((math.cos(a0) * R, math.sin(a0) * R, Z2 + 0.004))
        p1 = F + Vector((math.cos(a1) * R, math.sin(a1) * R, Z2 + 0.004))
        if abs(math.degrees((a0 + a1) / 2) - 270) < 12:
            continue                                            # (under the runner)
        bm_beam(sg, p0, p1, 0.035, 0.02)
        if i % 3 == 0:
            q = F + Vector((math.cos(a0) * (R + 0.07), math.sin(a0) * (R + 0.07), Z2 + 0.004))
            bm_beam(sg, F + Vector((math.cos(a0) * (R - 0.05), math.sin(a0) * (R - 0.05), Z2 + 0.004)), q, 0.03, 0.02)
    k.emit("Rune_Circle", col, root)
    # ---- the obelisk: a moulded base, the chamfered shaft, an iron collar, the pyramidion with a gilded capstone
    bm_box(k["stone_dark:0.1:0.6"], (0.74, 0.74, 0.12), (F.x, F.y, Z3 + 0.06))
    bm_box(k["stone_dark:0.0:0.5"], (0.62, 0.62, 0.12), (F.x, F.y, Z3 + 0.18))
    k.emit("Obelisk_Base", col, root, bevel=0.015, vary=0.05)
    bm_loft(k["black:0.05:0.5"], [_shaft_ring(SB), _shaft_ring((SB + ST) / 2, 0.006), _shaft_ring(ST)])
    tipring = [Vector((F.x + x, F.y + y, ST)) for x, y in ((HW1 + 0.012, -HW1 - 0.012), (HW1 + 0.012, HW1 + 0.012), (-HW1 - 0.012, HW1 + 0.012), (-HW1 - 0.012, -HW1 - 0.012))]
    mid = [Vector((F.x + (p.x - F.x) * 0.3, F.y + (p.y - F.y) * 0.3, TIP - 0.09)) for p in tipring]
    bm_loft(k["black:0.0:0.35"], [tipring, mid])
    k.emit("Obelisk", col, root)
    bm_loft(k["gold:0.1:0.55"], [mid, [p + Vector((0, 0, 0.0)) for p in mid]], tip1=(F.x, F.y, TIP))
    k.emit("Obelisk_Cap", col, root)
    # the faces: a raised border round a panel of five runes each
    bd = k["stone_dark:0.0:0.45"]
    rg = k[glow(VIO, 0.8)]
    for f in range(4):
        a = math.radians(90 * f + 90)
        o = Vector((math.cos(a), math.sin(a), 0))
        rt = Vector((-o.y, o.x, 0))
        nrm = (o * (ST - SB) + Vector((0, 0, HW0 - HW1))).normalized()

        def fp(u, z, lift=0.0):
            return Vector((F.x, F.y, z)) + o * hw(z) + rt * u + nrm * lift
        z0, z1 = SB + 0.08, COLLAR - 0.12
        for s in (-1, 1):
            bm_beam(bd, fp(s * (hw(z0) - 0.055), z0, 0.008), fp(s * (hw(z1) - 0.055), z1, 0.008), 0.04, 0.03, up=tuple(nrm))
        for z in (z0, z1):
            bm_beam(bd, fp(-(hw(z) - 0.035), z, 0.008), fp(hw(z) - 0.035, z, 0.008), 0.04, 0.03, up=tuple(nrm))
        for i, zc in enumerate(RINGS):
            g = GLYPHS[(f * 2 + i * 5 + (i * f) % 3) % len(GLYPHS)]
            gw, gh = 0.15, 0.17
            for (u0, v0), (u1, v1) in g:
                p0 = fp(u0 * gw, zc - gh / 2 + v0 * gh, 0.004)
                p1 = fp(u1 * gw, zc - gh / 2 + v1 * gh, 0.004)
                dd = (p1 - p0).normalized()
                bm_beam(rg, p0 - dd * 0.012, p1 + dd * 0.012, 0.03, 0.02, up=tuple(nrm))
    k.emit("Obelisk_Faces", col, root)
    # the iron collar at the shoulders, lugs and rings at its corners for the chains
    ir = k[IRON]
    h = hw(COLLAR) + 0.025
    for f in range(4):
        a = math.radians(90 * f)
        o = Vector((math.cos(a), math.sin(a), 0))
        rt = Vector((-o.y, o.x, 0))
        c = Vector((F.x, F.y, COLLAR)) + o * h
        bm_beam(ir, c - rt * (h + 0.03), c + rt * (h + 0.03), 0.05, 0.12)
        for s in (-0.5, 0.5):
            bm_box(ir, (0.03, 0.03, 0.03), tuple(c + rt * (s * h) + o * 0.03), (0, 0, math.degrees(a)))
    for p in POSTS:
        d = (p - F).normalized()
        bm_box(ir, (0.09, 0.09, 0.14), (F.x + d.x * (h * 1.414 - 0.02), F.y + d.y * (h * 1.414 - 0.02), COLLAR))
    k.emit("Collar", col, root)
    lug = {}
    for p in POSTS:
        d = (p - F).normalized()
        lug[p.to_tuple()] = Vector((F.x + d.x * (h * 1.414 + 0.05), F.y + d.y * (h * 1.414 + 0.05), COLLAR - 0.02))
        ring(k["iron:0.15:0.8"], tuple(lug[p.to_tuple()]), 0.06, 0.035, -0.015, 0.015, seg=8, axis="Z")
    k.emit("Collar_Rings", col, root)
    # ---- the four posts: square pillars on the hexagonal tier, a skull on each, a torn team banner down its outer face
    for p in POSTS:
        bm_box(k["stone_dark:0.1:0.7"], (0.2, 0.2, POST_TOP - Z2), (p.x, p.y, (Z2 + POST_TOP) / 2), (0, 0, _yaw_to(p.x - F.x, p.y - F.y)))
        bm_box(k["stone_dark:0.0:0.45"], (0.27, 0.27, 0.07), (p.x, p.y, POST_TOP + 0.035), (0, 0, _yaw_to(p.x - F.x, p.y - F.y)))
        bm_box(k["stone_dark:0.0:0.45"], (0.26, 0.26, 0.06), (p.x, p.y, Z2 + 0.03), (0, 0, _yaw_to(p.x - F.x, p.y - F.y)))
    k.emit("Posts", col, root, bevel=0.012, vary=0.06)
    for p in POSTS:
        d = (p - F).normalized()
        gs_skull(k, place((p.x, p.y, POST_TOP + 0.07), yaw=_yaw_to(d.x, d.y), scale=0.24), n=6)
    k.emit("Post_Skulls", col, root, vary=0.05)
    for p in POSTS:                                             # the chains, and the iron ring each is made fast to
        d = (p - F).normalized()
        a = Vector((p.x - d.x * 0.12, p.y - d.y * 0.12, POST_TOP - 0.1))
        ring(k["iron:0.15:0.8"], tuple(a), 0.06, 0.035, -0.015, 0.015, seg=8, axis="Z")
        gs_chain(k[IRON], lug[p.to_tuple()], a, sag=0.07, link=0.12, w=0.075, th=0.03)
    k.emit("Chains", col, root)
    for i, p in enumerate(POSTS):
        d = (p - F).normalized()
        rt = Vector((-d.y, d.x, 0))
        gs_banner(k["team!:0.1:0.75"], tuple(p + d * 0.105 + Vector((0, 0, POST_TOP - 0.04))), tuple(rt), (0, 0, -1), 0.18, 0.4,
                  rnd=random.Random(40 + i), cols=4, rows=3, tatter=0.35)
    k.emit("Post_Banners", col, root)
    # ---- the runner up the dais, gold-edged, and the mourner kneeling on it
    path = [(-1.9, T + 0.012), (-1.875, Z1 + 0.01), (F.y - T2R * 0.866 - 0.015, Z1 + 0.01), (F.y - T2R * 0.866 + 0.01, Z2 + 0.01),
            (F.y - 0.475, Z2 + 0.01), (F.y - 0.455, Z3 + 0.01), (F.y - 0.37, Z3 + 0.01)]
    _runner(k["team!:0.05:0.6"], path, RUN_W, 0.016)
    k.emit("Runner", col, root)
    for s in (-1, 1):
        for (y0, z0), (y1, z1) in zip(path, path[1:]):
            d = Vector((0, y1 - y0, z1 - z0))
            n = Vector((0, -d.z, d.y)).normalized()
            bm_beam(k["gold:0.15:0.55"], Vector((s * (RUN_W / 2 - 0.025), y0, z0)) + n * 0.01, Vector((s * (RUN_W / 2 - 0.025), y1, z1)) + n * 0.01,
                    0.035, 0.012, up=tuple(n))
    k.emit("Runner_Trim", col, root)
    c = MOURN
    st = k["stone:0.12:0.6"]
    rings_ = [oval(c + Vector((0, cy, z)), (1, 0, 0), (0, 1, 0), rx, ry, 10, power=2.2, phase=0.5)
              for z, cy, rx, ry in ((0.0, -0.1, 0.2, 0.27), (0.1, -0.08, 0.2, 0.23), (0.25, -0.03, 0.165, 0.14), (0.4, 0.0, 0.175, 0.13), (0.47, 0.01, 0.15, 0.11))]
    bm_loft(st, rings_, tip1=c + Vector((0, 0.02, 0.5)))
    hood = [oval(c + Vector((0, cy, z)), (1, 0, 0), (0, 1, 0), rx, ry, 10, power=2.2, phase=0.5)
            for z, cy, rx, ry in ((0.42, 0.03, 0.105, 0.105), (0.53, 0.07, 0.125, 0.13), (0.63, 0.06, 0.112, 0.12), (0.7, 0.03, 0.075, 0.085))]
    bm_loft(st, hood, tip1=c + Vector((0, -0.01, 0.76)))
    for sx in (-1, 1):
        bm_tube(st, [c + Vector((sx * 0.15, 0.02, 0.45)), c + Vector((sx * 0.15, 0.12, 0.34)), c + Vector((sx * 0.05, 0.2, 0.37))], [0.062, 0.056, 0.05], n=6)
        bm_box(st, (0.08, 0.07, 0.045), (c.x + sx * 0.075, c.y - 0.36, c.z + 0.022))
    bm_blob(st, rnd, tuple(c + Vector((0, 0.22, 0.39))), 0.058, jitter=0.1)
    k.emit("Mourner", col, root, vary=0.04)
    bm_ellipsoid(k["black:0.4:0.8"], tuple(c + Vector((0, 0.165, 0.555))), (0.07, 0.03, 0.08), u=8, v=5)
    k.emit("Mourner_Face", col, root)
    ob = c + Vector((0, 0.36, 0))                              # his offering: a bowl with a captured soul in it
    gs_lathe(k["stone_dark:0.1:0.6"], tuple(ob), [(0.07, 0.0), (0.05, 0.03), (0.11, 0.08), (0.13, 0.12), (0.11, 0.12), (0.07, 0.07)], n=10, cap0=True, cap1=True)
    k.emit("Offering", col, root)
    bm_ellipsoid(k[glow(PALE, 0.9)], tuple(ob + Vector((0, 0, 0.14))), (0.075, 0.075, 0.07), u=8, v=5)
    for sx in (-1, 1):
        gs_bone(k[BONE], ob + Vector((sx * 0.1, -0.1, 0.02)), ob + Vector((sx * 0.25, 0.08, 0.02)), r=0.022, n=4)
    k.emit("Offering_Soul", col, root)
    # ---- two urns of soul-fire flanking the runner on the back cell, candles along the way
    for sx in (-1, 1):
        u = Vector((sx * 0.6, -1.08, Z1))
        gs_lathe(k["stone_dark:0.1:0.7"], tuple(u), [(0.13, 0.0), (0.09, 0.05), (0.06, 0.16), (0.1, 0.21), (0.17, 0.28), (0.19, 0.36), (0.16, 0.42),
                                                    (0.12, 0.42), (0.11, 0.34)], n=10, cap0=True, cap1=True)
        k.emit("Urn", col, root, vary=0.04)
        gs_flame(k[glow(VIO, 0.85)], tuple(u + Vector((0, 0, 0.33))), h=0.36, r=0.1, rnd=rnd, tongues=3)
        k.emit("Urn_Fire", col, root)
    for (x, y, z, n_) in ((0.36, -0.3, Z1, 3), (-0.36, -0.3, Z1, 2), (0.5, F.y + 0.48, Z2, 3), (-0.52, F.y + 0.4, Z2, 2), (0.3, -1.5, Z1, 2)):
        for j in range(n_):
            a = 2 * math.pi * j / n_ + x
            gs_candle(k, (x + math.cos(a) * 0.055 * (n_ > 1), y + math.sin(a) * 0.055 * (n_ > 1), z), h=0.1 + 0.05 * ((j + 1) % 2), r=0.03,
                      flame=glow(PALE, 0.9))
    k.emit("Candles", col, root)
    head = empty("Head", col, root, (F.x, F.y, TIP), 0.5, "SINGLE_ARROW")
    empty("Muzzle", col, head, (0, 0, CRY), 0.2, "SPHERE")
    return root


BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "crystal": ((0, 0, CRY), (0, 0, CRY + 0.3), "root")}
for _i, (_r, _z, _d) in enumerate(WISPS):
    BONES["orbit.%d" % (_i + 1)] = ((0, 0, _z - TIP), (0, 0, _z - TIP + 0.2), "root")
    BONES["wisp.%d" % (_i + 1)] = ((_r, 0, _z - TIP), (_r, 0, _z - TIP + 0.15), "orbit.%d" % (_i + 1))
for _i, _z in enumerate(RINGS):
    BONES["pulse.%d" % (_i + 1)] = ((0, 0, _z - TIP), (0, 0, _z - TIP + 0.1), "root")


def build_head():
    col = collection("Soul_obelisk")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    rnd = random.Random(5)
    k = Kit()
    # the soul crystal: a long double point, three shards circling it
    c = Vector((0, 0, CRY))
    bm_crystal(k[glow(VIO, 0.9)], c, c + Vector((0, 0, 0.42)), 0.17, n=6, shoulder=0.3, foot=1.0)
    bm_crystal(k[glow(VIO, 0.9)], c, c - Vector((0, 0, 0.28)), 0.17, n=6, shoulder=0.25, foot=1.0)
    for i in range(3):
        a = 2 * math.pi * i / 3
        p = c + Vector((math.cos(a) * 0.29, math.sin(a) * 0.29, 0.04 * (i - 1)))
        bm_crystal(k[glow(PALE, 0.9)], p - Vector((0, 0, 0.07)), p + Vector((math.cos(a) * 0.03, math.sin(a) * 0.03, 0.1)), 0.04, n=4, shoulder=0.5, foot=0.6)
    k.emit("Head_Crystal", col, rig=rig, bone="crystal")
    for i, (r, z, d) in enumerate(WISPS):
        zh = z - TIP
        gs_wisp(k[glow(PALE, 0.8)], (r, 0, zh), r=0.085, tail=(-0.3, -d, 0.0), length=0.46, curl=(-0.55, 0, 0.3), eyes=k["black:0.3:0.6"])
        k.emit("Head_Wisp%d" % (i + 1), col, rig=rig, bone="wisp.%d" % (i + 1))
    for i, z in enumerate(RINGS):
        r = hw(z) * 1.414 + 0.055
        ring(k[glow(VIO, 1.0)], (0, 0, z - TIP), r, r - 0.04, -0.03, 0.03, seg=16)
        k.emit("Head_Pulse%d" % (i + 1), col, rig=rig, bone="pulse.%d" % (i + 1))
    return rig


IDLE_LEN = 96
FIRE_LEN = 18


def _bump(x, c, w):
    return smooth(1.0 - abs(x - c) / w) if abs(x - c) < w else 0.0


def pose(rig, t=0.0, whirl=0.0, rings=None, kick=0.0, spin=0.0, pull=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    ph = 2 * math.pi * t
    cr = pb["crystal"]
    cr.rotation_quaternion = q(cr, (0, 0, 1), 360.0 * t + spin)
    cr.location = arm_space_loc(cr, (0, 0, 0.06 * math.sin(2 * ph) + 0.17 * kick))
    s = 1.0 + 0.05 * math.sin(3 * ph) + 0.55 * kick
    cr.scale = (s, s, s)
    for i, (r, z, d) in enumerate(WISPS):
        o, w = pb["orbit.%d" % (i + 1)], pb["wisp.%d" % (i + 1)]
        o.rotation_quaternion = q(o, (0, 0, 1), d * 360.0 * (t + whirl) + 120.0 * i)
        o.location = arm_space_loc(o, (0, 0, 0.08 * math.sin(2 * math.pi * (2 * t + 0.3 * i)) + 0.25 * pull))
        w.location = arm_space_loc(w, (-r * 0.3 * pull, 0, 0))
        sw = 1.0 + 0.1 * math.sin(2 * math.pi * (3 * t + 0.4 * i)) + 0.3 * pull
        w.scale = (sw, sw, sw)
    for i in range(len(RINGS)):
        v = rings[i] if rings is not None else 0.01 + 0.93 * _bump((t - 0.06 * i) % 1.0, 0.2, 0.09)
        pb["pulse.%d" % (i + 1)].scale = (max(v, 0.01),) * 3


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(rig, t=f / IDLE_LEN)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        # the rings flare one after another up the shaft (frames 0-8), the crystal kicks as the last one reaches it
        rs = [0.01 + 1.3 * _bump(f, 2.0 + 1.6 * i, 2.0) for i in range(len(RINGS))]
        kick = smooth((f - 6) / 2.5) * (1 - smooth((f - 9) / 8.0))
        pose(rig, t=0.0, whirl=smooth(f / FIRE_LEN), rings=rs, kick=kick, spin=120.0 * smooth((f - 4) / 13.0),
             pull=smooth(f / 4.0) * (1 - smooth((f - 7) / 10.0)))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.2, 1.5), "dist": 9.6, "yaw": 150, "pitch": 18, "anim_target": (F.x, F.y, 2.3), "anim_dist": 5.4,
           "frames": [("idle", 0), ("idle", 20), ("fire", 3), ("fire", 6), ("fire", 8), ("fire", 11)],
           "extra": [{"yaw": 160, "pitch": 10, "dist": 3.2, "target": (F.x, F.y, 2.0)},
                     {"yaw": 200, "pitch": 16, "dist": 3.2, "target": (0, -0.7, 0.8)},
                     {"yaw": 90, "pitch": 12, "dist": 7.6, "target": (0, 0, 1.4)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
