"""Builds the Seraph (footprint "arrow3": [0,0] front, [1,0] back-right, [-1,1] back-left), a creature tower.

    blender -b --factory-startup --python tools/blender/build_tower.py -- seraph <preview dir>

An armored angel (KayKit's Paladin with helmet) hovers over a round shrine on the front cell, with feathered wings, a
halo and a spear of light; two stone obelisks with team banners and holy flames stand on the back cells. The angel is
the Head: it turns toward targets and throws (spears leave from the Muzzle at its hand).
idle: it hovers, the wings beat slowly, the halo turns. fire: the throw (from the pack's clip, its wind-up trimmed so the
spear leaves on the first frames), a hard wing beat, and the spear forms again in its hand.
"""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "angel_common.py"), encoding="utf-8").read())

TID = "seraph"
CELLS = [(0, 0), (1, 0), (-1, 1)]
MID = footprint_mid(CELLS)
FRONT = hex_to_world(0, 0, MID)
BR = hex_to_world(1, 0, MID)
BL = hex_to_world(-1, 1, MID)
TOP = 0.34
SHRINE = 0.68                 # shrine top (the Head)
CHAR = "Paladin_with_Helmet.glb"
HEIGHT = 1.5
HOVER = 0.5
GOLD = (1.0, 0.8, 0.35)


def build_base():
    col = collection("Seraph")
    root = empty("Seraph", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    F = FRONT
    bm = bmesh.new()
    bm_cyl(bm, 0.95, 0.98, 0.18, (F.x, F.y, TOP + 0.09), seg=16)
    bm_cyl(bm, 0.72, 0.75, 0.16, (F.x, F.y, TOP + 0.26), seg=16)
    o = paint(mesh_obj("Shrine_Tiers", bm, col, root), "stone", lo=0.05, hi=0.55)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    ring(bm, (F.x, F.y, 0), 0.99, 0.9, TOP + 0.16, TOP + 0.2, seg=24)
    ring(bm, (F.x, F.y, 0), 0.76, 0.68, SHRINE - 0.03, SHRINE + 0.005, seg=24)
    for i in range(8):
        a = math.radians(45 * i)
        p = F + Vector((math.cos(a) * 0.86, math.sin(a) * 0.86, 0))
        bm_cyl(bm, 0.06, 0.0, 0.16, (p.x, p.y, TOP + 0.27), seg=4)
    paint(mesh_obj("Shrine_Gold", bm, col, root), "gold", lo=0.1, hi=0.5)
    bm = bmesh.new()
    ring(bm, (F.x, F.y, 0), 0.5, 0.42, SHRINE - 0.004, SHRINE + 0.004, seg=24)
    for i in range(4):
        a = math.radians(90 * i + 45)
        p = F + Vector((math.cos(a) * 0.3, math.sin(a) * 0.3, 0))
        bm_box(bm, (0.12, 0.12, 0.008), (p.x, p.y, SHRINE + 0.002), (0, 0, 45))
    paint(mesh_obj("Shrine_Inlay", bm, col, root), "team", team=True, lo=0.1, hi=0.4)

    # two obelisks with banners and holy flames on the back cells
    fire = glow_mat("holy_fire", (1.0, 0.72, 0.3), 1.6)
    for side, C in (("R", BR), ("L", BL)):
        c = C + Vector((-0.15 if side == "R" else 0.15, 0.05, 0))
        bm = bmesh.new()
        bm_box(bm, (0.62, 0.62, 0.18), (c.x, c.y, TOP + 0.09))
        bm_box(bm, (0.44, 0.44, 0.14), (c.x, c.y, TOP + 0.25))
        _obelisk(bm, c, TOP + 0.32, 0.17, 0.12, 1.7)
        o = paint(mesh_obj("Obelisk_" + side, bm, col, root), "stone", lo=0.05, hi=0.7)
        b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.015; b.segments = 1; b.limit_method = "ANGLE"
        bm = bmesh.new()
        bm_cyl(bm, 0.16, 0.1, 0.12, (c.x, c.y, TOP + 0.32 + 1.7 + 0.06), seg=8)
        ring(bm, (c.x, c.y, 0), 0.25, 0.22, TOP + 0.31, TOP + 0.35, seg=4)
        paint(mesh_obj("Obelisk_Gold_" + side, bm, col, root), "gold", lo=0.1, hi=0.5)
        bm = bmesh.new()
        fc = Vector((c.x, c.y, TOP + 0.32 + 1.7 + 0.12))
        import random
        rnd = random.Random(4 if side == "R" else 9)
        for k in range(5):
            a = math.radians(72 * k + rnd.uniform(-12, 12))
            d = 0.0 if k == 0 else 0.07
            cc = fc + Vector((math.cos(a) * d, math.sin(a) * d, 0))
            h = 0.34 if k == 0 else rnd.uniform(0.16, 0.24)
            top = bm.verts.new(cc + Vector((0, 0, h)))
            ms = [bm.verts.new(cc + Vector((math.cos(math.radians(90 * j + 45)) * 0.06, math.sin(math.radians(90 * j + 45)) * 0.06, 0)))
                  for j in range(4)]
            for j in range(4):
                bm.faces.new((ms[j], ms[(j + 1) % 4], top))
        o = mesh_obj("Obelisk_Flame_" + side, bm, col, root)
        o.data.materials.append(fire)
        # a team banner down the face that looks toward the shrine
        to = (Vector((F.x, F.y, 0)) - Vector((c.x, c.y, 0))).normalized()
        tv = Vector((-to.y, to.x, 0))
        bm = bmesh.new()
        w = 0.13
        z0, z1 = TOP + 1.7, TOP + 0.75
        base_p = Vector((c.x, c.y, 0)) + to * 0.16
        pts = [base_p + tv * w + Vector((0, 0, z0)), base_p - tv * w + Vector((0, 0, z0)), base_p - tv * w + Vector((0, 0, z1 + 0.12)),
               base_p + Vector((0, 0, z1)), base_p + tv * w + Vector((0, 0, z1 + 0.12))]
        for off in (0.0, 0.012):
            vs = [bm.verts.new(p + to * off) for p in pts]
            bm.faces.new(vs if off > 0 else list(reversed(vs)))
        paint(mesh_obj("Obelisk_Banner_" + side, bm, col, root), "team", team=True, lo=0.1, hi=0.7)
    kk = [
        ("dungeon/candle_triple", (FRONT.x + 0.75, FRONT.y - 0.75, TOP), 30, 0.36),
        ("dungeon/candle_triple", (FRONT.x - 0.8, FRONT.y - 0.7, TOP), 80, 0.32),
    ]
    for i, (rel, loc, rot, sc) in enumerate(kk):
        for o in kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d_%s" % (i, rel.split("/")[1])):
            pass
    empty("Head", col, root, (F.x, F.y, SHRINE), 0.5, "SINGLE_ARROW")
    return root


def _obelisk(bm, c, z0, r0, r1, h):
    """A square tapering shaft with a pyramid tip."""
    a = [bm.verts.new((c.x + sx * r0, c.y + sy * r0, z0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    b = [bm.verts.new((c.x + sx * r1, c.y + sy * r1, z0 + h)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    bm.faces.new(list(reversed(a)))
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((a[i], a[j], b[j], b[i]))
    tip = bm.verts.new((c.x, c.y, z0 + h + r1 * 1.6))
    for i in range(4):
        bm.faces.new((b[i], b[(i + 1) % 4], tip))


def build_head():
    col = collection("Seraph")
    return make_angel(CHAR, col, bpy.data.objects["Head"], HEIGHT, HOVER, span=1.05, halo_r=0.17, weapon=(0.45, 1.15),
                      blade=(0.17, 0.42), gold=GOLD)


def build_anims():
    # the throw's wind-up is trimmed, so the spear leaves on the first frames (the game fires as the clip starts)
    angel_anims(bpy.data.objects["Rig"], "Jump_Idle", "Throw", fire_start=0.32, fire_speed=0.68, hide=(3, 14, 22))


PREVIEW = {"target": (0, 0, 1.4), "dist": 9.0, "yaw": 160, "pitch": 18, "anim_target": (0, FRONT.y, 1.8), "anim_dist": 5.0,
           "frames": [("idle", 0), ("idle", 30), ("fire", 2), ("fire", 8), ("fire", 20)]}


def build_all():
    build_base()
    build_head()
    build_anims()
