"""Builds the Tide Spire (footprint "single"), a Tide tower: pulses of tidewater slow everything nearby, and it senses
camouflaged enemies.

    blender -b --factory-startup --python tools/blender/build_tower.py -- mer_tide <preview dir>

A tall spiral conch spire, knobbed and pale, rises from a rock-rimmed tidepool with coral and kelp round it; at its tip an
open scallop cradles a glowing pearl (the eye that sees hidden things). It's an aura (it doesn't turn). idle: the pearl
bobs and turns, a ripple rings out across the pool. fire (every pulse): the pearl flares and a ring of tidewater
surges out from the pool, past the hex's edge.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "tide_common.py"), encoding="utf-8").read())

TID = "mer_tide"
CELLS = [(0, 0)]
TOP = 0.34
WATER = TOP + 0.08
PEARL = (0.7, 0.95, 1.0)
TIDE = (0.55, 0.85, 1.0)
SPIRE = 2.05


def build_base():
    col = collection("Mer_tide")
    root = empty("Mer_tide", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    rnd = random.Random(61)
    bm = bmesh.new()
    bm_cyl(bm, 0.92, 0.92, 0.04, (0, 0, WATER - 0.02), seg=12)
    paint_water(mesh_obj("Pool", bm, col, root))
    bm = bmesh.new()
    for k in range(13):                                 # the pool's rim of rounded rocks
        a = math.radians(360 * k / 13 + rnd.uniform(-6, 6))
        r = rnd.uniform(0.13, 0.2)
        bm_ellipsoid(bm, (math.cos(a) * 0.9, math.sin(a) * 0.9, T + r * 0.45), (r * 1.25, r, r * 0.8),
                     rot=(0, 0, math.degrees(a) + rnd.uniform(-20, 20)), u=6, v=4)
    paint(mesh_obj("Rim", bm, col, root), "stone2", lo=0.1, hi=0.7)
    # the spire: whorls of a conch shrinking as they climb a slow spiral, knobs round each one
    shell, knobs = bmesh.new(), bmesh.new()
    n = 8
    z = WATER - 0.05
    for k in range(n):
        t = k / (n - 1)
        r = 0.42 - 0.34 * t
        h = r * 0.95
        a = k * 1.1
        c = Vector((math.cos(a) * 0.12 * (1 - t), math.sin(a) * 0.12 * (1 - t), z + h * 0.5))
        bm_ellipsoid(shell, tuple(c), (r, r * 0.9, h * 0.6), rot=(14, 0, math.degrees(a)), u=10, v=6)   # tilted whorls: a spiral
        for j in range(3 if k < 6 else 0):
            b = a + math.radians(120 * j + 30)
            p = c + Vector((math.cos(b) * r * 0.95, math.sin(b) * r * 0.95, h * 0.05))
            d = Vector((math.cos(b), math.sin(b), 0.45)).normalized()
            bm_beam(knobs, p - d * 0.02, p + d * r * 0.4, r * 0.24, r * 0.24, w1=0.0, h1=0.0)
        z += h * 0.78
    tip = Vector((0, 0, z))
    bm_cyl(shell, 0.07, 0.0, 0.22, (0, 0, z + 0.06), seg=8)
    paint(mesh_obj("Spire", shell, col, root), "cream", lo=0.1, hi=0.8)
    paint(mesh_obj("Spire_Knobs", knobs, col, root), "salmon", lo=0.2, hi=0.7)
    # coral and kelp in the pool
    coral, coral2 = bmesh.new(), bmesh.new()
    bm_coral(coral, rnd, (0.55, -0.3, WATER), h=0.55, n=4)
    bm_coral(coral2, rnd, (-0.5, 0.42, WATER), h=0.45, n=3)
    bm_coral(coral, rnd, (-0.35, -0.55, WATER), h=0.35, n=3)
    paint(mesh_obj("Coral_A", coral, col, root), "salmon", lo=0.1, hi=0.7)
    paint(mesh_obj("Coral_B", coral2, col, root), "orange", lo=0.1, hi=0.7)
    bm = bmesh.new()
    bm_kelp(bm, rnd, (0.45, 0.5, WATER), h=0.75, n=3)
    paint(mesh_obj("Kelp", bm, col, root), "teal", lo=0.1, hi=0.8)
    empty("Head", col, root, (0, 0, TOP), 0.5, "SINGLE_ARROW")
    return tip


BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "pearl": ((0, 0, 0), (0, 0, 0.2), "root"),
         "ripple": ((0, 0, WATER - TOP), (0, 0, WATER - TOP + 0.2), "root"),
         "surge": ((0, 0, WATER - TOP), (0, 0, WATER - TOP + 0.2), "root")}


def build_head():
    col = collection("Mer_tide")
    head = bpy.data.objects["Head"]
    tip = Vector((0, 0, SPIRE))
    for o in bpy.data.objects:
        if o.name == "Spire":
            zs = [(o.matrix_world @ v.co).z for v in o.data.vertices]
            tip = Vector((0, 0, max(zs)))
    pz = tip.z - TOP + 0.12                     # the pearl rides just above the shell's tip
    BONES["pearl"] = ((0, 0, pz), (0, 0, pz + 0.2), "root")
    rig = make_rig(col, head, BONES)
    bm = bmesh.new()
    for sg in (-1, 1):                          # the scallop cradle: two small fans tipped open
        bm_ellipsoid(bm, (sg * 0.1, 0, pz - 0.06), (0.16, 0.13, 0.035), rot=(0, sg * -35, 0), u=9, v=4)
    rig_part("Head_Cradle", bm, "cream", rig, "pearl", col, bevel=0, lo=0.2, hi=0.6)
    bm = bmesh.new()
    bm_ellipsoid(bm, (0, 0, pz + 0.04), (0.13, 0.13, 0.13), u=10, v=7)
    rig_part("Head_Pearl", bm, None, rig, "pearl", col, bevel=0, mat=glow_mat("tide_pearl", PEARL, 0.9))
    bm = bmesh.new()
    ring(bm, (0, 0, 0), 0.62, 0.55, WATER - TOP + 0.01, WATER - TOP + 0.04, seg=24)
    rig_part("Head_Ripple", bm, None, rig, "ripple", col, bevel=0, mat=glow_mat("tide_ripple", TIDE, 0.45))
    bm = bmesh.new()
    ring(bm, (0, 0, 0), 1.0, 0.82, WATER - TOP, WATER - TOP + 0.14, seg=24)
    for k in range(12):                          # foam crests on the surge
        a = math.radians(30 * k)
        bm_ellipsoid(bm, (math.cos(a) * 0.92, math.sin(a) * 0.92, WATER - TOP + 0.13), (0.12, 0.12, 0.07), u=6, v=4)
    rig_part("Head_Surge", bm, None, rig, "surge", col, bevel=0, mat=glow_mat("tide_surge", TIDE, 0.6))
    empty("Muzzle", col, head, (0, 0, pz + 0.04), 0.25, "SPHERE")
    return rig


IDLE_LEN = 72
FIRE_LEN = 24


def pose(rig, bob=0.0, spin=0.0, flare=1.0, ripple=0.0, surge=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["pearl"].location = arm_space_loc(pb["pearl"], (0, 0, bob))
    pb["pearl"].rotation_quaternion = arm_space_quat(pb["pearl"], (0, 0, 1), spin)
    pb["pearl"].scale = (flare, flare, flare)
    # (these bones point up: their own Y is the height)
    r = 0.6 + 1.0 * ripple
    pb["ripple"].scale = (r, max(0.001, 1.0 - ripple), r) if ripple > 0 else (0.001, 0.001, 0.001)
    s = 0.5 + 1.8 * surge
    pb["surge"].scale = (s, max(0.001, 1.2 * (1 - surge) * min(1.0, surge * 6)), s) if surge > 0 else (0.001, 0.001, 0.001)
    if surge <= 0:
        pb["surge"].scale = (0.001, 0.001, 0.001)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        pose(rig, bob=0.06 * math.sin(2 * math.pi * t), spin=360 * t, flare=1.0 + 0.06 * math.sin(4 * math.pi * t),
             ripple=(t * 2) % 1.0 if f % IDLE_LEN else 0.0)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        t = f / FIRE_LEN
        flare = 1.0 + 0.8 * smooth(f / 2.0) * (1 - smooth((f - 4) / 10.0))
        pose(rig, bob=0.1 * smooth(f / 3.0) * (1 - t), spin=180 * t, flare=flare, surge=smooth(min(1.0, f / (FIRE_LEN * 0.9))))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 1.1), "dist": 6.5, "yaw": 160, "pitch": 18, "anim_target": (0, 0, 0.9), "anim_dist": 6.0,
           "frames": [("idle", 0), ("idle", 20), ("fire", 4), ("fire", 12), ("fire", 20)]}


def build_all():
    build_base()
    build_head()
    build_anims()
