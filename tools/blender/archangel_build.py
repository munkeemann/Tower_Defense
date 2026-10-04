"""Builds the Archangel (footprint "fan4": [0,0] the back cell, [0,-1] front, [-1,0] front-left, [1,-1] front-right).

    blender -b --factory-startup --python tools/blender/build_tower.py -- archangel <preview dir>

A great angel (KayKit's Paladin, bare-headed) with broad wings, a big halo and a greatsword of light hovers over a round
dais where the four hexes meet. Behind it a tall stone arch frames a glowing sun window, hung with team banners; golden
statues and braziers stand on the side cells; steps lead down toward the back. The angel is the Head (it turns to face
whoever it judges; the game drops the pillar of light on the target). idle: the hover. fire: the summon clip with a hard
wing beat, the sword kept in hand.
"""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "angel_common.py"), encoding="utf-8").read())

TID = "archangel"
CELLS = [(0, 0), (0, -1), (-1, 0), (1, -1)]
MID = footprint_mid(CELLS)
BACK = hex_to_world(0, 0, MID)
FRONT = hex_to_world(0, -1, MID)
FL = hex_to_world(-1, 0, MID)
FR = hex_to_world(1, -1, MID)
TOP = 0.34
DAIS = 0.7
CHAR = "Paladin.glb"
HEIGHT = 2.0
HOVER = 0.75
GOLD = (1.0, 0.82, 0.4)
ARCH_Y = BACK.y - 0.25          # the arch stands behind the angel (it faces the front)
ARCH_X = 0.78
PILLAR_TOP = 2.55


def build_base():
    col = collection("Archangel")
    root = empty("Archangel", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    C = Vector((0, 0, 0))
    bm = bmesh.new()
    bm_cyl(bm, 1.0, 1.04, 0.18, (C.x, C.y, TOP + 0.09), seg=20)
    bm_cyl(bm, 0.8, 0.84, 0.18, (C.x, C.y, TOP + 0.27), seg=20)
    for k, (w, d) in enumerate(((1.1, 0.3), (0.95, 0.3))):     # steps down toward the front
        bm_box(bm, (w, d, 0.18 - 0.09 * k), (0, FRONT.y - 0.05 + k * 0.28, TOP + (0.09 - 0.045 * k)))
    o = paint(mesh_obj("Dais", bm, col, root), "stone", lo=0.05, hi=0.55)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    ring(bm, (0, 0, 0), 1.05, 0.96, TOP + 0.15, TOP + 0.19, seg=28)
    ring(bm, (0, 0, 0), 0.85, 0.76, DAIS - 0.03, DAIS + 0.005, seg=28)
    for i in range(12):
        a = math.radians(30 * i)
        p = Vector((math.cos(a) * 0.92, math.sin(a) * 0.92, 0))
        bm_cyl(bm, 0.05, 0.0, 0.14, (p.x, p.y, TOP + 0.26), seg=4)
    paint(mesh_obj("Dais_Gold", bm, col, root), "gold", lo=0.1, hi=0.5)
    bm = bmesh.new()
    ring(bm, (0, 0, 0), 0.6, 0.52, DAIS - 0.004, DAIS + 0.004, seg=28)
    for i in range(8):
        a = math.radians(45 * i)
        p0 = Vector((math.cos(a) * 0.18, math.sin(a) * 0.18, DAIS + 0.002))
        p1 = Vector((math.cos(a) * 0.5, math.sin(a) * 0.5, DAIS + 0.002))
        bm_beam(bm, p0, p1, 0.06, 0.006, w1=0.0, h1=0.006)
    paint(mesh_obj("Dais_Inlay", bm, col, root), "team", team=True, lo=0.1, hi=0.4)

    # the arch behind: two pillars, a ring of voussoirs, a glowing sun window and team banners
    bm = bmesh.new()
    for sx in (-1, 1):
        x = sx * ARCH_X
        bm_box(bm, (0.42, 0.42, 0.2), (x, ARCH_Y, TOP + 0.1))
        bm_box(bm, (0.3, 0.3, PILLAR_TOP - TOP - 0.2), (x, ARCH_Y, (TOP + 0.2 + PILLAR_TOP) / 2))
        bm_box(bm, (0.4, 0.4, 0.14), (x, ARCH_Y, PILLAR_TOP))
    n = 9
    for i in range(n):
        a0 = math.pi * i / n
        a1 = math.pi * (i + 1) / n
        p0 = Vector((math.cos(a0) * ARCH_X, ARCH_Y, PILLAR_TOP + 0.07 + math.sin(a0) * ARCH_X))
        p1 = Vector((math.cos(a1) * ARCH_X, ARCH_Y, PILLAR_TOP + 0.07 + math.sin(a1) * ARCH_X))
        bm_beam(bm, p0, p1, 0.3, 0.3, up=(0, 1, 0))
    o = paint(mesh_obj("Arch_Stone", bm, col, root), "stone", lo=0.05, hi=0.6)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    bm_cyl(bm, 0.18, 0.0, 0.3, (0, ARCH_Y, PILLAR_TOP + 0.07 + ARCH_X + 0.3), seg=4)
    for sx in (-1, 1):
        bm_cyl(bm, 0.12, 0.12, 0.05, (sx * ARCH_X, ARCH_Y, PILLAR_TOP + 0.09), seg=8)
    ring(bm, (0, ARCH_Y, PILLAR_TOP - 0.05), 0.5, 0.44, -0.04, 0.04, seg=24, axis="Y")
    paint(mesh_obj("Arch_Gold", bm, col, root), "gold", lo=0.1, hi=0.5)
    sun = glow_mat("archangel_sun", GOLD, 1.3)
    bm = bmesh.new()   # an open sun ring with rays: the angel stays visible through it from the game camera
    ring(bm, (0, ARCH_Y, PILLAR_TOP - 0.05), 0.44, 0.34, -0.025, 0.025, seg=24, axis="Y")
    for i in range(12):
        a = math.radians(30 * i)
        p0 = Vector((math.cos(a) * 0.44, ARCH_Y, PILLAR_TOP - 0.05 + math.sin(a) * 0.44))
        p1 = Vector((math.cos(a) * 0.62, ARCH_Y, PILLAR_TOP - 0.05 + math.sin(a) * 0.62))
        if p1.z < PILLAR_TOP + 0.6:
            bm_beam(bm, p0, p1, 0.07, 0.03, w1=0.0, h1=0.02, up=(0, 1, 0))
    o = mesh_obj("Arch_Sun", bm, col, root)
    o.data.materials.append(sun)
    bm = bmesh.new()
    for sx in (-1, 1):
        x = sx * ARCH_X
        p = Vector((x, ARCH_Y - 0.16, 0))
        pts = [Vector((x - 0.14, ARCH_Y - 0.16, PILLAR_TOP - 0.15)), Vector((x + 0.14, ARCH_Y - 0.16, PILLAR_TOP - 0.15)),
               Vector((x + 0.14, ARCH_Y - 0.16, TOP + 1.05)), Vector((x, ARCH_Y - 0.16, TOP + 0.9)),
               Vector((x - 0.14, ARCH_Y - 0.16, TOP + 1.05))]
        for face in (0.0, 0.32):            # on both faces of the pillars
            for off in (0.0, -0.012):
                vs = [bm.verts.new(q + Vector((0, face + (off if face == 0.0 else -off), 0))) for q in pts]
                bm.faces.new(vs if (off < 0) == (face == 0.0) else list(reversed(vs)))
    paint(mesh_obj("Arch_Banners", bm, col, root), "team", team=True, lo=0.1, hi=0.7)

    # side cells: golden statues on plinths, braziers
    fire = glow_mat("holy_fire", (1.0, 0.72, 0.3), 1.6)
    import random
    for side, P in (("L", FL), ("R", FR)):
        sx = -1 if side == "L" else 1
        sp = P + Vector((sx * 0.2, 0.25, 0))
        bm = bmesh.new()
        bm_box(bm, (0.5, 0.5, 0.36), (sp.x, sp.y, TOP + 0.18))
        bm_box(bm, (0.58, 0.58, 0.08), (sp.x, sp.y, TOP + 0.4))
        bz = P + Vector((-sx * 0.3, -0.45, 0))
        bm_cyl(bm, 0.08, 0.12, 0.5, (bz.x, bz.y, TOP + 0.25), seg=6)
        bm_cyl(bm, 0.26, 0.16, 0.16, (bz.x, bz.y, TOP + 0.58), seg=8)
        paint(mesh_obj("Side_Stone_" + side, bm, col, root), "stone", lo=0.1, hi=0.6)
        rnd = random.Random(3 if side == "L" else 8)
        bm = bmesh.new()
        fc = Vector((bz.x, bz.y, TOP + 0.65))
        for kf in range(5):
            a = math.radians(72 * kf + rnd.uniform(-12, 12))
            d = 0.0 if kf == 0 else 0.09
            cc = fc + Vector((math.cos(a) * d, math.sin(a) * d, 0))
            h = 0.4 if kf == 0 else rnd.uniform(0.18, 0.28)
            top = bm.verts.new(cc + Vector((0, 0, h)))
            ms = [bm.verts.new(cc + Vector((math.cos(math.radians(90 * j + 45)) * 0.07, math.sin(math.radians(90 * j + 45)) * 0.07, 0)))
                  for j in range(4)]
            for j in range(4):
                bm.faces.new((ms[j], ms[(j + 1) % 4], top))
        o = mesh_obj("Side_Flame_" + side, bm, col, root)
        o.data.materials.append(fire)
        for o in kk_import("props/paladin_statue", col, root, (sp.x, sp.y, TOP + 0.44), 180 + sx * 30, 0.36, name="Prop_Statue_" + side):
            pass
    for i, (loc, rot, sc) in enumerate((((0.62, FRONT.y + 0.3, TOP), 30, 0.36), ((-0.66, FRONT.y + 0.25, TOP), 70, 0.32))):
        for o in kk_import("dungeon/candle_triple", col, root, loc, rot, sc, name="Prop_Candles_%d" % i):
            pass
    empty("Head", col, root, (0, 0, DAIS), 0.5, "SINGLE_ARROW")
    return root


def build_head():
    col = collection("Archangel")
    return make_angel(CHAR, col, bpy.data.objects["Head"], HEIGHT, HOVER, span=1.45, wing_scale=1.4, halo_r=0.26,
                      weapon=(0.18, 0.22), blade=(0.26, 1.0), muzzle_off=(0.0, 0.3, 0.9), gold=GOLD)


def build_anims():
    angel_anims(bpy.data.objects["Rig"], "Jump_Idle", "Ranged_Magic_Summon", fire_len=30, hide=None, beat=1.2, bob=0.08)


PREVIEW = {"target": (0, 0.3, 1.7), "dist": 10.5, "yaw": 160, "pitch": 16, "anim_target": (0, 0.2, 2.1), "anim_dist": 6.0,
           "frames": [("idle", 0), ("idle", 30), ("fire", 6), ("fire", 14), ("fire", 24)]}


def build_all():
    build_base()
    build_head()
    build_anims()
