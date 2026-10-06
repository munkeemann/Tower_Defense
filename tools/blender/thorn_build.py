"""Builds the Thornspitter (footprint "single"), a Verdant tower: a carnivorous flower that spits thorns.

    python tools/blender/build.py thorn --out <preview dir>

One plant owns the hex. A thick vine lies coiled on a mound of dark earth ringed with mossy stones, then corkscrews up
(the coil tightens as it climbs) to a heavy bulb head: a toothed mouth with red lips, a ruff of petals in the team's
color, a star of spiked sepals behind it and glowing venom sacs on its crown. Broad leaves, roots and three small buds
(the same flower, not yet open) grow out of the mound between the stones.
The vine and the head are the Head (they turn to aim; thorns leave from the mouth): the tube is skinned along a bone
chain, so it sways and uncoils. idle: the vine sways, the head looks about and chews, the petals ripple, the sacs
pulse. fire (0.2 s): the head rears a touch, darts forward with its jaws wide and spits, and springs back.
"""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "wildwood_common.py"), encoding="utf-8").read())

TID = "thorn"
CELLS = [(0, 0)]
MID = footprint_mid(CELLS)
TOP = 0.34
VENOM = "glow:0.5,1.0,0.16,0.75"
HEAD_UP = 0.19                  # the Head sits this far above the plinth (inside the mound's top)
NECK = Vector((0, 0.07, 1.06))  # where the vine ends and the bulb begins (head space)
TILT = 9.0                      # the bulb looks this many degrees down
HM = Matrix.Translation(NECK) @ Matrix.Rotation(math.radians(-TILT), 4, "X")     # bulb space -> head space
PETALS = 8


MOUND = [(0.0, 0.25), (0.36, 0.245), (0.64, 0.2), (0.86, 0.1), (1.0, -0.03)]     # (share of the rim's radius, height)


def mound_h(r, a=0.0):
    return spline(MOUND, min(r / min(hex_r(a, 0.27), 0.86), 1.0))


def build_base():
    col = collection("Thorn")
    root = empty("Thorn", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP, turf=True)
    rnd = random.Random(5)
    k = Kit()
    # ---- the mound: dark earth heaped over the roots, following the hex
    bm = k["wood_red:0.5:0.95"]
    n = 18
    mid = bm.verts.new((0, 0, T + MOUND[0][1]))
    rings = []
    for fr, h in MOUND[1:]:
        ring_ = []
        for i in range(n):
            a = 2 * math.pi * i / n
            R = min(hex_r(a, 0.27), 0.86) * fr * rnd.uniform(0.95, 1.05)
            ring_.append(bm.verts.new((math.cos(a) * R, math.sin(a) * R, T + h + rnd.uniform(-0.015, 0.015))))
        rings.append(ring_)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((mid, rings[0][i], rings[0][j]))
        for a_, b_ in zip(rings, rings[1:]):
            bm.faces.new((a_[i], b_[i], b_[j], a_[j]))
    k.emit("Mound", col, root)
    # ---- stones round it (big and small, in clumps), moss on the big ones
    stones = [(4, 0.3), (36, 0.15), (118, 0.24), (152, 0.15), (178, 0.11), (236, 0.31), (266, 0.13), (316, 0.22)]
    for a, s in stones:
        ar = math.radians(a)
        R = hex_r(ar, 0.2 + s * 0.75)
        p = Vector((math.cos(ar) * R, math.sin(ar) * R, 0))
        bm_boulder(k["stone:0.15:0.9"], rnd, (p.x, p.y, T - 0.03), s, squash=(1, 1, rnd.uniform(0.8, 1.05)), n=12)
        if s > 0.18:
            bm_blob(k["grass:0.3:0.8"], rnd, (p.x * 0.96, p.y * 0.96, T + s * 1.25), s * 0.62, squash=(1, 1, 0.36), jitter=0.12)
    k.emit("Stones", col, root, vary=0.08, seed=4)
    # ---- roots crawling out from under the coil, down the mound, between the stones
    for a, ln, w in ((62, 0.92, 0.07), (95, 0.8, 0.055), (200, 0.95, 0.075), (288, 0.86, 0.06), (345, 0.9, 0.065), (135, 0.78, 0.05)):
        pts = []
        for i, fr in enumerate((0.3, 0.5, 0.7, 0.87, 1.0)):
            ar = math.radians(a + (10, -8, 9, -5, 0)[i])
            r = fr * hex_r(ar, 0.14) * ln
            pts.append(Vector((math.cos(ar) * r, math.sin(ar) * r, T + mound_h(r, ar) + w * (0.55 - 0.5 * fr))))
        bm_tube(k["wood:0.35:0.95"], pts, [w, w * 0.9, w * 0.75, w * 0.5, 0.0], n=5)
    k.emit("Roots", col, root)
    # ---- broad leaves sprouting from the mound's shoulder, arching out over the stones
    for i, (a, ln, wd) in enumerate(((70, 1.0, 0.4), (128, 0.92, 0.36), (205, 1.0, 0.42), (282, 0.95, 0.38), (338, 0.9, 0.36))):
        ar = math.radians(a)
        d = Vector((math.cos(ar), math.sin(ar), 0))
        R = hex_r(ar, 0.07) * ln
        pts = [d * 0.44 + Vector((0, 0, T + 0.17)), d * (0.44 + (R - 0.44) * 0.22) + Vector((0, 0, T + 0.34)),
               d * (0.44 + (R - 0.44) * 0.48) + Vector((0, 0, T + 0.42)), d * (0.44 + (R - 0.44) * 0.72) + Vector((0, 0, T + 0.37)),
               d * (0.44 + (R - 0.44) * 0.9) + Vector((0, 0, T + 0.25)), d * R + Vector((0, 0, T + 0.1))]
        leaf(k["grass:0.1:0.85"], pts, wd)
        bm_tube(k["lime:0.1:0.5"], [p + Vector((0, 0, 0.024)) for p in pts[:5]], [0.016, 0.016, 0.014, 0.011, 0.006], n=4)    # midrib
    k.emit("Leaves", col, root, vary=0.05)
    # ---- three buds of the same flower: a green cup, the team's petals still furled, a couple of sepal spikes
    for a, r, h, s in ((100, 0.66, 0.42, 1.0), (240, 0.6, 0.3, 0.8), (322, 0.7, 0.36, 0.9)):
        ar = math.radians(a)
        d = Vector((math.cos(ar), math.sin(ar), 0))
        p0 = d * r + Vector((0, 0, T + mound_h(r, ar) - 0.03))
        p1 = p0 + d * 0.05 + Vector((0, 0, h * 0.55))
        p2 = p0 + d * 0.14 + Vector((0, 0, h))
        ax = (p2 - p1).normalized()
        bm_tube(k["teal:0.2:0.8"], [p0, p1, p2], [0.05 * s, 0.04 * s, 0.035 * s], n=5)
        bm_tube(k["grass:0.1:0.7"], [p2 - ax * 0.02, p2 + ax * 0.07 * s, p2 + ax * 0.17 * s], [0.04 * s, 0.11 * s, 0.1 * s], n=7)
        bm_tube(k["team!:0.1:0.7"], [p2 + ax * 0.15 * s, p2 + ax * 0.24 * s, p2 + ax * 0.36 * s], [0.094 * s, 0.075 * s, 0.0], n=7)
        side = ax.cross(Vector((0, 0, 1))).normalized()
        for sg in (-1, 1):
            b = p2 + ax * 0.05 * s + side * sg * 0.08 * s
            bm_crystal(k["teal:0.2:0.7"], b, b + (side * sg * 0.7 + ax * 0.5).normalized() * 0.17 * s, 0.035 * s, n=4, shoulder=0.3)
    k.emit("Buds", col, root)
    for i, (rel, a, r, sc) in enumerate((("forest/Grass_1_B_Color1", 18, 0.93, 0.42), ("forest/Grass_2_A_Color1", 196, 0.95, 0.4),
                                         ("props/Mushroom", 300, 0.9, 0.34))):
        ar = math.radians(a)
        kk_import(rel, col, root, (math.cos(ar) * r, math.sin(ar) * r, T - 0.02), rnd.uniform(0, 360), sc, name="Prop_KK_%d" % i)
    empty("Head", col, root, (0, 0, T + HEAD_UP), 0.5, "SINGLE_ARROW")
    return root


# ---- the vine, in the head's space (+Y forward): 2.4 turns, wide and flat on the mound, tightening as it climbs
TURNS = 2.4
RHO = [(0.0, 0.43), (0.3, 0.31), (0.6, 0.16), (0.85, 0.07), (1.0, 0.0)]          # the coil's radius
ZK = [(0.0, 0.03), (0.2, 0.1), (0.42, 0.3), (0.7, 0.66), (1.0, NECK.z)]           # its height
AXIS = [(0.0, 0.0), (0.35, -0.1), (0.62, -0.19), (0.85, -0.12), (1.0, NECK.y)]    # the coil's middle leans back, then forward
RAD = [(0.0, 0.0), (0.05, 0.085), (0.2, 0.15), (0.6, 0.145), (1.0, 0.12)]         # the tube's thickness


def vine_point(s):
    th = math.radians(100) - 2 * math.pi * TURNS * (1.0 - s)
    rho = spline(RHO, s)
    return Vector((math.cos(th) * rho, spline(AXIS, s) + math.sin(th) * rho, spline(ZK, s)))


BONES = {
    "root": ((0, 0, 0), (0, 0, 0.1), None),
    "stalk.1": ((0, -0.03, 0.14), (0, -0.16, 0.44), "root"),
    "stalk.2": ((0, -0.16, 0.44), (0, -0.16, 0.76), "stalk.1"),
    "stalk.3": ((0, -0.16, 0.76), tuple(NECK), "stalk.2"),
    "head": (tuple(NECK), tuple(HM @ Vector((0, 0.45, 0))), "stalk.3"),
    "jaw": (tuple(HM @ Vector((0, 0.2, -0.02))), tuple(HM @ Vector((0, 0.6, -0.02))), "head"),
    "sacs": (tuple(HM @ Vector((0, 0.3, 0.16))), tuple(HM @ Vector((0, 0.3, 0.36))), "head"),
}
JOINTS = [0.2, 0.46, 0.78]      # the heights where the vine's bones meet


def _petal(i):
    """Petal i's root, its direction and the axis it flaps about (bulb space)."""
    a = 2 * math.pi * (i + 0.5) / PETALS
    sw = math.radians(26)
    base = Vector((math.cos(a) * 0.17, 0.07, 0.04 + math.sin(a) * 0.17))
    d = Vector((math.cos(a) * math.cos(sw), -math.sin(sw), math.sin(a) * math.cos(sw)))
    return base, d, Vector((-math.sin(a), 0, math.cos(a)))


for _i in range(PETALS):
    _b, _d, _t = _petal(_i)
    BONES["petal.%d" % _i] = (tuple(HM @ _b), tuple(HM @ (_b + _d * 0.5)), "head")

# the bulb's sections along its length: (y, middle height, half width, height above, depth below)
SKULL = [(-0.1, 0.02, 0.1, 0.1, 0.1), (0.0, 0.03, 0.27, 0.25, 0.23), (0.14, 0.04, 0.37, 0.31, 0.28), (0.27, 0.05, 0.41, 0.32, 0.05),
         (0.43, 0.05, 0.4, 0.3, 0.02), (0.58, 0.04, 0.33, 0.24, 0.015), (0.72, 0.03, 0.21, 0.15, 0.01)]
JAW = [(0.15, -0.03, 0.24, 0.02, 0.2), (0.28, -0.02, 0.385, 0.02, 0.25), (0.44, -0.015, 0.385, 0.02, 0.23), (0.58, -0.01, 0.32, 0.02, 0.18),
       (0.71, -0.005, 0.205, 0.015, 0.11)]


def _row(rows, y):
    for a, b in zip(rows, rows[1:]):
        if a[0] <= y <= b[0]:
            t = (y - a[0]) / (b[0] - a[0])
            return tuple(a[i] + (b[i] - a[i]) * t for i in range(1, 5))
    return rows[-1][1:] if y > rows[-1][0] else rows[0][1:]


def _sect(y, zc, rx, up, dn, n_up=7, n_dn=5):
    """One section of the bulb: half an ellipse above the mouth line, half another below it (flat when dn ~ 0)."""
    pts = []
    for i in range(n_up):
        a = math.pi * i / (n_up - 1)
        pts.append(Vector((math.cos(a) * rx, y, zc + math.sin(a) * up)))
    for i in range(1, n_dn + 1):
        a = math.pi + math.pi * i / (n_dn + 1)
        pts.append(Vector((math.cos(a) * rx, y, zc + math.sin(a) * dn)))
    return pts


def build_head():
    col = collection("Thorn")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    k = Kit()
    # ---- the vine: one tube, thorns along its outer side, a pale underside
    N = 34
    ss = [i / (N - 1) for i in range(N)]
    pts = [vine_point(s) for s in ss] + [NECK + Vector((0, 0.07, 0.03))]
    bm_tube(k["teal:0.12:0.9"], pts, [spline(RAD, s) for s in ss] + [0.11], n=7)
    for i in range(15):
        s = 0.13 + 0.058 * i
        p = vine_point(s)
        out = (p - Vector((0, spline(AXIS, s), p.z))).normalized() if spline(RHO, s) > 0.03 else Vector((0, -1, 0))
        out = (out + Vector((0, 0, 0.35 if i % 2 else 0.8))).normalized()
        r = spline(RAD, s)
        bm_crystal(k["cream:0.15:0.75"], p + out * r * 0.6, p + out * (r + 0.17), 0.042, n=4, shoulder=0.22, foot=1.0)
    for o in k.emit("Head_Vine", col, rig=rig, bone="root"):
        skin_chain(o, rig, ["root", "stalk.1", "stalk.2", "stalk.3"], JOINTS)
    # ---- the head, laid out in the bulb's own space (+Y down its length) on its bones, one mesh per color
    hk = BoneKit()
    hk.bone("head")
    # the bulb: one loft, round behind and flat under the upper lip (the palate), ribs down its crown
    bm_loft(hk["grass:0.04:0.8"], [_sect(*r) for r in SKULL], tip1=(0, 0.83, 0.03))
    for ang in (52, 90, 128):
        rib = []
        for y in (0.02, 0.14, 0.27, 0.43, 0.58, 0.72):
            zc, rx, up, dn = _row(SKULL, y)
            a = math.radians(ang)
            rib.append(Vector((math.cos(a) * (rx + 0.008), y, zc + math.sin(a) * (up + 0.008))))
        bm_tube(hk["teal:0.2:0.7"], rib, [0.03, 0.04, 0.042, 0.038, 0.03, 0.016], n=4)

    def lip(rows, y0, y1, zoff, tip):
        left, right = [], []
        for i in range(6):
            y = y0 + (y1 - y0) * i / 5
            zc, rx, up, dn = _row(rows, y)
            z = zc - dn if zoff < 0 else zc + up
            left.append(Vector((-rx, y, z)))
            right.append(Vector((rx, y, z)))
        return left + [Vector(tip)] + list(reversed(right))
    up_lip = lip(SKULL, 0.25, 0.72, -1, (0, 0.82, 0.02))
    bm_tube(hk["red:0.08:0.5"], up_lip, [0.03] + [0.048] * (len(up_lip) - 2) + [0.03], n=6)
    for sx in (-1, 1):
        for i, y in enumerate((0.33, 0.43, 0.53, 0.62, 0.7)):
            zc, rx, up, dn = _row(SKULL, y)
            ln = 0.15 - 0.012 * i
            b = Vector((sx * rx * 0.9, y, zc - dn + 0.01))
            bm_crystal(hk["cream:0.0:0.35"], b, b + Vector((sx * 0.02, 0.012, -ln)), 0.045, n=4, shoulder=0.3, foot=1.0)
        b = Vector((sx * 0.075, 0.775, 0.03))
        bm_crystal(hk["cream:0.0:0.35"], b, b + Vector((0, 0.02, -0.19)), 0.05, n=4, shoulder=0.3, foot=1.0)       # front fangs
    bm_ellipsoid(hk[VENOM], (0, 0.3, -0.02), (0.16, 0.12, 0.1), u=8, v=5)                                            # the glow in its throat
    # the star of spiked sepals behind the ruff, and the cup they grow from
    for i in range(PETALS):
        a = 2 * math.pi * i / PETALS
        b = Vector((math.cos(a) * 0.15, -0.02, 0.03 + math.sin(a) * 0.15))
        bm_crystal(hk["teal:0.2:0.7"], b, Vector((math.cos(a) * 0.5, -0.27, 0.03 + math.sin(a) * 0.5)), 0.085, n=4, shoulder=0.28, foot=1.0)
    bm_cyl(hk["teal:0.2:0.7"], 0.2, 0.25, 0.1, (0, -0.06, 0.03), rot=(90, 0, 0), seg=8)
    # the lower jaw: a bowl, flat on top (the tongue's floor), its own lip, teeth and tongue
    hk.bone("jaw")
    bm_loft(hk["grass:0.04:0.8"], [_sect(*r) for r in JAW], tip1=(0, 0.8, -0.005))
    dn_lip = lip(JAW, 0.26, 0.71, 1, (0, 0.8, 0.0))
    bm_tube(hk["red:0.08:0.5"], dn_lip, [0.03] + [0.044] * (len(dn_lip) - 2) + [0.03], n=6)
    for sx in (-1, 1):
        for i, y in enumerate((0.38, 0.48, 0.575, 0.66)):
            zc, rx, up, dn = _row(JAW, y)
            ln = 0.12 - 0.012 * i
            b = Vector((sx * rx * 0.84, y, zc + up - 0.01))
            bm_crystal(hk["cream:0.0:0.35"], b, b + Vector((sx * 0.015, 0.01, ln)), 0.04, n=4, shoulder=0.3, foot=1.0)
    bm_tube(hk["red:0.08:0.5"], [Vector((0, 0.24, 0.0)), Vector((0, 0.42, 0.03)), Vector((0, 0.6, 0.02)), Vector((0, 0.7, 0.01))],
            [0.05, 0.06, 0.05, 0.0], n=6, squash=2.2)
    # the ruff of petals in the team's color, a bone each, a gold vein down each
    for i in range(PETALS):
        hk.bone("petal.%d" % i)
        b, d, t = _petal(i)
        ln = 0.66 if i % 2 == 0 else 0.58
        pts = [b + d * 0.08, b + d * ln * 0.34 + Vector((0, 0.02, 0)), b + d * ln * 0.6 + Vector((0, 0.035, 0)),
               b + d * ln * 0.85 + Vector((0, 0.02, 0)), b + d * ln - Vector((0, 0.03, 0))]
        bm_tube(hk["team!:0.08:0.72"], pts, [0.03, 0.045, 0.042, 0.03, 0.0], n=6, up=(0, 1, 0), squash=4.1)
        bm_tube(hk["gold:0.15:0.6"], [p + Vector((0, 0.04, 0)) for p in pts[:4]], [0.014, 0.016, 0.013, 0.006], n=4, up=(0, 1, 0))
    # venom sacs bedded in the crown: they swell before a shot
    hk.bone("sacs")
    for x, y, r in ((-0.2, 0.3, 0.09), (0.2, 0.3, 0.09), (0.0, 0.19, 0.075), (-0.13, 0.5, 0.065), (0.13, 0.5, 0.065)):
        zc, rx, up, dn = _row(SKULL, y)
        z = zc + up * math.sqrt(max(0.0, 1 - (x / rx) ** 2))
        bm_ellipsoid(hk[VENOM], (x, y, z - r * 0.12), (r, r, r * 0.8), u=7, v=5)
    hk.transform(HM)
    bulb = hk.emit_bones("Head_Bulb", col, rig)[0]
    inv, inv3 = HM.inverted(), HM.to_3x3().inverted()
    paint_faces(bulb, "red", lambda c, n: abs((inv3 @ n).z) > 0.6 and (inv @ c).y > 0.2 and -0.04 < (inv @ c).z < 0.07, lo=0.55, hi=0.95)
    paint_faces(bulb, "lime", lambda c, n: ((inv3 @ n).z < -0.25 and (inv @ c).y <= 0.2) or ((inv3 @ n).z < -0.5 and (inv @ c).z < -0.07),
                lo=0.08, hi=0.5)
    empty("Muzzle", col, head, tuple(HM @ Vector((0, 0.86, 0.0))), 0.2, "SPHERE")
    return rig


IDLE_LEN = 60
FIRE_LEN = 6


def pose(rig, sway=0.0, nod=0.0, look=0.0, lean=0.0, ext=0.0, jaw=12.0, flare=0.0, ripple=0.0, sacs=1.0, pitch=0.0):
    """sway: the vine's side-to-side wave (degrees); lean: + back, - forward (the dart); ext: the coil stretching;
    jaw: degrees open; flare: the petals thrown back (+) or cupped forward (-); ripple: a phase for their wave."""
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    pb["stalk.1"].rotation_quaternion = q(pb["stalk.1"], (0, 1, 0), sway * 0.5) @ q(pb["stalk.1"], (1, 0, 0), lean)
    pb["stalk.2"].rotation_quaternion = q(pb["stalk.2"], (0, 1, 0), sway * 0.6) @ q(pb["stalk.2"], (1, 0, 0), lean * 0.5 + nod * 0.4)
    pb["stalk.3"].rotation_quaternion = q(pb["stalk.3"], (0, 1, 0), sway * 0.4) @ q(pb["stalk.3"], (1, 0, 0), -lean * 0.4 + nod * 0.6)
    for b, share in (("stalk.2", 0.5), ("stalk.3", 1.0)):
        pb[b].location = arm_space_loc(pb[b], (0, ext * 0.5 * share, ext * share))
    pb["head"].rotation_quaternion = (q(pb["head"], (0, 0, 1), look) @ q(pb["head"], (0, 1, 0), -sway * 1.2)
                                      @ q(pb["head"], (1, 0, 0), -lean * 1.1 - nod + pitch))
    pb["jaw"].rotation_quaternion = q(pb["jaw"], (1, 0, 0), -jaw)
    pb["sacs"].scale = (sacs, sacs, sacs)
    m3 = HM.to_3x3()
    for i in range(PETALS):
        b, d, t = _petal(i)
        w = 7.0 * math.sin(ripple + 2 * math.pi * i / PETALS * 2)
        pb["petal.%d" % i].rotation_quaternion = q(pb["petal.%d" % i], tuple(m3 @ t), -(flare * 30 + w))


def _idle(f):
    ph = 2 * math.pi * f / IDLE_LEN
    chew = max(0.0, math.sin(ph * 3)) ** 2
    return dict(sway=7 * math.sin(ph), nod=3 * math.sin(ph * 2), look=9 * math.sin(ph + 0.8) - 9 * math.sin(0.8), jaw=7 + 15 * chew,
                ripple=ph, sacs=1.0 + 0.12 * math.sin(ph * 2), ext=0.012 * math.sin(ph * 2))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(rig, **_idle(f))
        key_pose(rig, f)
    # fire: frame 1 rears and gapes, frame 2 the dart (the thorn is out), then it springs back through a small overshoot
    shot = {1: dict(lean=7, ext=-0.03, jaw=30, flare=0.5, sacs=1.35, pitch=-6),
            2: dict(lean=-25, ext=0.1, jaw=58, flare=-0.75, sacs=0.55, pitch=5),
            3: dict(lean=-21, ext=0.08, jaw=44, flare=-0.5, sacs=0.6, pitch=3),
            4: dict(lean=-8, ext=0.02, jaw=24, flare=0.15, sacs=0.8),
            5: dict(lean=3, ext=-0.012, jaw=13, flare=0.2, sacs=0.95)}
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        p = _idle(0)
        p.update(shot.get(f, {}))
        pose(rig, **p)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 1.15), "dist": 6.2, "yaw": 150, "pitch": 20, "anim_target": (0, 0.2, 1.45), "anim_dist": 4.6,
           "frames": [("idle", 0), ("idle", 16), ("fire", 1), ("fire", 2), ("fire", 4)],
           "extra": [{"yaw": 118, "pitch": 8, "dist": 3.0, "target": (0, 0.35, 1.55)},
                     {"yaw": 0, "pitch": 40, "dist": 3.4, "target": (0, 0.1, 1.45)},
                     {"yaw": 200, "pitch": 30, "dist": 3.4, "target": (0, 0, 0.6)},
                     {"yaw": 90, "pitch": 6, "dist": 5.0, "target": (0, 0, 1.2)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
