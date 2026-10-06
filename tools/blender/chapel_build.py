"""Builds the Chapel of Dawn (footprint "fan4": [0,0] the back cell, [0,-1] front, [-1,0] left, [1,-1] right).

    python tools/blender/build.py chapel --out <preview dir>

One chapel owning the whole churchyard. The nave runs front to back through the middle: coursed grey stone between
buttresses, tall arched windows glowing warm gold, a steep tiled roof in the team color under a gilded ridge, a rose
window in its back gable over the rounded apse (the side the camera sees). The square bell tower stands at its front
end: a west door, an open belfry with the bell, a tiled pyramid roof and a gilded sun finial over which the halo
hovers. A gabled porch opens from the nave's right side onto the paved forecourt (the font, the gate to the road, the
paladin: Crew); the left side is the statue garden (a stone paladin between two candle stands). A low coped wall rings
the yard. Rig under the root (nothing turns): idle (the halo wheels and breathes, the candles flicker, the bell
stirs), fire (the bell swings, the sun flares and a ring of light bursts out of the finial).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "castle_common.py"), encoding="utf-8").read())

TID = "chapel"
CELLS = [(0, 0), (0, -1), (-1, 0), (1, -1)]
MID = footprint_mid(CELLS)
BACK = hex_to_world(0, 0, MID)
FRONT = hex_to_world(0, -1, MID)
LEFT = hex_to_world(-1, 0, MID)
RIGHT = hex_to_world(1, -1, MID)
TOP = 0.34
NX = 0.74                         # the nave's half width
NY0, NY1 = -1.22, 0.75            # its back end (the apse) and front end (the tower)
WALL = TOP + 1.1
RIDGE = TOP + 2.0
TC = Vector((0.0, 1.25, 0.0))     # the bell tower's axis
TW = 1.0                          # its side
Z_STAGE = TOP + 1.2               # the string course
Z_BELFRY = TOP + 2.05             # the belfry floor
Z_CORNICE = TOP + 2.68
Z_ROOF = TOP + 2.76
Z_APEX = TOP + 3.26
Z_SUN = TOP + 3.58                # the sun finial's middle
Z_HALO = Z_SUN + 0.42
AC = Vector((0.0, NY0, 0.0))      # the apse's axis
AR = 0.66
AWALL = TOP + 0.95
PORCH_Y = -0.24                   # where the porch leaves the nave's right wall
FONT = Vector((2.1, -0.35, 0.0))
STATUE = Vector((-2.05, 0.0, 0.0))
CANDLES = [Vector((-1.45, 0.66, 0.0)), Vector((-1.45, -0.62, 0.0)), Vector((1.3, -0.72, 0.0))]
WARM = "glow:1.0,0.74,0.3,0.9"
HOLY = "glow:1.0,0.9,0.55,1.0"


def tangent(deg):
    """Along a round wall at `deg`, so that the wall faces outward (see wall_out)."""
    a = math.radians(deg)
    return Vector((-math.sin(a), math.cos(a), 0))


def candle_stand(k, p, z0, h=0.62):
    """A tall iron candle stand on a tripod foot, three cream candles in its dish. Returns where the flames start."""
    for i in range(3):
        a = math.radians(120 * i + 30)
        bm_beam(k[IRON], (p.x, p.y, z0 + 0.12), (p.x + math.cos(a) * 0.14, p.y + math.sin(a) * 0.14, z0), 0.03, 0.03)
    bm_cyl(k[IRON], 0.024, 0.02, h, (p.x, p.y, z0 + h / 2), seg=6)
    bm_cyl(k[IRON], 0.1, 0.12, 0.05, (p.x, p.y, z0 + h + 0.02), seg=8)
    tops = []
    for i in range(3):
        a = math.radians(120 * i + 90)
        q = Vector((p.x + math.cos(a) * 0.055, p.y + math.sin(a) * 0.055, z0 + h + 0.045))
        hh = (0.16, 0.12, 0.14)[i]
        bm_cyl(k["cream:0.05:0.5"], 0.028, 0.026, hh, (q.x, q.y, q.z + hh / 2), seg=6)
        tops.append(q + UP * hh)
    return tops


def stone_knight(k, p, z0, s=1.0, face=0.0):
    """A stone paladin standing on p at z0 (its sword tip 1.8 * s up): boots, a tabard and cuirass, pauldrons, a crested
    helm, the sword raised in the right hand, a kite shield on the left arm, a cloak behind. face: degrees, 0 = +X."""
    P, fw, lf = frame2((p[0], p[1]), face)          # fw: the way it faces; lf: its left
    S, D = "stone:0.0:0.5", "stone:0.25:0.75"

    def at(x, y, z):
        return P(x * s, y * s, z0 + z * s)

    def box(key, size, c, rot=(0, 0, 0)):
        bm_box(k[key], tuple(v * s for v in size), tuple(at(*c)), (rot[0], rot[1], rot[2] + face))

    def ov(x, y, z, rx, ry, n=8, power=2.6):
        return oval(at(x, y, z), fw, lf, rx * s, ry * s, n, power=power)
    for sy in (-1, 1):                                            # boots and greaves
        box(D, (0.2, 0.13, 0.08), (0.03, sy * 0.09, 0.04))
        box(S, (0.13, 0.12, 0.3), (0.0, sy * 0.09, 0.22))
    bm_loft(k[S], [ov(0, 0, 0.3, 0.14, 0.2), ov(0, 0, 0.55, 0.12, 0.16), ov(0, 0, 0.78, 0.15, 0.2), ov(0.01, 0, 0.92, 0.12, 0.17)])
    bm_loft(k[D], [ov(0, 0, 0.6, 0.13, 0.175), ov(0, 0, 0.66, 0.13, 0.175)])                                       # the belt
    for sy in (-1, 1):                                            # pauldrons
        bm_ellipsoid(k[D], tuple(at(0, sy * 0.21, 0.9)), (0.09 * s, 0.09 * s, 0.07 * s), u=7, v=4)
    box(S, (0.15, 0.15, 0.17), (0.0, 0.0, 1.03))                  # the head in its helm
    box(D, (0.16, 0.16, 0.04), (0.0, 0.0, 0.99))                  # the visor
    bm_crystal(k[D], at(-0.02, 0, 1.11), at(-0.02, 0, 1.28), 0.05 * s, n=4, shoulder=0.4)        # the crest
    sh, el, hd = at(0.02, -0.21, 0.86), at(0.14, -0.27, 1.0), at(0.1, -0.22, 1.2)             # the right arm, raised
    bm_tube(k[S], [sh, el, hd], [0.06 * s, 0.055 * s, 0.05 * s], n=6)
    bm_ellipsoid(k[S], tuple(hd), (0.06 * s, 0.06 * s, 0.06 * s), u=6, v=4)
    bm_beam(k[D], hd - UP * (0.12 * s), hd + UP * (0.62 * s), 0.07 * s, 0.025 * s, 0.03 * s, 0.015 * s, up=tuple(fw))   # the blade
    bm_beam(k[D], hd + UP * (0.08 * s) - lf * (0.1 * s), hd + UP * (0.08 * s) + lf * (0.1 * s), 0.03 * s, 0.03 * s)   # the guard
    sh, el = at(0.02, 0.21, 0.86), at(0.12, 0.3, 0.68)                                            # the left arm, with the shield
    bm_tube(k[S], [sh, el, at(0.2, 0.26, 0.6)], [0.06 * s, 0.055 * s, 0.05 * s], n=6)
    shield(k, at(0.22, 0.24, 0.62), fw, w=0.26 * s, h=0.36 * s, face=S, rim=D, device=D, th=0.03 * s, kind="cross")
    bm_loft(k[S], [ov(-0.1, 0, 0.9, 0.03, 0.2, power=2.0), ov(-0.14, 0, 0.5, 0.05, 0.24, power=2.0), ov(-0.2, 0, 0.04, 0.07, 0.3, power=2.0)])  # the cloak
    return k


def build_base():
    col = collection("Chapel")
    root = empty("Chapel", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    rnd = random.Random(11)
    k = Kit()
    # ---- the churchyard: flagstones wherever the chapel isn't, a low coped wall round the yard, open at the gates
    pave(k, rnd, CELLS, T, keep_out=[(-NX - 0.05, NY0 - 0.05, NX + 0.05, NY1 + 0.05), (AC.x, AC.y, AR + 0.1),
                                      (TC.x - 0.56, TC.y - 0.56, TC.x + 0.56, TC.y + 0.56), (NX, PORCH_Y - 0.33, NX + 0.5, PORCH_Y + 0.33)],
         inset=0.44, size=0.3)
    k.emit("Paving", col, root, vary=0.09)
    loop = outline(CELLS, 0.3)
    posts = []
    for i, a in enumerate(loop):
        b = loop[(i + 1) % len(loop)]
        m = (a + b) * 0.5
        if (m - AC).length < 0.95 or (m.y > 1.5 and abs(m.x) < 0.7):      # the apse closes the yard behind; the west door opens on the road
            continue
        if m.y > 0.5 and 1.3 < m.x < 2.3:                                   # the forecourt's gate
            posts.extend([a, b])
            continue
        crenel_wall(k, rnd, [a, b], T, 0.3, th=0.14, course=0.3, block=0.42, merlon=None, cap=STONE_LIGHT)
    for p in posts:
        bm_box(k[STONE_LIGHT], (0.2, 0.2, 0.56), (p.x, p.y, T + 0.28))
        bm_box(k[STONE_LIGHT], (0.26, 0.26, 0.05), (p.x, p.y, T + 0.585))
        bm_ellipsoid(k[GOLD], (p.x, p.y, T + 0.675), (0.065, 0.065, 0.065), u=8, v=5)
    k.emit("Yard_Wall", col, root, vary=0.07)

    # ---- the nave: coursed walls with quoins, buttresses between tall gold windows, the back gable with its rose
    stone_box(k, rnd, (0, (NY0 + NY1) / 2), 2 * NX, NY1 - NY0, T, WALL, quoins=STONE_LIGHT, sides="NEW")
    for sx, right, ys_b, ys_w in ((-1, (0, -1, 0), (-1.06, -0.5, 0.06, 0.6), (-0.78, -0.22, 0.33)),
                                  (1, (0, 1, 0), (-1.06, 0.58), (-0.78, 0.3))):
        for y in ys_b:
            buttress(k, (sx * NX, y), (sx, 0), T, WALL - 0.12, w=0.22, d0=0.3, d1=0.16)
        for y in ys_w:
            arch_window(k, (sx * (NX + 0.004), y, T + 0.3), right, 0.24, 0.72, glow=WARM, th=0.065, proud=0.045, n=5, bars=IRON)
    gable_wall(k, rnd, (-NX, NY0), (NX, NY0), WALL, RIDGE + 0.02)
    k.emit("Nave", col, root, vary=0.07)
    rz = WALL + 0.56
    bm_cyl(k[WARM], 0.16, 0.16, 0.03, (0, NY0 - 0.075, rz), rot=(90, 0, 0), seg=12)
    k.emit("Rose_Glow", col, root)
    ring(k[GOLD], (0, NY0, rz), 0.2, 0.155, -0.11, -0.065, seg=12, axis="Y")
    for i in range(6):
        a = math.radians(30 * i)
        bm_beam(k[GOLD], (-math.cos(a) * 0.17, NY0 - 0.095, rz - math.sin(a) * 0.17), (math.cos(a) * 0.17, NY0 - 0.095, rz + math.sin(a) * 0.17), 0.02, 0.025, up=(0, 1, 0))
    bm_ellipsoid(k[GOLD], (0, NY0 - 0.095, rz), (0.04, 0.03, 0.04), u=8, v=5)
    k.emit("Rose", col, root)

    # ---- the apse: a half round of coursed stone under a half cone of tiles, three windows toward the camera
    bm_block_course(k[STONE_FOOT], rnd, AC, AR + 0.06, T, 0.12, 12, depth=0.24, skip=lambda a: 8 < a < 172)
    course_tower(k, rnd, AC, AR, AR - 0.02, T + 0.12, AWALL, courses=5, n=12, skip=lambda c, a: 8 < a < 172)
    for a in (210, 270, 330):
        arch_window(k, polar(AC, AR + 0.004, a, T + 0.3), tangent(a), 0.18, 0.5, glow=WARM, th=0.055, proud=0.04, n=4)
    k.emit("Apse", col, root, vary=0.07)
    bm_tile_cone_arc(k[TILES], rnd, AC, AR + 0.1, AWALL, 0.45, 180, 360, rows=4, n=9, flare=0.05, top=0.08)
    k.emit("Apse_Roof", col, root, vary=0.09)
    half = lambda r, z: [polar(AC, r, 180 + 180.0 * i / 8, z) for i in range(9)]
    bm_loft(k[TILES_UNDER], [half(AR + 0.08, AWALL - 0.04), half(0.06, AWALL + 0.42)], cap0=False, cap1=False)
    k.emit("Apse_Roof_Under", col, root)

    # ---- the roof: steep team tiles under a gilded ridge, barge boards at the back gable (it runs into the tower in front)
    gable_roof(k, rnd, (0, (NY0 + NY1 + 0.2) / 2), NY1 + 0.1 - NY0, 2 * NX, WALL, RIDGE, rot=90, eave=0.12, verge=0.1, rows=4, cols=8, ends=(True, False))
    k.emit("Roof", col, root, vary=0.09)

    # ---- the porch: a little gabled vestibule off the right wall, its arched door onto the forecourt, candles beside it
    pw, pd, ph = 0.56, 0.44, T + 0.72
    pc = Vector((NX + pd / 2 - 0.02, PORCH_Y, 0))
    stone_box(k, rnd, (pc.x, pc.y), pd, pw, T, ph, sides="NSE", quoins=STONE_LIGHT, course=0.18, block=0.3)
    gable_wall(k, rnd, (pc.x + pd / 2, pc.y - pw / 2), (pc.x + pd / 2, pc.y + pw / 2), ph, ph + 0.34)
    arch_door(k, (pc.x + pd / 2 + 0.004, pc.y, T), (0, 1, 0), 0.3, 0.56, th=0.07)
    bm_box(k[STONE_FOOT], (0.2, 0.5, 0.08), (pc.x + pd / 2 + 0.1, pc.y, T + 0.04))
    k.emit("Porch", col, root, vary=0.07)
    gable_roof(k, rnd, (pc.x - 0.03, pc.y), pd + 0.1, pw, ph, ph + 0.34, rot=0, eave=0.08, verge=0.07, rows=2, cols=3, ends=(False, True))
    k.emit("Porch_Roof", col, root, vary=0.09)

    # ---- the bell tower: two coursed stages with quoins and a string course, the west door, slit windows
    stone_box(k, rnd, (TC.x, TC.y), TW, TW, T, Z_BELFRY, quoins=STONE_LIGHT, course=0.24, block=0.42)
    bm_box(k[STONE_LIGHT], (TW + 0.12, TW + 0.12, 0.07), (TC.x, TC.y, Z_STAGE))
    arch_door(k, (TC.x, TC.y + TW / 2 + 0.004, T), (-1, 0, 0), 0.34, 0.64, th=0.085)
    bm_box(k[STONE_FOOT], (0.66, 0.16, 0.1), (TC.x, TC.y + TW / 2 + 0.085, T + 0.05))
    for sx in (-1, 1):
        arch_window(k, (TC.x + sx * (TW / 2 + 0.004), TC.y, T + 1.45), (0, sx, 0), 0.11, 0.34, glow=WARM, th=0.045, proud=0.035, n=3, sill=False)
    arch_window(k, (TC.x, TC.y + TW / 2 + 0.004, T + 1.45), (-1, 0, 0), 0.11, 0.34, glow=WARM, th=0.045, proud=0.035, n=3, sill=False)
    # the belfry: a stone floor, four corner piers, an open arch in every face, spandrels and a cornice over them
    bm_box(k[STONE], (TW, TW, 0.08), (TC.x, TC.y, Z_BELFRY + 0.04))
    for sx in (-1, 1):
        for sy in (-1, 1):
            bm_box(k[STONE_LIGHT], (0.2, 0.2, Z_CORNICE - Z_BELFRY), (TC.x + sx * 0.4, TC.y + sy * 0.4, (Z_BELFRY + Z_CORNICE) / 2))
    for out in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        o = Vector((out[0], out[1], 0))
        rt = Vector((-o.y, o.x, 0))
        c = TC + o * (TW / 2) + UP * (Z_BELFRY + 0.08)
        bm_arch(k[STONE_LIGHT], c, rt, 0.44, 0.2, th=0.08, depth=0.2, n=5)
        bm_obox(k[STONE], TC + o * (TW / 2), rt, TW, 0.16, Z_CORNICE - (Z_BELFRY + 0.58), z0=Z_BELFRY + 0.58)
    bm_box(k[STONE_LIGHT], (TW + 0.16, TW + 0.16, 0.08), (TC.x, TC.y, Z_CORNICE + 0.04))
    bm_beam(k[TIMBER], (TC.x - 0.42, TC.y, Z_BELFRY + 0.5), (TC.x + 0.42, TC.y, Z_BELFRY + 0.5), 0.07, 0.07)       # the bell beam
    k.emit("Tower", col, root, vary=0.07)
    pyramid_roof(k, rnd, (TC.x, TC.y), TW, TW, Z_ROOF, Z_APEX, eave=0.12, rows=3, cols=3)
    k.emit("Tower_Roof", col, root, vary=0.09)
    # the gilded sun: a rod up from the apex, a disc with eight rays, facing the camera's way
    bm_cyl(k[GOLD], 0.04, 0.028, Z_SUN - Z_APEX + 0.02, (TC.x, TC.y, (Z_APEX + Z_SUN) / 2), seg=6)
    bm_ellipsoid(k[GOLD], (TC.x, TC.y, Z_APEX + 0.1), (0.06, 0.06, 0.06), u=8, v=5)
    bm_cyl(k[GOLD], 0.17, 0.17, 0.04, (TC.x, TC.y, Z_SUN), rot=(90, 0, 0), seg=12)
    for i in range(8):
        a = math.radians(45 * i)
        d = Vector((math.cos(a), 0, math.sin(a)))
        bm_crystal(k[GOLD], TC + UP * Z_SUN + d * 0.14, TC + UP * Z_SUN + d * (0.34 if i % 2 == 0 else 0.27), 0.04, n=4, shoulder=0.3)
    k.emit("Sun", col, root)

    # ---- the forecourt: the font (an octagonal basin of glowing water on a stem) by the gate; the paladin stands here
    bm_cyl(k[STONE_FOOT], 0.32, 0.28, 0.08, (FONT.x, FONT.y, T + 0.04), seg=8)
    bm_cyl(k[STONE], 0.12, 0.1, 0.3, (FONT.x, FONT.y, T + 0.23), seg=8)
    bm_cyl(k[STONE_LIGHT], 0.2, 0.3, 0.22, (FONT.x, FONT.y, T + 0.49), seg=8)
    k.emit("Font", col, root)
    bm_cyl(k[HOLY], 0.26, 0.26, 0.02, (FONT.x, FONT.y, T + 0.595), seg=8)
    k.emit("Font_Water", col, root)

    # ---- the statue garden: a stone paladin on an octagonal pedestal between two candle stands
    bm_cyl(k[STONE_FOOT], 0.5, 0.46, 0.1, (STATUE.x, STATUE.y, T + 0.05), seg=8)
    bm_cyl(k[STONE_LIGHT], 0.37, 0.33, 0.26, (STATUE.x, STATUE.y, T + 0.23), seg=8)
    bm_cyl(k[STONE_LIGHT], 0.4, 0.4, 0.05, (STATUE.x, STATUE.y, T + 0.385), seg=8)
    k.emit("Pedestal", col, root)
    stone_knight(k, STATUE, T + 0.41, 0.95, face=0.0)
    k.emit("Statue", col, root)
    flames = []
    for p in CANDLES:
        flames.append(candle_stand(k, p, T))
    k.emit("Candles", col, root)

    crew = empty("Crew", col, root, (1.62, 0.42, T), 0.3, "SINGLE_ARROW")
    crew_dummy(col, crew, 1.12, "sword")
    empty("Head", col, root, (TC.x, TC.y, Z_SUN), 0.5, "SINGLE_ARROW")
    return root, flames


# ---- the moving parts, on a rig under the root: the halo, the sun's glow, the flash, the bell, the candle flames
def bones_for(flames):
    b = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "halo": ((TC.x, TC.y, Z_HALO), (TC.x, TC.y, Z_HALO + 0.2), "root"),
         "sun": ((TC.x, TC.y, Z_SUN), (TC.x, TC.y, Z_SUN + 0.2), "root"),
         "flash": ((TC.x, TC.y, Z_SUN), (TC.x + 0.2, TC.y, Z_SUN), "root"),
         "bell": ((TC.x, TC.y, Z_BELFRY + 0.5), (TC.x, TC.y, Z_BELFRY + 0.2), "root")}
    for i, tops in enumerate(flames):
        c = sum(tops, Vector()) / len(tops)
        b["flame.%d" % (i + 1)] = (tuple(c - UP * 0.02), tuple(c + UP * 0.15), "root")
    return b


def build_rig(root, flames):
    col = collection("Chapel")
    rig = make_rig(col, root, bones_for(flames))
    k = Kit()
    c = TC + UP * Z_HALO
    bm_ring_n(k[HOLY], c, UP, 0.46, 0.39, 0.02, seg=20)
    for i in range(8):
        a = math.radians(45 * i)
        bm_gem(k["gold:0.0:0.45"], c + Vector((math.cos(a) * 0.425, math.sin(a) * 0.425, 0)), 0.045, 0.07, 0.07, n=4, girdle=0.02)
    k.emit("Halo", col, rig=rig, bone="halo")
    bm_cyl(k[HOLY], 0.1, 0.1, 0.06, (TC.x, TC.y, Z_SUN), rot=(90, 0, 0), seg=10)
    k.emit("Sun_Glow", col, rig=rig, bone="sun")
    bm_ring_n(k["glow:1.0,0.85,0.5,1.1"], TC + UP * Z_SUN, UP, 0.3, 0.24, 0.012, seg=16)
    k.emit("Flash", col, rig=rig, bone="flash")
    bz = Z_BELFRY + 0.5
    bm_box(k[TIMBER], (0.22, 0.1, 0.09), (TC.x, TC.y, bz - 0.04))                                                 # the yoke
    bm_tube(k["gold:0.05:0.5"], [(TC.x, TC.y, bz - 0.09), (TC.x, TC.y, bz - 0.16), (TC.x, TC.y, bz - 0.28), (TC.x, TC.y, bz - 0.36), (TC.x, TC.y, bz - 0.385)],
            [0.045, 0.1, 0.12, 0.17, 0.165], n=10)
    bm_ellipsoid(k[IRON], (TC.x, TC.y, bz - 0.37), (0.035, 0.035, 0.035), u=6, v=4)                               # the clapper
    k.emit("Bell", col, rig=rig, bone="bell")
    for i, tops in enumerate(flames):
        for j, t in enumerate(tops):
            bm_flame(k["glow:1.0,0.72,0.25,1.0"], t, 0.028, 0.1 + 0.02 * (j % 2), n=5)
        k.emit("Flame%d" % (i + 1), col, rig=rig, bone="flame.%d" % (i + 1))
    empty("Muzzle", col, bpy.data.objects["Head"], (0, 0, 0), 0.25, "SPHERE")
    return rig


IDLE_LEN = 120
FIRE_LEN = 20


def pose(rig, spin=0.0, tilt=10.0, roll=0.0, bob=0.0, breathe=1.0, flare=1.0, flash=0.0, swing=0.0, flicker=(1.0, 1.0, 1.0), lean=(0.0, 0.0, 0.0)):
    """spin: the halo's turn; tilt / roll: its lean and where the lean points (so it wheels); swing: the bell's angle,
    sideways as the camera sees it; flicker: the three candle groups' flame heights; flash: the burst ring's size."""
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    h = pb["halo"]
    h.rotation_quaternion = q(h, (0, 0, 1), roll) @ q(h, (1, 0, 0), tilt) @ q(h, (0, 0, 1), spin - roll)
    h.location = arm_space_loc(h, (0, 0, bob))
    h.scale = (breathe, breathe, breathe)
    pb["sun"].scale = (flare, flare, flare)
    s = max(flash, 0.001)
    pb["flash"].scale = (s, s, 1.0)
    pb["bell"].rotation_quaternion = q(pb["bell"], (0, 1, 0), swing)
    for i in range(3):
        name = "flame.%d" % (i + 1)
        if name in pb:
            f = pb[name]
            f.scale = (1.0, 1.0, flicker[i])
            f.rotation_quaternion = q(f, (1, 0, 0), lean[i])


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        w = 2 * math.pi * t
        pose(rig, spin=360 * t, tilt=12, roll=360 * t, bob=0.06 * math.sin(w * 2), breathe=1.0 + 0.04 * math.sin(w * 3),
             flare=1.0 + 0.1 * math.sin(w * 4), swing=2.5 * math.sin(w * 2),
             flicker=tuple(1.0 + 0.22 * math.sin(w * (9 + i * 2) + i * 1.9) for i in range(3)),
             lean=tuple(6 * math.sin(w * (5 + i) + i) for i in range(3)))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        # the bell swings a full stroke each way, the sun flares as it tolls (frame 4) and the ring of light runs out
        k = f / FIRE_LEN
        burst = smooth((f - 2) / 5.0) * (1 - smooth((f - 9) / 8.0))
        pose(rig, spin=0, tilt=12 + 10 * burst, roll=0, bob=0.2 * burst, breathe=1.0 + 0.25 * burst,
             flare=1.0 + 1.6 * burst, flash=6.0 * burst, swing=42 * math.sin(2 * math.pi * k) * (1 - 0.5 * smooth((f - 12) / 8.0)),
             flicker=tuple(1.0 + 0.5 * burst + 0.2 * math.sin(f * 2.1 + i) for i in range(3)), lean=(0, 0, 0))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.1, 1.5), "dist": 11.5, "yaw": 150, "pitch": 24, "anim_target": (TC.x, TC.y, Z_SUN - 0.35), "anim_dist": 4.4,
           "frames": [("idle", 0), ("idle", 40), ("fire", 4), ("fire", 8), ("fire", 14)],
           "extra": [{"yaw": 50, "pitch": 28, "dist": 5.6, "target": (1.5, 0.0, 0.9)},
                     {"yaw": 310, "pitch": 26, "dist": 5.4, "target": (-1.5, 0.0, 0.9)},
                     {"yaw": 0, "pitch": 14, "dist": 4.2, "target": (TC.x, TC.y, Z_BELFRY + 0.35)},
                     {"yaw": 250, "pitch": 18, "dist": 3.2, "target": (STATUE.x, STATUE.y, 1.1)}]}


def build_all():
    root, flames = build_base()
    build_rig(root, flames)
    build_anims()
