"""Builds the Snapjaw Crab (footprint "wing3": [0,0] back, [1,-1] front-right, [-1,0] front-left), a Tide creature
tower: a giant armoured crab that scuttles out to its prey, snaps both great claws shut on it and scuttles home
(GameData.STRIKES "lunge").

    python tools/blender/build.py snapjaw_crab --out <preview dir>

Its home is one tidal flat over all three hexes: a bank of rippled sand with a crescent pool cut into it (the crab's
wallow, its flooded burrow mouth in the middle, under where it sits), the ribs of a beached whale arching in over the
left hex, and on the right its midden of heaped shells round a broken spar that still flies a rag of the team's colors.
The crab is the Head and nothing else, so the game can send it across the map: a lofted carapace with spines, knobs,
barnacles and a war-paint band in the team's color, eyes on stalks, chewing mouthparts, a crusher and a cutter claw
(arm, claw and pincer bones each), six jointed legs.
Clips: idle (it breathes, its eyes twitch, it works its claws and taps a leg), run (a sideways-on scuttle, legs rippling,
looped while it travels), fire (claws flung wide, then snapped shut in front of it: the blow lands 0.15 s in).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "tide_beasts_common.py"), encoding="utf-8").read())

TID = "snapjaw_crab"
CELLS = [(0, 0), (1, -1), (-1, 0)]
MID = footprint_mid(CELLS)
BK = hex_to_world(0, 0, MID)
FR = hex_to_world(1, -1, MID)
FL = hex_to_world(-1, 0, MID)
TOP = 0.34
SAND = 0.085                    # the sand flat's top, above the plinth
WATER = 0.04                    # the pool's surface, above the plinth
CS = 1.25                       # crab scale (laid out at 1.0)
HOME = Vector((0.0, -0.3, 0.0))
SHELL = "ember:0.05:0.85"
POOL = [(0, -1.0), (0.55, -0.93), (0.95, -0.62), (1.35, -0.36), (1.62, 0.02), (1.48, 0.38), (1.05, 0.36), (0.68, 0.0),
        (0.22, -0.06), (-0.22, -0.06), (-0.68, 0.0), (-1.05, 0.36), (-1.48, 0.38), (-1.62, 0.02), (-1.35, -0.36),
        (-0.95, -0.62), (-0.55, -0.93)]


def build_base():
    col = collection("Snapjaw_crab")
    root = empty("Snapjaw_crab", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    rnd = random.Random(83)
    k = Kit()
    ZS = T + SAND
    # ---- the tidal flat: a bank of sand over all three hexes, a crescent pool cut into it, a wet shelf round the pool
    flat = tb_shore(CELLS, 0.2, rnd, step=0.3, jitter=0.03, rounds=2)
    pool = tb_wobble(tb_smooth(tb_resample([Vector((x, y, 0)) for x, y in POOL], 0.25), 2), rnd, 0.015)
    shelf = tb_offset(pool, 0.1)
    bm = bmesh.new()
    tb_plate(bm, flat, [shelf], ZS, z_skirt=T - 0.02, flare=0.07, z_hole=T + 0.05)
    tb_shore_obj("Flat_Sand", bm, col, root, top=0.3)
    bm = bmesh.new()
    tb_plate(bm, tb_offset(shelf, 0.02), [pool], T + 0.058, z_hole=T + 0.01, hole_flare=0.05)
    tb_shore_obj("Flat_Wet", bm, col, root, top=0.8, side=(0.7, 0.95))
    # the burrow mouth: a lip of dug sand in the middle of the pool, dark water down it
    bc = Vector((HOME.x, HOME.y - 0.2, 0))
    lip = []
    for r, z in ((0.42, T + 0.02), (0.35, T + 0.12), (0.28, T + 0.125), (0.2, T + 0.03)):
        lip.append([Vector((bc.x + math.cos(a) * r * (1.25 + 0.06 * math.sin(3 * a)), bc.y + math.sin(a) * r * (0.82 + 0.05 * math.cos(2 * a)), z))
                    for a in [2 * math.pi * i / 12 for i in range(12)]])
    bm = bmesh.new()
    bm_loft(bm, lip, cap0=False, cap1=False)
    tb_shore_obj("Burrow_Lip", bm, col, root, top=0.7, side=(0.45, 0.9))
    bm = bmesh.new()
    bm.faces.new([bm.verts.new(p) for p in lip[-1]])
    tb_sea_obj("Burrow_Dark", bm, col, root, top=0.93)
    tb_water("Pool", col, root, [tb_offset(pool, 0.03)], T + WATER, [0.46], holes=[[Vector((p.x, p.y, 0)) for p in lip[0]]])
    # ripples the tide left on the open sand
    bm = bmesh.new()
    keep = tb_offset(flat, -0.05)
    for c, ang, n, ln in (((-1.42, 0.9), 14, 3, 0.75), ((1.45, 0.92), -12, 3, 0.8), ((-2.12, -0.14), 32, 2, 0.6), ((0.1, -1.34), 2, 2, 0.6),
                          ((2.1, -0.3), -24, 2, 0.55)):
        tb_ripples(bm, c, ang, n, ln, ZS - 0.006, within=keep, avoid=[tb_offset(shelf, 0.04)])
    tb_shore_obj("Flat_Ripples", bm, col, root, top=0.1, side=(0.15, 0.45))
    # rocks on the pool's rim, weed and a starfish
    for x, y, r, sq in ((-0.5, -1.2, 0.26, 0.7), (-0.2, -1.32, 0.15, 0.8), (0.75, -1.0, 0.2, 0.75), (1.72, -0.28, 0.16, 0.8),
                        (-1.76, -0.24, 0.19, 0.8), (-1.58, 0.52, 0.13, 0.9), (0.2, 0.1, 0.1, 0.8)):
        bm_boulder(k["stone2:0.15:0.9"], rnd, (x, y, ZS - 0.03), r, squash=(1.1, 0.95, sq), n=11)
    k.emit("Rocks", col, root, vary=0.08)
    tb_starfish(k["orange:0.15:0.7"], (-0.5, -1.18, ZS + 0.15), r=0.15, yaw=20, h=0.04)
    tb_weed(k["teal:0.2:0.9"], rnd, (-0.82, -1.02, T + WATER), h=0.42, n=3)
    tb_weed(k["teal:0.2:0.9"], rnd, (1.74, -0.1, T + WATER), h=0.36, n=2)
    for p in ((-0.42, -1.34, ZS + 0.1), (-0.62, -1.28, ZS + 0.12), (0.78, -1.08, ZS + 0.1)):
        tb_barnacle(k, p, 0.045)
    k.emit("Rim_Life", col, root)
    # ---- the left hex: the ribs of a beached whale arching in over the wallow, its backbone half buried
    row0, row_d, arch = Vector((-2.2, 0.6, 0)), Vector((0.6, 0.8, 0)), (0.8, -0.6)
    for i, (off, h, reach) in enumerate(((-0.62, 1.15, 1.0), (-0.22, 1.5, 1.22), (0.2, 1.62, 1.28), (0.6, 1.3, 1.08))):
        p = row0 + row_d * off
        tb_rib(k["cream:0.12:0.9"], (p.x, p.y, ZS), arch, reach, h, r0=0.09, r1=0.038)
        bm_boulder(k["cream:0.3:0.95"], rnd, (p.x - 0.1, p.y + 0.08, ZS - 0.04), 0.18, squash=(1.0, 1.0, 0.75), n=10)     # a vertebra
    for x, y in ((-2.46, -0.16), (-1.62, 1.1)):                                                                          # the backbone's ends
        bm_boulder(k["cream:0.3:0.95"], rnd, (x, y, ZS - 0.04), 0.14, squash=(1.0, 1.0, 0.7), n=9)
    tb_rib(k["cream:0.2:0.95"], (-1.66, -0.3, ZS - 0.02), (0.3, 0.95), 0.75, 0.2, r0=0.06, r1=0.03, sink=0.05)                # a fallen rib
    k.emit("Whale", col, root, vary=0.05)
    tb_weed(k["teal:0.25:0.9"], rnd, (-2.36, 0.52, ZS), h=0.4, n=3)
    tb_barnacle(k, (-2.56, 0.16, ZS + 0.3), 0.04, nrm=(0.6, -0.4, 0.5))
    tb_barnacle(k, (-2.0, 0.84, ZS + 0.42), 0.045, nrm=(0.6, -0.5, 0.4))
    k.emit("Whale_Life", col, root)
    # ---- the right hex: the midden (a heap of sand and shells), round a broken spar still flying a rag of the team's colors
    mc = Vector((2.3, 0.2, 0))
    bm = bmesh.new()
    bm_blob(bm, rnd, (mc.x, mc.y, ZS), 0.56, squash=(1.2, 1.0, 0.36), jitter=0.1, sub=2)
    tb_shore_obj("Midden_Heap", bm, col, root, top=0.55, side=(0.25, 0.7))
    tb_scallop(k["cream:0.02:0.6"], (mc.x - 0.12, mc.y - 0.36, ZS + 0.1), 0.52, yaw=165, tilt=52, ribs=7)
    tb_scallop(k["salmon:0.0:0.5"], (mc.x - 0.12, mc.y - 0.36, ZS + 0.1), 0.52, yaw=165, tilt=52, ribs=7, t0=0.82, t1=1.02, rows=1, lift=0.014)
    tb_scallop(k["salmon:0.0:0.45"], (mc.x - 0.52, mc.y + 0.12, ZS + 0.08), 0.4, yaw=95, tilt=34, ribs=6, rows=3)
    tb_scallop(k["cream:0.1:0.7"], (mc.x + 0.2, mc.y - 0.66, ZS + 0.02), 0.34, yaw=-150, tilt=8, ribs=6, rows=3)
    tb_scallop(k["orange:0.0:0.45"], (mc.x + 0.5, mc.y - 0.2, ZS + 0.06), 0.26, yaw=-100, tilt=24, ribs=5, rows=2)
    tb_scallop(k["cream:0.05:0.6"], (mc.x - 0.62, mc.y - 0.44, ZS + 0.01), 0.22, yaw=70, tilt=6, ribs=5, rows=2)
    tb_whelk(k["sand:0.05:0.75"], (mc.x + 0.18, mc.y + 0.02, ZS + 0.2), 0.36, yaw=200, pitch=24)
    tb_whelk(k["salmon:0.1:0.6"], (mc.x - 0.5, mc.y + 0.56, ZS), 0.2, yaw=40)
    for dx, dy, r, key in ((0.44, 0.3, 0.1, "cream:0.1:0.6"), (-0.3, -0.62, 0.085, "salmon:0.0:0.5"), (0.6, 0.02, 0.08, "cream:0.2:0.7"),
                           (-0.1, 0.52, 0.09, "orange:0.1:0.5"), (-0.72, -0.12, 0.075, "cream:0.1:0.7")):
        bm_boulder(k[key], rnd, (mc.x + dx, mc.y + dy, ZS + 0.02), r, squash=(1.3, 1.0, 0.55), n=8)
    k.emit("Shells", col, root)
    foot = Vector((mc.x + 0.02, mc.y + 0.3, ZS - 0.05))
    head = foot + Vector((-0.4, 0.22, 2.0))
    bm_tube(k["wood_dark:0.2:0.85"], [foot, foot.lerp(head, 0.5), head], [0.095, 0.085, 0.07], n=6)
    yd = (head - foot).normalized()
    y0, y1 = foot.lerp(head, 0.84) + Vector((0.36, 0.28, 0.05)), foot.lerp(head, 0.84) + Vector((-0.42, -0.32, -0.04))
    bm_tube(k["wood_dark:0.3:0.9"], [y0, y1], [0.05, 0.045], n=5)
    bm_tube(k["sand:0.3:0.7"], [foot.lerp(head, 0.8), foot.lerp(head, 0.88)], 0.095, n=6)                                    # lashing
    for j in range(4):                                                                                                  # splintered top
        a = math.radians(90 * j + 20)
        bm_crystal(k["wood:0.2:0.8"], head - yd * 0.04 + Vector((math.cos(a) * 0.03, math.sin(a) * 0.03, 0)),
                   head + yd * rnd.uniform(0.1, 0.22) + Vector((math.cos(a) * 0.05, math.sin(a) * 0.05, 0)), 0.035, n=4, shoulder=0.3)
    k.emit("Spar", col, root)
    # the rag: what is left of a sail, hanging off the yard
    grid = []
    for i in range(5):
        u = i / 4.0
        top = y0.lerp(y1, 0.08 + 0.84 * u)
        drop = (0.8, 1.0, 0.64, 0.9, 0.52)[i]
        grid.append([top + Vector((0.06 * math.sin(v * 3.0 + u * 4), -0.1 * math.sin(v * 2.4) * (0.4 + u), -drop * v)) for v in (0.0, 0.34, 0.68, 1.0)])
    tb_sheet(k["team!:0.1:0.75"], grid, 0.016)
    k.emit("Spar_Rag", col, root)
    empty("Head", col, root, (HOME.x, HOME.y, T + WATER), 0.5, "SINGLE_ARROW")
    return root


# ---- the crab, in the head's space (+Y forward, the ground under its middle at the origin), laid out at 1.0
ZC = 0.5        # the height of the carapace's rim
ROWS = [  # y, half width, height above the rim, depth below it
    (-0.54, 0.26, 0.09, 0.05), (-0.44, 0.50, 0.19, 0.10), (-0.26, 0.66, 0.27, 0.14), (-0.04, 0.74, 0.31, 0.16),
    (0.16, 0.76, 0.30, 0.16), (0.32, 0.69, 0.25, 0.14), (0.43, 0.56, 0.17, 0.11), (0.5, 0.42, 0.09, 0.07)]
BAND = (-0.04, 0.16)          # the war-paint band: this strip of the carapace
SIZE = {"L": 1.05, "R": 1.3}   # the cutter and the crusher


def _row_at(y):
    y = min(max(y, ROWS[0][0]), ROWS[-1][0])
    for a, b in zip(ROWS, ROWS[1:]):
        if a[0] <= y <= b[0]:
            t = (y - a[0]) / (b[0] - a[0])
            return tuple(a[i] + (b[i] - a[i]) * t for i in (1, 2, 3))
    return ROWS[-1][1:]


def _ring(y, grow=0.0, n=12):
    """The carapace's section at y: a dome over a shallower belly, meeting in a sharp rim."""
    rx, zt, zb = _row_at(y)
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        ca, sa = math.cos(a), math.sin(a)
        out.append(Vector((math.copysign(abs(ca) ** 0.8, ca) * (rx + grow), y,
                           ZC + math.copysign(abs(sa) ** 0.9, sa) * ((zt if sa >= 0 else zb) + grow))))
    return out


def _top(x, y, lift=0.0):
    """A point on the carapace's top over (x, y)."""
    rx, zt, zb = _row_at(y)
    c = min(abs(x) / rx, 0.999) ** (1 / 0.8)
    return Vector((x, y, ZC + zt * math.sqrt(1 - c * c) ** 0.9 + lift))


def _arc(y, a0, a1, th, n=7):
    """A closed section hugging the carapace's top at y between two angles (degrees, 90 = the crest): painted trim."""
    rx, zt, zb = _row_at(y)
    out, inn = [], []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        ca, sa = math.cos(a), math.sin(a)
        x, z = math.copysign(abs(ca) ** 0.8, ca), abs(sa) ** 0.9
        out.append(Vector((x * (rx + th), y, ZC + z * (zt + th))))
        inn.append(Vector((x * (rx - 0.012), y, ZC + z * (zt - 0.012))))
    return out + list(reversed(inn))


def _claw(sx, s):
    """Side sx's arm: shoulder, elbow, and P(along, up, across) -> a point in the claw's own frame (scaled by its size)."""
    size = SIZE[s]
    sh = Vector((sx * 0.5, 0.34, 0.46))
    el = Vector((sx * 1.02, 0.42, 0.68))
    ax = Vector((sx * 0.1, 0.98, -0.14)).normalized()
    up = (Vector((0, 0, 1)) - ax * ax.z).normalized()
    sd = up.cross(ax)
    return sh, el, ax, up, (lambda x, z=0.0, y=0.0: el + ax * (x * size) + up * (z * size) + sd * (y * size))


LEGS = {}
for _sx, _s in ((-1, "L"), (1, "R")):
    for _i, (_hy, _ky, _fy, _fx) in enumerate(((0.22, 0.36, 0.5, 1.38), (0.0, -0.02, -0.04, 1.44), (-0.24, -0.26, -0.12, 1.24))):
        LEGS["%s%d" % (_s, _i + 1)] = (Vector((_sx * 0.56, _hy, 0.44)), Vector((_sx * (1.0 if _i != 2 else 0.95), _ky, 0.84 - 0.04 * _i)),
                                       Vector((_sx * _fx, _fy, 0.0)))
BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None), "body": ((0, -0.3, ZC), (0, 0.3, ZC), "root")}
for _sx, _s in ((-1, "L"), (1, "R")):
    _sh, _el, _ax, _up, _P = _claw(_sx, _s)
    BONES["arm." + _s] = (tuple(_sh), tuple(_el), "body")
    BONES["claw." + _s] = (tuple(_el), tuple(_P(0.48, -0.04)), "arm." + _s)
    BONES["pinch." + _s] = (tuple(_P(0.42, 0.1)), tuple(_P(0.87, -0.02)), "claw." + _s)
    BONES["eye." + _s] = ((_sx * 0.2, 0.46, 0.6), (_sx * 0.25, 0.55, 0.88), "body")
    BONES["mouth." + _s] = ((_sx * 0.065, 0.5, 0.49), (_sx * 0.065, 0.52, 0.34), "body")
for _n, (_a, _b, _c) in LEGS.items():
    BONES["leg.%s.1" % _n] = (tuple(_a), tuple(_b), "body")
    BONES["leg.%s.2" % _n] = (tuple(_b), tuple(_c), "leg.%s.1" % _n)


def build_head():
    col = collection("Snapjaw_crab")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES, scale=CS)
    rnd = random.Random(5)
    S = CS
    k = Kit()
    # ---- the carapace: one loft, the belly paler, a war-paint band in the team's color between cream lines
    bm_loft(k[SHELL], [_ring(y) for y, _, _, _ in ROWS])
    shell = k.emit("Head_Shell", col, rig=rig, bone="body", scale=S)[0]
    paint_faces(shell, "cream", lambda c, n: n.z < -0.45, lo=0.3, hi=0.85)
    paint_faces(shell, "team", lambda c, n: n.z > 0.2 and BAND[0] * S < c.y < BAND[1] * S, team=True, lo=0.1, hi=0.55)
    paint_faces(shell, "team", lambda c, n: n.z > 0.5 and BAND[1] * S < c.y < 0.32 * S and abs(c.x) < 0.2 * S, team=True, lo=0.1, hi=0.5)
    rk = RigidKit().to("body")
    for y in BAND:
        bm_loft(rk["cream:0.05:0.5"], [_arc(y + d, 0, 180, 0.014, n=6) for d in (-0.022, 0.022)])
    # knobs and plates on the shell, spines along its rim, teeth between the eyes, feelers, barnacles
    for x, y, r in ((-0.36, -0.28, 0.17), (0.36, -0.28, 0.17), (0.0, -0.36, 0.13), (-0.3, 0.33, 0.13), (0.3, 0.33, 0.13)):
        bm_boulder(rk["ember:0.1:0.6"], rnd, tuple(_top(x, y, -0.02)), r, squash=(1.2, 1.0, 0.42), n=10, sink=0.25)
    for sx in (-1, 1):
        for y, ln in ((0.4, 0.16), (0.27, 0.22), (0.1, 0.26), (-0.1, 0.22), (-0.3, 0.17)):
            rx = _row_at(y)[0]
            b = Vector((sx * (rx - 0.05), y, ZC + 0.01))
            bm_crystal(rk["cream:0.1:0.7"], b, b + Vector((sx * (ln + 0.05), ln * 0.5, 0.08)), 0.07, n=4, shoulder=0.25)
        bm_crystal(rk["ember:0.2:0.7"], (sx * 0.07, 0.48, ZC + 0.07), (sx * 0.15, 0.74, ZC + 0.2), 0.02, n=4, shoulder=0.2)
    for x in (-0.09, 0.0, 0.09):
        bm_crystal(rk["cream:0.1:0.7"], (x, 0.48, ZC + 0.03), (x * 1.3, 0.61, ZC + 0.02), 0.04, n=4, shoulder=0.25)
    for x, y, r in ((-0.5, -0.12, 0.05), (-0.42, -0.2, 0.038), (-0.56, -0.2, 0.034), (0.16, -0.46, 0.045), (0.25, -0.42, 0.032), (0.52, 0.26, 0.04)):
        p = _top(x, y, -0.01)
        tb_barnacle(rk, p, r, nrm=(p.x * 0.5, p.y * 0.3, 1.0), key="stone:0.0:0.45")
    # ---- eyes on stalks, mouthparts
    for sx, s in ((-1, "L"), (1, "R")):
        rk.to("eye." + s)
        a, b, _ = BONES["eye." + s]
        a, b = Vector(a), Vector(b)
        bm_tube(rk[SHELL], [a - Vector((0, 0.02, 0.04)), b], [0.06, 0.045], n=5)
        bm_ellipsoid(rk["black:0.2:0.6"], tuple(b + Vector((0, 0.01, 0.05))), (0.085, 0.085, 0.095), u=7, v=5)
        bm_box(rk["white:0.0:0.2"], (0.032, 0.02, 0.032), tuple(b + Vector((sx * 0.03, 0.078, 0.085))))
        rk.to("mouth." + s)
        bm_tube(rk["salmon:0.15:0.8"], [(sx * 0.068, 0.492, 0.5), (sx * 0.07, 0.522, 0.42), (sx * 0.05, 0.53, 0.325)], [0.02, 0.027, 0.011],
                n=6, up=(0, 1, 0), squash=2.4)                                                                           # a jaw plate, tapering
    rk.to("body")
    bm_box(rk["wood_dark:0.5:0.9"], (0.3, 0.05, 0.19), (0, 0.468, 0.415))                                                  # the dark of its mouth
    # ---- the claws: an arm, a fat palm running out into the fixed finger, a hooked pincer hinged on top
    for sx, s in ((-1, "L"), (1, "R")):
        sh, el, ax, up, P = _claw(sx, s)
        z = SIZE[s]
        rk.to("arm." + s)
        bm_tube(rk[SHELL], [sh - (el - sh) * 0.12, sh, sh.lerp(el, 0.55) + Vector((0, 0, 0.03)), el], [0.09, 0.125, 0.15, 0.12], n=6)
        bm_ellipsoid(rk[SHELL], tuple(el), (0.13 * z, 0.13 * z, 0.12 * z), u=7, v=5)
        bm_crystal(rk["cream:0.1:0.7"], el + Vector((sx * 0.06, -0.04, 0.05)), el + Vector((sx * 0.22, -0.1, 0.16)), 0.05, n=4, shoulder=0.25)
        rk.to("claw." + s)
        bm_tube(rk[SHELL], [P(-0.05), P(0.14, -0.02), P(0.32, -0.04), P(0.5, -0.05)], [0.1 * z, 0.2 * z, 0.22 * z, 0.15 * z], n=8, up=tuple(up), squash=0.8)
        bm_tube(rk[SHELL], [P(0.38, -0.13), P(0.58, -0.17), P(0.73, -0.16)], [0.13 * z, 0.1 * z, 0.07 * z], n=6, up=tuple(up), squash=0.8)
        bm_tube(rk["black:0.2:0.7"], [P(0.69, -0.165), P(0.8, -0.14), P(0.88, -0.09)], [0.074 * z, 0.05 * z, 0.0], n=6, up=tuple(up), squash=0.8)
        bm_tube(rk["team!:0.1:0.6"], [P(0.06, -0.01), P(0.14, -0.02), P(0.22, -0.028)], [0.172 * z, 0.218 * z, 0.228 * z], n=8, up=tuple(up), squash=0.8, cap=False)
        for x_, r_ in ((0.045, 0.172), (0.235, 0.232)):
            bm_tube(rk["cream:0.05:0.5"], [P(x_ - 0.014, -0.012), P(x_ + 0.014, -0.02)], [(r_ + 0.012) * z] * 2, n=8, up=tuple(up), squash=0.8, cap=False)
        for t in (0.46, 0.56, 0.66):
            bm_crystal(rk["cream:0.05:0.5"], P(t, -0.1), P(t + 0.02, -0.02), 0.03 * z, n=4, shoulder=0.3)
        for y_ in (-0.12, 0.12):                                                                                         # knuckles
            bm_boulder(rk["ember:0.1:0.6"], rnd, tuple(P(0.26, 0.14, y_)), 0.07 * z, squash=(1, 1, 0.6), n=8, sink=0.3)
        rk.to("pinch." + s)
        bm_tube(rk[SHELL], [P(0.38, 0.09), P(0.58, 0.17), P(0.73, 0.13)], [0.115 * z, 0.095 * z, 0.07 * z], n=6, up=tuple(up), squash=0.8)
        bm_tube(rk["black:0.2:0.7"], [P(0.69, 0.145), P(0.8, 0.075), P(0.875, -0.03)], [0.072 * z, 0.05 * z, 0.0], n=6, up=tuple(up), squash=0.8)
        for t in (0.52, 0.63):
            bm_crystal(rk["cream:0.05:0.5"], P(t, 0.1), P(t + 0.02, 0.02), 0.03 * z, n=4, shoulder=0.3)
    # ---- six legs: a thick thigh up to the knee, a shin down to a dark point
    for name, (a, b, c) in LEGS.items():
        rk.to("leg.%s.1" % name)
        bm_tube(rk[SHELL], [a - (b - a) * 0.15, a, a.lerp(b, 0.55) + Vector((0, 0, 0.04)), b], [0.085, 0.115, 0.125, 0.095], n=6)
        bm_ellipsoid(rk[SHELL], tuple(b), (0.105, 0.105, 0.1), u=6, v=4)
        rk.to("leg.%s.2" % name)
        bm_tube(rk[SHELL], [b, b.lerp(c, 0.4), b.lerp(c, 0.74)], [0.092, 0.085, 0.052], n=6)
        bm_tube(rk["black:0.2:0.7"], [b.lerp(c, 0.7), b.lerp(c, 0.86), c], [0.056, 0.036, 0.0], n=6)
    rk.emit("Head_Crab", col, rig, scale=S)
    for i, s in ((1, "L"), (2, "R")):
        sh, el, ax, up, P = _claw(-1 if s == "L" else 1, s)
        empty("Muzzle%d" % i, col, head, tuple(P(0.86, -0.04) * S), 0.2, "SPHERE")
    empty("Muzzle", col, head, (0.0, 1.2 * S, 0.5 * S), 0.2, "SPHERE")              # where the claws meet, in front of its mouth
    return rig


IDLE_LEN = 80
RUN_LEN = 12
FIRE_LEN = 20
GAIT = {"L1": 0.0, "L2": 2.1, "L3": 4.2, "R1": 3.14, "R2": 5.24, "R3": 1.05}


def pose(rig, bob=0.0, fwd=0.0, pitch=0.0, yaw=0.0, roll=0.0, eyes=(0.0, 0.0), chew=0.0, arms=None, legs=None, away=0.0):
    """arms: {"L" / "R": (sweep, lift, turn, tip, gape)} in degrees: the arm swung forward and inward, raised; the claw
    turned inward, its tip raised; the pincer's gape (0 = shut). legs: {name: (swing, lift, flex)}."""
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    pb["root"].location = arm_space_loc(pb["root"], (0, away, 0))
    pb["body"].location = arm_space_loc(pb["body"], (0, fwd, bob))
    pb["body"].rotation_quaternion = q(pb["body"], (0, 0, 1), yaw) @ q(pb["body"], (1, 0, 0), pitch) @ q(pb["body"], (0, 1, 0), roll)
    for sx, s, e in ((-1, "L", eyes[0]), (1, "R", eyes[1])):
        pb["eye." + s].rotation_quaternion = q(pb["eye." + s], (1, 0, 0), e) @ q(pb["eye." + s], (0, 1, 0), e * 0.6 * sx)
        pb["mouth." + s].rotation_quaternion = q(pb["mouth." + s], (0, 1, 0), sx * 9 * chew) @ q(pb["mouth." + s], (1, 0, 0), -6 * abs(chew))
        sweep, lift, turn, tip, gape = (arms or {}).get(s, (0, 0, 0, 0, 10))
        sh, el, ax, up, P = _claw(sx, s)
        d = el - sh
        la = Vector((d.x, d.y, 0)).normalized().cross(Vector((0, 0, 1)))
        pb["arm." + s].rotation_quaternion = q(pb["arm." + s], (0, 0, 1), sx * sweep) @ q(pb["arm." + s], tuple(la), lift)
        ca = Vector((ax.x, ax.y, 0)).normalized().cross(Vector((0, 0, 1)))
        pb["claw." + s].rotation_quaternion = q(pb["claw." + s], (0, 0, 1), sx * turn) @ q(pb["claw." + s], tuple(ca), tip)
        pb["pinch." + s].rotation_quaternion = q(pb["pinch." + s], tuple(ax.cross(up)), gape - 4)
    for name, (a, b, c) in LEGS.items():
        swing, lift, flex = (legs or {}).get(name, (0, 0, 0))
        sx = -1 if name[0] == "L" else 1
        la = Vector((sx, 0, 0)).cross(Vector((0, 0, 1)))
        pb["leg.%s.1" % name].rotation_quaternion = q(pb["leg.%s.1" % name], (0, 0, 1), swing) @ q(pb["leg.%s.1" % name], tuple(la), lift)
        pb["leg.%s.2" % name].rotation_quaternion = q(pb["leg.%s.2" % name], tuple(la), flex)


def _idle(ph):
    tap = max(0.0, math.sin(ph * 2 - 1.0)) ** 8
    return dict(bob=0.014 * math.sin(ph * 2), roll=1.2 * math.sin(ph), eyes=(12 * math.sin(ph * 3), 10 * math.sin(ph * 2)),
                chew=math.sin(ph * 6) * (0.5 + 0.5 * math.sin(ph)),
                arms={"L": (4 * math.sin(ph), 3 * math.sin(ph), 3 * math.sin(ph * 2), 0, 12 + 16 * max(0.0, math.sin(ph * 2)) ** 2),
                      "R": (3 * math.sin(ph + 2.0) - 2.7, 2 * math.sin(ph), 2 * math.sin(ph), 0, 12 + 20 * max(0.0, math.sin(ph * 2 + 2.6)) ** 3 - 2.7)},
                legs={"R2": (4 * tap, 16 * tap, -8 * tap), "L3": (0, 5 * max(0.0, math.sin(ph - 1.0)) ** 6, 0)})


def build_anims():
    rig = bpy.data.objects["Rig"]
    away = 40.0 if os.environ.get("TB_AWAY") else 0.0           # (a preview of its home with the crab out hunting)
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(rig, away=away, **_idle(2 * math.pi * f / IDLE_LEN))
        key_pose(rig, f)
    new_action(rig, "run", RUN_LEN)
    for f in range(RUN_LEN + 1):
        ph = 2 * math.pi * f / RUN_LEN
        legs = {}
        for name, off in GAIT.items():
            sx = -1 if name[0] == "L" else 1
            sw, up = math.sin(ph + off), max(0.0, math.cos(ph + off))
            legs[name] = (sx * 22 * sw, 5 + 20 * up, 10 * up)
        pose(rig, bob=-0.075 + 0.018 * math.sin(ph * 2), yaw=28, roll=2.5 * math.sin(ph), pitch=-2,
             eyes=(-8 + 4 * math.sin(ph), -8 - 4 * math.sin(ph)),
             arms={"L": (10, 12 + 4 * math.sin(ph), 4, 6, 26 + 8 * math.sin(ph * 2)), "R": (2, 9 - 4 * math.sin(ph), -6, 4, 24 - 8 * math.sin(ph * 2))}, legs=legs)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    base = _idle(0.0)
    for f in range(FIRE_LEN + 1):
        # the blow lands at frame 4.5 (0.15 s): claws flung wide, then both swing in and snap shut in front of it
        wind = smooth(f / 2.5) * (1 - smooth((f - 2.5) / 2.0))
        snap = smooth((f - 2.5) / 2.0) * (1 - smooth((f - 9) / 10.0))
        shake = math.sin(f * 2.4) * (1.0 if 5 <= f <= 9 else 0.0)
        d = (-20 * wind + 30 * snap + 2 * shake, 20 * wind + 5 * snap, -18 * wind + 28 * snap, 10 * wind - 4 * snap, 34 * wind - 12 * min(1.0, snap * 1.2))
        arms = {s: tuple(base["arms"][s][i] + d[i] for i in range(5)) for s in ("L", "R")}
        legs = {name: ((-1 if name[0] == "L" else 1) * (3 * wind - 7 * snap), 3 * wind, 0) for name in LEGS}
        legs["L3"] = (legs["L3"][0], legs["L3"][1] + base["legs"]["L3"][1], 0)
        pose(rig, bob=0.04 * wind - 0.05 * snap, fwd=-0.06 * wind + 0.13 * snap, pitch=7 * wind - 6 * snap, eyes=(-14 * wind + 10 * snap,) * 2,
             chew=snap, arms=arms, legs=legs)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.1, 0.75), "dist": 8.4, "yaw": 160, "pitch": 22, "anim_target": (HOME.x, HOME.y + 0.5, 0.9), "anim_dist": 6.0,
           "frames": [("idle", 0), ("run", 3), ("run", 9), ("fire", 2), ("fire", 5)],
           "extra": [{"yaw": 180, "pitch": 10, "dist": 4.0, "target": (HOME.x, HOME.y + 0.4, 0.95)},
                     {"yaw": 0, "pitch": 57, "dist": 6.0, "target": (0, 0.1, 0.5)},
                     {"yaw": 215, "pitch": 24, "dist": 5.2, "target": (FL.x + 0.3, FL.y - 0.1, 1.0)},
                     {"yaw": 140, "pitch": 26, "dist": 5.0, "target": (FR.x + 0.3, FR.y - 0.1, 0.9)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
