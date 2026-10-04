"""Builds the Sunlance Lighthouse (footprint "pair": [0,0] front, [0,1] back), the Crown's Tier IV beam tower: a lance of
sunlight that burns through everything on a straight line.

    blender -b --factory-startup --python tools/blender/build_tower.py -- sunlance <preview dir>

Front cell: a tall white lighthouse on a rocky foot, banded in the team color, with arched windows, a railed gallery and
an open lantern room of gold pillars under a gold dome and spire. Inside the lantern a gold lens barrel turns on the
light (the Head: it turns to its target; the beam leaves the lens) round a blazing sun crystal, ringed by sun rays.
Back cell: the keeper's stone cottage with a slate roof, a team pennant and a stack of firewood. idle: the crystal
breathes, the rays turn. fire: the crystal flares, the lens kicks back, the rays flash outward.
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "sunlance"
CELLS = [(0, 0), (0, 1)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)
B = hex_to_world(0, 1, MID)
TOP = 0.34
T = TOP
SHAFT = 2.3                  # height of the white tower above the plinth
LAMP = T + SHAFT + 0.36      # the lantern's middle (the Head)
SUN = (1.0, 0.86, 0.4)


def build_base():
    col = collection("Sunlance")
    root = empty("Sunlance", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(4)
    bm = bmesh.new()                                             # the rocky foot
    for k in range(9):
        a = 2 * math.pi * k / 9 + rnd.uniform(-0.2, 0.2)
        bm_rock(bm, rnd, Vector((F.x + 0.72 * math.cos(a), F.y + 0.72 * math.sin(a), 0)), rnd.uniform(0.3, 0.45), T, rnd.uniform(0.18, 0.34))
    paint(mesh_obj("Light_Rocks", bm, col, root), "stone2", lo=0.15, hi=0.75)
    bm = bmesh.new()
    bm_cyl(bm, 0.78, 0.8, 0.22, (F.x, F.y, T + 0.11), seg=16)
    o = paint(mesh_obj("Light_Footing", bm, col, root), "stone", lo=0.15, hi=0.6)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    bm_cyl(bm, 0.62, 0.42, SHAFT - 0.22, (F.x, F.y, T + 0.22 + (SHAFT - 0.22) / 2), seg=16)
    paint(mesh_obj("Light_Shaft", bm, col, root), "white", lo=0.1, hi=0.7)
    bm = bmesh.new()                                             # two team bands round the shaft
    for z, r in ((T + 0.85, 0.565), (T + 1.65, 0.5)):
        ring(bm, (F.x, F.y, 0), r + 0.03, r - 0.04, z, z + 0.16, seg=16)
    paint(mesh_obj("Light_Bands", bm, col, root), "team", team=True, lo=0.1, hi=0.6)
    bm = bmesh.new()                                             # arched windows, spiralling up
    for k, z in enumerate((T + 0.55, T + 1.25, T + 1.95)):
        a = math.radians(-90 + 120 * k)
        r = 0.62 - 0.2 * (z - T) / SHAFT
        p = Vector((F.x + r * math.cos(a), F.y + r * math.sin(a), z))
        bm_box(bm, (0.1, 0.18, 0.28), tuple(p), rot=(0, 0, math.degrees(a)))
        bm_cyl(bm, 0.09, 0.09, 0.1, tuple(p + Vector((0, 0, 0.14))), rot=(0, 90, math.degrees(a)), seg=8)
    paint(mesh_obj("Light_Windows", bm, col, root), "black", lo=0.3, hi=0.6)
    # the gallery: a flared ledge with a railing
    G = T + SHAFT
    bm = bmesh.new()
    bm_cyl(bm, 0.42, 0.68, 0.14, (F.x, F.y, G - 0.07), seg=16)
    bm_cyl(bm, 0.68, 0.68, 0.06, (F.x, F.y, G + 0.03), seg=16)
    paint(mesh_obj("Light_Gallery", bm, col, root), "stone", lo=0.2, hi=0.6)
    bm = bmesh.new()
    ring(bm, (F.x, F.y, 0), 0.68, 0.64, G + 0.22, G + 0.26, seg=20)
    for k in range(10):
        a = 2 * math.pi * k / 10
        bm_cyl(bm, 0.02, 0.02, 0.2, (F.x + 0.66 * math.cos(a), F.y + 0.66 * math.sin(a), G + 0.16), seg=5)
    paint(mesh_obj("Light_Rail", bm, col, root), "iron", lo=0.2, hi=0.5)
    # the lantern room: six gold pillars, a gold dome and a spire
    bm = bmesh.new()
    for k in range(6):
        a = 2 * math.pi * (k + 0.5) / 6
        bm_box(bm, (0.07, 0.07, 0.62), (F.x + 0.44 * math.cos(a), F.y + 0.44 * math.sin(a), G + 0.37), rot=(0, 0, math.degrees(a)))
    ring(bm, (F.x, F.y, 0), 0.5, 0.38, G + 0.06, G + 0.1, seg=12)
    ring(bm, (F.x, F.y, 0), 0.52, 0.38, G + 0.66, G + 0.72, seg=12)
    bm_ellipsoid(bm, (F.x, F.y, G + 0.72), (0.5, 0.5, 0.27), u=12, v=6)
    bm_cyl(bm, 0.06, 0.0, 0.42, (F.x, F.y, G + 1.12), seg=6)
    o = paint(mesh_obj("Light_Lantern", bm, col, root), "gold", lo=0.15, hi=0.6)
    bm = bmesh.new()
    bm_ellipsoid(bm, (F.x, F.y, G + 1.36), (0.07, 0.07, 0.07), u=8, v=5)
    glow_obj("Light_SpireGem", bm, col, root, SUN, 1.4)
    # the keeper's cottage on the back cell
    bm = bmesh.new()
    bm_box(bm, (1.05, 0.95, 0.62), (B.x, B.y - 0.05, T + 0.31))
    bm_box(bm, (0.42, 0.5, 0.55), (B.x - 0.1, B.y + 0.62, T + 0.275))       # the passage to the lighthouse
    o = paint(mesh_obj("Cottage_Walls", bm, col, root), "stone_warm", lo=0.15, hi=0.7)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    R0, Z0 = 0.62, T + 0.6
    pts = [(-R0, 0.0), (R0, 0.0), (0.0, 0.48)]
    vs0 = [bm.verts.new((B.x + x, B.y - 0.6, Z0 + z)) for x, z in pts]
    vs1 = [bm.verts.new((B.x + x, B.y + 0.5, Z0 + z)) for x, z in pts]
    bm.faces.new(vs0)
    bm.faces.new(list(reversed(vs1)))
    for i in range(3):
        j = (i + 1) % 3
        bm.faces.new((vs0[j], vs0[i], vs1[i], vs1[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    bm_box(bm, (0.48, 0.58, 0.08), (B.x - 0.1, B.y + 0.62, T + 0.58), rot=(0, 0, 0))
    paint(mesh_obj("Cottage_Roof", bm, col, root), "roof", lo=0.15, hi=0.7)
    bm = bmesh.new()
    bm_box(bm, (0.16, 0.16, 0.4), (B.x + 0.32, B.y - 0.25, T + 1.05))
    paint(mesh_obj("Cottage_Chimney", bm, col, root), "stone2", lo=0.2, hi=0.7)
    bm = bmesh.new()
    bm_box(bm, (0.24, 0.04, 0.36), (B.x - 0.15, B.y - 0.53, T + 0.18))
    bm_box(bm, (0.16, 0.04, 0.16), (B.x + 0.28, B.y - 0.53, T + 0.36))
    paint(mesh_obj("Cottage_Door", bm, col, root), "wood_dark", lo=0.2, hi=0.7)
    bm = bmesh.new()                                             # a pennant on a pole by the door
    bm_cyl(bm, 0.025, 0.025, 1.3, (B.x - 0.65, B.y - 0.55, T + 0.65), seg=6)
    paint(mesh_obj("Cottage_Pole", bm, col, root), "wood", lo=0.2, hi=0.7)
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in ((B.x - 0.65, B.y - 0.55, T + 1.28), (B.x - 0.65, B.y - 0.55, T + 1.0), (B.x - 0.2, B.y - 0.55, T + 1.14))]
    bm.faces.new(v)
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.02)
    paint(mesh_obj("Cottage_Pennant", bm, col, root), "team", team=True, lo=0.2, hi=0.6)
    kk_import("resources/Wood_Log_Stack", col, root, (B.x + 0.66, B.y + 0.2, T), 90, 0.45, name="Prop_KK_0")
    head = empty("Head", col, root, (F.x, F.y, LAMP), 0.5, "SINGLE_ARROW")
    empty("Muzzle", col, head, (0, 0.5, 0.0), 0.2, "SPHERE")
    return root


BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "lens": ((0, -0.05, 0), (0, 0.25, 0), "root"),
         "core": ((0, 0, -0.1), (0, 0, 0.15), "root"),
         "rays": ((0, 0, -0.05), (0, 0, 0.1), "root"),
         "flash": ((0, 0.46, 0), (0, 0.66, 0), "lens")}


def build_head():
    col = collection("Sunlance")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    # the lens barrel: a short gold tube on a yoke, a glowing lens at its mouth
    bm = bmesh.new()
    bm_cyl(bm, 0.1, 0.15, 0.3, (0, 0.28, 0), rot=(-90, 0, 0), seg=12)
    bm_box(bm, (0.5, 0.06, 0.06), (0, -0.02, -0.2))
    for sx in (-1, 1):
        bm_box(bm, (0.05, 0.06, 0.24), (sx * 0.23, -0.02, -0.09))
    rig_part("Head_Lens", bm, "gold", rig, "lens", col, bevel=0, lo=0.15, hi=0.6)
    bm = bmesh.new()
    bm_cyl(bm, 0.13, 0.13, 0.03, (0, 0.435, 0), rot=(-90, 0, 0), seg=14)
    rig_part("Head_LensGlass", bm, None, rig, "lens", col, bevel=0, mat=glow_mat("sun_lens", (1.0, 0.95, 0.7), 2.2))
    bm = bmesh.new()
    bm_ellipsoid(bm, (0, -0.04, 0.02), (0.15, 0.15, 0.2), u=4, v=2)
    rig_part("Head_Core", bm, None, rig, "core", col, bevel=0, mat=glow_mat("sun_core", SUN, 2.6))
    bm = bmesh.new()                                             # sun rays: thin shards in a halo round the core
    for k in range(8):
        a = 2 * math.pi * k / 8
        d = Vector((math.cos(a), 0, math.sin(a)))
        bm_beam(bm, Vector((0, -0.05, 0.02)) + d * 0.2, Vector((0, -0.05, 0.02)) + d * (0.34 if k % 2 else 0.27), 0.05, 0.02, 0.006, 0.006,
                up=(0, 1, 0))
    rig_part("Head_Rays", bm, None, rig, "rays", col, bevel=0, mat=glow_mat("sun_rays", SUN, 1.6))
    bm = bmesh.new()                                             # the flash at the lens when it fires (hidden at rest)
    bm_ellipsoid(bm, (0, 0.5, 0), (0.22, 0.12, 0.22), u=10, v=6)
    rig_part("Head_Flash", bm, None, rig, "flash", col, bevel=0, mat=glow_mat("sun_flash", (1.0, 0.97, 0.8), 3.0))
    return rig


IDLE_LEN = 72
FIRE_LEN = 20


def pose(rig, t=0.0, flare=1.0, kick=0.0, spin=0.0, burst=1.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["core"].scale = (flare, flare, flare)
    pb["rays"].rotation_quaternion = arm_space_quat(pb["rays"], (0, 1, 0), 360 * t + spin)
    pb["rays"].scale = (burst, burst, burst)
    pb["lens"].location = arm_space_loc(pb["lens"], (0, -0.08 * kick, 0))
    f = max(0.001, 1.6 * kick)
    pb["flash"].scale = (f, f, f)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        pose(rig, t=t * 0.5, flare=1.0 + 0.1 * math.sin(2 * math.pi * t * 2))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        k = smooth(f / 2.0) * (1 - smooth((f - 4) / 14.0))
        pose(rig, t=0.0, flare=1.0 + 0.9 * k, kick=k, spin=120 * smooth(f / FIRE_LEN), burst=1.0 + 0.7 * k)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 1.5), "dist": 9.0, "yaw": 150, "pitch": 18, "anim_target": (F.x, F.y, LAMP), "anim_dist": 3.0,
           "frames": [("idle", 0), ("fire", 3), ("fire", 10)]}


def build_all():
    build_base()
    build_head()
    build_anims()
