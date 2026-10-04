"""Builds the Magma Golem (footprint "arrow3": [0,0] front, [1,0] back-right, [-1,1] back-left), a Forge creature
tower: it hurls molten boulders that splash and leave enemies burning.

    blender -b --factory-startup --python tools/blender/build_tower.py -- magma_golem <preview dir>

The pack's Frost Golem, re-skinned as basalt with lava running through its cracks, stands in a lava pool on the front
cell with a molten boulder in its fist (the Head: it turns to aim; the boulder is the muzzle). Back-left: a volcanic
vent. Back-right: a heap of glowing boulders (its ammo). idle: the pack's idle. fire: a big
two-handed hurl; the boulder leaves the fist and a new one wells up in it.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "angel_common.py"), encoding="utf-8").read())

TID = "magma_golem"
CELLS = [(0, 0), (1, 0), (-1, 1)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)
BR = hex_to_world(1, 0, MID)
BL = hex_to_world(-1, 1, MID)
TOP = 0.34
LAVA = (1.0, 0.36, 0.05)
HEIGHT = 2.05
IDLE_CLIP, FIRE_CLIP = "Idle_A", "Melee_2H_Attack"
ROCK_TEX = None


def magma_images():
    """The golem's texture re-coloured. Its stone plates use the pale column's upper half: basalt. The seams between
    them use its lower half, and the ice crystals the blue column: lava (yellow-hot toward the top). A second image
    holds only the lava, for the glow."""
    src = bpy.data.images.load(os.path.join(KK, "chars", "frostgolem_texture.png"))
    w, h = src.size
    px = list(src.pixels)
    base, emit = [0.0] * len(px), [0.0] * len(px)
    for y in range(h):
        t = y / (h - 1)                 # 0 at the bottom, 1 at the top
        for x in range(w):
            i = (y * w + x) * 4
            if x < w // 2 and t >= 0.52:    # basalt plates
                k = 0.06 + 0.22 * (t - 0.52) / 0.48
                c = (k * 1.15, k, k * 0.95)
                e = (0.0, 0.0, 0.0)
            else:                           # lava seams and crystals
                c = (1.0, 0.22 + 0.55 * t, 0.03 + 0.2 * t * t)
                e = c
            base[i:i + 4] = (*c, 1.0)
            emit[i:i + 4] = (*e, 1.0)
    imgs = []
    for name, data in (("magma_base", base), ("magma_emit", emit)):
        img = bpy.data.images.new(name, w, h)
        img.pixels = data
        img.filepath_raw = os.path.join(TOWERS_DIR, "src", name + ".png")
        img.file_format = "PNG"
        img.save()
        img.pack()
        imgs.append(img)
    bpy.data.images.remove(src)
    return imgs


def magma_mat():
    base, emit = magma_images()
    m = bpy.data.materials.new("magma_golem")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tb = nt.nodes.new("ShaderNodeTexImage"); tb.image = base; tb.interpolation = "Closest"
    te = nt.nodes.new("ShaderNodeTexImage"); te.image = emit; te.interpolation = "Closest"
    nt.links.new(tb.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(te.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 0.8
    return m


def build_base():
    col = collection("Magma_golem")
    root = empty("Magma_golem", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP, stone="stone_dark", course="iron")
    rnd = random.Random(31)
    # the lava pool on the front cell, ringed with basalt
    bm = bmesh.new()
    bm_cyl(bm, 0.78, 0.78, 0.03, (F.x, F.y, T + 0.01), seg=14)
    glow_obj("Lava_Pool", bm, col, root, LAVA, 0.9)
    bm = bmesh.new()
    for k in range(11):
        a = math.radians(360 * k / 11 + rnd.uniform(-8, 8))
        r = rnd.uniform(0.12, 0.18)
        bm_ellipsoid(bm, F + Vector((math.cos(a) * 0.82, math.sin(a) * 0.78, T + 0.02)), (r * 1.2, r, r * rnd.uniform(0.7, 1.2)),
                     rot=(rnd.uniform(-15, 15), rnd.uniform(-15, 15), rnd.uniform(0, 90)), u=6, v=4)
    o = paint(mesh_obj("Pool_Rim", bm, col, root), "stone_dark", lo=0.05, hi=0.5)
    # lava fissures running back across the plinth
    bm = bmesh.new()
    for c in (BL, BR):
        p0 = F + (Vector(c) - F) * 0.35
        p1 = F + (Vector(c) - F) * 0.8
        mid = p0.lerp(p1, 0.5) + Vector((rnd.uniform(-0.15, 0.15), rnd.uniform(-0.15, 0.15), 0))
        for a, b in ((p0, mid), (mid, p1)):
            bm_beam(bm, (a.x, a.y, T + 0.005), (b.x, b.y, T + 0.005), 0.09, 0.02)
    glow_obj("Lava_Cracks", bm, col, root, LAVA, 0.9)
    # back-left: a volcanic vent with a glowing crater
    v = BL + Vector((0.1, 0.05, 0))
    bm = bmesh.new()
    bm_cyl(bm, 0.75, 0.32, 0.9, (v.x, v.y, T + 0.45), seg=9)
    for k in range(6):
        a = math.radians(60 * k + 15)
        bm_rock(bm, rnd, v + Vector((math.cos(a) * 0.62, math.sin(a) * 0.62, 0)), rnd.uniform(0.25, 0.35), T - 0.02, rnd.uniform(0.2, 0.4))
    o = paint(mesh_obj("Vent", bm, col, root), "stone_dark", lo=0.05, hi=0.6)
    bm = bmesh.new()
    bm_cyl(bm, 0.26, 0.26, 0.04, (v.x, v.y, T + 0.89), seg=9)
    glow_obj("Vent_Crater", bm, col, root, LAVA, 1.2)
    # back-right: the ammo heap, boulders with lava between them
    a = BR + Vector((0.05, 0.05, 0))
    bm = bmesh.new()
    bm_ellipsoid(bm, (a.x, a.y, T + 0.05), (0.55, 0.5, 0.2), u=10, v=5)
    glow_obj("Heap_Lava", bm, col, root, LAVA, 0.9)
    bm = bmesh.new()
    for k, (dx, dy, dz, r) in enumerate(((-0.25, -0.15, 0.2, 0.26), (0.25, -0.1, 0.2, 0.25), (0.0, 0.25, 0.2, 0.27),
                                          (0.02, 0.0, 0.5, 0.24), (-0.4, 0.25, 0.15, 0.18), (0.42, 0.28, 0.14, 0.17))):
        bm_ellipsoid(bm, (a.x + dx, a.y + dy, T + dz), (r, r * 0.95, r * 0.9), rot=(rnd.uniform(0, 40), 0, rnd.uniform(0, 90)), u=6, v=4)
    paint(mesh_obj("Heap", bm, col, root), "stone_dark", lo=0.05, hi=0.5)
    empty("Head", col, root, (F.x, F.y, T), 0.5, "SINGLE_ARROW")
    return root


def build_head():
    col = collection("Magma_golem")
    head = bpy.data.objects["Head"]
    arm, meshes = import_character("FrostGolem.glb", col, head, HEIGHT, 0.0)
    mat = magma_mat()
    for o in meshes:
        o.data.materials.clear()
        o.data.materials.append(mat)
    bpy.context.view_layer.update()
    # the boulder rides the right hand
    hand = bone_world(arm, "handslot.r")
    kn = arm.matrix_world.to_scale().x
    bc = hand + Vector((0, 0.05, 0.18))
    add_bones(arm, {"boulder": (to_arm(arm, bc), to_arm(arm, bc + Vector((0, 0, 0.3))), "handslot.r")})
    bpy.context.view_layer.update()
    rnd = random.Random(4)
    u = 1.0 / kn
    bm = bmesh.new()
    bm_ellipsoid(bm, to_arm(arm, bc), (0.21 * u,) * 3, u=10, v=6)
    o = mesh_obj("Boulder_Core", bm, col, arm)
    o.data.materials.append(glow_mat("lava_glow", LAVA, 1.1))
    o.data.uv_layers.new(name="UVMap")
    skin_to(o, arm, "boulder")
    bm = bmesh.new()
    for k in range(7):
        d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized()
        bm_ellipsoid(bm, to_arm(arm, bc + d * 0.12), (0.14 * u, 0.12 * u, 0.11 * u), rot=(rnd.uniform(0, 90),) * 3, u=5, v=4)
    o = paint(mesh_obj("Boulder_Crust", bm, col, arm), "stone_dark", lo=0.05, hi=0.4)
    skin_to(o, arm, "boulder")
    # shots leave above the right shoulder, where the hurl lets go
    m = head.matrix_world.inverted() @ (bone_world(arm, "upperarm.r") + Vector((0, 0.3, 0.45)))
    empty("Muzzle", col, head, tuple(m), 0.25, "SPHERE")
    return arm


IDLE_LEN = 48
FIRE_LEN = 28
HIDE = (3, 12, 24)      # the boulder flies at HIDE[0], wells up again from HIDE[1] to HIDE[2]
FIRE_START, FIRE_SPEED = 0.24, 0.76     # the wind-up is trimmed: the game launches the shot as the clip starts


def build_anims():
    arm = bpy.data.objects["Rig"]
    clips = load_clips([IDLE_CLIP, FIRE_CLIP], RIG_LARGE)
    idle = sample_clip(arm, clips[IDLE_CLIP], IDLE_LEN + 1, loop=True)
    fire = sample_clip(arm, clips[FIRE_CLIP], FIRE_LEN + 1, loop=False, start=FIRE_START, speed=FIRE_SPEED)
    def idle_extra(f, pb):
        pass

    def fire_extra(f, pb):
        sc = 1.0 if f < HIDE[0] else (0.001 if f < HIDE[1] else max(0.001, smooth((f - HIDE[1]) / (HIDE[2] - HIDE[1]))))
        pb["boulder"].scale = (sc, sc, sc)

    bake(arm, "idle", IDLE_LEN, idle, idle_extra)
    bake(arm, "fire", FIRE_LEN, fire, fire_extra)
    drop_clips(clips)
    arm.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 1.2), "dist": 9.0, "yaw": 150, "pitch": 18, "anim_target": (F.x, F.y, 1.4), "anim_dist": 5.5,
           "frames": [("idle", 0), ("fire", 0), ("fire", 3), ("fire", 8), ("fire", 20)]}


def build_all():
    build_base()
    build_head()
    build_anims()
