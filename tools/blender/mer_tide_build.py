"""Builds the Tide Spire (footprint "single"), a Tide tower: pulses of tidewater slow everything nearby, and it senses
camouflaged enemies.

    python tools/blender/build.py mer_tide --out <preview dir>

One thing: a giant turret shell standing in a tidal pool. Its whorls wind up, each with a sharp studded shoulder and a
ledge in the team's color, to a claw of coral that holds a great glowing pearl (the Muzzle); the shell's fluted mouth,
its flared lip in the team's color too, opens onto the pool at its foot. The pool fills the hex inside a rim of
sea-worn stones, with coral, tube sponges, barnacles, a starfish, a scallop and three stands of kelp.
It's an aura: nothing turns, so the Rig hangs on the root. idle: the pearl bobs and breathes, ripples run out across
the pool, the kelp sways. fire (every pulse): the pearl dips, flares, and two rings of tidewater surge out from the
shell's foot, over the rim and past the hex's edge; the kelp is pushed flat by them.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "tide_spires_common.py"), encoding="utf-8").read())

TID = "mer_tide"
CELLS = [(0, 0)]
TOP = 0.34
WATER = TOP + 0.075
SH_H = 1.62                      # the shell's height above the water
# each whorl: a round flank swelling to a sharp shoulder, then a ledge stepping in to the seam (the team's band)
PROFILE = [(0.0, 0.0), (0.12, 0.085), (0.46, 0.16), (0.7, 0.235), (0.83, 0.1), (1.0, 0.0)]
SHELL = TurretShell((0.0, 0.06, WATER - 0.02), SH_H, 0.41, turns=4.7, k=0.72, steps=12, profile=PROFILE, lean=(0.09, 0.06),
                    th0=math.radians(-50), sunk=0.75)
PEARL = SHELL.apex + Vector((0, 0, 0.29))
PEARL_GLOW = "glow:0.5,0.88,1.0,0.75"
KELP = [("kelp.A", Vector((-0.74, -0.18, WATER - 0.03)), 1.0, (-0.12, -0.06)),
        ("kelp.B", Vector((0.5, 0.6, WATER - 0.03)), 0.84, (0.1, 0.1)),
        ("kelp.C", Vector((-0.4, 0.66, WATER - 0.03)), 0.66, (-0.1, 0.06))]


def _mouth(k):
    """The shell's mouth: a fluted horn that leaves the lowest whorl along the spiral and opens toward the back (the
    player's side), flaring into a scalloped lip in the team's color round a dark throat."""
    a0 = SHELL.th0
    rad, tan = Vector((math.cos(a0), math.sin(a0), 0)), Vector((math.sin(a0), -math.cos(a0), 0))     # out, and back along the spiral
    ps = SHELL.point(0.0, 0.34)
    ax = (tan * 0.8 + rad * 0.6).normalized()
    path = [ps - ax * 0.3, ps - ax * 0.02 + Vector((0, 0, 0.0)), ps + ax * 0.2 + Vector((0, 0, 0.05))]
    d = (ax + Vector((0, 0, 0.5))).normalized()                 # the horn curls up, to show its lip from above
    side = d.cross(Vector((0, 0, 1))).normalized()
    up = side.cross(d).normalized()
    n = 14

    def ring(c, r, flute=0.93):
        pts = oval(c, side, up, r, r * 1.05, n)
        return [c + (q - c) * (flute if j % 2 else 1.0) for j, q in enumerate(pts)]
    horn = [ring(path[0], 0.16), ring(path[1], 0.2), ring(path[2], 0.235)]
    edge = ring(path[2] + d * 0.12, 0.4, 0.84)                   # the lip's rim, scalloped
    edge2 = ring(path[2] + d * 0.155, 0.385, 0.84)
    throat = [ring(path[2] + d * 0.03, 0.2), ring(path[1], 0.15), ring(path[0], 0.1)]
    bm_loft(k["cream:0.1:0.85"], horn, cap0=True, cap1=False)
    bm_loft(k["team!:0.1:0.7"], [horn[2], edge, edge2], cap0=False, cap1=False)
    for rings, key, cap in (([edge2, throat[0]], "team!:0.1:0.75", False), (throat, "black:0.25:0.75", True)):
        tmp = bmesh.new()                                       # seen from inside: the lip's face, then the dark throat
        bm_loft(tmp, rings, cap0=False, cap1=cap)
        bmesh.ops.reverse_faces(tmp, faces=tmp.faces[:])
        _join(k[key], tmp)
    rot = tuple(math.degrees(a) for a in Vector((0, 0, 1)).rotation_difference((path[1] - path[0]).normalized()).to_euler())
    bm_cyl(k["glow:%s,%s,%s,0.6" % SEA], 0.105, 0.105, 0.02, tuple(path[0].lerp(path[1], 0.35)), rot=rot, seg=8)    # a light deep in the throat
    return path[2] + d * 0.12, d


def build_base():
    col = collection("Mer_tide")
    root = empty("Mer_tide", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    rnd = random.Random(61)
    k = Kit()
    # ---- the pool: a dark bed, the water, a rim of sea-worn stones along the hex
    bm_flat(k["stone_dark:0.55:0.95"], outline(CELLS, 0.17), T + 0.012)
    k.emit("Pool_Bed", col, root)
    bm_flat(k["water"], outline(CELLS, 0.27), WATER)
    k.emit("Pool", col, root)
    keys = ["stone2:0.1:0.8", "stone:0.1:0.8", "stone2:0.2:0.9", "stone_warm:0.15:0.85"]
    rim_stones(lambda: k[rnd.choice(keys)], rnd, along_loop(outline(CELLS, 0.25), 0.31), T - 0.01, r=(0.12, 0.175))
    for i in (0, 2, 4):                                          # bigger rocks on three corners, where there's room
        c = hex_corners(Vector((0, 0, 0)), 0.9)[i]
        bm_boulder(k[rnd.choice(keys)], rnd, (c.x, c.y, T - 0.02), 0.25, squash=(1.1, 1.0, 0.85), n=13)
        bm_boulder(k[rnd.choice(keys)], rnd, (c.x * 0.86 + 0.08, c.y * 0.86 - 0.1, T + 0.2), 0.13, squash=(1.2, 1.0, 0.7), n=10)
    k.emit("Rim", col, root, vary=0.08, seed=4)
    # ---- the spire: one spiral shell, the team's band on each whorl's ledge, studs along the shoulders
    SHELL.build(k, "cream:0.04:0.92", {3: "team!:0.1:0.7", 4: "team!:0.1:0.7"})
    t = 0.2
    while t < 3.5:
        s = SHELL.k ** (t * 0.9)
        a = SHELL.th0 + 2 * math.pi * t
        d = Vector((math.cos(a), math.sin(a), 0.5)).normalized()
        p = SHELL.point(t, 0.7, out=-0.03)
        bm_crystal(k["beige:0.1:0.75"], p - d * 0.04, p + d * 0.17 * s, 0.085 * s, n=5, shoulder=0.3, foot=1.0)
        t += 1.0 / 7.0
    k.emit("Spire", col, root)
    # round windows up the spiral, lit from inside; barnacles on the lower whorls
    for turn, s in ((0.55, 1.0), (1.3, 0.8), (2.1, 0.62), (2.95, 0.48)):
        p, nr = SHELL.point(turn, 0.38), SHELL.normal(turn, 0.38)
        rot = tuple(math.degrees(a) for a in Vector((0, 0, 1)).rotation_difference(nr).to_euler())
        bm_cyl(k["salmon:0.3:0.8"], 0.095 * s, 0.08 * s, 0.05, tuple(p + nr * 0.005), rot=rot, seg=8)
        bm_cyl(k["glow:%s,%s,%s,0.9" % SEA], 0.058 * s, 0.058 * s, 0.02, tuple(p + nr * 0.024), rot=rot, seg=8)
    for turn, u in ((0.3, 0.28), (0.74, 0.5), (0.9, 0.22), (1.55, 0.4), (0.42, 0.55)):
        bm_barnacles(k["stone2:0.1:0.6"], k["black:0.3:0.6"], rnd, SHELL.point(turn, u, out=-0.01), SHELL.normal(turn, u),
                     n=rnd.randint(3, 5), r=0.05)
    k.emit("Spire_Bits", col, root)
    lip, d = _mouth(k)
    k.emit("Mouth", col, root)
    # foam where the shell and its mouth stand in the water
    bm_ring_flat(k["white:0.0:0.3"], (SHELL.base.x, SHELL.base.y, 0), 0.535, 0.44, WATER + 0.004, seg=14, th=0.008)
    k.emit("Foam", col, root)
    # ---- coral, sponges, a starfish and a scallop round the foot
    bm_coral(k["salmon:0.15:0.85"], rnd, (-0.6, -0.56, WATER - 0.05), h=0.72, r=0.075, depth=3, knob=1.5, up=(-0.2, -0.1, 1))
    bm_coral(k["orange:0.1:0.7"], rnd, (0.74, 0.3, WATER - 0.05), h=0.5, r=0.07, depth=2, up=(0.25, 0.1, 1), knob=1.5)
    bm_coral(k["red:0.05:0.5"], rnd, (0.02, 0.82, WATER - 0.05), h=0.5, r=0.065, depth=2, up=(0.1, 0.3, 1), knob=1.5)
    bm_tube_coral(k["sky:0.2:0.8"], k["black:0.3:0.7"], rnd, (-0.82, 0.2, WATER - 0.02), n=4, h=(0.16, 0.34), r=(0.05, 0.075))
    c = hex_corners(Vector((0, 0, 0)), 0.9)[0]
    bm_starfish(k["orange:0.15:0.6"], (c.x - 0.02, c.y + 0.03, T + 0.345), 0.15, yaw=20, normal=(0.1, 0.2, 1))
    bm_scallop(k["cream:0.1:0.7"], (0.62, -0.62, T + 0.16), r=0.17, yaw=140, tilt=42)
    k.emit("Reef", col, root)
    empty("Head", col, root, (0, 0, TOP), 0.5, "SINGLE_ARROW")
    return root


BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "pearl": (tuple(PEARL), tuple(PEARL + Vector((0, 0, 0.2))), "root"),
         "ripple.1": ((0, 0.04, WATER), (0, 0.04, WATER + 0.2), "root"),
         "ripple.2": ((0, 0.04, WATER), (0, 0.04, WATER + 0.2), "root"),
         "surge.1": ((0, 0.04, WATER), (0, 0.04, WATER + 0.2), "root"),
         "surge.2": ((0, 0.04, WATER), (0, 0.04, WATER + 0.2), "root")}
for _n, _b, _h, _l in KELP:
    kelp_bones(BONES, _n, _b, _h, lean=_l)


def build_rig():
    col = collection("Mer_tide")
    root = bpy.data.objects["Mer_tide"]
    head = bpy.data.objects["Head"]
    rig = make_rig(col, root, BONES)
    rnd = random.Random(8)
    k = Kit()
    # ---- the pearl
    bm_ellipsoid(k[PEARL_GLOW], tuple(PEARL), (0.18, 0.18, 0.18), u=10, v=7)
    k.emit("Pearl", col, rig=rig, bone="pearl")
    # ---- the claw of coral that holds it (it doesn't move: the pearl floats inside)
    ap = SHELL.apex
    bm_cyl(k["salmon:0.2:0.8"], 0.1, 0.07, 0.1, (ap.x, ap.y, ap.z + 0.02), seg=7)
    for i in range(4):
        a = math.radians(90 * i + 30)
        o = Vector((math.cos(a), math.sin(a), 0))
        bm_tube(k["salmon:0.1:0.8"], [ap + o * 0.04, ap + o * 0.2 + Vector((0, 0, 0.08)), ap + o * 0.3 + Vector((0, 0, 0.3)),
                                      ap + o * 0.2 + Vector((0, 0, 0.52))], [0.05, 0.045, 0.035, 0.0], n=5)
        bm_ellipsoid(k["salmon:0.1:0.6"], tuple(ap + o * 0.265 + Vector((0, 0, 0.17))), (0.045,) * 3, u=5, v=3)
    k.emit("Claw", col, root)
    # ---- ripples (idle) and the surge rings (fire), each on a bone that grows from the shell's foot
    for i in (1, 2):
        bm_ring_flat(k["white:0.0:0.35"], (0, 0.04, 0), 0.5, 0.47, WATER + 0.003, seg=20, th=0.008)
        k.emit("Ripple%d" % i, col, rig=rig, bone="ripple.%d" % i, tag="no_ao")
        bm_ring_flat(k["glow:0.35,0.78,1.0,0.7"], (0, 0.04, 0), 0.5, 0.42, WATER, seg=24, crest=0.075)
        bm_ring_flat(k["white:0.0:0.2"], (0, 0.04, 0), 0.535, 0.5, WATER, seg=24, crest=0.03)
        k.emit("Surge%d" % i, col, rig=rig, bone="surge.%d" % i, tag="no_ao")
    for (n, b, h, l), sw in zip(KELP, ("teal:0.1:0.75", "grass:0.3:0.9", "teal:0.2:0.8")):
        kelp_part("Kelp_" + n[-1], col, rig, n, rnd, b, h, lean=l, fronds=4, w=0.115, swatch=sw)
    empty("Muzzle", col, head, (PEARL.x, PEARL.y, PEARL.z - TOP), 0.25, "SPHERE")
    return rig


IDLE_LEN = 72
FIRE_LEN = 20
HIDE = (0.02, 0.02, 0.02)


def _ring(pb, name, t, r0, r1, lift=0.0, drop=0.12):
    """A ring's life at t (0..1): it rises out of the water at r0, runs out to r1, and sinks."""
    b = pb[name]
    if t <= 0.0 or t >= 1.0:
        b.scale = HIDE
        b.location = arm_space_loc(b, (0, 0, -drop))
        return
    s = r0 + (r1 - r0) * (1 - (1 - t) ** 1.6)
    up = min(1.0, t * 6.0) * (1.0 - smooth((t - 0.75) / 0.25))
    b.scale = (s, max(0.05, up), s)                 # (the bone points up: its own Y is the height)
    b.location = arm_space_loc(b, (0, 0, -drop * (1 - up) + lift * min(1.0, t * 1.5)))


def pose(rig, t=0.0, bob=0.0, flare=1.0, ripple=(0.0, 0.0), surge=(0.0, 0.0), push=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    pb["pearl"].location = arm_space_loc(pb["pearl"], (0, 0, bob))
    pb["pearl"].scale = (flare, flare, flare)
    for i in (0, 1):
        _ring(pb, "ripple.%d" % (i + 1), ripple[i], 1.1, 1.72, drop=0.05)
        _ring(pb, "surge.%d" % (i + 1), surge[i], 0.9, 2.75, lift=0.2, drop=0.75)
    for i, (n, b, h, l) in enumerate(KELP):
        out = Vector((b.x, b.y, 0)).normalized()
        sway_kelp(rig, n, t + 0.3 * i, push=(-out.y * push, out.x * push))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        pose(rig, t=t, bob=0.045 * math.sin(2 * math.pi * t), flare=1.0 + 0.05 * math.sin(4 * math.pi * t),
             ripple=((t * 2.0) % 1.0, (t * 2.0 + 0.5) % 1.0))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        dip = smooth(f / 2.0) * (1 - smooth((f - 2) / 2.0))
        burst = smooth((f - 2) / 2.0) * (1 - smooth((f - 5) / 12.0))
        pose(rig, t=0.0, bob=-0.05 * dip + 0.1 * burst, flare=1.0 - 0.15 * dip + 0.5 * burst,
             surge=((f - 2) / 14.0, (f - 6) / 13.0), push=26 * smooth((f - 4) / 4.0) * (1 - smooth((f - 9) / 10.0)))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 1.1), "dist": 6.2, "yaw": 150, "pitch": 18, "anim_target": (0, 0, 1.0), "anim_dist": 6.0,
           "frames": [("idle", 0), ("idle", 20), ("fire", 4), ("fire", 9), ("fire", 14)],
           "extra": [{"yaw": 40, "pitch": 14, "dist": 3.2, "target": (0.2, -0.3, 0.75)},
                     {"yaw": 150, "pitch": 10, "dist": 2.6, "target": (PEARL.x, PEARL.y, PEARL.z - 0.2)},
                     {"yaw": 250, "pitch": 30, "dist": 4.2, "target": (0, 0, 0.8)},
                     {"yaw": 0, "pitch": 57, "dist": 4.6, "target": (0, 0, 0.8)}]}


def build_all():
    build_base()
    build_rig()
    build_anims()
