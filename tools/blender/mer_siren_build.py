"""Builds the Siren Rock (footprint "pair": [0,0] front, [0,1] back), a Tide tower: her song arcs between enemies and
can leave them spellbound.

    blender -b --factory-startup --python tools/blender/build_tower.py -- mer_siren <preview dir>

Front cell: a craggy sea rock rising from a pool, where a siren sits (the pack's Witch turned mermaid: coral-red hair,
pale sea skin, a blue tail draped over the rock's edge, team-coloured fins) with a glowing pearl in her hand (the Head:
she turns toward her prey; the song leaves from the pearl). Back cell: the wreck her song drew in: a broken hull, a
snapped mast with a torn team-coloured sail, kegs, coral and kelp. idle: she sits and sways, her tail swishing.
fire: she sings out (her arms cast while she stays seated) and the pearl flares.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "angel_common.py"), encoding="utf-8").read())
exec(open(os.path.join(REPO, "tools", "blender", "tide_common.py"), encoding="utf-8").read())

TID = "mer_siren"
CELLS = [(0, 0), (0, 1)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)
B = hex_to_world(0, 1, MID)
TOP = 0.34
WATER = TOP + 0.06
ROCK_TOP = TOP + 0.72
SEAT = Vector((F.x, F.y - 0.12, ROCK_TOP))
PEARL = (0.7, 0.95, 1.0)
CHAR = "Witch.glb"
HEIGHT = 1.45


def build_base():
    col = collection("Mer_siren")
    root = empty("Mer_siren", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    rnd = random.Random(52)
    # the pool round the rock, and the rock: craggy boulders heaped to a flat seat
    bm = bmesh.new()
    bm_cyl(bm, 0.98, 0.98, 0.04, (F.x, F.y, WATER - 0.02), seg=12)
    paint_water(mesh_obj("Pool", bm, col, root))
    bm = bmesh.new()
    for k in range(9):
        a = math.radians(40 * k + rnd.uniform(-10, 10))
        r = rnd.uniform(0.25, 0.4)
        c = F + Vector((math.cos(a) * 0.5, math.sin(a) * 0.45, 0))
        bm_ellipsoid(bm, (c.x, c.y, T + r * 0.6), (r * 1.1, r, r * 0.9), rot=(rnd.uniform(-20, 20), rnd.uniform(-20, 20), rnd.uniform(0, 90)), u=6, v=4)
    bm_ellipsoid(bm, (F.x, F.y - 0.1, T + 0.42), (0.5, 0.48, 0.32), rot=(0, 0, 20), u=7, v=5)
    bm_ellipsoid(bm, (SEAT.x, SEAT.y - 0.05, ROCK_TOP - 0.12), (0.36, 0.34, 0.14), rot=(0, 0, 50), u=7, v=4)
    o = paint(mesh_obj("Rock", bm, col, root), "stone2", lo=0.1, hi=0.7)
    bm = bmesh.new()
    for k in range(5):                                       # barnacles and a seaweed fringe at the waterline
        a = math.radians(70 * k + 20)
        p = F + Vector((math.cos(a) * 0.62, math.sin(a) * 0.55, 0))
        bm_cyl(bm, 0.06, 0.03, 0.06, (p.x, p.y, WATER + 0.06), seg=6)
    paint(mesh_obj("Barnacles", bm, col, root), "cream", lo=0.3, hi=0.7)
    coral = bmesh.new()
    bm_coral(coral, rnd, (F.x + 0.72, F.y - 0.35, WATER), h=0.5, n=4)
    bm_coral(coral, rnd, (F.x - 0.75, F.y + 0.25, WATER), h=0.4, n=3)
    paint(mesh_obj("Coral_A", coral, col, root), "salmon", lo=0.1, hi=0.7)
    # the wreck: a broken hull (ribs and planks), a snapped mast with a torn sail
    W = B + Vector((0.05, -0.05, 0))
    hull, ribs = bmesh.new(), bmesh.new()
    for k in range(5):
        y = W.y + 0.55 - k * 0.28
        for sx in (-1, 1):
            p0 = Vector((W.x + sx * 0.18, y, T + 0.02))
            p1 = Vector((W.x + sx * 0.62, y, T + 0.32))
            p2 = Vector((W.x + sx * (0.7 - 0.05 * k), y, T + 0.75 - 0.08 * k))
            bm_beam(ribs, p0, p1, 0.07, 0.07)
            bm_beam(ribs, p1, p2, 0.06, 0.06)
    for sx in (-1, 1):
        for z, xo in ((0.12, 0.38), (0.3, 0.6), (0.48, 0.66)):
            bm_beam(hull, (W.x + sx * xo, W.y + 0.62, T + z), (W.x + sx * (xo + 0.02), W.y - 0.45 + 0.1 * z, T + z * 0.9), 0.05, 0.12, up=(sx, 0, 1))
    bm_box(hull, (0.5, 1.3, 0.08), (W.x, W.y + 0.05, T + 0.05))
    paint(mesh_obj("Wreck_Hull", hull, col, root), "wood_dark", lo=0.2, hi=0.7)
    paint(mesh_obj("Wreck_Ribs", ribs, col, root), "wood", lo=0.3, hi=0.8)
    bm = bmesh.new()
    mb = Vector((W.x + 0.05, W.y + 0.1, T + 0.05))
    mt = mb + Vector((0.25, -0.2, 1.5))
    bm_beam(bm, mb, mt, 0.12, 0.12, w1=0.09, h1=0.09)
    bm_beam(bm, mt - Vector((0.5, 0.0, 0.25)), mt + Vector((0.5, 0.0, -0.18)), 0.07, 0.07)
    paint(mesh_obj("Wreck_Mast", bm, col, root), "wood_dark", lo=0.3, hi=0.8)
    bm = bmesh.new()
    yard = [mt + Vector((-0.45, 0.0, -0.24)), mt + Vector((0.45, 0.0, -0.18))]
    pts = [yard[0], yard[1], yard[1] + Vector((0.05, -0.12, -0.55)), yard[0] + Vector((0.35, -0.1, -0.75)),
           yard[0] + Vector((0.1, -0.1, -0.42))]
    for off in (-0.008, 0.008):
        vs = [bm.verts.new(p + Vector((0, off, 0))) for p in pts]
        bm.faces.new(vs if off > 0 else list(reversed(vs)))
    paint(mesh_obj("Wreck_Sail", bm, col, root), "team", team=True, lo=0.2, hi=0.6)
    bm = bmesh.new()
    bm_kelp(bm, rnd, (W.x - 0.55, W.y - 0.55, T), h=0.8, n=3)
    bm_kelp(bm, rnd, (W.x + 0.6, W.y + 0.4, T), h=0.6, n=2)
    paint(mesh_obj("Kelp", bm, col, root), "teal", lo=0.1, hi=0.8)
    coral = bmesh.new()
    bm_coral(coral, rnd, (W.x + 0.62, W.y - 0.5, T), h=0.55, n=4)
    paint(mesh_obj("Coral_B", coral, col, root), "orange", lo=0.1, hi=0.7)
    kk_import("dungeon/barrel_small_stack", col, root, (W.x - 0.6, W.y + 0.45, T), 30, 0.35, name="Prop_KK_0")
    empty("Head", col, root, tuple(SEAT), 0.5, "SINGLE_ARROW")
    return root


def build_head():
    col = collection("Mer_siren")
    head = bpy.data.objects["Head"]
    # seated: the tail leaves the hips forward and drops over the rock's front edge
    arm = make_merfolk(CHAR, col, head, HEIGHT, hover=0.0, drop=("Hat", "Glasses"), skin=(0.66, 0.86, 0.88),
                       tail=[(0, 0.02, -0.03), (0.02, 0.2, -0.1), (0.08, 0.34, -0.3), (0.16, 0.36, -0.52)],
                       tail_r=(0.13, 0.04), tail_sw="blue", fin_sw="team", tex_name="siren_skin")
    hand = bone_world(arm, "handslot.r")
    add_bones(arm, {"pearl": (to_arm(arm, hand + Vector((0, 0.04, 0))), to_arm(arm, hand + Vector((0, 0.04, 0.2))), "handslot.r")})
    bpy.context.view_layer.update()
    bm = bmesh.new()
    bm_ellipsoid(bm, tuple(hand + Vector((0, 0.04, 0.0))), (0.075, 0.075, 0.075), u=9, v=6)
    mer_part("Mer_Pearl", bm, None, arm, "pearl", col, mat=glow_mat("siren_pearl", PEARL, 0.9))
    m = head.matrix_world.inverted() @ (bone_world(arm, "chest") + Vector((0.0, 0.35, 0.2)))
    empty("Muzzle", col, head, tuple(m), 0.25, "SPHERE")
    return arm


def build_anims():
    def extra(name, f, pb):
        if name == "fire":
            s = 1.0 + 1.2 * smooth(f / 2.0) * (1 - smooth((f - 6) / 10.0))
            pb["pearl"].scale = (s, s, s)
        else:
            s = 1.0 + 0.1 * math.sin(2 * math.pi * f / 48 * 2)
            pb["pearl"].scale = (s, s, s)

    merfolk_anims(bpy.data.objects["Rig"], "Sit_Floor_Idle", "Ranged_Magic_Shoot", idle_len=96, fire_len=22,
                  upper_only=True, sway=7.0, extra=extra)


PREVIEW = {"target": (0, 0, 0.9), "dist": 7.5, "yaw": 160, "pitch": 18, "anim_target": (F.x, F.y, 1.4), "anim_dist": 3.8,
           "frames": [("idle", 0), ("idle", 48), ("fire", 3), ("fire", 8), ("fire", 16)]}


def build_all():
    build_base()
    build_head()
    build_anims()
