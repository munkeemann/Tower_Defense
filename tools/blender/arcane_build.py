"""Builds the Arcane Spire (footprint "pair": cells [0,0] front, [0,1] back).

    exec(open(r"<repo>/tools/blender/kk_helpers.py").read())
    exec(open(r"<repo>/tools/blender/arcane_build.py").read())
    build_all()

Front cell: a tapered stone spire with team banners, a crenellated balcony and four slender pillars cradling a
floating arcane crystal inside two gold rune rings (the Head: it turns toward targets, orbs leave from the Muzzle at
the crystal). Back cell: a rune-circle dais with a lectern and spellbook, shelves, candles and crystal clusters, where
the game stands a mage (Crew). Animations: idle (the crystal bobs and turns, rings and orbiting shards wheel round),
fire (the crystal flares, the rings whirl).
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "arcane"
CELLS = [(0, 0), (0, 1)]
MID = footprint_mid(CELLS)
FRONT = hex_to_world(0, 0, MID)
BACK = hex_to_world(0, 1, MID)
TOP = 0.34                  # plinth top
BALCONY = 2.62              # balcony floor (the Head sits here)
CRYSTAL_Z = 0.86            # crystal centre above the balcony
VIOLET = (0.5, 0.2, 1.0)
GLOW = 1.1                  # emission strength: enough to glow without washing out to white


def _octagon(r, z, center, rot=22.5):
    return [Vector((center.x + r * math.cos(math.radians(45 * i + rot)), center.y + r * math.sin(math.radians(45 * i + rot)), z))
            for i in range(8)]


def _taper(bm, center, r0, z0, r1, z1, seg=8, rot=22.5):
    """A tapered prism (closed) around a vertical axis."""
    a = [bm.verts.new(p) for p in _polygon(center, r0, z0, seg, rot)]
    b = [bm.verts.new(p) for p in _polygon(center, r1, z1, seg, rot)]
    bm.faces.new(list(reversed(a)))
    bm.faces.new(b)
    for i in range(seg):
        j = (i + 1) % seg
        bm.faces.new((a[i], a[j], b[j], b[i]))
    return bm


def _polygon(center, r, z, seg, rot):
    return [Vector((center.x + r * math.cos(math.radians(360.0 * i / seg + rot)),
                    center.y + r * math.sin(math.radians(360.0 * i / seg + rot)), z)) for i in range(seg)]


def build_base():
    col = collection("Arcane")
    root = empty("Arcane", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    F = FRONT
    # ---- the spire: footing, tapered shaft, trim bands, balcony with merlons
    bm = bmesh.new(); _taper(bm, F, 0.86, TOP, 0.8, TOP + 0.3)
    paint(mesh_obj("Spire_Footing", bm, col, root), "stone_dark", lo=0.2, hi=0.7)
    bm = bmesh.new(); _taper(bm, F, 0.7, TOP + 0.3, 0.6, BALCONY - 0.12)
    o = paint(mesh_obj("Spire_Shaft", bm, col, root), "stone", lo=0.05, hi=0.75)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new()
    for z, r in ((1.25, 0.69), (1.95, 0.65)):
        _taper(bm, F, r, z - 0.05, r, z + 0.05)
    _taper(bm, F, 0.66, BALCONY - 0.22, 0.86, BALCONY - 0.05)       # corbel flaring out under the balcony
    paint(mesh_obj("Spire_Trim", bm, col, root), "stone_dark", lo=0.3, hi=0.6)
    bm = bmesh.new()
    _taper(bm, F, 0.88, BALCONY - 0.05, 0.88, BALCONY)
    for i in range(8):
        a = math.radians(45 * i + 22.5)
        p = F + Vector((math.cos(a) * 0.8, math.sin(a) * 0.8, 0))
        bm_box(bm, (0.2, 0.16, 0.2), (p.x, p.y, BALCONY + 0.1), (0, 0, 45 * i + 22.5 + 90))
    o = paint(mesh_obj("Spire_Balcony", bm, col, root), "stone", lo=0.1, hi=0.5)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.015; b.segments = 1; b.limit_method = "ANGLE"
    # windows and the door (dark insets on the shaft faces)
    bm = bmesh.new()
    for i, z in ((0, 1.6), (2, 1.6), (4, 1.6), (6, 1.6), (1, 0.95), (5, 0.95)):
        a = math.radians(45 * i + 45)
        r = 0.66 - (z - TOP) * 0.045
        p = F + Vector((math.cos(a) * r, math.sin(a) * r, 0))
        bm_box(bm, (0.16, 0.06, 0.3), (p.x, p.y, z), (0, 0, 45 * i + 45 + 90))
        bm_cyl(bm, 0.08, 0.08, 0.06, (p.x, p.y, z + 0.15), rot=(90, 0, 45 * i + 45 + 90), seg=8)
    paint(mesh_obj("Spire_Windows", bm, col, root), "black", lo=0.3, hi=0.6)
    bm = bmesh.new()
    a = math.radians(270)
    p = F + Vector((0, -0.66, 0))
    bm_box(bm, (0.34, 0.08, 0.56), (p.x, p.y, TOP + 0.58))
    bm_cyl(bm, 0.17, 0.17, 0.08, (p.x, p.y, TOP + 0.86), rot=(90, 0, 0), seg=10)
    paint(mesh_obj("Spire_Door", bm, col, root), "wood_red", lo=0.3, hi=0.7)
    # team banners hanging from the trim band
    bm = bmesh.new()
    for i in (0, 4):
        a = math.radians(45 * i)
        p = F + Vector((math.cos(a) * 0.665, math.sin(a) * 0.665, 0))
        n = Vector((math.cos(a), math.sin(a), 0))
        t = Vector((-n.y, n.x, 0))
        pts = [p + t * 0.17 + Vector((0, 0, 2.2)), p - t * 0.17 + Vector((0, 0, 2.2)), p - t * 0.17 + Vector((0, 0, 1.45)),
               p + Vector((0, 0, 1.3)), p + t * 0.17 + Vector((0, 0, 1.45))]
        vs = [bm.verts.new(v + n * 0.02) for v in pts]
        bm.faces.new(vs)
        bm.faces.new(list(reversed([bm.verts.new(v.co + n * 0.015) for v in vs])))
    paint(mesh_obj("Spire_Banners", bm, col, root), "team", team=True, lo=0.1, hi=0.7)
    # four slender pillars on the balcony with gold caps
    bm = bmesh.new()
    caps = bmesh.new()
    for i in range(4):
        a = math.radians(90 * i + 45)
        p0 = F + Vector((math.cos(a) * 0.62, math.sin(a) * 0.62, BALCONY))
        p1 = F + Vector((math.cos(a) * 0.5, math.sin(a) * 0.5, BALCONY + 1.15))
        bm_beam(bm, p0, p1, 0.09, 0.09, w1=0.06, h1=0.06)
        bm_cyl(caps, 0.06, 0.0, 0.16, tuple(p1 + Vector((0, 0, 0.08))), seg=6)
        bm_cyl(caps, 0.075, 0.075, 0.05, tuple(p1), seg=8)
    o = paint(mesh_obj("Spire_Pillars", bm, col, root), "stone", lo=0.05, hi=0.4)
    paint(mesh_obj("Spire_PillarCaps", caps, col, root), "gold", lo=0.1, hi=0.5)

    # ---- back cell: rune dais, lectern, shelves, candles, crystals
    B = BACK
    bm = bmesh.new(); bm_cyl(bm, 0.86, 0.86, 0.1, (B.x, B.y, TOP + 0.05), seg=16)
    o = paint(mesh_obj("Annex_Dais", bm, col, root), "stone", lo=0.05, hi=0.45)
    b = o.modifiers.new("Bevel", "BEVEL"); b.width = 0.02; b.segments = 1; b.limit_method = "ANGLE"
    bm = bmesh.new(); ring(bm, (B.x, B.y, 0), 0.72, 0.64, TOP + 0.1, TOP + 0.115, seg=24)
    for i in range(6):
        a = math.radians(60 * i + 30)
        p = B + Vector((math.cos(a) * 0.68, math.sin(a) * 0.68, 0))
        bm_box(bm, (0.1, 0.1, 0.012), (p.x, p.y, TOP + 0.112), (0, 0, 60 * i + 45))
    paint(mesh_obj("Annex_Runes", bm, col, root), "team", team=True, lo=0.1, hi=0.4)
    bm = bmesh.new()
    lp = B + Vector((0.0, 0.3, 0))
    bm_box(bm, (0.12, 0.12, 0.62), (lp.x, lp.y, TOP + 0.1 + 0.31))
    bm_box(bm, (0.34, 0.12, 0.04), (lp.x, lp.y, TOP + 0.12))
    bm_box(bm, (0.44, 0.3, 0.05), (lp.x, lp.y, TOP + 0.74), (-25, 0, 0))
    paint(mesh_obj("Annex_Lectern", bm, col, root), "wood_red", lo=0.2, hi=0.7)
    deck = TOP + 0.1
    kk = [
        ("gear/spellbook_open", (lp.x, lp.y - 0.02, TOP + 0.77), 180, 0.45),
        ("dungeon/candle_triple", (0.6, B.y + 0.25, deck), 0, 0.42),
        ("dungeon/candle_triple", (-0.66, B.y + 0.3, deck), 60, 0.36),
    ]
    for i, (rel, loc, rot, sc) in enumerate(kk):
        for o in kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d_%s" % (i, rel.split("/")[1])):
            for c in [o] + list(o.children_recursive):
                if c.type == "MESH":
                    teamify(c)
    # a bookshelf at the back, books in the pack's colors
    bm = bmesh.new()
    shc = B + Vector((-0.28, -0.62, 0))
    bm_box(bm, (0.78, 0.26, 0.05), (shc.x, shc.y, deck + 0.025))
    for z in (0.34, 0.66, 0.96):
        bm_box(bm, (0.78, 0.26, 0.04), (shc.x, shc.y, deck + z))
    for sx in (-1, 1):
        bm_box(bm, (0.05, 0.26, 0.98), (shc.x + sx * 0.37, shc.y, deck + 0.49))
    bm_box(bm, (0.78, 0.03, 0.98), (shc.x, shc.y + 0.115, deck + 0.49))   # back panel north: books face the camera
    o = paint(mesh_obj("Annex_Shelf", bm, col, root), "wood_red", lo=0.25, hi=0.75)
    import random
    rnd = random.Random(5)
    books = {k: bmesh.new() for k in ("red", "blue", "teal", "gold", "wood_dark", "cream")}
    for z in (0.045, 0.36, 0.68):
        x = shc.x - 0.33
        while x < shc.x + 0.3:
            w = rnd.uniform(0.045, 0.08)
            h = rnd.uniform(0.18, 0.26)
            k = rnd.choice(list(books))
            tilt = rnd.uniform(-8, 8) if rnd.random() < 0.25 else 0
            bm_box(books[k], (w - 0.006, 0.17, h), (x + w / 2, shc.y - 0.01, deck + z + h / 2), (0, tilt, 0))
            x += w
    for k, bmk in books.items():
        paint(mesh_obj("Annex_Books_" + k, bmk, col, root), k, lo=0.25, hi=0.6)
    # glowing crystal clusters, and one on a little stone pedestal
    bm = bmesh.new()
    def shard(c, h, r, lean):
        top = bm.verts.new(c + Vector((lean[0], lean[1], h)))
        ms = [bm.verts.new(c + Vector((math.cos(math.radians(72 * k)) * r, math.sin(math.radians(72 * k)) * r, h * 0.12)))
              for k in range(5)]
        base = bm.verts.new(c)
        for k in range(5):
            k2 = (k + 1) % 5
            bm.faces.new((ms[k], ms[k2], top))
            bm.faces.new((ms[k2], ms[k], base))
    for cc, n in ((B + Vector((0.55, -0.45, deck)), 4), (B + Vector((-0.6, -0.05, deck)), 3), (B + Vector((0.12, -0.78, deck)), 2)):
        for k in range(n):
            a = rnd.uniform(0, 6.28)
            d = 0.0 if k == 0 else rnd.uniform(0.07, 0.13)
            c = cc + Vector((math.cos(a) * d, math.sin(a) * d, 0))
            shard(c, rnd.uniform(0.18, 0.34) * (1.25 if k == 0 else 1.0), rnd.uniform(0.045, 0.07),
                  (math.cos(a) * 0.06 * (k > 0), math.sin(a) * 0.06 * (k > 0)))
    o = mesh_obj("Annex_Crystals", bm, col, root)
    o.data.materials.append(glow_mat("arcane_glow", VIOLET, GLOW))
    o.data.uv_layers.new(name="UVMap")
    crew = empty("Crew", col, root, (lp.x, lp.y - 0.42, deck), 0.3, "SINGLE_ARROW")
    crew.rotation_euler = (0, 0, 0)   # faces +Y: the lectern and the spire beyond
    head = empty("Head", col, root, (F.x, F.y, BALCONY), 0.5, "SINGLE_ARROW")
    return root


BONES = {
    "root": ((0, 0, 0), (0, 0, 0.3), None),
    "crystal": ((0, 0, CRYSTAL_Z), (0, 0, CRYSTAL_Z + 0.3), "root"),
    "ring.1": ((0, 0, CRYSTAL_Z), (0.3, 0, CRYSTAL_Z), "root"),
    "ring.2": ((0, 0, CRYSTAL_Z), (0, 0.3, CRYSTAL_Z), "root"),
    "orbit": ((0, 0, CRYSTAL_Z), (0, 0, CRYSTAL_Z - 0.3), "root"),
}
RING1_TILT = (Vector((0.4, 0.0, 1.0)).normalized())
RING2_TILT = (Vector((-0.2, 0.45, 1.0)).normalized())


def _ring_obj(bm, r, th, w, normal, center):
    """A thin band (washer) around `normal` through center."""
    q = Vector((0, 0, 1)).rotation_difference(normal)
    tmp = bmesh.new()
    ring(tmp, (0, 0, 0), r, r - w, -th / 2, th / 2, seg=28)
    bmesh.ops.rotate(tmp, verts=tmp.verts, cent=(0, 0, 0), matrix=q.to_matrix())
    bmesh.ops.translate(tmp, verts=tmp.verts, vec=center)
    me = bpy.data.meshes.new("_tmp")
    tmp.to_mesh(me)
    tmp.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)


def build_head():
    col = collection("Arcane")
    head = bpy.data.objects["Head"]
    for o in [o for o in col.objects if o.name.startswith("Head_")]:
        bpy.data.objects.remove(o, do_unlink=True)
    rig = make_rig(col, head, BONES)
    c = Vector((0, 0, CRYSTAL_Z))
    # the crystal: a tall six-sided bipyramid that glows, with a darker core facet ring
    bm = bmesh.new()
    top = bm.verts.new(c + Vector((0, 0, 0.42)))
    bot = bm.verts.new(c - Vector((0, 0, 0.34)))
    mid = [bm.verts.new(c + Vector((math.cos(math.radians(60 * i)) * 0.21, math.sin(math.radians(60 * i)) * 0.21, 0.02)))
           for i in range(6)]
    for i in range(6):
        j = (i + 1) % 6
        bm.faces.new((mid[i], mid[j], top))
        bm.faces.new((mid[j], mid[i], bot))
    rig_part("Head_Crystal", bm, None, rig, "crystal", col, bevel=0, mat=glow_mat("arcane_glow", VIOLET, GLOW))
    # two gold rune rings, tilted different ways
    bm = bmesh.new(); _ring_obj(bm, 0.5, 0.035, 0.05, RING1_TILT, c)
    rig_part("Head_Ring1", bm, "gold", rig, "ring.1", col, bevel=0, lo=0.1, hi=0.5)
    bm = bmesh.new(); _ring_obj(bm, 0.42, 0.035, 0.045, RING2_TILT, c)
    rig_part("Head_Ring2", bm, "gold", rig, "ring.2", col, bevel=0, lo=0.25, hi=0.6)
    # rune studs on the outer ring (team colored)
    bm = bmesh.new()
    q = Vector((0, 0, 1)).rotation_difference(RING1_TILT)
    for i in range(6):
        a = math.radians(60 * i)
        p = c + q @ Vector((math.cos(a) * 0.5, math.sin(a) * 0.5, 0))
        bm_box(bm, (0.07, 0.07, 0.07), tuple(p), tuple(math.degrees(x) for x in q.to_euler()))
    rig_part("Head_RingRunes", bm, "team", rig, "ring.1", col, team=True, bevel=0, lo=0.1, hi=0.4)
    # three small shards orbiting below the crystal
    bm = bmesh.new()
    for i in range(3):
        a = math.radians(120 * i)
        p = c + Vector((math.cos(a) * 0.62, math.sin(a) * 0.62, -0.25))
        t = bm.verts.new(p + Vector((0, 0, 0.13)))
        bt = bm.verts.new(p - Vector((0, 0, 0.1)))
        ms = [bm.verts.new(p + Vector((math.cos(math.radians(90 * k + 45)) * 0.06, math.sin(math.radians(90 * k + 45)) * 0.06, 0)))
              for k in range(4)]
        for k in range(4):
            kk_ = (k + 1) % 4
            bm.faces.new((ms[k], ms[kk_], t))
            bm.faces.new((ms[kk_], ms[k], bt))
    rig_part("Head_Shards", bm, None, rig, "orbit", col, bevel=0, mat=glow_mat("arcane_glow", VIOLET, GLOW))
    empty("Muzzle", col, head, (0, 0, CRYSTAL_Z), 0.25, "SPHERE")
    return rig


IDLE_LEN = 60
FIRE_LEN = 18


def pose(rig, spin=0.0, bob=0.0, flare=1.0, ring=0.0, orbit=0.0, lift=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["crystal"].rotation_quaternion = arm_space_quat(pb["crystal"], (0, 0, 1), spin)
    pb["crystal"].location = arm_space_loc(pb["crystal"], (0, 0, bob + lift))
    pb["crystal"].scale = (flare, flare, flare)
    pb["ring.1"].rotation_quaternion = arm_space_quat(pb["ring.1"], tuple(RING1_TILT), ring)
    pb["ring.2"].rotation_quaternion = arm_space_quat(pb["ring.2"], tuple(RING2_TILT), -ring * 1.3)
    pb["ring.1"].location = arm_space_loc(pb["ring.1"], (0, 0, lift * 0.6))
    pb["ring.2"].location = arm_space_loc(pb["ring.2"], (0, 0, lift * 0.6))
    pb["orbit"].rotation_quaternion = arm_space_quat(pb["orbit"], (0, 0, 1), orbit)
    pb["orbit"].location = arm_space_loc(pb["orbit"], (0, 0, bob * 0.5))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        pose(rig, spin=360 * t, bob=0.06 * math.sin(2 * math.pi * t), ring=360 * t, orbit=-360 * t)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        t = f / FIRE_LEN
        flare = 1.0 + 0.5 * (smooth(f / 3.0) - smooth((f - 3) / 12.0)) if f > 0 else 1.0
        lift = 0.12 * (smooth(f / 4.0) - smooth((f - 4) / 13.0))
        # whole turns, so the idle picks up exactly where the flare leaves off
        pose(rig, spin=360 * smooth(t), bob=0.0, flare=flare, ring=360 * smooth(t), orbit=-360 * smooth(t), lift=lift)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.2, 1.3), "dist": 9.5, "yaw": 150, "pitch": 24, "anim_target": (0, 1.04, 3.2), "anim_dist": 4.2,
           "frames": [("idle", 0), ("idle", 20), ("fire", 3), ("fire", 9)]}


def build_all():
    build_base()
    build_head()
    build_anims()
