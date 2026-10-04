"""Shared by the angel towers (Seraph, Archangel): a KayKit character (Rig_Medium) given wings, a halo and a weapon
of light, with the pack's animation clips baked together with wing beats into the tower's own "idle" and "fire".

Exec after kk_helpers.py. The character's armature becomes the tower's rig: it's renamed "Rig", parented to the Head,
turned to face +Y (the tower's front) and scaled to `height`. Extra bones: wing.L.1/2, wing.R.1/2 (on the chest),
halo (on the head) and weapon (on the right hand slot). Their meshes are rigid-skinned to them.
"""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix, Quaternion, Euler

ANIMS = os.path.join(KK, "anims")


def import_character(file, coll, head, height, hover=0.0):
    """Imports a KayKit character under `head` (the tower's Head), facing +Y, `height` tall, its feet `hover` up.
    Returns (armature, meshes)."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(KK, "chars", file))
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll.objects.link(o)
    arm = next(o for o in new if o.type == "ARMATURE")
    for o in new:   # the pack's files carry a stray cube and icosphere
        if o.type == "MESH" and (o.name.startswith("Cube") or o.name.startswith("Icosphere")):
            bpy.data.objects.remove(o, do_unlink=True)
    meshes = [o for o in coll.objects if o.type == "MESH" and o.parent == arm]
    bpy.context.view_layer.update()
    global IMPORT_MATRIX
    IMPORT_MATRIX = arm.matrix_world.copy()   # the armature where the file put it (slot_point maps into that space)
    top = root = arm
    while top.parent is not None:
        top = top.parent
    bpy.context.view_layer.update()
    zs = [(o.matrix_world @ Vector(c)).z for o in meshes for c in o.bound_box]
    h0 = max(zs) - min(zs)
    k = height / max(h0, 1e-6)
    top.parent = head
    top.matrix_parent_inverse = Matrix.Identity(4)
    top.location = (0, 0, hover)
    top.rotation_mode = "XYZ"
    top.rotation_euler = (top.rotation_euler.x, top.rotation_euler.y, math.radians(180))
    top.scale = (top.scale.x * k, top.scale.y * k, top.scale.z * k)
    arm.name = "Rig"
    arm.data.name = "Rig"
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"
    return arm, meshes


RIG_MEDIUM = ["Rig_Medium_General", "Rig_Medium_CombatMelee", "Rig_Medium_CombatRanged", "Rig_Medium_MovementBasic",
              "Rig_Medium_Simulation"]
RIG_LARGE = ["Rig_Large_General", "Rig_Large_CombatMelee", "Rig_Large_Simulation", "Rig_Large_Special"]


def load_clips(names, files=None):
    """Imports the pack's animation files (the medium rig's unless `files` says otherwise) and keeps the named clips
    (as actions); the files' own armatures go."""
    want = set(names)
    got = {}
    for f in files or RIG_MEDIUM:
        if want <= set(got):
            break
        before_o = set(bpy.data.objects)
        before_a = set(bpy.data.actions)
        bpy.ops.import_scene.gltf(filepath=os.path.join(ANIMS, f + ".glb"))
        for o in [o for o in bpy.data.objects if o not in before_o]:
            bpy.data.objects.remove(o, do_unlink=True)
        for a in [a for a in bpy.data.actions if a not in before_a]:
            base = a.name.split(".")[0]
            if a.name in want and a.name not in got:
                got[a.name] = a
            else:
                bpy.data.actions.remove(a)
    return got


def sample_clip(arm, act, n, loop=True, speed=1.0, start=0.0):
    """The clip's pose (every bone's loc / rot / scale) at n evenly spaced frames across it (or `speed` times through
    it). Returns [ {bone: (loc, quat, scale)} ]."""
    ad = arm.animation_data_create()
    ad.action = act
    if hasattr(ad, "action_slot") and len(act.slots) > 0:
        ad.action_slot = act.slots[0]
    f0, f1 = act.frame_range
    out = []
    scn = bpy.context.scene
    for i in range(n):
        t = start + (i / (n - 1 if not loop else n)) * speed
        if loop:
            t = t % 1.0
        else:
            t = min(t, 1.0)
        fr = f0 + (f1 - f0) * t
        scn.frame_set(int(fr), subframe=fr - int(fr))
        out.append({pb.name: (pb.location.copy(), pb.rotation_quaternion.copy(), pb.scale.copy()) for pb in arm.pose.bones})
    ad.action = None
    return out


def add_bones(arm, bones):
    """Adds bones to the character's armature: {name: (head, tail, parent)}, in the armature's own space."""
    bpy.context.view_layer.objects.active = arm
    with view3d_override(arm):
        bpy.ops.object.mode_set(mode="EDIT")
        eb = arm.data.edit_bones
        for name, (h, t, par) in bones.items():
            b = eb.new(name)
            b.head = h
            b.tail = t
            b.roll = 0.0
            b.parent = eb[par]
        bpy.ops.object.mode_set(mode="OBJECT")
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"


def bone_world(arm, name, tail=False):
    b = arm.data.bones[name]
    return arm.matrix_world @ (b.tail_local if tail else b.head_local)


def to_arm(arm, p):
    """A world point in the armature's own space."""
    return arm.matrix_world.inverted() @ Vector(p)


def wing_mesh(arm, side, coll, span, lift, feathers_mat_swatch="white", edge_swatch="gold"):
    """Two-segment feathered wing on one side (+1 right, -1 left). Built in world space at the rest pose, then skinned
    to wing.X.1 (inner) / wing.X.2 (outer)."""
    s = "R" if side > 0 else "L"
    r = bone_world(arm, "wing.%s.1" % s)
    e = bone_world(arm, "wing.%s.1" % s, tail=True)
    t = bone_world(arm, "wing.%s.2" % s, tail=True)
    back = Vector((0, -1, 0))
    parts = {}
    for seg, (a, b, n, ln) in {1: (r, e, 4, 0.55), 2: (e, t, 6, 0.85)}.items():
        bm = bmesh.new()
        d = (b - a)
        for i in range(n):
            u = (i + 0.5) / n
            root = a + d * u
            length = span * ln * (0.75 + 0.35 * u) * (1.0 if seg == 2 else 0.8)
            ang = math.radians(-20 - 35 * u * (1 if seg == 2 else 0.5))
            dirv = (Vector((0, 0, -1)) * math.cos(ang) + Vector((side, 0, 0)) * -math.sin(ang) * 0.6 + back * 0.25).normalized()
            w = span * 0.11
            tip = root + dirv * length
            side_v = d.normalized() * w
            pts = [root - side_v * 0.5, root + side_v * 0.5, root + dirv * length * 0.7 + side_v * 0.35, tip]
            for off in (0.006, -0.006):
                vs = [bm.verts.new(p + back * off + Vector((0, 0, 0.0))) for p in pts]
                bm.faces.new(vs if off < 0 else list(reversed(vs)))
        me = bpy.data.meshes.new("_tmp_wing")
        bm.to_mesh(me)
        bm.free()
        bm2 = bmesh.new()
        bm2.from_mesh(me)
        bpy.data.meshes.remove(me)
        # the wing's leading edge (its "arm"): a tapered beam
        bm_beam(bm2, a, b, span * 0.09, span * 0.07, w1=span * 0.06, h1=span * 0.05, up=(0, -1, 0))
        # bring into the armature's space
        bmesh.ops.transform(bm2, matrix=arm.matrix_world.inverted(), verts=bm2.verts)
        o = mesh_obj("Angel_Wing.%s.%d" % (s, seg), bm2, coll, arm)
        paint(o, feathers_mat_swatch, lo=0.05, hi=0.45)
        skin_to(o, arm, "wing.%s.%d" % (s, seg))
        parts[seg] = o
    return parts


def halo_mesh(arm, coll, radius, mat):
    c = bone_world(arm, "halo")
    bm = bmesh.new()
    ring(bm, tuple(c), radius, radius * 0.78, -radius * 0.08, radius * 0.08, seg=20)
    bmesh.ops.transform(bm, matrix=arm.matrix_world.inverted(), verts=bm.verts)
    o = mesh_obj("Angel_Halo", bm, coll, arm)
    o.data.materials.append(mat)
    o.data.uv_layers.new(name="UVMap")
    skin_to(o, arm, "halo")
    return o


def bake(arm, name, length, char_frames, extra):
    """One tower clip: the character's sampled poses (one per frame) plus extra(f, pose_bones) for the added bones."""
    new_action(arm, name, length)
    pb = arm.pose.bones
    for f in range(length + 1):
        rest_pose(arm)
        pose = char_frames[min(f, len(char_frames) - 1)]
        for bn, (loc, rot, scl) in pose.items():
            if bn in pb:
                pb[bn].location = loc
                pb[bn].rotation_quaternion = rot
                pb[bn].scale = scl
        extra(f, pb)
        key_pose(arm, f)


def drop_clips(clips):
    for a in clips.values():
        if a.name in bpy.data.actions:
            bpy.data.actions.remove(a)


def _glb_json(path):
    import json, struct
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[12:16])[0]
    return json.loads(b[20:20 + n])


def gltf_global(path, node_name):
    """A node's rest transform in the file's own (glTF, Y-up) space, as a 4x4 matrix."""
    j = _glb_json(path)
    nodes = j["nodes"]
    parent = {}
    for i, n in enumerate(nodes):
        for c in n.get("children", []):
            parent[c] = i
    idx = next(i for i, n in enumerate(nodes) if n.get("name") == node_name)

    def local(n):
        if "matrix" in n:
            m = n["matrix"]
            return Matrix([m[0:4], m[4:8], m[8:12], m[12:16]]).transposed()
        t = Vector(n.get("translation", [0, 0, 0]))
        r = n.get("rotation", [0, 0, 0, 1])
        q = Quaternion((r[3], r[0], r[1], r[2]))
        s = n.get("scale", [1, 1, 1])
        return Matrix.Translation(t) @ q.to_matrix().to_4x4() @ Matrix.Diagonal((s[0], s[1], s[2], 1))
    m = local(nodes[idx])
    while idx in parent:
        idx = parent[idx]
        m = local(nodes[idx]) @ m
    return m


GLTF_TO_BLENDER = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


def slot_point(char_file, slot, p):
    """A point given in a hand slot's space (where the pack's gear sits: its long axis is +Y) in the character's
    imported (armature) space."""
    m = gltf_global(os.path.join(KK, "chars", char_file), slot)
    return IMPORT_MATRIX.inverted() @ (GLTF_TO_BLENDER @ (m @ Vector(p)))


IMPORT_MATRIX = Matrix.Identity(4)


def held_axis(arm, clip, slot="handslot.r", want=(0.0, 0.35, 0.94)):
    """Which way a held weapon should point from `slot`: the slot's local axis (+-X, Y, Z) that, with the hand posed by
    `clip`'s first frame, points most along `want` (world: up and a little forward). Returns (origin, axis) in the
    armature's rest space."""
    ad = arm.animation_data_create()
    ad.action = clip
    if hasattr(ad, "action_slot") and len(clip.slots) > 0:
        ad.action_slot = clip.slots[0]
    bpy.context.scene.frame_set(int(clip.frame_range[0]))
    bpy.context.view_layer.update()
    pm = arm.pose.bones[slot].matrix.to_3x3()
    rest = arm.data.bones[slot].matrix_local
    best, best_s = None, -9.0
    for col in range(3):
        for sg in (1, -1):
            a = Vector((0, 0, 0))
            a[col] = sg
            w = (arm.matrix_world.to_3x3() @ (pm @ a)).normalized()
            sc = w.dot(Vector(want).normalized())
            if sc > best_s:
                best_s, best = sc, a
    ad.action = None
    bpy.context.scene.frame_set(0)
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)
    return rest.translation.copy(), (rest.to_3x3() @ best).normalized()


def make_angel(char, col, head, height, hover, span=1.05, wing_scale=1.0, halo_r=0.17, weapon=(0.45, 1.15),
               blade=(0.17, 0.42), muzzle_off=(0.0, 0.25, 0.2), gold=(1.0, 0.8, 0.35)):
    """The whole angel under `head`: the character, wing / halo / weapon bones and meshes, and the Muzzle.
    weapon: (length behind the hand, length ahead) in world units; blade: (width, length) of its tip."""
    arm, meshes = import_character(char, col, head, height, hover)
    bpy.context.view_layer.update()
    H = height
    chest = bone_world(arm, "chest")
    chest_t = bone_world(arm, "chest", tail=True)
    up = Vector((0, 0, 1))
    back = Vector((0, -1, 0))
    top_z = max((o.matrix_world @ Vector(cn)).z for o in meshes for cn in o.bound_box)
    hb = bone_world(arm, "head")
    bones = {}
    w = wing_scale
    for s, sx in (("R", 1), ("L", -1)):
        root = chest.lerp(chest_t, 0.55) + back * 0.11 * H + Vector((sx * 0.06 * H, 0, 0))
        elbow = root + Vector((sx * 0.36 * w, -0.12 * w, 0.34 * w))
        tip = elbow + Vector((sx * 0.62 * w, -0.08 * w, 0.1 * w))
        bones["wing.%s.1" % s] = (to_arm(arm, root), to_arm(arm, elbow), "chest")
        bones["wing.%s.2" % s] = (to_arm(arm, elbow), to_arm(arm, tip), "wing.%s.1" % s)
    halo_c = Vector((hb.x, hb.y - 0.04 * H / 1.5, top_z + 0.12 * H / 1.5))
    bones["halo"] = (to_arm(arm, halo_c), to_arm(arm, halo_c + up * 0.15), "head")
    pose_clip = load_clips(["Jump_Idle"])
    o0, ax = held_axis(arm, pose_clip["Jump_Idle"])
    drop_clips(pose_clip)
    kn = arm.matrix_world.to_scale().x
    s0 = o0 - ax * (weapon[0] / kn)
    s1 = o0 + ax * (weapon[1] / kn)
    bones["weapon"] = (s0, s1, "handslot.r")
    add_bones(arm, bones)
    bpy.context.view_layer.update()
    for s in ("R", "L"):
        wing_mesh(arm, 1 if s == "R" else -1, col, span, 0.0)
    gmat = glow_mat("angel_gold", gold, 1.2)
    halo_mesh(arm, col, halo_r, gmat)
    bm = bmesh.new()
    d = (s1 - s0).normalized()
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 0.1:
        side = Vector((1, 0, 0))
    u = 1.0 / kn
    bm_beam(bm, s0, s1, 0.045 * u, 0.045 * u, up=tuple(side))
    bw, bl = blade
    bm_beam(bm, s1 - d * 0.02 * u, s1 + d * bl * 0.36 * u, bw * u, 0.04 * u, w1=bw * u, h1=0.04 * u, up=tuple(side))
    bm_beam(bm, s1 + d * bl * 0.36 * u, s1 + d * bl * u, bw * 0.82 * u, 0.035 * u, w1=0.0, h1=0.01 * u, up=tuple(side))
    o = mesh_obj("Angel_Weapon", bm, col, arm)
    o.data.materials.append(gmat)
    o.data.uv_layers.new(name="UVMap")
    skin_to(o, arm, "weapon")
    rs = bone_world(arm, "upperarm.r")
    m = head.matrix_world.inverted() @ (rs + Vector(muzzle_off))
    empty("Muzzle", col, head, tuple(m), 0.25, "SPHERE")
    return arm


def angel_anims(arm, idle_clip, fire_clip, idle_len=60, fire_len=24, fire_start=0.0, fire_speed=1.0, hide=(3, 14, 22),
                beat=1.0, bob=0.06):
    """idle: the pack clip looping, a slow wing beat, a gentle bob, the halo turning. fire: the pack clip (from
    fire_start, fire_speed of it), a hard wing beat, and the weapon hidden between hide[0] and hide[1], growing back by
    hide[2] (hide = None keeps it)."""
    clips = load_clips([idle_clip, fire_clip])
    k = arm.matrix_world.to_scale().x
    fwd = (arm.matrix_world.inverted().to_3x3() @ Vector((0, 1, 0))).normalized()
    upa = (arm.matrix_world.inverted().to_3x3() @ Vector((0, 0, 1))).normalized()
    idle = sample_clip(arm, clips[idle_clip], idle_len + 1, loop=True)
    fire = sample_clip(arm, clips[fire_clip], fire_len + 1, loop=False, start=fire_start, speed=fire_speed)

    def wings(pb, flap, bend, spread=0.0):
        for s, sg in (("R", -1), ("L", 1)):
            q1 = arm_space_quat(pb["wing.%s.1" % s], tuple(fwd), sg * flap) @ arm_space_quat(pb["wing.%s.1" % s], tuple(upa), -sg * spread)
            pb["wing.%s.1" % s].rotation_quaternion = q1
            pb["wing.%s.2" % s].rotation_quaternion = arm_space_quat(pb["wing.%s.2" % s], tuple(fwd), sg * bend)

    def idle_extra(f, pb):
        t = f / idle_len
        ph = 2 * math.pi * t
        wings(pb, 14 * math.sin(ph), 10 * math.sin(ph - 0.9))
        pb["root"].location = pb["root"].location + arm_space_loc(pb["root"], tuple(upa * (bob / k) * math.sin(ph)))
        pb["halo"].rotation_quaternion = arm_space_quat(pb["halo"], tuple(upa), 180 * t)

    def fire_extra(f, pb):
        t = f / fire_len
        b = beat * (-28 * smooth(f / 4.0) + 48 * smooth((f - 4) / 6.0) - 20 * smooth((f - 10) / 12.0))
        wings(pb, b, b * 0.6, spread=10 * math.sin(math.pi * min(t * 1.5, 1.0)))
        pb["halo"].rotation_quaternion = arm_space_quat(pb["halo"], tuple(upa), 90 * t)
        if hide:
            sc = 1.0 if f < hide[0] else (0.001 if f < hide[1] else max(0.001, smooth((f - hide[1]) / max(1, hide[2] - hide[1]))))
            pb["weapon"].scale = (sc, sc, sc)

    bake(arm, "idle", idle_len, idle, idle_extra)
    bake(arm, "fire", fire_len, fire, fire_extra)
    drop_clips(clips)
    arm.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)
