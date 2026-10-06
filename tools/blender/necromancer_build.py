"""Builds the Necromancer (footprint "star5": [0,0] in the middle, with [1,-1], [-1,0], [1,0], [-1,1] at its four
corners), the Bone Legion's tier III caster: dark bolts every 1.25 s, and what dies in its reach gets up again.

    python tools/blender/build.py necromancer --out <preview dir>

The whole cross is one ritual diagram. In the middle a six-sided dais of dark stone rises in three steps; the
necromancer stands on it (Crew, on the Head: the game puts a KayKit Skeleton_Mage there and turns him to his target)
inside a burning summoning circle. From four of the dais's sides a stone channel of soul-fire runs out to a grave on
each outer hex: a kerbed tomb with its slab thrown aside, a pall in the team's color sliding off it, the dead reaching
out; the light in each grave, the channel and the circle are one line. Each outer hex is paved along its channel.
Two braziers on piers flank the dais; a banner stele stands at its far side, a runner in the team's color comes down
its near steps.
On the Head (so they turn with his aim; Rig is under it): the circle's rings and star, six soul-flames round it, and
three burning skulls circling over his head.
Clips: idle (the skulls circle, bob and gnash: one slow round is the loop; the rings turn against each other and
pulse; the flames flicker),
fire (the skulls dart forward into a volley and snap; the circle flares and the flames leap).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "grave_big_common.py"), encoding="utf-8").read())

TID = "necromancer"
CELLS = [(0, 0), (1, -1), (-1, 0), (1, 0), (-1, 1)]
MID = footprint_mid(CELLS)
C = hex_to_world(0, 0, MID)
GRAVES = [hex_to_world(q, s, MID) for q, s in CELLS[1:]]     # the outer cells: front right, front left, back right, back left
TOP = 0.34
STEP = 0.1
DAIS = TOP + 3 * STEP           # the dais's top: where the necromancer stands (the Head)
A1, A2, A3 = 0.86, 0.71, 0.56   # its three steps (each hexagon's middle-of-side distance)
TEAM = "team!:0.1:0.75"
LINE = glow(SOULFIRE, 0.62)     # the diagram's lines
DARK, DARK2 = "stone_dark:0.3:0.98", "stone_dark:0.08:0.8"
GD = [(g - C).normalized() for g in GRAVES]                  # out along each channel
GN = [Vector((-d.y, d.x, 0)) for d in GD]                    # across it
G_R = 2.12                      # how far out each grave's middle is
GW, GL, GH, GT = 0.66, 1.2, 0.24, 0.1                        # a grave's kerb: width, length, height, thickness
KERB = G_R - GL * 0.5           # where a kerb's foot is
STYLES = (("tilt", 1, "round"), ("slid", 1, "cross"), ("broken", -1, "point"), ("askew", 1, "round"))
RING_R = 0.47                   # the summoning circle
WISPS, WISP_R = 6, 0.53
ORBIT_R, ORBIT_Z = 0.9, 1.9     # the skulls' round over his head (in the head's space)
SKULL_S = 0.42
SKULL_A = (90.0, 210.0, 330.0)
FORM = ((0.0, 0.95, 2.32), (-0.5, 0.82, 1.84), (0.5, 0.82, 1.84))     # where each skull darts to when he casts


def _grave(k, rnd, M, style, flip, kind):
    """An opened grave in its own space (its middle at the origin on the ground, its head and headstone toward +Y),
    set down with M. style: how its slab was thrown off; flip: to which side."""
    t = Kit()
    zt = 0.05 + GH                                              # the kerb's top
    for sx in (-1, 1):
        bm_box(t[STONE], (GT, GL, zt), (sx * (GW - GT) * 0.5, 0, zt * 0.5))
        bm_box(t[STONE], (GW - 2 * GT, GT, zt), (0, sx * (GL - GT) * 0.5, zt * 0.5))
        bm_box(t[STONE_LT], (GT + 0.05, GL + 0.05, 0.06), (sx * (GW - GT) * 0.5, 0, 0.03))             # a footing course
        bm_box(t[STONE_LT], (GW - 2 * GT, GT + 0.05, 0.06), (0, sx * (GL - GT) * 0.5, 0.03))
    bm_box(t[SOCKET], (GW - 2 * GT, GL - 2 * GT, 0.03), (0, 0, 0.075))
    bm_box(t[glow(SOULFIRE, 0.6)], (GW - 2 * GT - 0.1, GL - 2 * GT - 0.16, 0.02), (0, 0, 0.1))
    lw, ll, lt = GW + 0.07, GL + 0.07, 0.075

    def slab(l0, l1, pall=False, mark=False, flaps=True):
        """A piece of the slab from l0 to l1 along it (its underside on z = 0), a pall over it, a cross cut in it."""
        s = Kit()
        bm_box(s[STONE_LT], (lw, l1 - l0, lt), (0, (l0 + l1) * 0.5, lt * 0.5))
        if mark:
            bm_box(s[SOCKET], (0.05, 0.44, 0.012), (0, l1 - 0.3, lt + 0.002))
            bm_box(s[SOCKET], (0.26, 0.05, 0.012), (0, l1 - 0.2, lt + 0.002))
        if pall:
            pl = min(0.56, l1 - l0 - 0.04)
            y0 = l0 + 0.03
            bm_box(s[TEAM], (lw + 0.012, pl, 0.016), (0, y0 + pl * 0.5, lt + 0.008))
            bm_box(s["cream:0.2:0.7"], (0.05, pl * 0.7, 0.008), (0, y0 + pl * 0.5, lt + 0.02))
            bm_box(s["cream:0.2:0.7"], (0.26, 0.05, 0.008), (0, y0 + pl * 0.62, lt + 0.02))
            if flaps:
                for sx in (-1, 1):
                    a, b = (sx * (lw * 0.5 + 0.008), y0, lt + 0.014), (sx * (lw * 0.5 + 0.008), y0 + pl, lt + 0.014)
                    bm_cloth(s[TEAM], a if sx > 0 else b, b if sx > 0 else a, 0.21, cols=3, rows=2, wave=0.015, tatter=0.45, rnd=rnd, th=0.012)
        return s
    arms = []
    if style == "slid":                 # pushed off to one side, a little askew: an arm comes up through the gap
        stamp(t, slab(-ll * 0.5, ll * 0.5, pall=True, mark=True), xf((flip * 0.21, 0.03, zt), (0, 0, flip * 10)))
        arms.append(((-flip * 0.16, -0.12, 0.05), (-flip * 0.3, -0.2, 0.78), (-flip, -0.4, 0), 0.38, 0.35))
    elif style == "tilt":               # heaved up on its long edge from inside: a skull looks out under it
        hinge = Matrix.Translation((-flip * lw * 0.5, 0, zt)) @ Matrix.Rotation(math.radians(-flip * 32), 4, "Y") @ Matrix.Translation((flip * lw * 0.5, 0, 0))
        stamp(t, slab(-ll * 0.5, ll * 0.5, mark=True), hinge)
        bm_box(t[TEAM], (0.3, 0.62, 0.024), (-flip * (GW * 0.5 + 0.2), -0.12, 0.062), (0, flip * 5, 4))      # its pall, fallen beside it
        bm_box(t[TEAM], (0.2, 0.36, 0.03), (-flip * (GW * 0.5 + 0.13), 0.06, 0.08), (0, flip * 24, -12))
        skull(t, xf((flip * 0.08, -0.22, zt + 0.06), (-24, 0, -90 * flip)), s=0.26, bone=BONE, detail=1, jaw=True, eyes=glow(SOULFIRE, 0.8))
        arms.append(((flip * 0.12, 0.14, 0.05), (flip * 0.34, 0.2, 0.5), (flip, 0.0, -0.35), 0.36, 0.85))
    elif style == "broken":             # cracked across: one half still lies there, the other has slid off
        stamp(t, slab(-ll * 0.5, -0.03, pall=True), xf((flip * 0.02, 0, zt), (0, 0, 3)))
        stamp(t, slab(0.03, ll * 0.5, mark=True), xf((flip * 0.42, 0.02, zt - 0.11), (0, flip * 33, flip * -6)))
        arms.append(((-flip * 0.12, 0.26, 0.05), (-flip * 0.33, 0.3, 0.42), (-flip, 0.0, -0.4), 0.34, 0.85))
        arms.append(((flip * 0.06, 0.34, 0.05), (flip * 0.1, 0.4, 0.82), (0.25 * flip, -1.0, 0), 0.38, 0.35))
    else:                               # swung aside about its head end: an arm reaches for its master
        piv = ll * 0.5 - 0.12
        stamp(t, slab(-ll * 0.5, ll * 0.5, pall=True, mark=True),
              Matrix.Translation((0, piv, zt)) @ Matrix.Rotation(math.radians(flip * 19), 4, "Z") @ Matrix.Translation((0, -piv, 0)))
        arms.append(((flip * 0.12, -0.3, 0.05), (flip * 0.2, -0.5, 0.72), (0.15 * flip, -1.0, 0), 0.4, 0.4))
    for base, wrist, out, s, flex in arms:
        reach_arm(t[BONE if s > 0.36 else BONE_OLD], base, wrist, out, s=s, side=flip, curl=0.3, flex=flex, segs=3, rnd=rnd, elbow=0.0)
    gravestone(t, xf((0, GL * 0.5 + 0.2, 0.0), (rnd.uniform(-6, 5), rnd.uniform(-4, 4), rnd.uniform(-7, 7))), kind, w=0.48, h=0.8, th=0.12)
    for (x, y), h in (((-0.33, GL * 0.5 + 0.02), 0.16), ((0.34, GL * 0.5 - 0.02), 0.11), ((0.37, GL * 0.5 - 0.2), 0.19)):     # candles
        bm_cyl(t["cream:0.1:0.7"], 0.045, 0.038, h, (x, y, 0.05 + h * 0.5), seg=6)
        bm_cyl(t[glow(SOULFIRE, 0.75)], 0.032, 0.0, 0.09, (x, y, 0.05 + h + 0.045), seg=4)
    return stamp(k, t, M)


def build_base():
    col = collection("Necromancer")
    root = empty("Necromancer", col, None, (0, 0, 0), 0.6, "ARROWS")
    rnd = random.Random(41)
    plinth_cut(CELLS, col, root, TOP, grid=0.42)
    k = Kit()
    # ---- the dais: three six-sided steps of dark stone, a wheel of slabs on top
    for i, (ap, n) in enumerate(((A1, 4), (A2, 3), (A3, 3))):
        z = TOP + STEP * i - (0.03 if i == 0 else 0.0)
        hex_course(k, rnd, C, ap, 0.26, z, TOP + STEP * (i + 1) - z, per_side=n, keys=(DARK, DARK2, DARK) if i != 1 else (DARK2, DARK, DARK2))
        prism(k[SOCKET], hex_pts(C, ap - 0.1), z, TOP + STEP * (i + 1) - 0.012)
    inner, hub = hex_pts(C, A3 - 0.27), hex_pts(C, 0.14)
    for j in range(6):
        a, b, ia, ib = inner[j], inner[(j + 1) % 6], hub[j], hub[(j + 1) % 6]
        prism(k[DARK2 if j % 2 else STONE_LT], [a.lerp(b, 0.03), a.lerp(b, 0.97), ib.lerp(ia, 0.06), ia.lerp(ib, 0.06)], DAIS - 0.06, DAIS - 0.004 - rnd.uniform(0, 0.006))
    prism(k[DARK], hex_pts(C, 0.13), DAIS - 0.06, DAIS - 0.002)
    for j in (1, 2, 4, 5):                                  # low posts on its other corners, a skull keeping watch on each
        a = math.radians(60 * j)
        cp = C + Vector((math.cos(a), math.sin(a), 0)) * (A1 / math.cos(math.radians(30)) - 0.11)
        bm_box(k[DARK2], (0.17, 0.17, 0.34), (cp.x, cp.y, TOP + STEP + 0.165), (0, 0, 60 * j))
        bm_box(k[STONE_LT], (0.22, 0.22, 0.05), (cp.x, cp.y, TOP + STEP + 0.36), (0, 0, 60 * j))
        skull(k, xf((cp.x, cp.y, TOP + STEP + 0.385 + 0.065), (0, 0, 60 * j - 90)), s=0.18, bone=BONE_OLD, detail=0, jaw=False, eyes=glow(SOULFIRE, 0.8))
    k.emit("Dais", col, root, vary=0.08, seed=3)
    # ---- the four channels of soul-fire, each one line from the circle down the steps and out into its grave
    for i in range(4):
        d, n = GD[i], GN[i]
        for sd in (-1, 1):
            for j, (a, b) in enumerate(((A1 + 0.012, 1.19), (1.2, KERB - 0.01))):
                p0, p1 = C + d * a + n * (sd * 0.12), C + d * b + n * (sd * 0.12)
                bm_beam(k[STONE if (j + (sd > 0)) % 2 else STONE_LT], (p0.x, p0.y, TOP + 0.03), (p1.x, p1.y, TOP + 0.03), 0.08, 0.085)
        prof = [(RING_R + 0.02, DAIS + 0.012), (A3 + 0.012, DAIS + 0.012), (A3 + 0.012, TOP + 2 * STEP + 0.012), (A2 + 0.012, TOP + 2 * STEP + 0.012),
                (A2 + 0.012, TOP + STEP + 0.012), (A1 + 0.012, TOP + STEP + 0.012), (A1 + 0.012, TOP + 0.028), (KERB - 0.012, TOP + 0.028),
                (KERB - 0.012, TOP + 0.04 + GH)]
        bm_ribbon(k[LINE], [C + d * r + Vector((0, 0, z)) for r, z in prof], n, 0.12)
    k.emit("Channels", col, root, vary=0.08, seed=5)
    # ---- the graves
    for i, (style, flip, kind) in enumerate(STYLES):
        gc = C + GD[i] * G_R
        _grave(k, rnd, xf((gc.x, gc.y, TOP - 0.012), (0, 0, math.degrees(math.atan2(GD[i].y, GD[i].x)) - 90)), style, flip, kind)
    k.emit("Graves", col, root, vary=0.08, seed=7)
    # ---- each outer hex paved along its channel
    foot = outline(CELLS, 0.2)

    def paved(i):
        d, n = GD[i], GN[i]

        def where(x, y):
            if not inside(foot, x, y) or max(abs((x - C.x) * math.cos(a) + (y - C.y) * math.sin(a)) for a in (0.5236, 1.5708, 2.618)) < A1 + 0.14:
                return False
            if min(range(4), key=lambda j: (x - GRAVES[j].x) ** 2 + (y - GRAVES[j].y) ** 2) != i:
                return False
            u, v = (x - C.x) * d.x + (y - C.y) * d.y, (x - C.x) * n.x + (y - C.y) * n.y
            if abs(v) < 0.31 and u < KERB + 0.05:
                return False
            if abs(v) < GW * 0.5 + 0.02 and KERB - 0.02 < u < G_R + GL * 0.5 + 0.02:
                return False
            return abs(y) > 0.26 or abs(abs(x) - 1.12) > 0.42
        return where
    for i in range(4):
        bm_slabs(k[STONE if i in (0, 3) else "stone_dark:0.2:0.9"], rnd, paved(i), (-3.3, -2.4, 3.3, 2.4), TOP - 0.004, size=0.4, gap=0.034, h=0.05,
                 keep=0.93, yaw=math.degrees(math.atan2(GD[i].y, GD[i].x)), heave=0.08)
    k.emit("Paving", col, root, vary=0.1, seed=9)
    # ---- two braziers of soul-fire on piers at the dais's side corners
    for sx in (-1, 1):
        px = sx * 1.12
        pier(k, rnd, (px, 0), 0.34, TOP - 0.02, 1.02, cap="flat", course=0.17)
        fp = brazier(k, (px, 0, TOP + 1.07), h=0.3, r=0.2, coals=glow(SOULCORE, 0.8))
        bm_flame(k[glow(SOULFIRE, 0.7)], rnd, fp, h=0.5, r=0.15, n=4)
    k.emit("Braziers", col, root, vary=0.09, seed=11)
    # ---- the banner stele at the dais's far side; the runner down its near steps
    sy = A2 + 0.075
    gravestone(k, xf((0, sy, TOP + STEP - 0.01)), "point", w=0.58, h=1.74, th=0.14, stone=STONE, base=False)
    bm_box(k[STONE_LT], (0.74, 0.2, 0.12), (0, sy + 0.01, TOP + STEP + 0.05))
    by, zr = sy - 0.07 - 0.04, TOP + STEP + 1.44
    bm_cloth(k[TEAM], (-0.24, by, zr), (0.24, by, zr), 0.94, cols=4, rows=4, wave=0.03, tatter=0.3, rnd=rnd, th=0.014)
    bm_beam(k["wood_dark:0.2:0.7"], (-0.3, by, zr + 0.02), (0.3, by, zr + 0.02), 0.045, 0.045)
    skull(k, frame((0, by - 0.035, zr - 0.3), (0, -1, 0)), s=0.24, bone=BONE, detail=1, jaw=False, eyes=glow(VIOLET, 0.9))
    bm_disc(k[glow(VIOLET, 0.9)], (0, sy - 0.073, TOP + STEP + 1.6), (0, -1, 0), 0.06, n=6)
    k.emit("Stele", col, root, vary=0.06, seed=13)
    rp = [(-(RING_R + 0.06), DAIS + 0.014), (-(A3 + 0.016), DAIS + 0.014), (-(A3 + 0.016), TOP + 2 * STEP + 0.014), (-(A2 + 0.016), TOP + 2 * STEP + 0.014),
          (-(A2 + 0.016), TOP + STEP + 0.014), (-(A1 + 0.016), TOP + STEP + 0.014), (-(A1 + 0.016), TOP + 0.02)]
    bm_ribbon(k[TEAM], [Vector((0, y, z)) for y, z in rp], (1, 0, 0), 0.46)
    for sx in (-1, 1):
        bm_ribbon(k["cream:0.2:0.7"], [Vector((sx * 0.19, y - (0.004 if j % 2 else 0.0), z + 0.004)) for j, (y, z) in enumerate(rp)], (1, 0, 0), 0.035)
    k.emit("Runner", col, root)
    head = empty("Head", col, root, (C.x, C.y, DAIS), 0.5, "SINGLE_ARROW")
    crew = empty("Crew", col, head, (0, 0, 0), 0.3, "SINGLE_ARROW")
    empty("Muzzle", col, head, (0.3, 0.35, 1.35), 0.2, "SPHERE")
    crew_standin(col, crew)
    return root


def _skull_frame(i):
    a = math.radians(SKULL_A[i])
    p = Vector((math.cos(a) * ORBIT_R, math.sin(a) * ORBIT_R, ORBIT_Z))
    return p, frame(p, Vector((-math.sin(a), math.cos(a), 0)))


def build_head():
    col = collection("Necromancer")
    head = bpy.data.objects["Head"]
    bones = {"root": ((0, 0, 0), (0, 0, 0.2), None),
             "circle": ((0, 0, 0.012), (0, 0, 0.212), "root"), "star": ((0, 0, 0.016), (0, 0, 0.216), "root"),
             "orbit": ((0, 0, ORBIT_Z), (0, 0, ORBIT_Z + 0.2), "root")}
    for i in range(WISPS):
        a = math.radians(60 * i)
        bones["wisp.%d" % i] = ((math.cos(a) * WISP_R, math.sin(a) * WISP_R, 0.02), (math.cos(a) * WISP_R, math.sin(a) * WISP_R, 0.27), "root")
    for i in range(3):
        p, M = _skull_frame(i)
        bones["skull.%d" % i] = (tuple(p), tuple(M @ Vector((0, 0.2, 0))), "orbit")
        bones["jaw.%d" % i] = (tuple(M @ (Vector((0, -0.04, -0.1)) * SKULL_S)), tuple(M @ (Vector((0, 0.33, -0.42)) * SKULL_S)), "skull.%d" % i)
    rig = make_rig(col, head, bones)
    k = Kit()
    # ---- the summoning circle: two rings and the signs between them; the six-pointed star inside
    bm_annulus(k[LINE], (0, 0), RING_R - 0.05, RING_R + 0.03, 0.012, seg=24)
    bm_annulus(k[LINE], (0, 0), 0.295, 0.34, 0.012, seg=18)
    for i in range(6):
        a = math.radians(30 + 60 * i)
        d, n = Vector((math.cos(a), math.sin(a), 0)), Vector((-math.sin(a), math.cos(a), 0))
        bm_ribbon(k[LINE], [d * 0.345 + Vector((0, 0, 0.012)), d * 0.42 + Vector((0, 0, 0.012))], n, 0.036)
        bm_ribbon(k[LINE], [d * 0.385 - n * 0.05 + Vector((0, 0, 0.012)), d * 0.385 + n * 0.05 + Vector((0, 0, 0.012))], d, 0.032)
        a2 = a + math.radians(30)
        d2 = Vector((math.cos(a2), math.sin(a2), 0))
        bm_disc(k[LINE], d2 * 0.382 + Vector((0, 0, 0.012)), (0, 0, 1), 0.03, n=4)
    k.emit("Head_Circle", col, rig=rig, bone="circle")
    for tri in (90, 270):
        pts = [Vector((math.cos(math.radians(tri + 120 * j)) * 0.31, math.sin(math.radians(tri + 120 * j)) * 0.31, 0.016)) for j in range(3)]
        for j in range(3):
            a, b = pts[j], pts[(j + 1) % 3]
            bm_ribbon(k[glow(SOULCORE, 0.8)], [a, b], (b - a).cross(Vector((0, 0, 1))), 0.038)
    bm_annulus(k[glow(SOULCORE, 0.8)], (0, 0), 0.07, 0.095, 0.016, seg=6)
    k.emit("Head_Star", col, rig=rig, bone="star")
    # ---- six soul-flames standing round the circle
    for i in range(WISPS):
        a = math.radians(60 * i)
        c = Vector((math.cos(a) * WISP_R, math.sin(a) * WISP_R, 0.02))
        bm_flame(k[glow(SOULFIRE, 0.7)], random.Random(3), c, h=0.25, r=0.06, n=2, sides=4)
        bm_cyl(k[glow(SOULCORE, 0.85)], 0.042, 0.0, 0.085, (c.x, c.y, 0.062), seg=4)
    k.emit("Head_Wisps", col, rig=rig, bones=["wisp.%d" % i for i in range(WISPS)])
    # ---- three burning skulls circling over him: jaws on hinges, violet eyes, a crest of soul-fire streaming back
    for i in range(3):
        p, M = _skull_frame(i)
        tan = M.to_3x3() @ Vector((0, 1, 0))
        sj = Kit()
        skull(k, M, s=SKULL_S, bone=BONE, detail=2, jaw=True, eyes=glow(VIOLET, 0.9), jaw_k=sj)
        bm_flame(k[glow(SOULFIRE, 0.7)], random.Random(4), p + Vector((0, 0, 0.07)) - tan * 0.06, h=0.36, r=0.12, n=3, sides=4, lean=-tan * 0.3)
        k.emit("Head_Skull%d" % i, col, rig=rig, bone="skull.%d" % i)
        stamp(k, sj, M @ Matrix.Diagonal((SKULL_S, SKULL_S, SKULL_S, 1.0)))
        k.emit("Head_Jaw%d" % i, col, rig=rig, bone="jaw.%d" % i)
    return rig


IDLE_LEN = 288                  # one whole round of the skulls (so the loop closes exactly)
FIRE_LEN = 20


def pose(fk, f, cast=0.0, bite=0.0, flare=0.0):
    """f: where the idle is (the skulls' place on their round, the rings' turn); cast: 0..1, the skulls darted forward
    into their volley; bite: their jaws wide; flare: the circle and its flames leaping."""
    fk.clear()
    R = Fk.rot
    ph = 2 * math.pi * f / IDLE_LEN
    turn = 360.0 * f / IDLE_LEN
    fk.put("circle", R((0, 0, 1), turn + 20.0 * flare), loc=(0, 0, 0.03 * flare), scale=1.0 + 0.035 * math.sin(6 * ph) + 0.16 * flare)
    fk.put("star", R((0, 0, 1), -turn - 30.0 * flare), loc=(0, 0, 0.06 * flare), scale=1.0 + 0.06 * math.sin(6 * ph + 1.0) + 0.3 * flare)
    for i in range(WISPS):
        b = fk.pb["wisp.%d" % i]
        tall = 1.0 + 0.26 * math.sin(9 * ph + i * 1.9) + 0.12 * math.sin(21 * ph + i) + 1.4 * flare
        wide = 1.0 + 0.1 * math.sin(15 * ph + i * 2.3) + 0.25 * flare
        b.scale = (wide, tall, wide)
    fk.put("orbit", R((0, 0, 1), turn))
    for i, a in enumerate(SKULL_A):
        p, M = _skull_frame(i)
        wa = math.radians(a + turn)                         # where it is round him now
        face = ((-a + 180.0) % 360.0 - 180.0) * cast        # turned to look where he aims
        look = 14.0 * math.sin(2 * wa + 0.7) * (1.0 - cast)
        nod = M.to_3x3() @ Vector((1, 0, 0))
        fk.put("skull.%d" % i, R((0, 0, 1), face + look) @ Quaternion(nod, math.radians(-10.0 * math.sin(wa) * (1.0 - cast) + 8.0 * cast)),
               loc=(Vector(FORM[i]) - p) * cast + Vector((0, 0, 0.1 * math.sin(wa + 1.0) * (1.0 - cast))), scale=1.0 + 0.18 * cast)
        gnash = max(0.0, math.sin(5 * wa)) ** 2             # (by where it is, so the round loops)
        fk.put("jaw.%d" % i, Quaternion(nod, math.radians(-(5.0 + 15.0 * gnash * (1.0 - cast) + 42.0 * bite))))


def build_anims():
    rig = bpy.data.objects["Rig"]
    fk = Fk(rig)
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(fk, f)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        # 0-3: the skulls dart forward into a volley, jaws wide, the circle flares; 4-6: they snap (the bolt goes);
        # then they drift back to their round
        cast = smooth(f / 3.0) * (1.0 - smooth((f - 8) / 11.0))
        bite = smooth(f / 2.5) * (1.0 - smooth((f - 4) / 2.0))
        pose(fk, 0, cast=cast, bite=bite, flare=pulse(f, 0, 3, 13))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 0.9), "dist": 12.0, "yaw": -32, "pitch": 26, "anim_target": (0, 0, 1.5), "anim_dist": 7.0,
           "frames": [("idle", 0), ("idle", 60), ("fire", 3), ("fire", 5), ("fire", 11)],
           "extra": [{"yaw": 0, "pitch": 52, "dist": 6.5, "target": (0, -0.2, 0.9)},
                     {"yaw": 20, "pitch": 40, "dist": 5.0, "target": (GRAVES[2].x, GRAVES[2].y, 0.5)},
                     {"yaw": -25, "pitch": 40, "dist": 5.0, "target": (GRAVES[1].x * 0.9, GRAVES[1].y * 0.9, 0.5)},
                     {"yaw": 160, "pitch": 18, "dist": 9.5, "target": (0, 0, 1.0)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
