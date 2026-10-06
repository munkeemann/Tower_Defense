"""Builds the Dire Bear (footprint "pair": [0,0] front, [0,1] back), a Verdant creature tower: a war bear that charges
out of its den, mauls its prey where it stands, and trots home (GameData.STRIKES "lunge").

    python tools/blender/build.py dire_bear --out <preview dir>

Back cell: the den, a cave of heaped boulders under a turf roof, with a carved totem flying the team's colors, gnawed
bones and a clawed log. Front cell: the bear's trampled bed of earth and straw (what's left when it's out hunting),
and the bear itself: the Head, so the game can send it across the map. One lofted body, soft-skinned to its spine,
with a saddle cloth in the team's color, a spiked collar and glowing runes on its shoulders.
Clips: idle (breathes, sniffs, looks about), run (a gallop, looped while it charges or trots home), fire (rears, roars
and swipes down: the blow lands 0.2 s in).
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, Quaternion, Euler

TID = "dire_bear"
CELLS = [(0, 0), (0, 1)]
MID = footprint_mid(CELLS)
FRONT = hex_to_world(0, 0, MID)
BACK = hex_to_world(0, 1, MID)
TOP = 0.34
RUNE = (0.3, 1.0, 0.45)
BS = 1.18               # bear scale (laid out at 1.0)
HOME = Vector((FRONT.x, FRONT.y - 0.18, 0))

# the body's sections along its spine: (y, middle height, half width, half height)
BODY = [(-0.72, 0.60, 0.17, 0.18), (-0.58, 0.62, 0.33, 0.31), (-0.34, 0.63, 0.40, 0.37), (-0.06, 0.61, 0.39, 0.35),
        (0.20, 0.66, 0.42, 0.40), (0.37, 0.75, 0.38, 0.42), (0.52, 0.77, 0.27, 0.30)]
SKULL = [(0.42, 0.80, 0.21, 0.21), (0.58, 0.84, 0.27, 0.25), (0.73, 0.82, 0.25, 0.22), (0.83, 0.76, 0.16, 0.14),
         (0.97, 0.73, 0.12, 0.10), (1.05, 0.72, 0.085, 0.07)]


def _sections(rows, n=8, power=2.5, grow=0.0):
    return [oval((0, y, z), (1, 0, 0), (0, 0, 1), rx + grow, rz + grow, n, power=power, phase=0.5) for y, z, rx, rz in rows]


def _crescent(y, z, rx, rz, a0, a1, th, n=6):
    """A closed cross-section hugging the top of a body section from angle a0 to a1 (degrees, 90 = straight up)."""
    out, inn = [], []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        out.append(Vector((math.cos(a) * (rx + th), y, z + math.sin(a) * (rz + th))))
        inn.append(Vector((math.cos(a) * (rx - 0.01), y, z + math.sin(a) * (rz - 0.01))))
    return out + list(reversed(inn))


def _body_at(y):
    """The body's section (z, rx, rz) at spine position y."""
    for a, b in zip(BODY, BODY[1:]):
        if a[0] <= y <= b[0]:
            t = (y - a[0]) / (b[0] - a[0])
            return tuple(a[i] + (b[i] - a[i]) * t for i in (1, 2, 3))
    return BODY[-1][1:]


def build_base():
    col = collection("Dire_bear")
    root = empty("Dire_bear", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP, turf=True)
    rnd = random.Random(19)
    B = BACK
    k = Kit()
    # ---- the den: a horseshoe of boulders open to the front, a slab roof, turf and ferns on top
    for i, a in enumerate((205, 250, 290, 335, 20, 160)):
        r = 0.62 if i < 4 else 0.7
        p = B + Vector((math.cos(math.radians(a)) * r, math.sin(math.radians(a)) * r - 0.05, 0))
        bm_boulder(k["stone:0.15:0.9"], rnd, (p.x, p.y, T - 0.03), rnd.uniform(0.34, 0.46), squash=(1, 1, 1.25), n=13)
    for dx, dy, r in ((-0.52, 0.42, 0.26), (0.55, 0.4, 0.24), (0.0, -0.92, 0.3), (-0.8, -0.3, 0.2)):
        bm_boulder(k["stone:0.25:0.95"], rnd, (B.x + dx, B.y + dy, T - 0.02), r, n=10)
    bm_boulder(k["stone:0.1:0.75"], rnd, (B.x, B.y - 0.12, T + 0.6), 0.8, squash=(1.05, 0.95, 0.6), n=15, sink=0.0)
    bm_boulder(k["stone:0.1:0.7"], rnd, (B.x + 0.3, B.y - 0.42, T + 1.0), 0.34, squash=(1, 1, 0.8), n=11, sink=0.1)
    bm_boulder(k["stone:0.1:0.7"], rnd, (B.x - 0.42, B.y - 0.05, T + 0.95), 0.26, squash=(1, 1, 0.8), n=10, sink=0.1)
    k.emit("Den", col, root, vary=0.07, seed=3)
    bm = bmesh.new()
    bm_blob(bm, rnd, (B.x - 0.02, B.y - 0.08, T + 1.36), 0.4, squash=(1.0, 0.9, 0.32), jitter=0.1, sub=2)
    o = paint_ground(mesh_obj("Den_Turf", bm, col, root))
    o["ground"] = True
    bm_ellipsoid(k["black:0.2:0.6"], (B.x, B.y + 0.2, T + 0.3), (0.36, 0.3, 0.36), u=8, v=5)
    k.emit("Den_Mouth", col, root)
    for i, (rel, dx, dy, dz, sc, rot) in enumerate((("forest/Bush_2_B_Color1", 0.08, -0.2, 1.42, 0.26, 40),
                                                    ("forest/Grass_2_A_Color1", -0.18, 0.02, 1.42, 0.45, 10),
                                                    ("forest/Bush_1_C_Color1", -0.86, 0.15, 0.0, 0.3, 200),
                                                    ("forest/Grass_1_B_Color1", 0.84, -0.5, 0.0, 0.5, 100))):
        kk_import(rel, col, root, (B.x + dx, B.y + dy, T - 0.02 + dz), rot, sc, name="Den_Plant_%d" % i)
    # ---- a carved totem: stacked blocks, a bear's head on top, bands and a pennant in the team's color
    tp = B + Vector((-0.74, 0.62, 0))
    for i, (w, h, sw) in enumerate(((0.3, 0.34, "wood"), (0.27, 0.3, "wood_red"), (0.25, 0.3, "wood"))):
        z = T + sum(x[1] for x in ((0.3, 0.34), (0.27, 0.3), (0.25, 0.3))[:i])
        bm_box(k[sw + ":0.2:0.85"], (w, w, h), (tp.x, tp.y, z + h / 2), (0, 0, 12 * i))
        bm_box(k["wood_dark"], (w + 0.03, 0.05, 0.05), (tp.x, tp.y + w * 0.5, z + h * 0.62), (0, 0, 12 * i))     # brow
        for sx in (-1, 1):
            bm_box(k["glow:%s,%s,%s,0.7" % RUNE], (0.05, 0.03, 0.05), (tp.x + sx * w * 0.24, tp.y + w * 0.5 + 0.005, z + h * 0.45), (0, 0, 12 * i))
    zt = T + 0.94
    bm_ellipsoid(k["wood:0.2:0.8"], (tp.x, tp.y, zt + 0.14), (0.17, 0.17, 0.15), u=8, v=5)
    bm_ellipsoid(k["wood:0.3:0.8"], (tp.x, tp.y + 0.15, zt + 0.1), (0.09, 0.1, 0.07), u=6, v=4)
    for sx in (-1, 1):
        bm_cyl(k["wood_red"], 0.055, 0.055, 0.04, (tp.x + sx * 0.12, tp.y, zt + 0.28), rot=(90, 0, 0), seg=6)
    for z in (0.34, 0.64):
        bm_box(k["team!:0.1:0.5"], (0.34, 0.34, 0.05), (tp.x, tp.y, T + z))
    k.emit("Totem", col, root, bevel=0.012)
    # ---- a clawed log, gnawed bones, and the bear's bed of trampled earth and straw on the front cell
    bm_tube(k["wood_red:0.3:0.8"], [(B.x + 0.45, B.y + 0.82, T + 0.13), (B.x + 0.9, B.y + 0.38, T + 0.13)], 0.14, n=8)
    bm_tube(k["sand:0.3:0.6"], [(B.x + 0.445, B.y + 0.825, T + 0.13), (B.x + 0.46, B.y + 0.81, T + 0.13)], 0.105, n=8)
    for i in range(3):
        c = Vector((B.x + 0.6 + i * 0.07, B.y + 0.66 - i * 0.07, T + 0.262))
        bm_box(k["black:0.3:0.6"], (0.025, 0.2, 0.012), tuple(c), (0, 0, -20))
    k.emit("Log", col, root)
    bm_cyl(k["wood_red:0.55:0.9"], 0.82, 0.9, 0.05, (HOME.x, HOME.y, T + 0.02), seg=9)
    k.emit("Bed", col, root)
    bm = k["sand:0.25:0.6"]
    for i in range(26):
        a, r = rnd.uniform(0, 6.283), rnd.uniform(0.15, 0.82)
        p = HOME + Vector((math.cos(a) * r, math.sin(a) * r * 0.95, 0))
        bm_box(bm, (rnd.uniform(0.22, 0.36), 0.035, 0.02), (p.x, p.y, T + 0.055 + rnd.uniform(0, 0.012)), (0, rnd.uniform(-6, 6), rnd.uniform(0, 180)))
    k.emit("Bed_Straw", col, root, vary=0.1)
    for i, (rel, loc, sc) in enumerate((("halloween/bone_A", (B.x + 0.22, B.y + 0.6, T), 0.55), ("halloween/bone_B", (HOME.x - 0.72, HOME.y - 0.5, T + 0.04), 0.5),
                                        ("halloween/ribcage", (B.x - 0.22, B.y + 0.74, T), 0.32), ("halloween/skull", (HOME.x + 0.74, HOME.y - 0.42, T + 0.04), 0.2),
                                        ("forest/Bush_1_C_Color1", (FRONT.x + 0.82, FRONT.y + 0.5, T - 0.02), 0.3),
                                        ("forest/Grass_1_B_Color1", (FRONT.x - 0.8, FRONT.y + 0.52, T - 0.02), 0.5),
                                        ("props/Mushroom", (B.x + 0.92, B.y - 0.1, T), 0.5))):
        kk_import(rel, col, root, loc, rnd.uniform(0, 360), sc, name="Prop_KK_%d" % i)
    empty("Head", col, root, (HOME.x, HOME.y, T + 0.04), 0.5, "SINGLE_ARROW")
    return root


# ---- the bear, in the head's space (+Y forward), laid out at 1.0
LEGS = {  # name: (shoulder / hip, elbow / knee, wrist / ankle), then the paw sits in front of the last
    "FL": ((-0.25, 0.30, 0.60), (-0.27, 0.36, 0.32), (-0.27, 0.36, 0.11)),
    "FR": ((0.25, 0.30, 0.60), (0.27, 0.36, 0.32), (0.27, 0.36, 0.11)),
    "BL": ((-0.25, -0.38, 0.58), (-0.28, -0.30, 0.33), (-0.28, -0.44, 0.11)),
    "BR": ((0.25, -0.38, 0.58), (0.28, -0.30, 0.33), (0.28, -0.44, 0.11)),
}
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "hips": ((0, -0.5, 0.62), (0, -0.08, 0.62), "root"),
    "chest": ((0, -0.08, 0.62), (0, 0.36, 0.72), "hips"),
    "neck": ((0, 0.36, 0.76), (0, 0.52, 0.8), "chest"),
    "head": ((0, 0.52, 0.8), (0, 0.9, 0.76), "neck"),
    "jaw": ((0, 0.7, 0.68), (0, 0.98, 0.65), "head"),
}
for _n, (_a, _b, _c) in LEGS.items():
    BONES["leg.%s.1" % _n] = (_a, _b, "chest" if _n[0] == "F" else "hips")
    BONES["leg.%s.2" % _n] = (_b, (_c[0], _c[1], 0.03), "leg.%s.1" % _n)


def build_head():
    col = collection("Dire_bear")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES, scale=BS)
    k = Kit()
    S = BS
    # ---- body: one loft from rump to neck, soft-skinned along the spine; the belly is paler
    bm_loft(k["wood_red:0.12:0.82"], _sections(BODY))
    bm_blob(k["wood_red:0.3:0.8"], random.Random(2), (0, -0.76, 0.72), 0.09, jitter=0.05)                 # tail
    body = k.emit("Head_Body", col, rig=rig, bones=["hips", "chest", "neck"], scale=S)[0]
    paint_faces(body, "wood", lambda c, n: n.z < -0.55, lo=0.45, hi=0.8)
    # ---- saddle cloth in the team's color with gold trim, a girth strap, a spiked collar
    cloth = [_crescent(y, *_body_at(y)[:1], *_body_at(y)[1:], 28, 152, 0.022) for y in (-0.3, -0.06, 0.18)]
    bm_loft(k["team!:0.12:0.6"], cloth)
    for y in (-0.33, 0.19):
        z, rx, rz = _body_at(y)
        bm_loft(k["gold:0.1:0.5"], [_crescent(y + d, z, rx, rz, 26, 154, 0.032) for d in (0.0, 0.035)])
    z, rx, rz = _body_at(-0.06)
    bm_loft(k["wood_dark:0.3:0.7"], [oval((0, -0.06 + d, z), (1, 0, 0), (0, 0, 1), rx + 0.012, rz + 0.012, 8, power=2.5, phase=0.5) for d in (-0.04, 0.04)],
            cap0=False, cap1=False)
    k.emit("Head_Cloth", col, rig=rig, bones=["hips", "chest"], scale=S)
    z, rx, rz = _body_at(0.47)
    bm_loft(k["wood_dark:0.2:0.6"], [oval((0, 0.47 + d, z), (1, 0, 0), (0, 0, 1), rx + 0.03, rz + 0.03, 8, power=2.3, phase=0.5) for d in (-0.045, 0.045)])
    for i in range(6):
        a = math.radians(20 + 28 * i)
        p = Vector((math.cos(a) * (rx + 0.03), 0.47, z + math.sin(a) * (rz + 0.03)))
        bm_crystal(k["iron:0.1:0.5"], p, p + Vector((math.cos(a), 0, math.sin(a))) * 0.11, 0.035, n=4, shoulder=0.2)
    k.emit("Head_Collar", col, rig=rig, bone="neck", scale=S)
    # runes glowing on the shoulder hump
    for sx in (-1, 1):
        for dy, dz, s in ((0.3, 0.02, 0.07), (0.2, -0.08, 0.045)):
            bm_box(k["glow:%s,%s,%s,0.7" % RUNE], (0.02, s, s), (sx * 0.365, dy, 0.9 + dz), (45, 0, 22 * sx))
    k.emit("Head_Runes", col, rig=rig, bone="chest", scale=S)
    # ---- head: skull to snout in one loft, pale muzzle, ears, brows, eyes, nose, fangs
    bm_loft(k["wood_red:0.1:0.7"], _sections(SKULL, power=2.3))
    for sx in (-1, 1):
        bm_cyl(k["wood_red:0.1:0.6"], 0.085, 0.075, 0.06, (sx * 0.19, 0.55, 1.06), rot=(78, 0, sx * 16), seg=7)
    skull = k.emit("Head_Skull", col, rig=rig, bone="head", scale=S)[0]
    paint_faces(skull, "sand", lambda c, n: c.y > 0.8 * S, lo=0.25, hi=0.7)
    for sx in (-1, 1):
        bm_cyl(k["salmon:0.5:0.8"], 0.052, 0.045, 0.02, (sx * 0.19, 0.585, 1.065), rot=(78, 0, sx * 16), seg=7)     # inner ear
        bm_box(k["wood_dark:0.3:0.7"], (0.15, 0.07, 0.045), (sx * 0.13, 0.79, 0.965), (18, sx * 24, 0))             # brow
        bm_ellipsoid(k["black:0.2:0.5"], (sx * 0.135, 0.815, 0.905), (0.036, 0.03, 0.036), u=6, v=4)
        bm_cyl(k["cream:0.05:0.3"], 0.026, 0.0, 0.085, (sx * 0.07, 0.99, 0.665), rot=(180, 0, 0), seg=5)             # upper fangs
    bm_ellipsoid(k["black:0.3:0.6"], (0, 1.055, 0.75), (0.055, 0.04, 0.042), u=6, v=4)
    k.emit("Head_Face", col, rig=rig, bone="head", scale=S)
    jaw = [(0.70, 0.665, 0.14, 0.05), (0.86, 0.655, 0.115, 0.045), (0.99, 0.65, 0.085, 0.035)]
    bm_loft(k["wood:0.4:0.8"], _sections(jaw, n=6, power=2.6))
    for sx in (-1, 1):
        bm_cyl(k["cream:0.05:0.3"], 0.022, 0.0, 0.07, (sx * 0.062, 0.955, 0.705), seg=5)                             # lower fangs
    bm_box(k["red:0.3:0.6"], (0.15, 0.24, 0.012), (0, 0.84, 0.701))                                                # tongue
    k.emit("Head_Jaw", col, rig=rig, bone="jaw", scale=S)
    # ---- legs: a tapering tube each, bending at the elbow / knee; paws with claws
    for name, (a, b, c) in LEGS.items():
        front = name[0] == "F"
        bm_tube(k["wood_red:0.25:0.9"], [(a[0], a[1], a[2] + 0.08), a, b, c, (c[0], c[1], 0.06)],
                [0.15, 0.2 if front else 0.23, 0.155 if front else 0.15, 0.125, 0.12], n=7)
        k.emit("Head_Leg" + name, col, rig=rig, bones=["leg.%s.1" % name, "leg.%s.2" % name], scale=S)
        y0 = c[1]
        paw = [(y0 - 0.14, 0.075, 0.125, 0.07), (y0 + 0.02, 0.085, 0.155, 0.085), (y0 + 0.2, 0.075, 0.15, 0.075), (y0 + 0.27, 0.06, 0.11, 0.05)]
        bm_loft(k["wood_red:0.5:0.95"], [oval((c[0], y, z), (1, 0, 0), (0, 0, 1), rx, rz, 6, power=2.8, phase=0.5) for y, z, rx, rz in paw])
        for i in range(4):
            p = Vector((c[0] + (i - 1.5) * 0.068, y0 + 0.26, 0.05))
            bm_crystal(k["cream:0.05:0.35"], p, p + Vector((0, 0.11, -0.035)), 0.026, n=4, shoulder=0.25)
        k.emit("Head_Paw" + name, col, rig=rig, bone="leg.%s.2" % name, scale=S)
    empty("Muzzle", col, head, (0, 1.05 * S, 0.75 * S), 0.2, "SPHERE")
    return rig


IDLE_LEN = 72
RUN_LEN = 14
FIRE_LEN = 22


def pose(rig, breathe=0.0, look=0.0, sniff=0.0, rear=0.0, swipe=0.0, roar=0.0, lunge=0.0, gallop=None):
    """gallop: a phase 0..1 of the run cycle (None: standing)."""
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    pb["hips"].rotation_quaternion = q(pb["hips"], (1, 0, 0), rear * 34)
    pb["hips"].location = arm_space_loc(pb["hips"], (0, lunge * 0.16 + rear * 0.05, 0))
    pb["chest"].scale = (1 + breathe, 1 + breathe, 1 + breathe)
    pb["chest"].rotation_quaternion = q(pb["chest"], (1, 0, 0), rear * 12 - lunge * 10)
    pb["neck"].rotation_quaternion = q(pb["neck"], (0, 0, 1), look * 0.5) @ q(pb["neck"], (1, 0, 0), -rear * 28 + sniff)
    pb["head"].rotation_quaternion = q(pb["head"], (0, 0, 1), look * 0.5) @ q(pb["head"], (1, 0, 0), roar * 16)
    pb["jaw"].rotation_quaternion = q(pb["jaw"], (1, 0, 0), -roar * 34)
    for s in ("L", "R"):
        pb["leg.F%s.1" % s].rotation_quaternion = q(pb["leg.F%s.1" % s], (1, 0, 0), rear * 46 + swipe * (62 if s == "R" else 30))
        pb["leg.F%s.2" % s].rotation_quaternion = q(pb["leg.F%s.2" % s], (1, 0, 0), -rear * 30 - max(0.0, swipe) * (30 if s == "R" else 12))
        pb["leg.B%s.1" % s].rotation_quaternion = q(pb["leg.B%s.1" % s], (1, 0, 0), -rear * 30)
    if gallop is not None:
        ph = 2 * math.pi * gallop
        # front legs reach while the hind legs gather, then the back drives through: a rocking gallop
        pb["hips"].rotation_quaternion = q(pb["hips"], (1, 0, 0), 9 * math.sin(ph + 0.4))
        pb["hips"].location = arm_space_loc(pb["hips"], (0, 0, 0.09 * abs(math.sin(ph)) + 0.02))
        pb["chest"].rotation_quaternion = q(pb["chest"], (1, 0, 0), -11 * math.sin(ph + 0.4))
        pb["neck"].rotation_quaternion = q(pb["neck"], (1, 0, 0), 8 * math.sin(ph + 0.4) - 6)
        pb["jaw"].rotation_quaternion = q(pb["jaw"], (1, 0, 0), -10)
        for s, off in (("L", 0.0), ("R", 0.5)):
            f = math.sin(ph + off)
            pb["leg.F%s.1" % s].rotation_quaternion = q(pb["leg.F%s.1" % s], (1, 0, 0), 46 * f)
            pb["leg.F%s.2" % s].rotation_quaternion = q(pb["leg.F%s.2" % s], (1, 0, 0), -40 * max(0.0, -math.sin(ph + off - 0.9)))
            b = math.sin(ph + off + math.pi * 0.85)
            pb["leg.B%s.1" % s].rotation_quaternion = q(pb["leg.B%s.1" % s], (1, 0, 0), 42 * b)
            pb["leg.B%s.2" % s].rotation_quaternion = q(pb["leg.B%s.2" % s], (1, 0, 0), 36 * max(0.0, math.sin(ph + off + math.pi * 0.85 - 0.9)))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        ph = 2 * math.pi * f / IDLE_LEN
        pose(rig, breathe=0.022 * math.sin(ph * 2), look=24 * math.sin(ph) * (0.5 + 0.5 * math.sin(ph * 0.5)),
             sniff=7 * max(0.0, math.sin(ph * 3)) ** 4)
        key_pose(rig, f)
    new_action(rig, "run", RUN_LEN)
    for f in range(RUN_LEN + 1):
        pose(rig, gallop=f / RUN_LEN)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        # the blow lands on frame 6 (0.2 s): up on its hind legs, the right paw comes down
        rear = smooth(f / 4.0) * (1 - smooth((f - 6) / 5.0))
        swipe = -0.7 * smooth(f / 3.0) * (1 - smooth((f - 3) / 2.0)) + 1.0 * smooth((f - 4) / 2.0) * (1 - smooth((f - 9) / 9.0))
        roar = smooth(f / 3.0) * (1 - smooth((f - 9) / 8.0))
        lunge = smooth((f - 4) / 2.5) * (1 - smooth((f - 9) / 9.0))
        pose(rig, rear=rear, swipe=swipe, roar=roar, lunge=lunge)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.2, 0.8), "dist": 7.5, "yaw": 148, "pitch": 20, "anim_target": (HOME.x, HOME.y + 0.1, 1.0), "anim_dist": 4.6,
           "frames": [("idle", 0), ("run", 3), ("run", 9), ("fire", 3), ("fire", 6)],
           "extra": [{"yaw": 120, "pitch": 12, "dist": 3.6, "target": (HOME.x, HOME.y + 0.3, 1.0)},
                     {"yaw": 200, "pitch": 24, "dist": 4.4, "target": (BACK.x, BACK.y, 0.9)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
