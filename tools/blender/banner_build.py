"""Builds the War Banner (footprint "single": one hex). A support aura: nothing aims, nothing fires.

    blender -b --factory-startup --python tools/blender/build_tower.py -- banner <preview dir>

A tall pole on a stepped stone block flies a big team-colored war flag with a gold crown emblem, rigged as a chain so it
ripples. Around it: a weapon rack, a war drum, a brazier and a knight on guard (the game's Crew, with a halberd).
idle: the flag ripples and flutters (it's the only clip; the tower never attacks).
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "banner"
CELLS = [(0, 0)]
MID = footprint_mid(CELLS)
TOP = 0.34
POLE_X, POLE_Y = -0.18, 0.12
POLE_TOP = 3.25
FLAG_TOP = 3.05
FLAG_H = 0.78
FLAG_LEN = 1.25
SEGS = 4


def build_base():
    col = collection("Banner")
    root = empty("Banner", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    # stepped stone block, pole, crossbar and finial
    bm = bmesh.new()
    bm_box(bm, (0.62, 0.62, 0.16), (POLE_X, POLE_Y, TOP + 0.08), (0, 0, 15))
    bm_box(bm, (0.42, 0.42, 0.16), (POLE_X, POLE_Y, TOP + 0.24), (0, 0, 15))
    o = paint(mesh_obj("Banner_Block", bm, col, root), "stone", lo=0.1, hi=0.6)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    bm_cyl(bm, 0.06, 0.05, POLE_TOP - TOP - 0.3, (POLE_X, POLE_Y, (TOP + 0.3 + POLE_TOP) / 2), seg=8)
    paint(mesh_obj("Banner_Pole", bm, col, root), "wood_dark", lo=0.2, hi=0.7)
    bm = bmesh.new()
    bm_cyl(bm, 0.09, 0.09, 0.08, (POLE_X, POLE_Y, POLE_TOP), seg=8)
    bm_cyl(bm, 0.08, 0.0, 0.26, (POLE_X, POLE_Y, POLE_TOP + 0.17), seg=6)
    for z in (TOP + 0.36, 1.7):
        bm_cyl(bm, 0.075, 0.075, 0.06, (POLE_X, POLE_Y, z), seg=8)
    paint(mesh_obj("Banner_Fittings", bm, col, root), "gold", lo=0.1, hi=0.5)

    # war drum: a squat barrel drum on three legs, with sticks
    D = Vector((0.55, -0.35, TOP))
    bm = bmesh.new()
    for k in range(3):
        a = math.radians(120 * k + 20)
        bm_beam(bm, D + Vector((math.cos(a) * 0.3, math.sin(a) * 0.3, 0)), D + Vector((math.cos(a) * 0.18, math.sin(a) * 0.18, 0.32)),
                0.05, 0.05)
    bm_cyl(bm, 0.28, 0.28, 0.3, tuple(D + Vector((0, 0, 0.47))), seg=12)
    paint(mesh_obj("Drum_Body", bm, col, root), "wood_red", lo=0.3, hi=0.7)
    bm = bmesh.new()
    bm_cyl(bm, 0.25, 0.25, 0.02, tuple(D + Vector((0, 0, 0.63))), seg=12)
    paint(mesh_obj("Drum_Skin", bm, col, root), "cream", lo=0.1, hi=0.3)
    bm = bmesh.new()
    for z in (0.34, 0.6):
        ring(bm, tuple(D + Vector((0, 0, 0))), 0.295, 0.27, z - 0.015, z + 0.015, seg=12)
    bm_beam(bm, D + Vector((0.12, 0.05, 0.66)), D + Vector((0.28, 0.32, 0.8)), 0.035, 0.035)
    bm_beam(bm, D + Vector((-0.05, 0.12, 0.66)), D + Vector((-0.02, 0.42, 0.74)), 0.035, 0.035)
    paint(mesh_obj("Drum_Bands", bm, col, root), "team", team=True, lo=0.2, hi=0.5)
    # brazier
    Z = Vector((-0.62, -0.42, TOP))
    bm = bmesh.new()
    bm_cyl(bm, 0.07, 0.1, 0.42, tuple(Z + Vector((0, 0, 0.21))), seg=6)
    bm_cyl(bm, 0.24, 0.14, 0.14, tuple(Z + Vector((0, 0, 0.48))), seg=8)
    paint(mesh_obj("Brazier", bm, col, root), "iron", lo=0.1, hi=0.5)
    import random
    rnd = random.Random(2)
    bm = bmesh.new()
    fc = Z + Vector((0, 0, 0.54))
    for k in range(5):
        a = math.radians(72 * k + rnd.uniform(-12, 12))
        d = 0.0 if k == 0 else 0.09
        c = fc + Vector((math.cos(a) * d, math.sin(a) * d, 0))
        h = 0.36 if k == 0 else rnd.uniform(0.18, 0.28)
        top = bm.verts.new(c + Vector((0, 0, h)))
        ms = [bm.verts.new(c + Vector((math.cos(math.radians(90 * j + 45)) * 0.07, math.sin(math.radians(90 * j + 45)) * 0.07, 0)))
              for j in range(4)]
        for j in range(4):
            bm.faces.new((ms[j], ms[(j + 1) % 4], top))
    o = mesh_obj("Brazier_Flame", bm, col, root)
    o.data.materials.append(glow_mat("brazier_fire", (1.0, 0.55, 0.15), 1.6))
    kk = [
        ("hex/weaponrack", (0.62, 0.42, TOP), 230, 2.4),
        ("hex/shield_{t}".replace("{t}", "blue_full"), (-0.72, 0.3, TOP + 0.12), 100, 2.6),
        ("hex/crate_A_small", (0.18, -0.72, TOP), 25, 2.4),
    ]
    for i, (rel, loc, rot, sc) in enumerate(kk):
        for o in kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d_%s" % (i, rel.split("/")[1])):
            for c in [o] + list(o.children_recursive):
                if c.type == "MESH":
                    teamify(c)
    crew = empty("Crew", col, root, (0.12, 0.62, TOP), 0.3, "SINGLE_ARROW")   # on guard at the front, facing out
    empty("Head", col, root, (0, 0, 0), 0.5, "SINGLE_ARROW")
    return root


def _flag_bones():
    bones = {"root": ((0, 0, 0), (0, 0, 0.3), None),
             "pole": ((POLE_X, POLE_Y, FLAG_TOP - FLAG_H), (POLE_X, POLE_Y, FLAG_TOP), "root")}
    prev = "pole"
    step = FLAG_LEN / SEGS
    for k in range(SEGS):
        name = "flag.%d" % (k + 1)
        x0 = POLE_X + 0.05 + step * k
        bones[name] = ((x0, POLE_Y, FLAG_TOP), (x0 + step, POLE_Y, FLAG_TOP - 0.02 * (k + 1)), prev)
        prev = name
    return bones


BONES = None


def build_head():
    global BONES
    BONES = _flag_bones()
    col = collection("Banner")
    head = bpy.data.objects["Head"]
    for o in [o for o in col.objects if o.name.startswith("Head_")]:
        bpy.data.objects.remove(o, do_unlink=True)
    rig = make_rig(col, head, BONES)
    step = FLAG_LEN / SEGS
    for k in range(SEGS):
        x0 = POLE_X + 0.05 + step * k
        x1 = x0 + step
        h0 = FLAG_H
        h1 = FLAG_H
        bm = bmesh.new()
        z_top0 = FLAG_TOP - 0.02 * k
        z_top1 = FLAG_TOP - 0.02 * (k + 1)
        last = k == SEGS - 1
        pts = [Vector((x0, POLE_Y, z_top0)), Vector((x1, POLE_Y, z_top1))]
        if last:   # swallowtail
            pts += [Vector((x1, POLE_Y, z_top1 - h1)), Vector((x1 - step * 0.6, POLE_Y, z_top1 - h1 * 0.5)), Vector((x1, POLE_Y, z_top1 - h1 * 0.0 - h1)),
                    Vector((x0, POLE_Y, z_top0 - h0))]
            pts = [pts[0], pts[1], Vector((x1, POLE_Y, z_top1 - h1 * 0.02)), Vector((x1 - step * 0.55, POLE_Y, z_top1 - h1 * 0.5)),
                   Vector((x1, POLE_Y, z_top1 - h1)), Vector((x0, POLE_Y, z_top0 - h0))]
            pts = [pts[0], pts[1], pts[3], pts[4], pts[5]]
        else:
            pts += [Vector((x1, POLE_Y, z_top1 - h1)), Vector((x0, POLE_Y, z_top0 - h0))]
        for side in (1, -1):
            vs = [bm.verts.new(p + Vector((0, side * 0.006, 0))) for p in pts]
            bm.faces.new(vs if side < 0 else list(reversed(vs)))
        rig_part("Head_Flag.%d" % (k + 1), bm, "team", rig, "flag.%d" % (k + 1), col, team=True, bevel=0, lo=0.15, hi=0.7)
    # the emblem: a gold crown on both faces, on the second segment
    bm = bmesh.new()
    cx = POLE_X + 0.05 + step * 1.45
    cz = FLAG_TOP - FLAG_H * 0.5
    crown = [(-0.2, -0.13), (0.2, -0.13), (0.22, 0.12), (0.11, 0.0), (0.0, 0.16), (-0.11, 0.0), (-0.22, 0.12)]
    for side in (1, -1):
        vs = [bm.verts.new((cx + x, POLE_Y + side * 0.012, cz + z)) for x, z in crown]
        bm.faces.new(vs if side < 0 else list(reversed(vs)))
    rig_part("Head_Emblem", bm, "gold", rig, "flag.2", col, bevel=0, lo=0.1, hi=0.45)
    empty("Muzzle", col, head, (POLE_X, POLE_Y, POLE_TOP + 0.2), 0.25, "SPHERE")
    return rig


IDLE_LEN = 72


def build_anims():
    rig = bpy.data.objects["Rig"]
    pb = rig.pose.bones
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        rest_pose(rig)
        for k in range(SEGS):
            ph = 2 * math.pi * (t * 2 - k * 0.18)
            yaw = (6 + 5 * k) * math.sin(ph)
            name = "flag.%d" % (k + 1)
            # yaw about each segment's leading edge only: the edges stay joined (a droop would open gaps)
            pb[name].rotation_quaternion = arm_space_quat(pb[name], (0, 0, 1), yaw)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 1.4), "dist": 7.5, "yaw": 150, "pitch": 22, "anim_target": (0.2, 0.1, 2.6), "anim_dist": 4.5,
           "frames": [("idle", 0), ("idle", 18), ("idle", 36)]}


def build_all():
    build_base()
    build_head()
    build_anims()
