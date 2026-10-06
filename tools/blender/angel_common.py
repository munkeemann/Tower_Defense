"""Shared by the angel towers (Seraph, Archangel): a KayKit character (Rig_Medium) given wings, a halo and a weapon
of light, with the pack's animation clips baked together with wing beats into the tower's own "idle" and "fire".

Exec after kk_helpers.py. The character's armature becomes the tower's rig: it's renamed "Rig", parented to the Head,
turned to face +Y (the tower's front) and scaled to `height`. Extra bones: wing.L.1/2, wing.R.1/2 (on the chest),
halo (on the head) and weapon (on the right hand slot). Their meshes are rigid-skinned to them.
"""
import bpy, bmesh, math, os
from mathutils import Vector, Matrix, Quaternion, Euler

ANIMS = os.path.join(KK, "anims")


def rot_deg(d, axis="Z"):
    """Euler degrees (for bm_cyl / bm_box / bm_ellipsoid's rot) that turn local `axis` to point along d."""
    return tuple(math.degrees(x) for x in Vector(d).to_track_quat(axis, "Y").to_euler())


def arc_blocks(bm, rnd, c, r, z0, z1, a0, a1, depth, courses=1, n=48, phase=0.0):
    """Coursed wedge blocks round c between angles a0 and a1 (degrees), outer radius r, `depth` deep, in `courses`
    rows from z0 to z1 (joints staggered): steps, stylobates, parapets, entablatures of a round shrine."""
    h = (z1 - z0) / courses
    for k in range(courses):
        bm_block_course(bm, rnd, c, r, z0 + k * h, h, n, depth=depth, phase=phase + 0.5 * (k % 2),
                        skip=lambda a: not (a0 <= a <= a1))
    return bm


def wedge(bm, c, a0, a1, r_in, r_out, z0, z1):
    """A block between two angles (radians) and two radii round c (x, y): a piece of a ring."""
    vs = []
    for z in (z0, z1):
        for r, a in ((r_in, a0), (r_out, a0), (r_out, a1), (r_in, a1)):
            vs.append(bm.verts.new((c[0] + r * math.cos(a), c[1] + r * math.sin(a), z)))
    lo, hi = vs[:4], vs[4:]
    bm.faces.new(list(reversed(lo)))
    bm.faces.new(hi)
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    return bm


def ring_blocks(bm, rnd, c, r_out, depth, z0, z1, a0, a1, block=0.4, gap=0.022, phase=0.0, keep=None, jit=0.01, fit=False):
    """One course of blocks round c from angle a0 to a1 (degrees, a0 < a1), outer radius r_out, `depth` deep, z0 to
    z1. phase shifts the joints by part of a block (the end blocks come out shorter). A block with a corner where
    keep(x, y) is False is left out (clips the course to a footprint); fit=True instead shortens the arc (from its
    middle out) to where it fits, so it ends cleanly."""
    if keep and fit:
        def ok(a):
            ar = math.radians(a)
            return all(keep(c[0] + r * math.cos(ar), c[1] + r * math.sin(ar)) for r in (r_out - depth, r_out))
        lo_ = hi_ = (a0 + a1) * 0.5
        while lo_ - 0.5 >= a0 and ok(lo_ - 0.5):
            lo_ -= 0.5
        while hi_ + 0.5 <= a1 and ok(hi_ + 0.5):
            hi_ += 0.5
        a0, a1, keep = lo_, hi_, None
    r_mid = r_out - depth * 0.5
    span = math.radians(a1 - a0)
    n = max(1, int(round(span * r_mid / block)))
    step = span / n
    ga = gap / max(r_out, 1e-3)
    A0, A1 = math.radians(a0), math.radians(a1)
    for i in range(n + (1 if phase else 0)):
        b0 = max(A0 + step * (i - phase), A0)
        b1 = min(A0 + step * (i + 1 - phase), A1)
        if b1 - b0 < ga * 3:
            continue
        b0, b1 = b0 + ga * 0.5, b1 - ga * 0.5
        ri, ro = r_out - depth, r_out + rnd.uniform(-jit, jit)
        if keep and not all(keep(c[0] + r * math.cos(a), c[1] + r * math.sin(a)) for r in (ri, ro) for a in (b0, b1)):
            continue
        wedge(bm, c, b0, b1, ri, ro, z0 + rnd.uniform(0, jit * 0.5), z1 - gap * 0.4 - rnd.uniform(0, jit * 0.5))
    return bm


def ring_paving(kit, rnd, c, r0, r1, z, keep, width=0.32, block=0.46, h=0.05, swatches=("white:0.12:0.55",)):
    """Concentric rings of paving slabs round c from radius r0 out to r1, joints staggered, clipped by keep(x, y);
    swatches cycle ring by ring."""
    r, k = r0, 0
    while r + width <= r1 + 1e-6:
        off = rnd.uniform(0, 360)
        ring_blocks(kit[swatches[k % len(swatches)]], rnd, c, r + width, width, z - 0.012, z + h, off, off + 360,
                    block=block, gap=0.03, keep=keep, jit=0.006)
        r += width
        k += 1
    return kit


def report_envelope(arm, prefix="Angel_Wing", head="Head"):
    """Debug: the wings' reach (the farthest from the Head's axis, by height band) over idle and fire, printed."""
    hc = bpy.data.objects[head].matrix_world.translation.copy()
    for act in ("idle", "fire"):
        bands = {}
        a = bpy.data.actions[act]
        arm.animation_data.action = a
        if hasattr(arm.animation_data, "action_slot") and len(a.slots) > 0:
            arm.animation_data.action_slot = a.slots[0]
        f0, f1 = (int(x) for x in a.frame_range)
        for f in range(f0, f1 + 1, 2):
            bpy.context.scene.frame_set(f)
            dg = bpy.context.evaluated_depsgraph_get()
            for o in [o for o in bpy.data.objects if o.name.startswith(prefix) and o.type == "MESH"]:
                oe = o.evaluated_get(dg)
                me = oe.to_mesh()
                for v in me.vertices:
                    p = oe.matrix_world @ v.co
                    b = round(p.z * 5) / 5
                    bands[b] = max(bands.get(b, 0.0), math.hypot(p.x - hc.x, p.y - hc.y))
                oe.to_mesh_clear()
        print("ENVELOPE", act, " ".join("%.1f:%.2f" % (b, bands[b]) for b in sorted(bands)))
    arm.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)
    dg = bpy.context.evaluated_depsgraph_get()
    tris = []
    for o in bpy.data.objects:
        if o.type == "MESH":
            oe = o.evaluated_get(dg)
            me = oe.to_mesh()
            tris.append((sum(len(p.vertices) - 2 for p in me.polygons), o.name))
            oe.to_mesh_clear()
    print("TRIS total=%d" % sum(t for t, n in tris), " ".join("%s=%d" % (n, t) for t, n in sorted(tris, reverse=True)[:24]))


def drape(k, c, r, a0, a1, z_top, sag, height, swatch="team!:0.1:0.7", fringe="gold:0.1:0.5", n=6):
    """A swag of cloth hung round c at radius r between angles a0 and a1 (degrees): its top edge sags by `sag` in the
    middle, it hangs `height` down, with a gilded fringe along the hem."""
    c = Vector((c[0], c[1], 0))
    pts = []
    for i in range(n + 1):
        f = i / n
        a = math.radians(a0 + (a1 - a0) * f)
        s = math.sin(math.pi * f)
        pts.append(c + Vector((math.cos(a) * r, math.sin(a) * r, z_top - sag * s - (height * (0.5 + 0.1 * s)))))
    for p, q in zip(pts, pts[1:]):
        m = (p + q) * 0.5
        rad = Vector((m.x - c.x, m.y - c.y, 0)).normalized()
        hh = height * (1.0 + 0.2 * math.sin(math.pi * ((pts.index(p) + 0.5) / n)))
        bm_beam(k[swatch], p, q, hh, 0.016, up=tuple(rad))
    hem = [p - Vector((0, 0, height * 0.5 + 0.1 * height * math.sin(math.pi * i / n))) for i, p in enumerate(pts)]
    bm_tube(k[fringe], hem, 0.02, n=4)
    return k


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
        t = start + (i / (n - 1)) * speed           # a loop's last sample comes round to its first exactly
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


def _to_arm_kit(arm, kit):
    for bm in kit.parts.values():
        bmesh.ops.transform(bm, matrix=arm.matrix_world.inverted(), verts=bm.verts)


def wing_mesh(arm, side, coll, span, feather="white", covert="cream", arm_sw="gold"):
    """One wing (+1 right, -1 left) like the gryphon's: a gilded arm in two segments with a shoulder cap, a row of long
    flight feathers hanging from it (secondaries on the inner arm, primaries fanning out from the outer), and a row of
    shorter gilded coverts over their roots on both faces. Built in world space at the rest pose, then skinned to
    wing.X.1 / wing.X.2."""
    s = "R" if side > 0 else "L"
    r = bone_world(arm, "wing.%s.1" % s)
    e = bone_world(arm, "wing.%s.1" % s, tail=True)
    t = bone_world(arm, "wing.%s.2" % s, tail=True)
    u = span
    fwd, back, down, out = Vector((0, 1, 0)), Vector((0, -1, 0)), Vector((0, 0, -1)), Vector((side, 0, 0))
    k_in, k_out = Kit(), Kit()
    bm_tube(k_in[arm_sw + ":0.15:0.55"], [r, e], [0.075 * u, 0.058 * u], n=7)
    bm_ellipsoid(k_in[arm_sw + ":0.1:0.5"], r, (0.1 * u, 0.09 * u, 0.1 * u), u=8, v=5)
    bm_tube(k_out[arm_sw + ":0.15:0.55"], [e, t], [0.058 * u, 0.026 * u], n=6)
    bm_ellipsoid(k_out[arm_sw + ":0.1:0.5"], e, (0.07 * u, 0.065 * u, 0.07 * u), u=7, v=5)

    def feathers(kit, a, b, n, length, dirn, width):
        for i in range(n):
            f = (i + 0.5) / n
            p = a.lerp(b, f)
            d = dirn(f)
            ln = length(f) * u
            bm_beam(kit[feather + ":0.03:0.42"], p - d * 0.04 * u, p + d * ln, width * u, 0.016, w1=width * 0.55 * u, h1=0.01, up=fwd)
            for sg in (1, -1):
                bm_beam(kit[covert + ":0.08:0.5"], p + fwd * (sg * 0.014) - d * 0.03 * u, p + fwd * (sg * 0.014) + d * ln * 0.42,
                        width * 1.06 * u, 0.012, w1=width * 0.62 * u, h1=0.008, up=fwd)
    feathers(k_in, r, e, 5, lambda f: 0.52 * (0.8 + 0.4 * f), lambda f: (down + out * (0.05 + 0.2 * f) + back * 0.22).normalized(), 0.17)
    feathers(k_out, e, t, 7, lambda f: 0.9 * (1.08 - 0.34 * f), lambda f: (down * (1.0 - 0.78 * f * f) + out * (0.15 + 0.95 * f) + back * 0.18).normalized(), 0.15)
    _to_arm_kit(arm, k_in)
    _to_arm_kit(arm, k_out)
    parts = {1: k_in.emit("Angel_Wing.%s.1" % s, coll, rig=arm, bone="wing.%s.1" % s, vary=0.05),
             2: k_out.emit("Angel_Wing.%s.2" % s, coll, rig=arm, bone="wing.%s.2" % s, vary=0.05, seed=3)}
    return parts


def halo_mesh(arm, coll, radius, mat):
    """A halo of light: a ring, a thinner ring inside it and eight rays, tilted up at the front a little so the game
    camera (behind and above) sees its face."""
    c = bone_world(arm, "halo")
    bm = bmesh.new()
    ring(bm, tuple(c), radius, radius * 0.8, -radius * 0.1, radius * 0.1, seg=16)
    ring(bm, tuple(c), radius * 0.62, radius * 0.54, -radius * 0.05, radius * 0.05, seg=12)
    for i in range(8):
        a = 2 * math.pi * (i + 0.5) / 8
        d = Vector((math.cos(a), math.sin(a), 0))
        bm_crystal(bm, c + d * radius * 0.96, c + d * radius * 1.42, radius * 0.1, n=4, shoulder=0.3, foot=1.0)
    bmesh.ops.rotate(bm, cent=c, matrix=Matrix.Rotation(math.radians(14), 3, "X"), verts=bm.verts)
    bmesh.ops.transform(bm, matrix=arm.matrix_world.inverted(), verts=bm.verts)
    o = mesh_obj("Angel_Halo", bm, coll, arm)
    o.data.materials.append(mat)
    o.data.uv_layers.new(name="UVMap")
    skin_to(o, arm, "halo")
    return o


def column(k, rnd, c, z0, h, r, stone="white:0.08:0.5", core="cream:0.4:0.8", trim="gold:0.1:0.5", courses=4, drums=0):
    """A marble column standing at c on z0, h tall: a square base, drums with joints, a flared capital with a gilded
    abacus. Into a Kit (stone, core, trim, cream). drums > 0: that many plain tapering drums (cheaper) instead of
    coursed blocks."""
    c = Vector((c[0], c[1], 0))
    bm_box(k["cream:0.2:0.6"], (r * 2.7, r * 2.7, 0.08), (c.x, c.y, z0 + 0.04))
    bm_cyl(k[stone], r * 1.25, r * 1.08, 0.06, (c.x, c.y, z0 + 0.11), seg=10)
    if drums:
        dh = (h - 0.34) / drums
        for i in range(drums):
            ra = r * (1.0 - 0.1 * i / drums)
            bm_cyl(k[stone], ra, ra * 0.93, dh, (c.x, c.y, z0 + 0.14 + dh * (i + 0.5)), seg=8)
    else:
        round_tower(k, rnd, (c.x, c.y, 0), r, r * 0.88, z0 + 0.14, z0 + h - 0.2, courses=courses, n=8, depth=r * 0.3, stone=stone, core=core)
    bm_cyl(k["cream:0.15:0.5"], r * 0.9, r * 1.35, 0.13, (c.x, c.y, z0 + h - 0.135), seg=10)
    bm_box(k[trim], (r * 2.9, r * 2.9, 0.07), (c.x, c.y, z0 + h - 0.035))
    return k


def brazier(k, rnd, c, z0, h=0.55, flame="glow:1.0,0.72,0.3,1.0"):
    """A standing brazier at c: a stone pedestal, a gilded bowl, a flame of light."""
    c = Vector((c[0], c[1], 0))
    bm_box(k["white:0.15:0.6"], (0.3, 0.3, 0.1), (c.x, c.y, z0 + 0.05))
    bm_cyl(k["white:0.15:0.6"], 0.07, 0.09, h - 0.1, (c.x, c.y, z0 + 0.1 + (h - 0.1) / 2), seg=6)
    bm_cyl(k["gold:0.1:0.5"], 0.1, 0.22, 0.16, (c.x, c.y, z0 + h + 0.06), seg=8)
    bm_cyl(k["black:0.5:0.9"], 0.17, 0.19, 0.03, (c.x, c.y, z0 + h + 0.145), seg=8)
    fc = Vector((c.x, c.y, z0 + h + 0.14))
    for i in range(5):
        a = math.radians(72 * i + rnd.uniform(-14, 14))
        d = 0.0 if i == 0 else 0.08
        base = fc + Vector((math.cos(a) * d, math.sin(a) * d, 0))
        bm_crystal(k[flame], base, base + Vector((math.cos(a) * 0.03, math.sin(a) * 0.03, 0.4 if i == 0 else rnd.uniform(0.18, 0.28))),
                   0.07 if i == 0 else 0.045, n=4, shoulder=0.35, foot=1.0)
    return k


def statue(k, c, facing, z0, h=0.85, sw="gold:0.08:0.5", trim="gold:0.02:0.35"):
    """A gilded statue of a robed angel standing on z0 at c, facing `facing` (x, y): folded wings rising over its
    head and sweeping down to its hem, a sword held point-down before it."""
    f = Vector((facing[0], facing[1], 0)).normalized()
    s = Vector((f.y, -f.x, 0))
    up = Vector((0, 0, 1))
    c = Vector((c[0], c[1], z0))
    u = h / 0.85
    rows = [(0.0, 0.15, 0.13), (0.07, 0.16, 0.14), (0.42, 0.11, 0.09), (0.58, 0.13, 0.095), (0.66, 0.125, 0.085), (0.71, 0.05, 0.045)]
    bm_loft(k[sw], [oval(c + up * (z * u), s, f, rx * u, ry * u, n=8) for z, rx, ry in rows])
    bm_ellipsoid(k[sw], c + up * (0.79 * u) + f * (0.01 * u), (0.075 * u, 0.075 * u, 0.088 * u), u=8, v=5)
    hand = c + f * (0.14 * u) + up * (0.43 * u)
    for sg in (1, -1):
        sh = c + s * (sg * 0.12 * u) + up * (0.64 * u)
        el = c + s * (sg * 0.14 * u) + f * (0.05 * u) + up * (0.5 * u)
        bm_tube(k[sw], [sh, el, hand + s * (sg * 0.035 * u)], [0.042 * u, 0.038 * u, 0.034 * u], n=5)
        r0 = c + s * (sg * 0.09 * u) - f * (0.08 * u) + up * (0.62 * u)
        bm_beam(k[trim], r0, c + s * (sg * 0.21 * u) - f * (0.14 * u) + up * (1.08 * u), 0.17 * u, 0.04 * u, w1=0.03 * u, h1=0.025 * u, up=tuple(s * sg))
        bm_beam(k[trim], r0, c + s * (sg * 0.16 * u) - f * (0.12 * u) + up * (0.1 * u), 0.19 * u, 0.04 * u, w1=0.06 * u, h1=0.025 * u, up=tuple(s * sg))
    top = c + f * (0.16 * u) + up * (0.37 * u)
    bm_beam(k[trim], top, c + f * (0.16 * u) + up * (0.02 * u), 0.022 * u, 0.075 * u, w1=0.016 * u, h1=0.0, up=tuple(s))     # blade
    bm_beam(k[trim], top - s * (0.1 * u), top + s * (0.1 * u), 0.035 * u, 0.035 * u)                                         # crossguard
    bm_tube(k[trim], [top, top + up * (0.1 * u)], 0.02 * u, n=4)
    bm_ellipsoid(k[trim], top + up * (0.12 * u), (0.03 * u, 0.03 * u, 0.03 * u), u=5, v=4)
    return k


def fire_bowl(k, rnd, c, z0, r=0.18, tall=0.36, flame="glow:1.0,0.72,0.3,1.0"):
    """A gilded fire bowl standing on z0 at c (on a cornice, a newel, a plinth), a flame of light in it."""
    c = Vector((c[0], c[1], 0))
    bm_cyl(k["gold:0.1:0.5"], r * 0.5, r * 0.62, 0.06, (c.x, c.y, z0 + 0.03), seg=8)
    bm_cyl(k["gold:0.1:0.5"], r * 0.45, r, r * 0.7, (c.x, c.y, z0 + 0.06 + r * 0.35), seg=8)
    bm_cyl(k["black:0.5:0.9"], r * 0.84, r * 0.88, 0.03, (c.x, c.y, z0 + 0.05 + r * 0.7), seg=8)
    fc = Vector((c.x, c.y, z0 + 0.04 + r * 0.7))
    for i in range(5):
        a = math.radians(72 * i + rnd.uniform(-14, 14))
        d = 0.0 if i == 0 else r * 0.45
        base = fc + Vector((math.cos(a) * d, math.sin(a) * d, 0))
        h = tall if i == 0 else rnd.uniform(0.45, 0.7) * tall
        bm_crystal(k[flame], base, base + Vector((math.cos(a) * 0.03, math.sin(a) * 0.03, h)), r * (0.42 if i == 0 else 0.26),
                   n=4, shoulder=0.35, foot=1.0)
    return k


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
               blade=(0.17, 0.42), muzzle_off=(0.0, 0.25, 0.2), gold=(1.0, 0.8, 0.35), kind="spear"):
    """The whole angel under `head`: the character, wing / halo / weapon bones and meshes, and the Muzzle.
    weapon: (length behind the hand, length ahead) in world units; blade: (width, length) of its tip; kind: "spear"
    (a gilded shaft, a leaf blade of light) or "sword" (a gilded grip and crossguard, a long blade of light)."""
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
        elbow = root + Vector((sx * 0.34 * w, -0.14 * w, 0.42 * w))
        tip = elbow + Vector((sx * 0.74 * w, -0.1 * w, 0.0 * w))
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
        wing_mesh(arm, 1 if s == "R" else -1, col, span)
    gmat = glow_mat("angel_gold", gold, 1.2)
    halo_mesh(arm, col, halo_r, gmat)
    # the weapon, in the armature's space (u = one world unit there)
    k = Kit()
    glow = "glow:%.2f,%.2f,%.2f,1.1" % tuple(gold)
    d = (s1 - s0).normalized()
    side = d.cross(Vector((0, 0, 1)))
    if side.length < 0.1:
        side = Vector((1, 0, 0))
    side.normalize()
    u = 1.0 / kn
    bw, bl = blade
    if kind == "spear":
        bm_tube(k["gold:0.15:0.55"], [s0, s1], [0.03 * u, 0.034 * u], n=6)
        bm_cyl(k["gold:0.05:0.4"], 0.05 * u, 0.04 * u, 0.08 * u, s1 + d * 0.0, rot=rot_deg(d), seg=6)
        bm_cyl(k["gold:0.05:0.4"], 0.05 * u, 0.035 * u, 0.06 * u, s0 + d * 0.03 * u, rot=rot_deg(d), seg=6)
        for sg in (1, -1):              # the socket's wings
            bm_beam(k["gold:0.05:0.4"], s1 + side * (sg * 0.03 * u), s1 + side * (sg * 0.13 * u) - d * 0.06 * u, 0.03 * u, 0.025 * u, w1=0.0, h1=0.012 * u, up=tuple(d))
        bm_beam(k[glow], s1 + d * 0.02 * u, s1 + d * bl * 0.4 * u, bw * 0.5 * u, 0.035 * u, w1=bw * u, h1=0.04 * u, up=tuple(side))
        bm_beam(k[glow], s1 + d * bl * 0.4 * u, s1 + d * bl * u, bw * u, 0.04 * u, w1=0.0, h1=0.008 * u, up=tuple(side))
        bm_beam(k[glow], s1 + d * 0.02 * u, s1 + d * bl * 0.4 * u, 0.025 * u, bw * 0.3 * u, w1=0.025 * u, h1=bw * 0.5 * u, up=tuple(side))
    else:
        bm_tube(k["wood_dark:0.3:0.7"], [s0, s0 + d * (s1 - s0).length * 0.78], [0.028 * u, 0.028 * u], n=6)
        bm_ellipsoid(k["gold:0.05:0.4"], s0, (0.05 * u, 0.05 * u, 0.05 * u), u=7, v=5)
        bm_beam(k["gold:0.05:0.45"], s1 - side * 0.2 * u, s1 + side * 0.2 * u, 0.06 * u, 0.045 * u, up=tuple(d))
        for sg in (1, -1):
            bm_beam(k["gold:0.05:0.45"], s1 + side * (sg * 0.19 * u), s1 + side * (sg * 0.26 * u) + d * 0.1 * u, 0.045 * u, 0.04 * u, w1=0.0, h1=0.02 * u, up=tuple(d))
        bm_beam(k[glow], s1 + d * 0.0, s1 + d * bl * 0.72 * u, bw * u, 0.035 * u, w1=bw * 0.9 * u, h1=0.03 * u, up=tuple(side))
        bm_beam(k[glow], s1 + d * bl * 0.72 * u, s1 + d * bl * u, bw * 0.9 * u, 0.03 * u, w1=0.0, h1=0.008 * u, up=tuple(side))
        bm_beam(k[glow], s1 + d * 0.0, s1 + d * bl * 0.7 * u, 0.02 * u, bw * 0.25 * u, w1=0.02 * u, h1=bw * 0.45 * u, up=tuple(side))
    for o in k.emit("Angel_Weapon", col, rig=arm, bone="weapon"):
        pass
    rs = bone_world(arm, "upperarm.r")
    m = head.matrix_world.inverted() @ (rs + Vector(muzzle_off))
    empty("Muzzle", col, head, tuple(m), 0.25, "SPHERE")
    return arm


def angel_anims(arm, idle_clip, fire_clip, idle_len=60, fire_len=24, fire_start=0.0, fire_speed=1.0, hide=(3, 14, 22),
                beat=1.0, bob=0.06, down=28.0, flap=14.0):
    """idle: the pack clip looping, a slow wing beat (flap degrees), a gentle bob, the halo turning. fire: the pack
    clip (from fire_start, fire_speed of it), a hard wing beat (down: the wind-up's downstroke), and the weapon hidden
    between hide[0] and hide[1], growing back by hide[2] (hide = None keeps it)."""
    clips = load_clips([idle_clip, fire_clip])
    k = arm.matrix_world.to_scale().x
    fwd = (arm.matrix_world.inverted().to_3x3() @ Vector((0, 1, 0))).normalized()
    upa = (arm.matrix_world.inverted().to_3x3() @ Vector((0, 0, 1))).normalized()
    idle = sample_clip(arm, clips[idle_clip], idle_len + 1, loop=True)
    fire = sample_clip(arm, clips[fire_clip], fire_len + 1, loop=False, start=fire_start, speed=fire_speed)

    def blend(a, b, w):                 # pose a eased toward pose b (w 0..1)
        out = {}
        for bn, (la, ra, sa) in a.items():
            lb, rb, sb = b.get(bn, (la, ra, sa))
            if ra.dot(rb) < 0:
                rb = -rb
            out[bn] = (la.lerp(lb, w), ra.slerp(rb, w), sa.lerp(sb, w))
        return out
    ease_in, ease_out = 2, 6            # fire starts and ends on the idle's first pose
    for f in range(len(fire)):
        w = max(1.0 - f / ease_in, (f - (len(fire) - 1 - ease_out)) / ease_out, 0.0)
        if w > 0.0:
            fire[f] = blend(fire[f], idle[0], smooth(min(w, 1.0)))

    def wings(pb, flap, bend, spread=0.0):
        for s, sg in (("R", -1), ("L", 1)):
            q1 = arm_space_quat(pb["wing.%s.1" % s], tuple(fwd), sg * flap) @ arm_space_quat(pb["wing.%s.1" % s], tuple(upa), -sg * spread)
            pb["wing.%s.1" % s].rotation_quaternion = q1
            pb["wing.%s.2" % s].rotation_quaternion = arm_space_quat(pb["wing.%s.2" % s], tuple(fwd), sg * bend)

    def idle_extra(f, pb):
        t = f / idle_len
        ph = 2 * math.pi * t
        wings(pb, flap * math.sin(ph), flap * 0.7 * math.sin(ph - 0.9))
        pb["root"].location = pb["root"].location + arm_space_loc(pb["root"], tuple(upa * (bob / k) * math.sin(ph)))
        pb["halo"].rotation_quaternion = arm_space_quat(pb["halo"], tuple(upa), 180 * t)

    def fire_extra(f, pb):
        t = f / fire_len
        b = beat * (-down * smooth(f / 4.0) + (down + 20) * smooth((f - 4) / 6.0) - 20 * smooth((f - 10) / 12.0))
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
