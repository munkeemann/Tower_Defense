"""The Tide towers' shared pieces.

Merfolk: a KayKit adventurer (Rig_Medium) turned sea-folk. Its legs (and any hat) come off, its skin is re-tinted, and
a scaly fish tail on three bones off the hips (with a waist fin skirt and a fluke) and fin ears are added; the pack's
clips are baked into idle / fire with the tail swaying. Sea props: branching coral, a giant clam, a conch, kelp.

Exec'd by a tower script after kk_helpers.py and angel_common.py (it uses import_character, load_clips, sample_clip,
add_bones, held_axis, bake).
"""
import bpy, bmesh, math, os, random
import numpy as np
from mathutils import Vector, Matrix, Quaternion, Euler


# ------------------------------------------------------------------------------------------- sea props
def bm_coral(bm, rnd, base, h=0.6, n=4, w=0.07):
    """A branching coral: a short trunk forking into tapering, upturned branches with rounded tips."""
    base = Vector(base)
    top = base + Vector((0, 0, h * 0.32))
    bm_beam(bm, base, top, w * 1.5, w * 1.5, w1=w * 1.15, h1=w * 1.15)
    for k in range(n):
        a = math.radians(360 * k / n + rnd.uniform(-25, 25))
        out = Vector((math.cos(a), math.sin(a), 0))
        mid = top + out * h * rnd.uniform(0.18, 0.3) + Vector((0, 0, h * rnd.uniform(0.22, 0.38)))
        bm_beam(bm, top, mid, w * 1.1, w * 1.1, w1=w * 0.8, h1=w * 0.8)
        tip = mid + out * h * 0.08 + Vector((0, 0, h * rnd.uniform(0.18, 0.34)))
        bm_beam(bm, mid, tip, w * 0.8, w * 0.8, w1=w * 0.45, h1=w * 0.45)
        bm_ellipsoid(bm, tuple(tip), (w * 0.4,) * 3, u=5, v=3)
        if rnd.random() < 0.6:                          # a side twig
            tw = mid + (tip - mid) * 0.4
            bm_beam(bm, tw, tw + out.cross(Vector((0, 0, 1))) * h * 0.12 + Vector((0, 0, h * 0.14)), w * 0.55, w * 0.55, w1=w * 0.3, h1=w * 0.3)
    return bm


def bm_clam(shell, inner, c, size=0.5, yaw=0.0, open_deg=50.0):
    """A giant clam at c: a ribbed lower shell and an upper one hinged open at the back. Returns the pearl's spot."""
    c = Vector(c)
    rz = Matrix.Rotation(math.radians(yaw), 4, "Z")
    s = size
    bm_ellipsoid(shell, tuple(c + Vector((0, 0, s * 0.12))), (s, s * 0.82, s * 0.24), rot=(0, 0, yaw), u=12, v=6)
    hinge = c + rz @ Vector((0, -s * 0.78, s * 0.2))
    up = Euler((math.radians(open_deg), 0, math.radians(yaw))).to_matrix()
    bm_ellipsoid(shell, tuple(hinge + up @ Vector((0, s * 0.78, s * 0.02))), (s, s * 0.82, s * 0.2),
                 rot=(open_deg, 0, yaw), u=12, v=6)
    for k in range(7):                                  # ribs on both halves
        a = math.radians(-60 + 20 * k)
        d = Vector((math.sin(a), math.cos(a), 0))
        bm_beam(shell, c + rz @ (Vector((0, -s * 0.7, s * 0.3))), c + rz @ (d * s * 0.95 + Vector((0, -s * 0.15, s * 0.25))),
                0.05 * s, 0.05 * s, w1=0.09 * s, h1=0.05 * s)
        bm_beam(shell, hinge + up @ (Vector((0, s * 0.05, s * 0.16))), hinge + up @ (d * s * 0.95 + Vector((0, s * 0.63, s * 0.16))),
                0.05 * s, 0.05 * s, w1=0.09 * s, h1=0.05 * s)
    bm_ellipsoid(inner, tuple(c + Vector((0, 0, s * 0.3))), (s * 0.8, s * 0.65, s * 0.07), rot=(0, 0, yaw), u=10, v=4)
    return c + rz @ Vector((0, -s * 0.15, s * 0.42))


def bm_conch(bm, c, length=0.4, yaw=0.0):
    """A spiral conch lying on its side: cones shrinking along a curl, with knobs."""
    c = Vector(c)
    rz = Matrix.Rotation(math.radians(yaw), 3, "Z")
    for k in range(5):
        t = k / 5
        r = length * (0.32 - 0.055 * k)
        p = c + rz @ Vector((length * (0.45 - 0.22 * k), 0, r * 0.9 + 0.02 * k))
        bm_ellipsoid(bm, tuple(p), (r * 1.15, r, r * 0.95), rot=(0, 15 * k, yaw), u=8, v=5)
    bm_cyl(bm, 0.0, length * 0.2, length * 0.45, tuple(c + rz @ Vector((-length * 0.62, 0, length * 0.1))), rot=(0, -90, yaw), seg=6)
    return bm


def bm_starfish(bm, c, r=0.22, yaw=0.0):
    """A five-armed starfish lying flat at c."""
    c = Vector(c)
    bm_ellipsoid(bm, tuple(c + Vector((0, 0, 0.025))), (r * 0.32, r * 0.32, 0.03), u=8, v=4)
    for k in range(5):
        a = math.radians(yaw + 72 * k)
        d = Vector((math.cos(a), math.sin(a), 0))
        bm_beam(bm, c + Vector((0, 0, 0.025)), c + d * r + Vector((0, 0, 0.012)), r * 0.38, 0.045, w1=0.0, h1=0.015)
    return bm


def bm_kelp(bm, rnd, base, h=0.8, n=3):
    """A tuft of kelp: tall, thin, wavy fronds."""
    base = Vector(base)
    for k in range(n):
        a = rnd.uniform(0, 2 * math.pi)
        p = base + Vector((math.cos(a) * 0.08, math.sin(a) * 0.08, 0))
        hh = h * rnd.uniform(0.6, 1.0)
        segs = 4
        for i in range(segs):
            z0, z1 = hh * i / segs, hh * (i + 1) / segs
            wob = lambda z: Vector((math.sin(z * 7 + a) * 0.06, math.cos(z * 5 + a) * 0.04, z))
            w = 0.09 * (1 - 0.5 * i / segs)
            bm_beam(bm, p + wob(z0), p + wob(z1), w, 0.025, w1=w * 0.8, h1=0.02, up=(math.cos(a), math.sin(a), 0))
    return bm

MER_SKIN = (0.96, 0.74, 0.60)       # the pack's shared skin colour


def sea_texture(img, tint, name):
    """A copy of a character texture with its skin re-tinted to `tint` (its shading kept); other colours untouched."""
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(-1, 4)
    r, g, b = a[:, 0], a[:, 1], a[:, 2]
    mx = a[:, :3].max(1)
    mn = a[:, :3].min(1)
    d = np.maximum(mx - mn, 1e-6)
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    hue = 60.0 * (g - b) / d                      # (for red-dominant pixels)
    skin = (r >= g) & (g >= b) & (hue > 14) & (hue < 38) & (s > 0.2) & (s < 0.52) & (mx > 0.6)
    k = mx / max(MER_SKIN)
    for c in range(3):
        a[skin, c] = np.clip(tint[c] * k[skin], 0.0, 1.0)
    img2 = bpy.data.images.new(name, w, h)
    img2.pixels = a.ravel()
    img2.filepath_raw = os.path.join(TOWERS_DIR, "src", name + ".png")
    img2.file_format = "PNG"
    img2.save()
    img2.pack()
    return img2


def _to_arm_bm(bm, arm):
    """Geometry built in world space, moved into the armature's own space (parts are its children)."""
    bmesh.ops.transform(bm, matrix=arm.matrix_world.inverted(), verts=bm.verts)
    return bm


def mer_part(name, bm, swatch, arm, bone, col, team=False, mat=None, **kw):
    """A world-space piece, painted from the atlas (or given `mat`) and rigid-skinned to one of the merfolk's bones."""
    _to_arm_bm(bm, arm)
    o = mesh_obj(name, bm, col, arm)
    if mat is not None:
        o.data.materials.append(mat)
        o.data.uv_layers.new(name="UVMap")
    else:
        paint(o, swatch, team=team, **kw)
    skin_to(o, arm, bone)
    return o


def make_merfolk(char, col, head, height, hover=0.0, drop=(), skin=(0.5, 0.8, 0.72), tail=None, tail_r=(0.15, 0.045),
                 tail_sw="teal", fin_sw="team", weapon=None, pose_clip="Idle_A", tex_name="mer_skin", skirt=False):
    """The merfolk under `head`, facing +Y, `height` tall as the pack's figure (legs included). tail: offsets (in units
    of height) from the hips for the tail's four points; skirt: a ring of fins over the waist; weapon: (back, ahead) lengths of a held harpoon along the hand
    slot's axis in `pose_clip`. Returns the armature ("Rig")."""
    arm, meshes = import_character(char, col, head, height, hover)
    H = height
    for o in list(meshes):
        if o.name.endswith(("_LegLeft", "_LegRight")) or any(o.name.endswith("_" + d) for d in drop):
            meshes.remove(o)
            bpy.data.objects.remove(o, do_unlink=True)
    # sea-green skin on a copy of the character's texture
    for o in meshes:
        for sl in o.material_slots:
            if sl.material and sl.material.node_tree:
                for nd in sl.material.node_tree.nodes:
                    if nd.type == "TEX_IMAGE" and nd.image and not nd.image.name.startswith(tex_name):
                        nd.image = sea_texture(nd.image, skin, tex_name)
    bpy.context.view_layer.update()
    hp = bone_world(arm, "hips")
    tail = tail or [(0, 0.02, -0.04), (0, -0.05, -0.2), (0.07, -0.25, -0.28), (0.2, -0.38, -0.2)]
    pts = [hp + Vector(t) * H for t in tail]
    bones = {"tail.1": (to_arm(arm, pts[0]), to_arm(arm, pts[1]), "hips"),
             "tail.2": (to_arm(arm, pts[1]), to_arm(arm, pts[2]), "tail.1"),
             "tail.3": (to_arm(arm, pts[2]), to_arm(arm, pts[3]), "tail.2")}
    held = None
    if weapon:
        pc = load_clips([pose_clip])
        o0, ax = held_axis(arm, pc[pose_clip])
        drop_clips(pc)
        kn = arm.matrix_world.to_scale().x
        s0 = o0 - ax * (weapon[0] / kn)
        s1 = o0 + ax * (weapon[1] / kn)
        bones["weapon"] = (s0, s1, "handslot.r")
        held = (s0, s1)
    add_bones(arm, bones)
    bpy.context.view_layer.update()
    # the tail: round segments easing thinner, a waist skirt of fins over the join, a forked fluke
    r0, r1 = tail_r[0] * H, tail_r[1] * H
    for i in range(3):
        bm = bmesh.new()
        seg = pts[i + 1] - pts[i]
        rot = tuple(math.degrees(x) for x in Vector((0, 0, 1)).rotation_difference(seg.normalized()).to_euler())
        n = 4
        for k in range(n):                      # overlapping, stretched along the tail so it reads as one piece
            t = (i + (k + 0.5) / n) / 3
            p = pts[i].lerp(pts[i + 1], (k + 0.5) / n)
            r = r0 + (r1 - r0) * t
            bm_ellipsoid(bm, tuple(p), (r, r * 0.92, max(r * 1.2, seg.length / n * 0.8)), rot=rot, u=9, v=6)
        mer_part("Mer_Tail%d" % (i + 1), bm, tail_sw, arm, "tail.%d" % (i + 1), col, lo=0.15 + 0.1 * i, hi=0.55 + 0.1 * i)
    bm = bmesh.new()
    c0 = pts[0]
    for k in range(9 if skirt else 0):
        a = math.radians(360 * k / 9)
        out = Vector((math.cos(a), math.sin(a), 0))
        root = c0 + out * r0 * 0.95 + Vector((0, 0, 0.03 * H))
        tip = root + out * 0.06 * H + Vector((0, 0, -0.1 * H))
        bm_beam(bm, root, tip, 0.07 * H, 0.025 * H, w1=0.0, h1=0.01 * H, up=tuple(out))
    if skirt:
        mer_part("Mer_Skirt", bm, fin_sw, arm, "hips", col, team=(fin_sw == "team"), lo=0.15, hi=0.55)
    bm = bmesh.new()
    d = (pts[3] - pts[2]).normalized()
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 0.1:
        side = Vector((1, 0, 0))
    side.normalize()
    for sg in (-1, 1):
        lobe = (d + side * sg * 0.75).normalized()
        c = pts[3] + lobe * 0.09 * H
        q = Vector((0, 1, 0)).rotation_difference(lobe)
        e = q.to_euler()
        bm_ellipsoid(bm, tuple(c), (0.05 * H, 0.11 * H, 0.016 * H), rot=tuple(math.degrees(x) for x in e), u=8, v=4)
    mer_part("Mer_Fluke", bm, fin_sw, arm, "tail.3", col, team=(fin_sw == "team"), lo=0.15, hi=0.55)
    # fin ears, at the sides of the head
    hm = next((o for o in meshes if o.name.endswith("_Head")), None)
    if hm:
        bb = [hm.matrix_world @ Vector(c) for c in hm.bound_box]
        cx = sum(p.x for p in bb) / 8
        cy = sum(p.y for p in bb) / 8
        zs = sorted(p.z for p in bb)
        cz = zs[0] + (zs[-1] - zs[0]) * 0.42
        half = (max(p.x for p in bb) - min(p.x for p in bb)) / 2
        bm = bmesh.new()
        for sg in (-1, 1):
            c = Vector((cx + sg * (half * 0.92), cy - 0.02 * H, cz))
            bm_ellipsoid(bm, tuple(c + Vector((sg * 0.03 * H, -0.04 * H, 0.03 * H))), (0.014 * H, 0.085 * H, 0.06 * H),
                         rot=(25, 0, sg * -25), u=7, v=4)
        mer_part("Mer_EarFins", bm, fin_sw, arm, "head", col, team=(fin_sw == "team"), lo=0.15, hi=0.55)
    # a barbed harpoon in the right hand
    if held:
        s0, s1 = (arm.matrix_world @ held[0], arm.matrix_world @ held[1])
        dd = (s1 - s0).normalized()
        sd = dd.cross(Vector((0, 0, 1)))
        if sd.length < 0.1:
            sd = Vector((1, 0, 0))
        bm = bmesh.new()
        bm_beam(bm, s0, s1, 0.035, 0.035, up=tuple(sd))
        mer_part("Mer_HarpoonShaft", bm, "wood", arm, "weapon", col, lo=0.3, hi=0.7)
        bm = bmesh.new()
        tip = s1 + dd * 0.22
        bm_beam(bm, s1 - dd * 0.02, tip, 0.07, 0.07, w1=0.0, h1=0.0, up=tuple(sd))
        for sg in (-1, 1):
            b0 = s1 + dd * 0.06
            bm_beam(bm, b0, b0 - dd * 0.1 + sd * sg * 0.07, 0.03, 0.02, w1=0.0, h1=0.0, up=tuple(dd.cross(sd)))
        ring(bm, tuple(s1 - dd * 0.03), 0.045, 0.03, -0.015, 0.015, seg=8, axis="Z")
        mer_part("Mer_HarpoonHead", bm, "iron", arm, "weapon", col, lo=0.05, hi=0.5)
    return arm


def merfolk_anims(arm, idle_clip, fire_clip, idle_len=60, fire_len=24, fire_start=0.0, fire_speed=1.0, hide=None,
                  sway=9.0, upper_only=False, extra=None):
    """idle: the pack clip looping and the tail swaying; fire: the pack clip (from fire_start, fire_speed of it), the
    tail lashing, and the harpoon hidden between hide[0] and hide[1], growing back by hide[2]. upper_only: fire moves
    only the chest up (arms, head), the rest holds the idle's first pose (a seated siren casting). extra(name, f, pb)
    adds the tower's own bones."""
    clips = load_clips([idle_clip, fire_clip])
    idle = sample_clip(arm, clips[idle_clip], idle_len + 1, loop=True)
    fire = sample_clip(arm, clips[fire_clip], fire_len + 1, loop=False, start=fire_start, speed=fire_speed)
    if upper_only:
        upper = {"chest"} | {b.name for b in arm.data.bones["chest"].children_recursive}
        upper -= {"tail.1", "tail.2", "tail.3"}
        fire = [{bn: (v if bn in upper else idle[0][bn]) for bn, v in fr.items()} for fr in fire]
    upa = (arm.matrix_world.inverted().to_3x3() @ Vector((0, 0, 1))).normalized()
    fwd = (arm.matrix_world.inverted().to_3x3() @ Vector((0, 1, 0))).normalized()

    def tail(pb, ph, amp):
        for i in range(3):
            b = pb["tail.%d" % (i + 1)]
            b.rotation_quaternion = (arm_space_quat(b, tuple(upa), amp * math.sin(ph - i * 0.9))
                                     @ arm_space_quat(b, tuple(fwd), amp * 0.4 * math.sin(ph * 2 - i)))

    def idle_extra(f, pb):
        tail(pb, 2 * math.pi * f / idle_len, sway)
        if extra:
            extra("idle", f, pb)

    def fire_extra(f, pb):
        tail(pb, 2 * math.pi * f / fire_len * 1.5, sway * 1.8 * (1 - f / fire_len) + sway * 0.5)
        if hide and "weapon" in pb:
            sc = 1.0 if f < hide[0] else (0.001 if f < hide[1] else max(0.001, smooth((f - hide[1]) / max(1, hide[2] - hide[1]))))
            pb["weapon"].scale = (sc, sc, sc)
        if extra:
            extra("fire", f, pb)

    bake(arm, "idle", idle_len, idle, idle_extra)
    bake(arm, "fire", fire_len, fire, fire_extra)
    drop_clips(clips)
    arm.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)
