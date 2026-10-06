"""Builds the Plague Cauldron (footprint "pair": [0,0] front, [0,1] back), a Bone Legion tower: it lobs a glob of
plague every 1.8 s that poisons whole groups.

    python tools/blender/build.py plague_cauldron --out <preview dir>

One plague kitchen. On the front cell a huge black iron cauldron sits sunk in a round stone hearth, green soul-fire
licking up round its belly and glowing out of three stoke holes, its brew bubbling round a floating skull and bones.
On the hearth's coping turns a timber collar carrying an onager: two leaning uprights, a twisted-rope skein, a stop
beam with a team-coloured pad and banner, and a long timber-and-bone arm ending in a great iron ladle that lies
scooped in the brew (the Head turns it all; Muzzle where the ladle lets go). A skeleton mage (Crew) rides the collar
beside the pot, stirring. On the back cell, the plague doctor's crooked lean-to under a team-tiled roof: herbs and a
rat cage hung from its beam, his beaked mask and hat on a post, a workbench of bottles; a duckboard runs from it to
the hearth and a chute feeds bones from its hopper into the back stoke hole.
Clips: idle (bubbles swell and pop on the floating bones, steam puffs rise, the fire flickers, the skull bobs, the
arm creaks, the banner stirs), fire (the arm dips, whips over and slams the pad, the brew splashes, the frame
shudders, then the ladle sinks back to scoop again).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "grave_shrines_common.py"), encoding="utf-8").read())

TID = "plague_cauldron"
CELLS = [(0, 0), (0, 1)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)          # front: the hearth and the cauldron
B = hex_to_world(0, 1, MID)          # back: the lean-to
TOP = 0.34
T = TOP
HR = 0.8                             # the hearth's outer radius
HZ = T + 0.47                        # the top of its coping: the Head sits here, on the cauldron's axis
H0 = Vector((F.x, F.y, HZ))
STOKE = (45.0, 165.0, 285.0)         # the stoke holes (degrees round the hearth; the chute feeds the last)
# the cauldron's profile (radius, height) in the head's space: belly, lip, and back down inside to under the brew
CAUL = [(0.18, -0.34), (0.32, -0.29), (0.42, -0.18), (0.49, -0.03), (0.52, 0.12), (0.51, 0.28), (0.46, 0.42), (0.465, 0.48),
        (0.52, 0.5), (0.545, 0.54), (0.515, 0.585), (0.455, 0.565), (0.445, 0.38)]
BREW = 0.44                          # the brew's surface
P = Vector((0.0, 0.82, 0.8))         # the arm's pivot (in the skein)
LADLE = Vector((0.0, -0.2, 0.47))    # the ladle bowl's middle at rest, scooped in the brew
D0 = (LADLE - P).normalized()        # the arm's direction at rest (back and down)
ARM_L = (LADLE - P).length
NUP = Vector((0.0, D0.z, -D0.y))     # the bowl's opening at rest (up, square to the arm)
SWING = ((90.0 - math.degrees(math.atan2(D0.z, D0.y)) + 180.0) % 360.0) - 180.0   # rest -> upright, about +X
SLOPE = 0.29                         # the uprights lean forward this much (y per z), through the pivot
UPX = 0.3


def up_y(z):
    return P.y + SLOPE * (z - P.z)


CROSS = Vector((0.0, up_y(P.z + 0.62), P.z + 0.62))      # the stop beam: the arm, upright, rests on its pad
BAN_TOP = CROSS + Vector((0.0, 0.075, -0.03))
MUZZLE = Vector((0.0, P.y + 0.05, P.z + ARM_L))          # the bowl's middle with the arm upright
CREW = Vector((-0.6, -0.4, 0.09))                         # the mage on the collar, back-left of the pot
SPL = Vector((LADLE.x, LADLE.y, BREW))
BUBS = [(0.13, 0.2, BREW + 0.07), (-0.16, 0.19, BREW + 0.02), (0.29, -0.02, BREW), (-0.31, -0.1, BREW), (0.04, 0.36, BREW)]
BUB_CYC = (2, 3, 2, 3, 4)
STEAM = [(0.12, 0.1), (-0.17, 0.02), (0.2, -0.22)]
FIRES = 6
DB0, DB1 = Vector((-0.2, -0.78, 0)), F + Vector((math.cos(math.radians(255)), math.sin(math.radians(255)), 0)) * 0.84
CH1 = F + Vector((math.cos(math.radians(STOKE[2])), math.sin(math.radians(STOKE[2])), 0)) * 0.84
CH0 = Vector((0.36, -0.45, 0))
LY0, LY1 = -1.78, -0.84              # the lean-to's back wall and front posts
ZB, ZF = T + 0.55, T + 1.12           # ... their tops
LW = 0.56                            # the front posts' half spacing


def _yaw_to(dx, dy):
    """The yaw that turns +Y toward (dx, dy)."""
    return math.degrees(math.atan2(-dx, dy))


def _seg_d(p, a, b):
    p, a, b = Vector((p[0], p[1], 0)), Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0))
    ab = b - a
    t = min(max((p - a).dot(ab) / max(ab.length_squared, 1e-9), 0.0), 1.0)
    return (a + ab * t - p).length


def _caul_r(z):
    pts = CAUL[:10]
    for (r0, z0), (r1, z1) in zip(pts, pts[1:]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / max(z1 - z0, 1e-6)
    return pts[-1][0] if z > pts[-1][1] else pts[0][0]


def _shift(k, v):
    v = Vector(v)
    for bm in k.parts.values():
        bmesh.ops.translate(bm, vec=v, verts=bm.verts)


def _roof_z(y, x=0.0):
    """The lean-to roof's underside: low over the back wall, high over the front beam; its right front sags."""
    t = (y - (LY0 - 0.12)) / ((LY1 + 0.14) - (LY0 - 0.12))
    return ZB + 0.08 + (ZF + 0.12 - ZB - 0.08) * t - 0.11 * t * max(0.0, x / (LW + 0.12)) ** 1.5


def build_base():
    col = collection("Plague_cauldron")
    root = empty("Plague_cauldron", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(31)
    k = Kit()
    # ---- the hearth: two courses of dark blocks round the fire, three stoke holes, a heavy coping the collar rides on
    def hole(a):
        return any(abs((a - h + 180.0) % 360.0 - 180.0) < 24.0 for h in STOKE)
    for c in range(2):
        bm_block_course(k["stone_dark:0.15:0.85"], rnd, (F.x, F.y, 0), HR - 0.012 * c, T + 0.19 * c, 0.19, 12, depth=0.17,
                        phase=0.5 * c, skip=hole)
    k.emit("Hearth", col, root, bevel=0.012, vary=0.09)
    bm_block_course(k["stone_dark:0.0:0.5"], rnd, (F.x, F.y, 0), HR + 0.04, T + 0.38, HZ - T - 0.38, 14, depth=0.22, gap=0.03)
    k.emit("Hearth_Coping", col, root, bevel=0.012, vary=0.07)
    for a in (105.0, 225.0, 345.0):                           # skulls mortared into the hearth between the stoke holes
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        gs_skull(k, place((F.x + ca * (HR - 0.02), F.y + sa * (HR - 0.02), T + 0.07), yaw=_yaw_to(ca, sa), scale=0.22), n=6)
    k.emit("Hearth_Skulls", col, root, vary=0.05)
    # the fire bed: a black floor, charred logs and bones, glowing embers, flames standing in the stoke holes
    bm_cyl(k["black:0.4:0.8"], 0.66, 0.66, 0.04, (F.x, F.y, T + 0.02), seg=14)
    for i in range(6):
        a = math.radians(30 + 60 * i + rnd.uniform(-10, 10))
        p0 = F + Vector((math.cos(a) * 0.2, math.sin(a) * 0.2, T + 0.06))
        p1 = F + Vector((math.cos(a) * 0.62, math.sin(a) * 0.62, T + 0.09))
        bm_beam(k["wood_dark:0.55:1.0"], p0, p1, 0.09, 0.08)
    k.emit("Fire_Bed", col, root)
    em = k[glow((0.45, 1.0, 0.25), 0.75)]
    for i in range(10):
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(0.25, 0.6)
        bm_boulder(em, rnd, (F.x + math.cos(a) * r, F.y + math.sin(a) * r, T + 0.04), rnd.uniform(0.04, 0.07), squash=(1, 1, 0.6), n=7)
    for a in STOKE:
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        gs_flame(k[glow(NECRO, 0.95)], (F.x + ca * 0.68, F.y + sa * 0.68, T + 0.03), h=0.3, r=0.09, rnd=rnd, tongues=3)
    k.emit("Fire_Glow", col, root)
    # ---- the cauldron (built in the head's space, then set on the hearth): black iron, riveted bands, ring handles
    gs_lathe(k["black:0.0:0.45"], (0, 0, 0), CAUL, n=16, tip0=-0.37, cap1=True)
    for z in (0.0, 0.3):
        rr = _caul_r(z) + 0.01
        gs_lathe(k[IRON], (0, 0, 0), [(rr - 0.006, z - 0.035), (rr + 0.008, z), (rr - 0.006, z + 0.035)], n=16)
        for i in range(8):
            a = 2 * math.pi * (i + 0.5 * (z > 0.1)) / 8
            bm_box(k[IRON], (0.03, 0.03, 0.03), (math.cos(a) * (rr + 0.012), math.sin(a) * (rr + 0.012), z), (0, 0, math.degrees(a)))
    for sx in (-1, 1):
        bm_box(k[IRON], (0.08, 0.1, 0.07), (sx * 0.47, 0, 0.46))
        ring(k["iron:0.2:0.9"], (sx * 0.545, 0, 0.33), 0.12, 0.085, -0.02, 0.02, seg=10, axis="X")
    bm_cyl(k[glow((0.2, 0.85, 0.16), 0.7)], 0.452, 0.452, 0.03, (0, 0, BREW - 0.015), seg=16)
    fr = k[glow((0.5, 1.0, 0.36), 0.85)]
    for i in range(9):
        a = 2 * math.pi * i / 9 + rnd.uniform(-0.2, 0.2)
        r = rnd.uniform(0.33, 0.4)
        bm_blob(fr, rnd, (math.cos(a) * r, math.sin(a) * r, BREW + 0.005), rnd.uniform(0.05, 0.08), squash=(1.3, 1.3, 0.35), jitter=0.2)
    for a in (20, 140, 215, 320):                               # brew slopped over the lip, running down the belly
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        zs = (0.565, 0.5, 0.42, 0.34, 0.26 + 0.05 * (a % 3))
        bm_tube(k[glow(NECRO, 0.8)], [(ca * (_caul_r(min(z, 0.54)) + 0.012), sa * (_caul_r(min(z, 0.54)) + 0.012), z) for z in zs],
                [0.032, 0.028, 0.024, 0.02, 0.0], n=5)
    _shift(k, H0)
    k.emit("Cauldron", col, root)
    # ---- paving: worn flags round the hearth, across the waist and round the lean-to
    def pave(x, y):
        if not in_footprint(CELLS, x, y, 0.2):
            return False
        if (x - F.x) ** 2 + (y - F.y) ** 2 < (HR + 0.1) ** 2:
            return False
        if y < LY1 + 0.1 and abs(x) < 0.74:
            return False
        return _seg_d((x, y), DB0, DB1) > 0.24 and _seg_d((x, y), CH0, CH1) > 0.15
    bm_flagstones(k["stone:0.45:0.95"], rnd, pave, (-1.3, -2.2, 1.3, 2.2), T, size=0.26, keep=0.88)
    k.emit("Paving", col, root, vary=0.1)
    # ---- the plague doctor's lean-to: a low rubble wall at the back, two crooked posts at the front, a tiled roof
    gs_block_wall(k["stone_dark:0.15:0.8"], rnd, (-0.46, LY0), (0.46, LY0), T, ZB, th=0.18, course=0.18, block=0.3)
    k.emit("Leanto_Wall", col, root, bevel=0.01, vary=0.09)
    bm_planks(k["wood:0.35:0.9"], rnd, (-0.5, LY0 + 0.09, T + 0.05), (1.0, 0, 0), (0, LY1 - LY0 + 0.02, 0), 5, th=0.05)
    k.emit("Leanto_Floor", col, root, vary=0.08)
    wd = k["wood_dark:0.2:0.8"]
    posts = {}
    for sx, lean in ((-1, -0.05), (1, 0.04)):
        x = sx * LW
        top = Vector((x + lean, LY1 - 0.01, ZF))
        posts[sx] = top
        bm_tube(wd, [(x, LY1, T), (x + lean * 0.35, LY1 + 0.025, T + 0.6), tuple(top)], [0.07, 0.062, 0.058], n=6)
    bm_beam(wd, (-LW - 0.14, LY1, ZF + 0.03), (0.02, LY1, ZF - 0.02), 0.1, 0.12)
    bm_beam(wd, (0.0, LY1, ZF - 0.02), (LW + 0.14, LY1, ZF - 0.06), 0.1, 0.12)
    bm_beam(wd, (-0.5, LY0, ZB + 0.04), (0.5, LY0, ZB + 0.04), 0.12, 0.08)
    for x in (-0.6, -0.2, 0.2, 0.58):
        xb = x * 0.8
        bm_beam(wd, (xb, LY0 - 0.12, _roof_z(LY0 - 0.12, xb) - 0.045), (x, LY1 + 0.14, _roof_z(LY1 + 0.14, x) - 0.045), 0.07, 0.08)
    for sx in (-1, 1):                                          # knee braces under the front beam
        p = posts[sx]
        bm_beam(wd, (p.x - sx * 0.02, LY1, ZF - 0.26), (p.x - sx * 0.22, LY1, ZF - 0.03), 0.06, 0.06)
    k.emit("Leanto_Frame", col, root, vary=0.06)
    e0, e1 = (-0.54, LY0 - 0.14, _roof_z(LY0 - 0.14, -0.54)), (0.54, LY0 - 0.14, _roof_z(LY0 - 0.14, 0.54))
    r0, r1 = (-LW - 0.12, LY1 + 0.16, _roof_z(LY1 + 0.16, -LW - 0.12)), (LW + 0.12, LY1 + 0.16, _roof_z(LY1 + 0.16, LW + 0.12))
    bm_tile_slope(k["team!:0.1:0.7"], rnd, e0, e1, r0, r1, rows=5, cols=5, th=0.045)
    k.emit("Leanto_Roof", col, root, vary=0.1)
    bm_beam(k["wood_dark:0.3:0.85"], (r0[0] - 0.03, r0[1] + 0.02, r0[2] + 0.04), (r1[0] + 0.03, r1[1] + 0.02, r1[2] + 0.04), 0.06, 0.12)
    for x in (-0.36, 0.06, 0.4):                                # stones weighting the roof
        bm_boulder(k["stone:0.3:0.8"], rnd, (x, LY0 + 0.45 + 0.1 * (x > 0), _roof_z(LY0 + 0.45 + 0.1 * (x > 0), x) + 0.06), 0.085, squash=(1.2, 1, 0.7), n=8)
    k.emit("Leanto_Ridge", col, root, vary=0.08)
    nrm = Vector((0.0, -(ZF + 0.12 - ZB - 0.08), 1.2)).normalized()
    for (x0, y0, x1, y1) in ((-0.5, -1.5, -0.12, -1.24), (-0.46, -1.36, -0.1, -1.1), (0.16, -1.02, 0.5, -1.16)):   # boards patching the roof
        bm_beam(k["wood:0.15:0.6"], (x0, y0, _roof_z(y0, x0) + 0.075), (x1, y1, _roof_z(y1, x1) + 0.075), 0.1, 0.025, up=tuple(nrm))
    k.emit("Leanto_Patches", col, root, vary=0.1)
    sp = [Vector((-0.3, -1.42, T + 0.66)), Vector((-0.3, -1.42, T + 1.08)), Vector((-0.26, -1.48, T + 1.3)), Vector((-0.17, -1.55, T + 1.42))]
    bm_tube(k["iron:0.2:0.8"], sp, [0.045, 0.045, 0.045, 0.045], n=6)                  # the stovepipe through the roof, a cap on it
    bm_cyl(k["iron:0.0:0.5"], 0.1, 0.02, 0.09, tuple(sp[-1] + Vector((0.01, -0.01, 0.06))), seg=6)
    bm_cyl(k["black:0.3:0.7"], 0.055, 0.055, 0.03, tuple(sp[-1] + Vector((0, 0, 0.0))), seg=6)
    ring(k["iron:0.1:0.6"], tuple(sp[1] + Vector((0, 0, -0.18))), 0.07, 0.04, -0.02, 0.02, seg=6)
    k.emit("Stovepipe", col, root)
    # the workbench down the left side: bottles, a mortar, a candle on a skull, an open book
    bx, by0, by1, bz = -0.3, -1.5, -0.98, T + 0.52
    bm_box(k["wood:0.3:0.8"], (0.34, by1 - by0, 0.06), (bx, (by0 + by1) / 2, bz - 0.03))
    bm_box(k["wood:0.4:0.9"], (0.3, by1 - by0 - 0.06, 0.04), (bx, (by0 + by1) / 2, T + 0.2))
    for x in (bx - 0.13, bx + 0.13):
        for y in (by0 + 0.05, by1 - 0.05):
            bm_box(k["wood_dark:0.3:0.8"], (0.055, 0.055, bz - T - 0.06), (x, y, (T + bz - 0.06) / 2))
    k.emit("Bench", col, root, bevel=0.008, vary=0.08)
    for i, (y, h, r, glass) in enumerate(((-1.44, 0.2, 0.05, "teal:0.2:0.85"), (-1.36, 0.15, 0.06, glow(NECRO, 0.8)), (-1.28, 0.24, 0.045, "sand:0.2:0.7"),
                                          (-1.04, 0.17, 0.055, "salmon:0.2:0.7"))):
        gs_bottle(k, (bx + (0.07 if i % 2 else -0.06), y, bz), h=h, r=r, glass=glass, squat=(i == 1))
    gs_lathe(k["stone:0.2:0.7"], (bx + 0.06, -1.18, bz), [(0.06, 0.0), (0.085, 0.05), (0.09, 0.09), (0.075, 0.09), (0.06, 0.04)], n=8, cap0=True, cap1=True)
    bm_beam(k["wood:0.2:0.6"], (bx + 0.06, -1.18, bz + 0.05), (bx + 0.12, -1.12, bz + 0.17), 0.025, 0.025)
    gs_skull(k, place((bx - 0.06, -1.2, bz), yaw=60, scale=0.15), n=6)
    gs_candle(k, (bx - 0.06, -1.205, bz + 0.15), h=0.09, r=0.025, flame=glow(NECRO, 0.9))
    k.emit("Bench_Things", col, root)
    # herbs hung from the front beam, and a rat cage
    for x, sw in ((-0.36, "grass:0.2:0.8"), (-0.21, "tan:0.15:0.6"), (0.12, "lime:0.2:0.85")):
        top = Vector((x, LY1, ZF - 0.06 + 0.04 * (x < 0) - 0.04 * max(0.0, x / LW)))
        bm_tube(k["sand:0.3:0.6"], [top, top - Vector((0, 0, 0.1))], 0.009, n=3)
        c = top - Vector((0, 0, 0.12))
        bm_cyl(k["wood_red:0.3:0.8"], 0.028, 0.03, 0.04, tuple(c), seg=5)
        for j in range(6):
            a = 2 * math.pi * j / 6 + rnd.uniform(-0.3, 0.3)
            tip = c + Vector((math.cos(a) * 0.075, math.sin(a) * 0.075, -rnd.uniform(0.2, 0.27)))
            bm_beam(k[sw], c + Vector((0, 0, 0.01)), tip, 0.055, 0.016, w1=0.02, h1=0.01, up=(math.cos(a), math.sin(a), 0))
    k.emit("Herbs", col, root)
    cc = Vector((0.3, LY1, ZF - 0.5))
    gs_chain(k[IRON], (cc.x, LY1, ZF - 0.08), (cc.x, LY1, cc.z + 0.3), sag=0.0, link=0.07, w=0.045, th=0.016)
    bm_cyl(k[IRON], 0.13, 0.13, 0.025, (cc.x, cc.y, cc.z), seg=10)
    bm_cyl(k[IRON], 0.135, 0.03, 0.09, (cc.x, cc.y, cc.z + 0.27), seg=10)
    for i in range(10):
        a = 2 * math.pi * i / 10
        p = Vector((cc.x + math.cos(a) * 0.12, cc.y + math.sin(a) * 0.12, cc.z))
        bm_beam(k[IRON], p, p + Vector((0, 0, 0.23)), 0.016, 0.016)
    k.emit("Rat_Cage", col, root)
    rz = cc.z + 0.012
    bm_tube(k["stone_dark:0.2:0.7"], [(cc.x - 0.07, cc.y, rz + 0.04), (cc.x - 0.01, cc.y, rz + 0.055), (cc.x + 0.05, cc.y, rz + 0.045),
                                      (cc.x + 0.1, cc.y, rz + 0.03)], [0.036, 0.045, 0.034, 0.0], n=6)
    for s in (-1, 1):
        bm_cyl(k["salmon:0.2:0.6"], 0.018, 0.018, 0.01, (cc.x + 0.045, cc.y + s * 0.025, rz + 0.085), rot=(0, 70, 0), seg=6)
        bm_box(k["black:0.3:0.6"], (0.012, 0.012, 0.012), (cc.x + 0.075, cc.y + s * 0.018, rz + 0.055))
    bm_tube(k["salmon:0.25:0.7"], [(cc.x - 0.07, cc.y, rz + 0.03), (cc.x - 0.11, cc.y + 0.03, rz + 0.02), (cc.x - 0.14, cc.y + 0.08, rz - 0.04),
                                   (cc.x - 0.13, cc.y + 0.11, rz - 0.13)], [0.012, 0.01, 0.008, 0.0], n=4)
    k.emit("Rat", col, root)
    # the plague doctor's hat and beaked mask hung on the left post, looking at the pot
    p = posts[-1]
    hp = Vector((p.x, p.y + 0.12, ZF - 0.22))
    bm_beam(k["wood_dark:0.3:0.8"], (p.x, p.y, ZF - 0.24), (p.x, p.y + 0.1, ZF - 0.22), 0.025, 0.025)
    bm_cyl(k["black:0.2:0.6"], 0.17, 0.17, 0.02, tuple(hp), rot=(-80, 0, 0), seg=12)
    bm_cyl(k["black:0.1:0.5"], 0.09, 0.08, 0.13, tuple(hp + Vector((0, 0.07, 0.01))), rot=(-80, 0, 0), seg=10)
    bm_cyl(k["wood_red:0.3:0.7"], 0.093, 0.093, 0.03, tuple(hp + Vector((0, 0.025, 0.003))), rot=(-80, 0, 0), seg=10)
    mp = Vector((p.x, p.y + 0.09, ZF - 0.5))
    bm_ellipsoid(k["black:0.15:0.5"], tuple(mp), (0.085, 0.05, 0.1), u=8, v=5)
    bm_tube(k["tan:0.2:0.65"], [mp + Vector((0, 0.03, -0.01)), mp + Vector((0, 0.13, -0.04)), mp + Vector((0, 0.22, -0.1)), mp + Vector((0, 0.26, -0.17))],
            [0.052, 0.04, 0.022, 0.0], n=6)
    for s in (-1, 1):
        ring(k["iron:0.1:0.6"], tuple(mp + Vector((s * 0.04, 0.035, 0.03))), 0.034, 0.022, -0.012, 0.012, seg=8, axis="Y")
        bm_cyl(k[glow((0.55, 1.0, 0.4), 0.55)], 0.025, 0.025, 0.012, tuple(mp + Vector((s * 0.04, 0.04, 0.03))), rot=(90, 0, 0), seg=8)
    k.emit("Doctor_Mask", col, root)
    # a soul-fire lantern over the bench
    gs_lantern(k, place((-0.05, LY1 - 0.02, ZF - 0.07), scale=0.5), fire=glow(NECRO, 0.9), rnd=rnd)
    k.emit("Leanto_Lantern", col, root)
    # ---- the hopper of bones at the front right and its chute down into the back stoke hole
    hx, hy = CH0.x, CH0.y - 0.16
    for x in (hx - 0.14, hx + 0.14):
        for y in (hy - 0.12, hy + 0.12):
            bm_box(k["wood_dark:0.3:0.85"], (0.06, 0.06, 0.72), (x, y, T + 0.36))
    for (a, b) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
        bm_beam(k["wood:0.35:0.85"], (hx + a[0] * 0.17, hy + a[1] * 0.15, T + 0.83), (hx + b[0] * 0.17, hy + b[1] * 0.15, T + 0.83), 0.035, 0.22)
    bm_box(k["wood:0.4:0.9"], (0.32, 0.28, 0.03), (hx, hy, T + 0.73))
    k.emit("Hopper", col, root, bevel=0.006, vary=0.08)
    a, b = Vector((CH0.x, CH0.y, T + 0.76)), Vector((CH1.x, CH1.y, T + 0.2))
    along = (b - a).normalized()
    rt = along.cross(Vector((0, 0, 1))).normalized()
    upv = rt.cross(along).normalized()
    bm_beam(k["wood:0.35:0.85"], a, b, 0.22, 0.03, up=tuple(upv))
    for s in (-1, 1):
        bm_beam(k["wood:0.3:0.8"], a + rt * (s * 0.11) + upv * 0.045, b + rt * (s * 0.11) + upv * 0.045, 0.03, 0.1, up=tuple(upv))
    m = a.lerp(b, 0.45)
    for s in (-1, 1):
        bm_beam(k["wood_dark:0.3:0.85"], m + rt * (s * 0.1) - upv * 0.02, Vector((m.x + rt.x * s * 0.16, m.y + rt.y * s * 0.16, T)), 0.05, 0.05)
    k.emit("Chute", col, root, bevel=0.006, vary=0.07)
    bn = k[BONE]
    for (u, du, side) in ((0.2, 0.18, 0.04), (0.55, 0.16, -0.05), (0.75, 0.14, 0.02)):
        p0 = a.lerp(b, u) + rt * side + upv * 0.05
        gs_bone(bn, p0, p0 + along * du + rt * 0.03, r=0.025)
    gs_skull(k, place(tuple(a.lerp(b, 0.36) + upv * 0.02), yaw=_yaw_to(along.x, along.y), pitch=-40, scale=0.15), n=6)
    for i in range(4):                                          # the hopper's load
        p0 = Vector((hx + rnd.uniform(-0.12, 0.12), hy + rnd.uniform(-0.1, 0.1), T + 0.76))
        d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.6, 1.4))).normalized()
        gs_bone(bn, p0, p0 + d * rnd.uniform(0.18, 0.26), r=0.025, n=4)
    gs_skull(k, place((hx + 0.04, hy - 0.02, T + 0.84), yaw=160, pitch=15, scale=0.16), n=6)
    k.emit("Bones", col, root, vary=0.05)
    # ---- the duckboard from the lean-to to the hearth
    d = (DB1 - DB0)
    L = d.length
    dn = d.normalized()
    sd = Vector((-dn.y, dn.x, 0))
    for s in (-1, 1):
        bm_beam(k["wood_dark:0.3:0.85"], DB0 + sd * (s * 0.11) + Vector((0, 0, T + 0.025)), DB1 + sd * (s * 0.11) + Vector((0, 0, T + 0.025)), 0.06, 0.05)
    n = int(L / 0.115)
    for i in range(n):
        c = DB0 + dn * ((i + 0.5) * L / n) + sd * rnd.uniform(-0.02, 0.02)
        bm_box(k["wood:0.12:0.6"], (0.36 + rnd.uniform(-0.03, 0.03), 0.09, 0.03), (c.x, c.y, T + 0.065 + rnd.uniform(-0.006, 0.006)),
               (rnd.uniform(-3, 3), 0, _yaw_to(dn.x, dn.y) + rnd.uniform(-6, 6)))
    k.emit("Duckboard", col, root, bevel=0.006, vary=0.1)
    # ---- a barrel of brew in the left corner, the bone pile in the right
    gs_barrel(k, (-0.84, -1.0, T), r=0.17, h=0.4, fill=glow(NECRO, 0.8))
    gs_bottle(k, (-0.66, -0.78, T), h=0.16, r=0.05, glass=glow((0.7, 1.0, 0.3), 0.7))
    k.emit("Barrel", col, root, vary=0.06)
    for i in range(5):
        p0 = Vector((0.84 + rnd.uniform(-0.14, 0.12), -1.04 + rnd.uniform(-0.18, 0.18), T + 0.03 + 0.03 * (i % 3)))
        aa = rnd.uniform(0, 2 * math.pi)
        gs_bone(k[BONE], p0, p0 + Vector((math.cos(aa) * 0.24, math.sin(aa) * 0.24, rnd.uniform(-0.02, 0.08))), r=0.028, n=4)
    for (dx, dy, dz, yaw, pitch, s) in ((0.0, 0.0, 0.05, 230, 0, 0.2), (-0.1, 0.14, 0.0, 300, -15, 0.17)):
        gs_skull(k, place((0.84 + dx, -1.04 + dy, T + dz), yaw=yaw, pitch=pitch, scale=s), n=6)
    k.emit("Bone_Pile", col, root, vary=0.06)
    head = empty("Head", col, root, tuple(H0), 0.5, "SINGLE_ARROW")
    empty("Muzzle", col, head, tuple(MUZZLE), 0.2, "SPHERE")
    crew = empty("Crew", col, head, tuple(CREW), 0.3, "SINGLE_ARROW")
    crew.rotation_euler = (0, 0, math.radians(_yaw_to(-CREW.x, -CREW.y)))
    gs_standin(tuple(CREW), yaw=_yaw_to(-CREW.x, -CREW.y), parent=head, h=1.0)
    return root


BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "yoke": ((0, 0.62, 0.15), (0, 0.62, 0.45), "root"),
         "arm": (tuple(P), tuple(P + D0 * 0.4), "yoke"),
         "glob": (tuple(LADLE), tuple(LADLE + NUP * 0.15), "arm"),
         "swirl": ((0, 0, BREW), (0, 0, BREW + 0.15), "root"),
         "splash": (tuple(SPL), tuple(SPL + Vector((0, 0, 0.15))), "root")}
for _i, _b in enumerate(BUBS):
    BONES["bub.%d" % (_i + 1)] = (_b, (_b[0], _b[1], _b[2] + 0.08), "swirl")
for _i, (_x, _y) in enumerate(STEAM):
    BONES["steam.%d" % (_i + 1)] = ((_x, _y, 0.6), (_x, _y, 0.75), "root")
for _i in range(FIRES):
    _a = math.radians(30 + 60 * _i)
    BONES["fire.%d" % (_i + 1)] = ((0.575 * math.cos(_a), 0.575 * math.sin(_a), -0.37), (0.575 * math.cos(_a), 0.575 * math.sin(_a), -0.2), "root")
flag_bones(BONES, "ban", tuple(BAN_TOP), (0, 0, -1), 0.52, segs=3, parent="yoke")


def build_head():
    col = collection("Plague_cauldron")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    rnd = random.Random(7)
    k = Kit()
    # ---- the collar: an octagon of timbers riding the coping, iron-strapped at the joints
    R = 0.77
    for i in range(8):
        a0, a1 = math.radians(22.5 + 45 * i), math.radians(22.5 + 45 * (i + 1))
        p0 = Vector((math.cos(a0) * R, math.sin(a0) * R, 0.045))
        p1 = Vector((math.cos(a1) * R, math.sin(a1) * R, 0.045))
        dd = (p1 - p0).normalized()
        bm_beam(k["wood_dark:0.25:0.8"], p0 - dd * 0.05, p1 + dd * 0.05, 0.13, 0.09)
    k.emit("Head_Collar", col, rig=rig, bone="root", bevel=0.008, vary=0.07)
    for i in range(8):
        a0 = math.radians(22.5 + 45 * i)
        bm_box(k[IRON], (0.1, 0.16, 0.1), (math.cos(a0) * R, math.sin(a0) * R, 0.05), (0, 0, math.degrees(a0)))
    k.emit("Head_Collar_Straps", col, rig=rig, bone="root")
    # ---- the onager's frame: a sill across the collar, two leaning uprights through the skein, the stop beam
    wd = k["wood_dark:0.2:0.75"]
    bm_beam(wd, (-0.52, 0.64, 0.14), (0.52, 0.64, 0.14), 0.14, 0.1)
    for sx in (-1, 1):
        bm_beam(wd, (sx * UPX, up_y(0.19), 0.19), (sx * UPX, up_y(P.z + 0.74), P.z + 0.74), 0.13, 0.13, up=(0, 1, 0))
        bm_beam(wd, (sx * UPX, up_y(0.62), 0.62), (sx * 0.62, 0.3, 0.1), 0.09, 0.09)               # a brace back to the collar
    bm_beam(wd, (-UPX - 0.06, up_y(0.38), 0.38), (UPX + 0.06, up_y(0.38), 0.38), 0.12, 0.1)          # the lower tie
    bm_beam(wd, (-0.45, CROSS.y, CROSS.z), (0.45, CROSS.y, CROSS.z), 0.13, 0.13)                     # the stop beam
    k.emit("Head_Yoke", col, rig=rig, bone="yoke", bevel=0.008, vary=0.06)
    ir = k[IRON]
    for sx in (-1, 1):
        for z in (0.38, CROSS.z):
            bm_box(ir, (0.15, 0.15, 0.04), (sx * UPX, up_y(z), z + 0.085), (math.degrees(math.atan(SLOPE)), 0, 0))
        bm_box(ir, (0.04, 0.15, 0.15), (sx * 0.45, CROSS.y, CROSS.z))
        ring(k["iron:0.15:0.85"], (sx * (UPX + 0.09), P.y, P.z), 0.13, 0.08, -0.025, 0.025, seg=10, axis="X")   # the skein's capstans
        for j in range(4):
            aa = math.radians(45 * j)
            v = Vector((0, math.cos(aa), math.sin(aa))) * 0.12
            bm_beam(ir, Vector((sx * (UPX + 0.09), P.y, P.z)) - v, Vector((sx * (UPX + 0.09), P.y, P.z)) + v, 0.03, 0.03)
        bm_beam(ir, (sx * (UPX + 0.1), P.y + 0.1, P.z + 0.1), (sx * (UPX + 0.1), P.y + 0.2, P.z - 0.02), 0.025, 0.04)          # pawl
    k.emit("Head_Yoke_Iron", col, rig=rig, bone="yoke")
    bm_ellipsoid(k["team!:0.1:0.6"], (0, CROSS.y - 0.095, CROSS.z), (0.16, 0.05, 0.1), u=8, v=5)        # the pad the arm slams
    for x in (-0.1, 0.1):
        ring(k["sand:0.3:0.7"], (x, CROSS.y - 0.04, CROSS.z), 0.115, 0.085, -0.012, 0.012, seg=8, axis="X")
    for sx in (-1, 1):                                          # skull finials on the uprights
        gs_skull(k, place((sx * UPX, up_y(P.z + 0.74) + 0.0, P.z + 0.74), yaw=sx * -20, pitch=-10, scale=0.2), n=6)
    k.emit("Head_Pad", col, rig=rig, bone="yoke")
    gs_banner(k["team!:0.1:0.75"], tuple(BAN_TOP), (1, 0, 0), (0, 0, -1), 0.42, 0.52, rnd=rnd, cols=5, rows=4, tatter=0.32)
    k.emit("Head_Banner", col, rig=rig, bones=["ban.1", "ban.2", "ban.3"])
    for yaw, dy in ((0, 0.012), (180, -0.012)):
        gs_skull(k, place((0, BAN_TOP.y + dy, BAN_TOP.z - 0.27), yaw=yaw, scale=0.17) @ Matrix.Diagonal((1.0, 0.25, 1.0, 1.0)), n=6)
    k.emit("Head_Banner_Badge", col, rig=rig, bones=["ban.1", "ban.2", "ban.3"])
    # ---- the skein: twisted rope between the uprights, the arm thrust through it (it turns with the arm)
    for s in range(4):
        pts = []
        for j in range(7):
            x = -UPX + 2 * UPX * j / 6
            aa = 2 * math.pi * s / 4 + x * 7.0
            pts.append((x, P.y + math.cos(aa) * 0.06, P.z + math.sin(aa) * 0.06))
        bm_tube(k["sand:0.25:0.7"], pts, 0.042, n=5)
    M = Matrix(((-1.0, D0.x, NUP.x, LADLE.x), (0.0, D0.y, NUP.y, LADLE.y), (0.0, D0.z, NUP.z, LADLE.z), (0.0, 0.0, 0.0, 1.0)))
    with Stamp(M, k["iron:0.05:0.55"]):                         # the ladle's great iron bowl
        gs_lathe(k["iron:0.05:0.55"], (0, 0, 0), [(0.1, -0.12), (0.16, -0.08), (0.19, -0.01), (0.198, 0.03), (0.172, 0.036), (0.15, -0.02),
                                                 (0.09, -0.07)], n=10, tip0=-0.13, cap1=True)
    k.emit("Head_Skein", col, rig=rig, bone="arm")
    # ---- the arm: a squared timber with a great thigh bone lashed along it, iron-banded, ending in the ladle
    bm_beam(k["wood:0.35:0.85"], P - D0 * 0.22, P + D0 * (ARM_L - 0.15), 0.12, 0.13, w1=0.1, h1=0.1, up=tuple(NUP))
    gs_bone(k[BONE], P + D0 * 0.12 + NUP * 0.1, P + D0 * 0.8 + NUP * 0.085, r=0.042, knob=1.7, n=6)
    for s in (0.02, 0.46, 0.86):
        bm_beam(k[IRON], P + D0 * (s - 0.025), P + D0 * (s + 0.025), 0.14, 0.15, up=tuple(NUP))
    k.emit("Head_Arm", col, rig=rig, bone="arm", bevel=0.006)
    # the glob in the ladle: it's flung (shrinks away) as the arm hits the pad, and scooped up again
    g = k[glow((0.78, 1.0, 0.22), 1.0)]
    bm_blob(g, rnd, tuple(LADLE + NUP * 0.06), 0.16, squash=(1.0, 1.0, 0.85), jitter=0.12, sub=1)
    bm_blob(g, rnd, tuple(LADLE + NUP * 0.15 + D0 * 0.05), 0.085, jitter=0.15)
    k.emit("Head_Glob", col, rig=rig, bone="glob")
    # ---- what bobs in the brew: a skull face up, a thigh bone, a rib; bubbles swell and pop on them
    gs_skull(k, place((0.13, 0.19, BREW - 0.06), yaw=200, pitch=70, scale=0.17), n=6)
    gs_bone(k[BONE], (-0.28, 0.07, BREW - 0.005), (-0.05, 0.3, BREW + 0.012), r=0.027)
    gs_rib(k[BONE], (0.3, -0.06, BREW - 0.04), (0, 0, 1), (-0.9, 0.4, 0), 0.24, r=0.022, curve=0.55)
    k.emit("Head_Floaters", col, rig=rig, bone="swirl", vary=0.05)
    for i, (x, y, z) in enumerate(BUBS):
        bm_ellipsoid(k[glow((0.86, 1.0, 0.72), 0.9)], (x, y, z + 0.012), (0.06, 0.06, 0.052), u=8, v=5)
        k.emit("Head_Bubble%d" % (i + 1), col, rig=rig, bone="bub.%d" % (i + 1))
    for i, (x, y) in enumerate(STEAM):
        st = k[glow((0.55, 0.88, 0.45), 0.4)]
        bm_blob(st, rnd, (x, y, 0.62), 0.075, squash=(1.2, 1.2, 0.8), jitter=0.18)
        bm_blob(st, rnd, (x + 0.07, y - 0.02, 0.64), 0.055, jitter=0.18)
        bm_blob(st, rnd, (x - 0.05, y + 0.04, 0.66), 0.05, jitter=0.18)
        k.emit("Head_Steam%d" % (i + 1), col, rig=rig, bone="steam.%d" % (i + 1))
    for i in range(FIRES):
        a = math.radians(30 + 60 * i)
        gs_flame(k[glow(NECRO, 0.95)], (0.575 * math.cos(a), 0.575 * math.sin(a), -0.37), h=0.47, r=0.08, rnd=rnd, tongues=2, n=5)
        k.emit("Head_Fire%d" % (i + 1), col, rig=rig, bone="fire.%d" % (i + 1))
    sp = k[glow((0.5, 1.0, 0.35), 1.0)]                       # the splash as the ladle rips out of the brew
    for i in range(7):
        a = 2 * math.pi * i / 7
        dv = Vector((math.cos(a), math.sin(a), 0))
        bm_crystal(sp, SPL + dv * 0.13, SPL + dv * 0.24 + Vector((0, 0, 0.22 + 0.06 * (i % 2))), 0.035, n=4, shoulder=0.5)
    bm_crystal(sp, SPL, SPL + Vector((0, 0.02, 0.36)), 0.06, n=5, shoulder=0.5)
    k.emit("Head_Splash", col, rig=rig, bone="splash")
    return rig


IDLE_LEN = 96
FIRE_LEN = 18


def pose(rig, t=0.0, arm=0.0, glob=1.0, splash=0.0, shudder=0.0, boil=0.0, flare=0.0, flap=0.0):
    """t: the idle's phase (0..1 loops); arm: the arm's turn from rest (degrees about +X, SWING is upright);
    boil: an extra run through the bubbles' and the steam's cycles (1 = one whole run, so it loops)."""
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    ph = 2 * math.pi * t
    pb["arm"].rotation_quaternion = q(pb["arm"], (1, 0, 0), arm + 1.6 * math.sin(ph) + 0.8 * math.sin(3 * ph))
    pb["glob"].scale = (max(glob, 0.01),) * 3
    pb["yoke"].rotation_quaternion = q(pb["yoke"], (1, 0, 0), shudder)
    pb["swirl"].rotation_quaternion = q(pb["swirl"], (0, 0, 1), 18 * math.sin(ph) + 6 * math.sin(2 * ph + 0.4))
    pb["swirl"].location = arm_space_loc(pb["swirl"], (0, 0, 0.012 * math.sin(3 * ph)))
    for i, cyc in enumerate(BUB_CYC):
        u = (cyc * (t + boil) + 0.23 * i) % 1.0
        if u < 0.74:
            s = 0.01 + 0.99 * smooth(u / 0.74)
        elif u < 0.84:
            s = 1.0 + 0.32 * (u - 0.74) / 0.1
        else:
            s = 0.01
        pb["bub.%d" % (i + 1)].scale = (s, s, s)
    for i in range(len(STEAM)):
        u = (2 * t + boil + i / 3.0) % 1.0
        s = (0.06 + 1.2 * smooth(u / 0.4)) * (1.0 - smooth((u - 0.5) / 0.5))
        b = pb["steam.%d" % (i + 1)]
        b.location = arm_space_loc(b, (0.12 * u * (1 if i % 2 else -1), 0.08 * u, 0.85 * u))
        b.scale = (max(s, 0.01),) * 3
    for i in range(FIRES):
        f = 1.0 + 0.2 * math.sin(2 * math.pi * (5 * t + 0.37 * i)) + 0.12 * math.sin(2 * math.pi * (9 * t + 0.71 * i)) + flare
        b = pb["fire.%d" % (i + 1)]
        b.scale = (0.92 + 0.08 * f, f, 0.92 + 0.08 * f)
        b.rotation_quaternion = q(b, (0, 0, 1), 14 * math.sin(2 * math.pi * (3 * t + 0.2 * i)))
    pb["splash"].scale = (max(splash, 0.01),) * 3
    sway(rig, "ban", 2.5, segs=3, axis=(1, 0, 0), lag=0.12, phase=2 * t)
    for kk in range(3):
        b = pb["ban.%d" % (kk + 1)]
        b.rotation_quaternion = b.rotation_quaternion @ q(b, (1, 0, 0), flap * (0.6 + 0.5 * kk))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(rig, t=f / IDLE_LEN)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        # a short dip (0-1), the whip up and over (1-4: it hits the pad on 4 and the glob flies), a bounce off the pad,
        # then the ladle sinks back into the brew (7-17) and scoops a new glob
        if f <= 1:
            a = 7.0 * f
        elif f <= 4:
            u = (f - 1) / 3.0
            a = 7.0 + (SWING - 7.0) * u * u
        elif f <= 7:
            a = SWING + 13.0 * math.sin(math.pi * (f - 4) / 3.0)
        else:
            a = SWING * (1.0 - smooth((f - 7) / 10.0))
        glob = 1.0 if f <= 2 else (0.6 if f == 3 else (0.01 if f < 13 else smooth((f - 13) / 4.0)))
        spl = smooth((f - 1) / 2.0) * (1.0 - smooth((f - 5) / 5.0))
        shud = {4: 3.5, 5: -2.5, 6: 1.2}.get(f, 0.0)
        flap = 22.0 * math.sin(math.pi * min(max((f - 4) / 8.0, 0.0), 1.0)) * (1.0 if f < 12 else 1.0 - smooth((f - 12) / 5.0))
        pose(rig, t=0.0, arm=a, glob=glob, splash=1.2 * spl, shudder=shud, boil=f / FIRE_LEN,
             flare=0.45 * smooth(f / 2.0) * (1 - smooth((f - 4) / 10.0)), flap=flap)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.1, 1.1), "dist": 8.6, "yaw": 150, "pitch": 20, "anim_target": (F.x, F.y - 0.1, HZ + 0.8), "anim_dist": 5.0,
           "frames": [("idle", 0), ("idle", 48), ("fire", 2), ("fire", 4), ("fire", 7), ("fire", 12)],
           "extra": [{"yaw": 150, "pitch": 14, "dist": 3.4, "target": (0, -1.2, 0.85)},
                     {"yaw": 160, "pitch": 52, "dist": 3.4, "target": (F.x, F.y, HZ + 0.45)},
                     {"yaw": 270, "pitch": 14, "dist": 6.4, "target": (0, 0, 1.0)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
