"""Builds the Hall of Knights (footprint "arrow3": [0,0] front, [1,0] back-right, [-1,1] back-left), the Crown's Tier IV
tower: it musters knights who march out onto the road and pin the foe.

    python tools/blender/build.py knight_hall --out <preview dir>

One fortified hall owning the arrowhead. The great hall runs across all three hexes: coursed walls on a footing,
buttresses between tall glowing windows, a steep team-tiled roof with dormers and a timber lantern on the ridge; squat
round towers close its two ends. Out of its middle, on the front hex, stands a strong gatehouse: an arched gate with a
portcullis between two round towers with team cone roofs flying the royal standards, a corbelled parapet over a hanging
banner, and the roof walk where the knight-commander stands (Crew, on the Head: he turns to the foe). Behind the hall,
on the back hexes, battlemented curtain walls run from the end towers round two yards: the training yard (sanded, a
quintain, straw dummies in team tabards, a weapon rack) and the smithy court (a lean-to forge against the hall with a
glowing hearth and a smoking chimney, an anvil, a quench tub). Rig under the root: idle (the standards fly, torches
flicker, the quintain swings, the forge breathes, smoke rises), fire (the portcullis lifts and drops, the standards snap).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "castle_common.py"), encoding="utf-8").read())

TID = "knight_hall"
CELLS = [(0, 0), (1, 0), (-1, 1)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)            # (0, 0.69): the gatehouse
R = hex_to_world(1, 0, MID)            # (1.8, -0.35): the smithy court
L = hex_to_world(-1, 1, MID)           # (-1.8, -0.35): the training yard
TOP = 0.34
T = TOP
HX, HY0, HY1 = 2.3, -0.2, 0.62        # the great hall: half its length, its back and front wall faces
HC, HD = (HY0 + HY1) * 0.5, HY1 - HY0
Z_EAVE, Z_RIDGE = T + 1.2, T + 2.0
GX, GY0, GY1 = 0.45, 0.5, 1.15        # the gatehouse: half its width, its back (inside the hall) and its front face
GYM = (GY0 + GY1) * 0.5
Z_GATE = T + 1.75                     # its roof walk
ARCH_W, ARCH_S = 0.4, 0.4             # the gate: width, spring height
GT = [Vector((-0.56, 0.95, 0)), Vector((0.56, 0.95, 0))]     # the gate towers
GT_R, Z_GT, GT_H = 0.32, T + 2.1, 0.85
ET = [Vector((-2.42, -0.3, 0)), Vector((2.42, -0.3, 0))]     # the end towers
ET_R, Z_ET = 0.33, T + 1.8
YARD_WALL = [(2.26, -0.5), (2.26, -1.15), (1.35, -1.15), (0.845, -0.27)]   # the right yard's wall (mirrored on the left)
YARD = [(2.18, -0.21), (0.9, -0.21), (1.4, -1.07), (2.18, -1.07)]          # inside it
QUIN = Vector((-1.56, -0.68, 0))      # the quintain's post
FORGE = Vector((1.68, -0.37, 0))      # the forge, against the hall's back wall under a lean-to
Z_CHIM = T + 1.55
LANT = Vector((0, HC, Z_RIDGE))
POLE = [Vector((c.x, c.y, Z_GT + 0.08 + GT_H + 0.62)) for c in GT]        # the standards' pole tops
FLAG_DIR = Vector((1.0, -0.22, 0.0))
FLAG_L, FLAG_H = 0.78, 0.4
WARM = "glow:1.0,0.74,0.3,0.9"
FIRE = "glow:1.0,0.48,0.1,0.9"
EMBER = "glow:1.0,0.36,0.08,0.85"
FLAMES = []                           # torch flame bases, filled by build_base


def tangent(deg):
    """The `right` for a curved wall facing out at deg degrees (so wall_out(right) points out)."""
    a = math.radians(deg)
    return Vector((-math.sin(a), math.cos(a), 0))


def mirror(pts, sx):
    return [(sx * x, y) for x, y in pts]


def dummy(k, rnd, p, face):
    """A straw practice dummy on a post, its arms on a crossbar, a team tabard front and back."""
    p = Vector((p[0], p[1], T))
    o = Vector((math.cos(math.radians(face)), math.sin(math.radians(face)), 0))
    rt = Vector((-o.y, o.x, 0))
    bm_cyl(k[TIMBER], 0.035, 0.03, 0.66, (p.x, p.y, T + 0.33), seg=6)
    bm_cyl(k["wood_dark:0.5:0.9"], 0.09, 0.07, 0.05, (p.x, p.y, T + 0.025), seg=6)
    bm_beam(k[TIMBER], p - rt * 0.21 + UP * 0.47, p + rt * 0.21 + UP * 0.47, 0.045, 0.045)
    bm_blob(k["gold:0.35:0.8"], rnd, p + UP * 0.4, 0.125, squash=(1.0, 0.82, 1.3), jitter=0.1)
    for s in (-1, 1):
        bm_blob(k["gold:0.35:0.8"], rnd, p + rt * (s * 0.2) + UP * 0.47, 0.05, squash=(1.2, 1.0, 1.0), jitter=0.12)
    bm_blob(k["beige:0.2:0.6"], rnd, p + UP * 0.64, 0.075, squash=(1.0, 1.0, 1.1), jitter=0.08)
    for s in (-1, 1):
        bm_obox(k["team!:0.1:0.6"], p + o * (s * 0.088) + UP * 0.37, rt, 0.17, 0.035, 0.26)
    bm_obox(k[GOLD], p + UP * 0.37, rt, 0.2, 0.2, 0.035)


def build_base():
    col = collection("Knight_hall")
    root = empty("Knight_hall", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(11)
    k = Kit()
    FLAMES.clear()
    # ---- the great hall: coursed walls on a footing with quoins, gable ends, buttresses between tall windows
    bm_box(k[STONE_FOOT], (2 * HX + 0.1, HD + 0.1, 0.16), (0, HC, T + 0.08))
    stone_box(k, rnd, (0, HC), 2 * HX, HD, T + 0.14, Z_EAVE, course=0.24, block=0.46, quoins=STONE_LIGHT)
    for sx in (-1, 1):
        gable_wall(k, rnd, (sx * (HX - 0.08), HY0), (sx * (HX - 0.08), HY1), Z_EAVE, Z_RIDGE - 0.03, course=0.22, block=0.44)
    cull_box(k[STONE], (0, HC), 2 * HX, HD)
    for key in (STONE_FOOT, STONE_LIGHT, CORE):
        cull_down(k[key])
    k.emit("Hall", col, root, vary=0.07, tag="no_refine")
    back = (1, 0, 0)                  # `right` along the back wall (it faces -Y), and along the front (+Y)
    front = (-1, 0, 0)
    for x in (-1.5, -0.75, 0.75):
        arch_window(k, (x, HY0, T + 0.42), back, 0.24, 0.62, glow=WARM, n=4)
    arch_window(k, (0, HY0, T + 0.36), back, 0.3, 0.8, glow=WARM, n=5, bars=IRON)
    for x in (-1.95, -1.3, 1.3, 1.95):
        arch_window(k, (x, HY1, T + 0.42), front, 0.24, 0.62, glow=WARM, n=4)
    for x in (-1.85, -1.12, -0.42, 0.42, 1.12):
        buttress(k, (x, HY0), (0, -1), T, T + 1.06, w=0.16, d0=0.24, d1=0.13)
    for x in (-1.62, -1.0, 1.0, 1.62):
        buttress(k, (x, HY1), (0, 1), T, T + 1.06, w=0.16, d0=0.22, d1=0.12)
    for sx in (-1, 1):                # torches flanking the great window
        FLAMES.append(torch(k, (sx * 0.29, HY0, T + 0.64), out=(0, -1)))
    k.emit("Hall_Trim", col, root, vary=0.06)
    # ---- the roof: steep team tiles, a gold ridge, dormers, and a timber lantern on the ridge
    gable_roof(k, rnd, (0, HC), 2 * HX, HD, Z_EAVE, Z_RIDGE, eave=0.12, verge=0.1, rows=4, cols=11)
    for x in (-0.75, 0.75):
        dormer(k, rnd, (x, HY0 + 0.03, Z_EAVE - 0.02), (0, -1), w=0.3, h=0.3, run=0.4, rise=0.15)
    k.emit("Hall_Roof", col, root, vary=0.08, tag="no_refine")
    zl = Z_RIDGE + 0.08
    bm_box(k[TIMBER], (0.4, 0.44, 0.58), (LANT.x, LANT.y, zl - 0.29))
    for i in range(8):
        a = 22.5 + 45 * i
        p = polar(LANT, 0.165, a, zl + 0.12)
        bm_box(k[TIMBER], (0.05, 0.05, 0.24), tuple(p), (0, 0, a))
    bm_cyl(k[WARM], 0.13, 0.13, 0.22, (LANT.x, LANT.y, zl + 0.11), seg=8)
    bm_cyl(k[TIMBER], 0.22, 0.22, 0.05, (LANT.x, LANT.y, zl + 0.26), seg=8)
    cone_roof(k, rnd, LANT, 0.27, zl + 0.28, 0.36, rows=3, n=9, spike=0.18)
    k.emit("Lantern", col, root, tag="no_refine")
    # ---- the end towers: squat round towers closing the hall's gable ends
    for i, c in enumerate(ET):
        sx = -1 if c.x < 0 else 1
        course_tower(k, rnd, c, ET_R + 0.02, ET_R - 0.01, T, Z_ET, courses=6, n=9)
        cull_tower(k[STONE], c, ET_R + 0.05)
        bm_block_course(k[STONE_LIGHT], rnd, c, ET_R + 0.05, Z_ET - 0.02, 0.11, 12, depth=0.2)
        cone_roof(k, rnd, c, ET_R + 0.12, Z_ET + 0.06, 0.72, rows=4, n=9, spike=0.24)
        for a, z in ((270, T + 0.9), (90 - sx * 120, T + 1.3)):
            p = polar(c, ET_R - 0.01, a, z)
            bm_box(k["black:0.3:0.7"], (0.04, 0.07, 0.22), tuple(p), (0, 0, a))
        arch_door(k, polar(c, ET_R - 0.02, 270 - sx * 60, T), tangent(270 - sx * 60), 0.2, 0.34, n=4)
    k.emit("EndTowers", col, root, vary=0.07, tag="no_refine")
    # ---- the gatehouse: three coursed walls, the front built round a real arched opening, a corbelled parapet
    stone_box(k, rnd, (0, GYM), 2 * GX, GY1 - GY0, T, Z_GATE, sides="EWS", course=0.21, block=0.36)
    yf = GY1 - 0.08
    for sx in (-1, 1):
        bm_block_wall(k[STONE], rnd, (sx * GX, yf), (sx * 0.29, yf), T, Z_GATE - 0.05, 0.16, 0.21, 0.3)
        bm_box(k[STONE], (0.1, 0.16, 0.12), (sx * 0.25, yf, T + ARCH_S + 0.26))
    bm_block_wall(k[STONE], rnd, (-0.29, yf), (0.29, yf), T + ARCH_S + ARCH_W * 0.5 + 0.1, Z_GATE - 0.05, 0.16, 0.2, 0.3)
    cull_box(k[STONE], (0, GYM), 2 * GX, GY1 - GY0)
    cull_down(k[CORE])
    k.emit("Gatehouse", col, root, vary=0.07, tag="no_refine")
    bm_arch(k[STONE_LIGHT], (0, GY1 - 0.06, T), front, ARCH_W, ARCH_S, th=0.1, depth=0.17, n=7)
    bm_extrude(k["black:0.4:0.75"], arch_outline((0, GY1 - 0.062, T), front, ARCH_W, ARCH_S + ARCH_W * 0.5, 6), (0, -0.01, 0))
    for x in (-0.24, -0.08, 0.08, 0.24):                                    # corbels under the parapet
        bm_box(k[STONE_LIGHT], (0.07, 0.1, 0.15), (x, GY1 + 0.03, Z_GATE - 0.12))
    bm_box(k[STONE_LIGHT], (2 * GX + 0.02, GY1 - GY0 + 0.1, 0.08), (0, GYM + 0.05, Z_GATE))   # its floor and string course
    battlements(k[STONE], (-GX + 0.02, GY1 + 0.02), (GX - 0.02, GY1 + 0.02), Z_GATE + 0.04, w=0.15, h=0.17, th=0.13, gap=0.12)
    battlements(k[STONE], (-GX + 0.02, GY0 + 0.07), (GX - 0.02, GY0 + 0.07), Z_GATE + 0.04, w=0.15, h=0.17, th=0.13, gap=0.12)
    for sx in (-1, 1):
        battlements(k[STONE], (sx * (GX - 0.06), GY0 + 0.2), (sx * (GX - 0.06), GY1 - 0.12), Z_GATE + 0.04, w=0.14, h=0.17, th=0.12, gap=0.12, ends=False)
    hanging_banner(k, (0, GY1, T + 1.5), front, 0.34, 0.5, kind="sun")
    k.emit("Gatehouse_Trim", col, root, vary=0.05)
    # ---- the gate towers: tall round towers with corbelled tops, team cone roofs and the standards' poles
    for i, c in enumerate(GT):
        sx = -1 if c.x < 0 else 1
        course_tower(k, rnd, c, GT_R + 0.02, GT_R - 0.02, T, Z_GT, courses=8, n=10)
        cull_tower(k[STONE], c, GT_R + 0.05)
        bm_block_course(k[STONE_LIGHT], rnd, c, GT_R + 0.06, Z_GT - 0.04, 0.13, 12, depth=0.22)
        cone_roof(k, rnd, c, GT_R + 0.13, Z_GT + 0.08, GT_H, rows=5, n=11, spike=0.0)
        bm_cyl(k[TIMBER], 0.024, 0.02, 0.56, (c.x, c.y, POLE[i].z - 0.26), seg=6)
        bm_ellipsoid(k[GOLD], tuple(POLE[i] + UP * 0.04), (0.04, 0.04, 0.04), u=6, v=4)
        for a, z in ((90 - sx * 40, T + 0.95), (90 - sx * 75, T + 1.55), (270 + sx * 40, T + 1.2)):
            p = polar(c, GT_R - 0.01, a, z)
            bm_box(k["black:0.3:0.7"], (0.04, 0.07, 0.24), tuple(p), (0, 0, a))
        a = 90 - sx * 28
        FLAMES.append(torch(k, polar(c, GT_R - 0.01, a, T + 0.62), out=tuple(polar((0, 0), 1, a))))
    k.emit("GateTowers", col, root, vary=0.07, tag="no_refine")
    # ---- the curtain walls round the two yards behind the hall, with stout piers at the bends
    for sx in (-1, 1):
        pts = mirror(YARD_WALL, sx)
        crenel_wall(k, rnd, pts, T, 0.36, th=0.17, course=0.18, block=0.4, merlon=(0.18, 0.14, 0.15))
    cull_down(k[STONE])
    k.emit("Curtain", col, root, vary=0.07, tag="no_refine")
    # ---- the ground: paving in front of the gate, a sanded training yard, a flagged smithy court
    keep = [(c.x, c.y, GT_R + 0.04) for c in GT] + [(-GX - 0.02, GY0, GX + 0.02, GY1 + 0.05)]
    pave(k, rnd, CELLS, T, keep_out=keep, inset=0.2, size=0.27, where=lambda x, y: y > HY1 + 0.05)
    yl = [Vector((x, y, 0)) for x, y in mirror(YARD, -1)]
    yr = [Vector((x, y, 0)) for x, y in YARD]
    bm_extrude(k["sand:0.3:0.62"], [(p.x, p.y, T - 0.01) for p in yl], (0, 0, 0.035))
    pave(k, rnd, CELLS, T, inset=0.2, size=0.26, keep=0.92, where=lambda x, y: inside(yr, x, y) and not (1.3 < x < 2.06 and y > -0.74))
    bm_flagstones(k["stone2:0.15:0.65"], rnd, lambda x, y: 1.32 < x < 2.04 and -0.72 < y < -0.22, (1.3, -0.74, 2.06, -0.2), T, size=0.24)
    k.emit("Paving", col, root, vary=0.09)
    # ---- the training yard: a quintain, two straw dummies in team tabards, a weapon rack
    q = QUIN
    bm_cyl(k[TIMBER], 0.05, 0.04, 0.62, (q.x, q.y, T + 0.31), seg=6)
    for a in (45, 135, 225, 315):
        d = polar((0, 0), 1, a)
        bm_beam(k[TIMBER], q + d * 0.2 + UP * (T + 0.02), q + d * 0.03 + UP * (T + 0.22), 0.04, 0.04)
    dummy(k, rnd, (-2.0, -0.95), 30)
    dummy(k, rnd, (-1.98, -0.56), 0)
    k.emit("Training", col, root)
    for o in kk_import("hex/weaponrack", col, root, (-1.5, -1.0, T), 0, 2.0, name="Prop_KK_Rack"):
        pass
    # ---- the smithy: a lean-to against the hall, the forge with its hood and chimney, an anvil, a quench tub
    x0, x1, yf2 = 1.3, 2.06, -0.76
    for x in (x0 + 0.04, x1 - 0.04):
        bm_box(k[TIMBER], (0.07, 0.07, 0.64), (x, yf2 + 0.04, T + 0.32))
    bm_beam(k[TIMBER], (x0 - 0.02, yf2 + 0.04, T + 0.64), (x1 + 0.02, yf2 + 0.04, T + 0.64), 0.08, 0.08)
    for x in (x0 + 0.04, (x0 + x1) * 0.5, x1 - 0.04):
        bm_beam(k[TIMBER], (x, yf2 - 0.04, T + 0.62), (x, HY0, T + 1.0), 0.06, 0.06)
    k.emit("Smithy", col, root)
    bm_tile_slope(k[TILES], rnd, (x0 - 0.08, yf2 - 0.1, T + 0.6), (x1 + 0.06, yf2 - 0.1, T + 0.6), (x0 - 0.08, HY0, T + 1.02), (x1 + 0.06, HY0, T + 1.02),
                  rows=3, cols=4)
    k.emit("Smithy_Roof", col, root, vary=0.08)
    f = FORGE
    bm_box(k[STONE_FOOT], (0.5, 0.34, 0.36), (f.x, f.y, T + 0.18))
    bm_box(k[STONE_LIGHT], (0.56, 0.4, 0.06), (f.x, f.y - 0.01, T + 0.39))
    bm_arch(k[STONE_LIGHT], (f.x, f.y - 0.17, T + 0.06), (1, 0, 0), 0.22, 0.09, th=0.06, depth=0.06, n=5)
    bm_hull(k[STONE], [(f.x + sx * 0.26, y, T + 0.62) for sx in (-1, 1) for y in (HY0, f.y - 0.2)] +
            [(f.x + sx * 0.13, y, T + 0.92) for sx in (-1, 1) for y in (HY0, HY0 - 0.22)])
    bm_box(k[STONE], (0.26, 0.22, Z_CHIM - T - 0.9), (f.x, HY0 - 0.11, (T + 0.9 + Z_CHIM) * 0.5))
    bm_box(k[STONE_LIGHT], (0.32, 0.28, 0.06), (f.x, HY0 - 0.11, Z_CHIM + 0.01))
    bm_box(k["black:0.3:0.6"], (0.16, 0.12, 0.02), (f.x, HY0 - 0.11, Z_CHIM + 0.04))
    a = Vector((1.56, -0.95, 0))
    bm_cyl(k["wood:0.4:0.85"], 0.09, 0.08, 0.16, (a.x, a.y, T + 0.08), seg=7)
    bm_box(k[IRON], (0.08, 0.15, 0.06), (a.x, a.y, T + 0.19))
    bm_box(k[IRON], (0.11, 0.24, 0.05), (a.x, a.y, T + 0.245))
    bm_cyl(k[IRON], 0.035, 0.0, 0.1, (a.x, a.y + 0.17, T + 0.245), rot=(-90, 0, 0), seg=5)
    b = Vector((2.0, -0.95, 0))
    bm_cyl(k["wood:0.2:0.75"], 0.12, 0.13, 0.18, (b.x, b.y, T + 0.09), seg=10)
    for z in (0.04, 0.14):
        ring(k[IRON], (b.x, b.y, T + z), 0.135, 0.11, -0.012, 0.012, seg=10)
    bm_cyl(k["water"], 0.11, 0.11, 0.01, (b.x, b.y, T + 0.17), seg=10)
    k.emit("Forge", col, root, vary=0.06)
    # ---- the commander's place on the gatehouse roof walk: the Head turns him to face the foe
    head = empty("Head", col, root, (0, GYM + 0.02, Z_GATE + 0.04), 0.5, "SINGLE_ARROW")
    crew = empty("Crew", col, head, (0, 0, 0), 0.3, "SINGLE_ARROW")
    crew_dummy(col, crew, 1.12, "sword")
    empty("Muzzle", col, head, (0, 0.35, 1.0), 0.2, "SPHERE")      # (the commander's raised sword)
    return root


# ---- the moving parts, on a rig under the root
PORT_Y = GY1 - 0.035
SMOKE = Vector((FORGE.x, HY0 - 0.11, Z_CHIM + 0.08))


def bones():
    b = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "port": ((0, PORT_Y, T), (0, PORT_Y, T + 0.3), "root"),
         "quin": ((QUIN.x, QUIN.y, T + 0.62), (QUIN.x, QUIN.y, T + 0.82), "root"),
         "forge": ((FORGE.x, FORGE.y - 0.17, T + 0.1), (FORGE.x, FORGE.y - 0.17, T + 0.3), "root")}
    for i, p in enumerate(FLAMES):
        b["torch.%d" % (i + 1)] = (tuple(p), tuple(p + UP * 0.15), "root")
    for i in range(3):
        b["smoke.%d" % (i + 1)] = (tuple(SMOKE), tuple(SMOKE + UP * 0.2), "root")
    for n, top in (("flagL", POLE[0]), ("flagR", POLE[1])):
        flag_bones(b, n, top + Vector((0.02, 0, -0.03)), FLAG_DIR, FLAG_L, segs=3)
    return b


def build_rig(root):
    col = collection("Knight_hall")
    rig = make_rig(col, root, bones())
    k = Kit()
    # the portcullis: an iron grille in the gate's slot, its points down; it slides up into the wall
    for x in (-0.15, -0.075, 0.0, 0.075, 0.15):
        bm_box(k[IRON], (0.028, 0.028, 0.9), (x, PORT_Y, T + 0.52))
        bm_cyl(k[IRON], 0.0, 0.02, 0.08, (x, PORT_Y, T + 0.035), seg=4)
    for z in (0.17, 0.33, 0.49, 0.65, 0.81):
        bm_box(k[IRON], (0.38, 0.022, 0.028), (0, PORT_Y, T + z))
    k.emit("Portcullis", col, rig=rig, bone="port")
    # the quintain's arm: a team shield on one end, a sandbag on the other
    q = QUIN + UP * (T + 0.64)
    bm_cyl(k[IRON], 0.06, 0.06, 0.06, tuple(q), seg=6)
    bm_beam(k[TIMBER], q + Vector((-0.36, 0, 0.04)), q + Vector((0.32, 0, 0.04)), 0.05, 0.05)
    shield(k, q + Vector((-0.36, -0.03, -0.06)), (0, -1, 0), w=0.2, h=0.25, kind="chevron")
    bm_beam(k["sand:0.3:0.6"], q + Vector((0.3, 0, 0.03)), q + Vector((0.3, 0, -0.2)), 0.014, 0.014)
    bm_blob(k["beige:0.25:0.7"], random.Random(3), q + Vector((0.3, 0, -0.28)), 0.085, squash=(1.0, 1.0, 1.3), jitter=0.1)
    k.emit("Quintain", col, rig=rig, bone="quin", bevel=0.006)
    # the forge's fire: the glowing mouth and the coal bed
    f = FORGE
    bm_extrude(k[EMBER], arch_outline((f.x, f.y - 0.172, T + 0.06), (1, 0, 0), 0.22, 0.2, 5), (0, 0.04, 0))
    bm_box(k[EMBER], (0.32, 0.2, 0.03), (f.x, f.y, T + 0.43))
    for dx, dy in ((-0.08, 0.03), (0.06, -0.04), (0.0, 0.05), (0.1, 0.04)):
        bm_flame(k[FIRE], (f.x + dx, f.y + dy, T + 0.43), 0.035, 0.1, n=5)
    k.emit("ForgeFire", col, rig=rig, bone="forge")
    for i, p in enumerate(FLAMES):
        bm_flame(k[FIRE], p, 0.05, 0.16, n=5)
        k.emit("TorchFlame%d" % (i + 1), col, rig=rig, bone="torch.%d" % (i + 1))
    rs = random.Random(9)
    for i in range(3):
        bm_blob(k["white:0.05:0.4"], rs, SMOKE + UP * 0.08, 0.09, squash=(1.0, 1.0, 0.85), jitter=0.16)
        k.emit("Smoke%d" % (i + 1), col, rig=rig, bone="smoke.%d" % (i + 1))
    # the royal standards, flying from the gate towers
    crown = stamp(CROWN, 0.22, 0.62, 0.22, 0.78, key=GOLD)

    def color(u, v):
        if v < 0.1 or v > 0.9:
            return GOLD
        return crown(u, v)
    for n, top in (("flagL", POLE[0]), ("flagR", POLE[1])):
        cloth_grid(k, top + Vector((0.02, 0, -0.03)), FLAG_DIR, (0, 0, -1), FLAG_L, FLAG_H, nu=8, nv=6, tail="swallow", notch=0.8,
                   tail_from=0.74, color=color)
        k.emit("Standard_" + n, col, rig=rig, bones=["%s.%d" % (n, i + 1) for i in range(3)])
    return rig


IDLE_LEN = 120
FIRE_LEN = 20


def pose(rig, t, lift=0.0, snap=0.0, phase=0.0, flare=0.0):
    """t: where in the idle loop (0..1); lift: the portcullis raised (0..1); snap: the standards whipped up; phase: extra
    turns of their flutter; flare: the torches flaring."""
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    w = 2 * math.pi * t
    pb["port"].location = arm_space_loc(pb["port"], (0, 0, 0.5 * lift))
    for n, ph in (("flagL", 0.0), ("flagR", 1.7)):
        amp = 1.0 + snap
        for i in range(3):
            b = pb["%s.%d" % (n, i + 1)]
            b.rotation_quaternion = q(b, (0, 0, 1), (6.0 + 6.0 * i) * amp * math.sin(3 * w + 2 * math.pi * phase - 1.0 * i + ph)) \
                @ q(b, (0, 1, 0), (3.0 + 4.0 * i) * amp * math.sin(4 * w + 2 * math.pi * phase - 1.2 * i + ph + 0.8) - 4.0 * snap * (i + 1))
    for i in range(len(FLAMES)):
        b = pb["torch.%d" % (i + 1)]
        s = 1.0 + 0.22 * math.sin(9 * w + i * 1.9) * math.sin(5 * w + i) + 0.4 * flare
        b.scale = (1.0 + 0.08 * math.sin(11 * w + i), s, 1.0 + 0.08 * math.sin(13 * w + i))
        b.rotation_quaternion = q(b, (1, 0, 0), 8 * math.sin(7 * w + i)) @ q(b, (0, 1, 0), 6 * math.sin(6 * w + 2 * i))
    pb["quin"].rotation_quaternion = q(pb["quin"], (0, 0, 1), 26 * math.sin(w) + 8 * math.sin(3 * w + 0.6))
    s = 1.0 + 0.07 * math.sin(3 * w) + 0.04 * math.sin(7 * w)
    pb["forge"].scale = (s, s, s)
    for i in range(3):
        p = (2 * t + i / 3.0) % 1.0
        b = pb["smoke.%d" % (i + 1)]
        b.location = arm_space_loc(b, (0.12 * p, -0.05 * p, 0.62 * p))
        sz = max(0.02, math.sin(math.pi * p) * (0.7 + 0.8 * p))
        b.scale = (sz, sz, sz)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(rig, f / IDLE_LEN)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        # the portcullis rattles up (frames 0-4), holds while the knights pass, drops (11-18); the standards snap
        lift = smooth(f / 4.0) * (1 - smooth((f - 11) / 7.0))
        snap = 1.4 * smooth(f / 3.0) * (1 - smooth((f - 4) / 15.0))
        pose(rig, 0.0, lift=lift, snap=snap, phase=2.0 * f / FIRE_LEN, flare=snap / 1.4)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.1, 1.3), "dist": 12.5, "yaw": 150, "pitch": 22, "anim_target": (0, GY1, T + 0.9), "anim_dist": 5.0,
           "frames": [("idle", 0), ("idle", 60), ("fire", 4), ("fire", 10), ("fire", 16)],
           "extra": [{"yaw": 330, "pitch": 42, "dist": 4.6, "target": (L.x + 0.3, -0.6, 0.7)},
                     {"yaw": 25, "pitch": 38, "dist": 4.6, "target": (R.x - 0.1, -0.55, 0.8)},
                     {"yaw": 180, "pitch": 12, "dist": 4.6, "target": (0, 1.0, 1.3)},
                     {"yaw": 0, "pitch": 57, "dist": 6.0, "target": (0, 0.4, 1.8)}]}


def build_all():
    root = build_base()
    build_rig(root)
    build_anims()
