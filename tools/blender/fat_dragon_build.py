"""Builds the Fat Dragon (footprint "arrow5": [0,0] front, [1,0] / [-1,1] the flanks, [0,1] middle, [0,2] back), the
Forge's tier-3 creature: too heavy to move, it lies on its hoard and breathes fire in a straight line where it faces.

    python tools/blender/build.py fat_dragon --out <preview dir>

One gloriously fat red dragon sprawled over all five hexes on the gold it has worn into a bed: a red back (one loft,
soft-skinned over its spine) on a pale belly that bulges out sideways in scutes, a short thick neck laid forward, the
big horned head with its chin on the floor of the front hex between its forepaws, hind legs splayed onto the flank
heaps, two silly little wings standing on its shoulders, a row of plates down its spine and a tail that curls round
the back heap, its spade lying on the gold. Plates, wing skins and spade are the team's color. The hoard is one
surface (hoard(x, y)) over a scorched stone floor: coins everywhere, chests, a crown, goblets, an urn, gems, and the
arms of those who came for it (shields, a sword, a lance still flying its pennant).
It never turns (the game aims it), so the Head is a bare marker at the root and the rig spans the whole beast.
idle: slow heavy breaths, smoke puffing from its nostrils on each one, an eye opening to look at you, the wings
shrugging, the tail tip swishing, the pennant waving. fire: the fire in its belly shows between the scutes as its
chest swells, the head heaves up, the jaw drops and the flame roars out level, wings flaring; then it settles.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "megabeast_common.py"), encoding="utf-8").read())

TID = "fat_dragon"
CELLS = [(0, 0), (1, 0), (-1, 1), (0, 1), (0, 2)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)          # front (0, 1.66): the head between its forepaws
FR = hex_to_world(1, 0, MID)         # right flank (1.8, 0.62)
FL = hex_to_world(-1, 1, MID)        # left flank (-1.8, 0.62)
M = hex_to_world(0, 1, MID)          # middle (0, -0.42): the belly
B = hex_to_world(0, 2, MID)          # back (0, -2.49): the tail's curl
TOP = 0.34
T = TOP
FIRE = "glow:1.0,0.4,0.06,0.95"
HOT = "glow:1.0,0.74,0.2,1.0"
EYE = "glow:1.0,0.8,0.15,1.0"
RED, DARK, PALE, HORN, CLAW = "red:0.12:0.85", "red:0.5:0.96", "tan:0.1:0.75", "cream:0.05:0.75", "stone_dark:0.3:0.9"
TEAM = "team!:0.12:0.72"


# ---- the hoard: one surface over the footprint, so the dragon, its treasure and the coins all sit on the same gold
OUT = outline(CELLS)
HEAPS = [  # x, y, radius x, radius y, height
    (0.0, 0.15, 2.2, 2.35, 0.38),       # the bed the dragon has worn into its gold
    (2.25, 0.75, 0.6, 0.6, 0.40),       # right flank: the chest
    (-2.25, 0.8, 0.62, 0.62, 0.42),     # left flank: arms and the crown
    (0.05, -2.6, 0.66, 0.62, 0.52),     # the back heap, in the tail's curl
]


def edge_dist(x, y):
    """How far inside the footprint's outline (x, y) is (negative: outside it)."""
    best = 9.0
    n = len(OUT)
    for i in range(n):
        a, b = OUT[i], OUT[(i + 1) % n]
        ab = b - a
        t = min(max(((x - a.x) * ab.x + (y - a.y) * ab.y) / ab.length_squared, 0.0), 1.0)
        best = min(best, math.hypot(a.x + ab.x * t - x, a.y + ab.y * t - y))
    return best if inside(OUT, x, y) else -best


def hoard(x, y):
    """The gold's depth over the floor at (x, y)."""
    h = 0.0
    for cx, cy, rx, ry, hh in HEAPS:
        h += hh * math.exp(-(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2))
    return h * smooth((edge_dist(x, y) - 0.2) / 0.42)


def gold_at(x, y, lift=0.0):
    """The point `lift` above the gold (or the bare floor) at (x, y)."""
    return Vector((x, y, T + max(hoard(x, y) - 0.035, 0.03) + lift))


# ---- the dragon. Sections are megabeast's (y, zc, rx, up, dn, pinch); heights here are above the plinth
def _secs(rows):
    return [(r[0], T + r[1]) + tuple(r[2:]) + ((0.0,) if len(r) < 6 else ()) for r in rows]


def _grown(sec, k):
    y, zc, rx, up, dn, pinch = sec
    return (y, zc, rx * k, up * k, dn * k, pinch)


BACK = _secs([(-1.50, 0.50, 0.36, 0.36, 0.30, 0.10), (-1.25, 0.56, 0.60, 0.60, 0.40, 0.20), (-0.90, 0.63, 0.84, 0.86, 0.46, 0.28),
              (-0.50, 0.68, 1.02, 1.02, 0.50, 0.32), (-0.05, 0.70, 1.12, 1.10, 0.52, 0.34), (0.40, 0.72, 1.12, 1.08, 0.52, 0.34),
              (0.80, 0.74, 0.98, 0.96, 0.50, 0.32), (1.10, 0.74, 0.76, 0.78, 0.46, 0.28), (1.32, 0.70, 0.60, 0.62, 0.42, 0.22),
              (1.55, 0.62, 0.52, 0.50, 0.38, 0.18), (1.78, 0.55, 0.46, 0.42, 0.33, 0.14), (1.95, 0.50, 0.38, 0.34, 0.28, 0.10)])
BELLY = _secs([(-1.44, 0.36, 0.34, 0.26, 0.26), (-1.22, 0.40, 0.66, 0.34, 0.30), (-0.90, 0.46, 0.96, 0.40, 0.36),
               (-0.50, 0.50, 1.24, 0.44, 0.40), (-0.05, 0.52, 1.44, 0.46, 0.42), (0.40, 0.52, 1.44, 0.46, 0.42),
               (0.80, 0.52, 1.20, 0.44, 0.42), (1.10, 0.52, 0.86, 0.40, 0.40), (1.32, 0.48, 0.64, 0.34, 0.36),
               (1.55, 0.40, 0.52, 0.28, 0.30), (1.78, 0.33, 0.44, 0.24, 0.24), (1.94, 0.28, 0.36, 0.20, 0.20)])
SKULL = _secs([(1.66, 0.50, 0.38, 0.34, 0.20, 0.10), (1.84, 0.54, 0.56, 0.46, 0.22, 0.20), (2.04, 0.55, 0.55, 0.45, 0.21, 0.28),
               (2.18, 0.49, 0.42, 0.31, 0.16, 0.22), (2.38, 0.46, 0.36, 0.25, 0.14, 0.18), (2.56, 0.46, 0.34, 0.24, 0.14, 0.15),
               (2.68, 0.43, 0.25, 0.17, 0.12, 0.10)])
JAW = _secs([(1.72, 0.22, 0.36, 0.11, 0.13), (1.92, 0.21, 0.46, 0.12, 0.13), (2.18, 0.21, 0.345, 0.11, 0.12),
             (2.42, 0.21, 0.29, 0.10, 0.11), (2.62, 0.22, 0.21, 0.08, 0.10)])
SCUTES = 13
SCUTE_Y = [BELLY[0][0] + (BELLY[-1][0] - BELLY[0][0]) * i / SCUTES for i in range(SCUTES + 1)]

TAIL_XY = [(0.00, -1.38, 0.40), (0.10, -1.72, 0.36), (0.34, -2.08, 0.31), (0.66, -2.46, 0.27), (0.74, -2.86, 0.23), (0.50, -3.16, 0.20),
           (0.12, -3.28, 0.17), (-0.28, -3.20, 0.14), (-0.60, -2.95, 0.12), (-0.76, -2.60, 0.10), (-0.72, -2.26, 0.085)]
TAIL = [gold_at(x, y, r * 0.72) for x, y, r in TAIL_XY]
TAIL[0].z = T + 0.5
TAIL[1].z = max(TAIL[1].z, T + 0.45)
TAIL_R = [r for _, _, r in TAIL_XY]

MOUTH = Vector((0, 2.58, T + 0.33))
NOSE = Vector((0, 2.6, T + 0.72))
EYE_C = Vector((0.41, 2.11, T + 0.7))                 # the right eye (the left mirrors it)
WING_R, WING_W = Vector((0.42, 0.74, T + 1.5)), Vector((0.76, 0.58, T + 2.12))     # the right wing's root and wrist
LANCE = (gold_at(-2.3, 1.0, -0.1), Vector((-2.5, 0.88, T + 2.1)))
FLAG_DIR, FLAG_LEN = (0.2, -1.0, 0.0), 0.78
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "hips": ((0, -1.5, T + 0.52), (0, -1.15, T + 0.56), "root"),
    "belly": ((0, -0.6, T + 0.6), (0, 0.5, T + 0.6), "hips"),          # a leaf: it swells with each breath
    "chest": ((0, 0.6, T + 0.9), (0, 1.25, T + 0.9), "hips"),
    "ribs": ((0, 0.9, T + 0.62), (0, 1.22, T + 0.62), "chest"),        # likewise
    "neck.1": ((0, 1.25, T + 0.68), (0, 1.62, T + 0.58), "chest"),
    "neck.2": ((0, 1.62, T + 0.58), (0, 1.86, T + 0.5), "neck.1"),
    "head": ((0, 1.86, T + 0.5), (0, 2.6, T + 0.46), "neck.2"),
    "jaw": ((0, 1.78, T + 0.3), (0, 2.6, T + 0.22), "head"),
    # the fire under the scutes lies where the belly's bones do (the same weights), and swells a little more
    "heat.b": ((0, -0.6, T + 0.6), (0, 0.5, T + 0.6), "hips"),
    "heat.r": ((0, 0.9, T + 0.62), (0, 1.22, T + 0.62), "chest"),
    "heat.n": ((0, 1.25, T + 0.68), (0, 1.62, T + 0.58), "neck.1"),
    "flame": (tuple(MOUTH), tuple(MOUTH + Vector((0, 0.6, 0))), "head"),
}
for _s, _sx in (("L", -1), ("R", 1)):
    BONES["wing." + _s] = ((WING_R.x * _sx, WING_R.y, WING_R.z), (WING_W.x * _sx, WING_W.y, WING_W.z), "chest")
    BONES["lid." + _s] = ((EYE_C.x * _sx, EYE_C.y, EYE_C.z + 0.112), (EYE_C.x * _sx, EYE_C.y, EYE_C.z - 0.112), "head")
for _i in range(3):
    BONES["smoke.%d" % (_i + 1)] = (tuple(NOSE), tuple(NOSE + Vector((0, 0, 0.25))), "root")
for _i in range(5):
    BONES["tail.%d" % (_i + 1)] = (tuple(TAIL[_i * 2]), tuple(TAIL[_i * 2 + 2]), "hips" if _i == 0 else "tail.%d" % _i)
flag_bones(BONES, "flag", tuple(LANCE[1] - Vector((0, 0, 0.1))), FLAG_DIR, FLAG_LEN, segs=3, parent="root")
TORSO = ["hips", "belly", "ribs", "neck.1", "neck.2"]
HEAT = ["hips", "heat.b", "heat.r", "heat.n", "neck.2"]


def _under(x, y, margin=0.3):
    """Is (x, y) under the dragon's belly (where no one sees the gold)?"""
    return BELLY[0][0] + 0.15 < y < 1.7 and abs(x) < sec_at(BELLY, y)[2] - margin


# ---- small parts
def bm_coin(bm, c, nrm, r, th=0.028, n=6, rot=0.0):
    """A coin lying on c, its face along nrm (no underside)."""
    c, nrm = Vector(c), Vector(nrm).normalized()
    x = nrm.orthogonal().normalized()
    y = nrm.cross(x)
    ring_ = [(x * math.cos(rot + 2 * math.pi * i / n) + y * math.sin(rot + 2 * math.pi * i / n)) * r for i in range(n)]
    top = [bm.verts.new(c + nrm * th + p) for p in ring_]
    bot = [bm.verts.new(c - nrm * 0.01 + p) for p in ring_]
    bm.faces.new(top)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    return bm


def bm_fin(bm, p, fwd, up, length, th, height, lean=0.3):
    """A dorsal plate standing on p: a diamond `length` long (along fwd) and `th` thick, drawn up to a point that leans back."""
    p, f, u = Vector(p), Vector(fwd).normalized(), Vector(up).normalized()
    s = f.cross(u).normalized()
    lo = p - u * 0.06
    r0 = [lo + f * (length * 0.5), lo + s * (th * 0.5), lo - f * (length * 0.5), lo - s * (th * 0.5)]
    c1 = p + u * (height * 0.42) - f * (lean * height * 0.25)
    r1 = [c1 + f * (length * 0.34), c1 + s * (th * 0.42), c1 - f * (length * 0.3), c1 - s * (th * 0.42)]
    return bm_loft(bm, [r0, r1], tip1=p + u * height - f * (lean * height))


def bm_spade(bm, p, d, w, length, th=0.07):
    """The tail's spade: flat, from p along d."""
    p, d = Vector(p), Vector(d).normalized()
    s = d.cross(Vector((0, 0, 1))).normalized()
    u = s.cross(d)

    def rect(c, ww, tt):
        return [c + s * ww + u * tt, c - s * ww + u * tt, c - s * ww - u * tt, c + s * ww - u * tt]
    return bm_loft(bm, [rect(p, 0.05, th * 0.5), rect(p + d * (length * 0.34), w * 0.5, th * 0.5), rect(p + d * (length * 0.52), w * 0.4, th * 0.4)],
                   tip1=p + d * length)


def bm_sheet(bm, pts, th=0.016):
    """A thin fan of triangles from pts[0] through the rest, with both faces (a wing's skin)."""
    pts = [Vector(p) for p in pts]
    n = (pts[1] - pts[0]).cross(pts[-1] - pts[0]).normalized() * (th * 0.5)
    for side in (1, -1):
        vs = [bm.verts.new(p + n * side) for p in pts]
        for i in range(1, len(vs) - 1):
            tri = (vs[0], vs[i], vs[i + 1])
            bm.faces.new(tri if side > 0 else tuple(reversed(tri)))
    return bm


def bm_lathe(bm, prof, n=8):
    """A turned shape standing on the origin: prof = [(z, radius), ...] from the foot up."""
    return bm_loft(bm, [[Vector((math.cos(2 * math.pi * i / n) * r, math.sin(2 * math.pi * i / n) * r, z)) for i in range(n)] for z, r in prof])


def stamp(k, t, loc, rot=(0, 0, 0), scale=1.0):
    """Moves what the kit t holds (built standing on the origin) to loc, turned by rot (degrees), into the kit k."""
    m = Matrix.Translation(Vector(loc)) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4() @ Matrix.Scale(scale, 4)
    for key, bm in t.parts.items():
        bmesh.ops.transform(bm, matrix=m, verts=bm.verts)
        me = bpy.data.meshes.new("stamp")
        bm.to_mesh(me)
        bm.free()
        k[key].from_mesh(me)
        bpy.data.meshes.remove(me)
    t.parts = {}


GOLD = "gold:0.03:0.72"


def t_goblet(t):
    bm_lathe(t[GOLD], [(0.0, 0.085), (0.02, 0.085), (0.045, 0.026), (0.15, 0.024), (0.19, 0.06), (0.31, 0.105)])
    bm_cyl(t["wood_dark:0.5:0.9"], 0.085, 0.085, 0.012, (0, 0, 0.311), seg=8)


def t_urn(t):
    bm_lathe(t[GOLD], [(0.0, 0.08), (0.05, 0.11), (0.2, 0.2), (0.33, 0.17), (0.42, 0.085), (0.48, 0.08), (0.52, 0.13)])
    bm_cyl(t["wood_dark:0.5:0.9"], 0.1, 0.1, 0.012, (0, 0, 0.521), seg=8)
    for a in (0, 180):
        ring(t["gold:0.3:0.9"], (math.cos(math.radians(a)) * 0.17, 0, 0.38), 0.085, 0.05, -0.022, 0.022, seg=6, axis="Y")


def t_crown(t):
    g = t["gold:0.0:0.6"]
    ring(g, (0, 0, 0), 0.21, 0.17, 0.0, 0.11, seg=10)
    for i in range(5):
        a = 2 * math.pi * i / 5
        p = Vector((math.cos(a) * 0.19, math.sin(a) * 0.19, 0.1))
        bm_crystal(g, p, p + Vector((math.cos(a) * 0.035, math.sin(a) * 0.035, 0.19)), 0.055, n=4, shoulder=0.3)
        b = a + math.pi / 5
        bm_box(t["red:0.1:0.5" if i % 2 else "teal:0.1:0.5"], (0.055, 0.055, 0.055), (math.cos(b) * 0.2, math.sin(b) * 0.2, 0.055), (0, 0, math.degrees(b) + 45))


def t_shield(t):
    bm_cyl(t[TEAM], 0.31, 0.28, 0.05, (0, 0, 0.025), seg=10)
    ring(t["gold:0.0:0.6"], (0, 0, 0), 0.34, 0.27, 0.0, 0.07, seg=10)
    bm_ellipsoid(t[GOLD], (0, 0, 0.05), (0.1, 0.1, 0.07), u=6, v=3)


def t_sword(t):
    bm_beam(t["iron:0.0:0.6"], (0, 0, 0), (0, 0, 0.66), 0.1, 0.03, w1=0.11, h1=0.035, up=(0, 1, 0))
    bm_box(t[GOLD], (0.32, 0.07, 0.055), (0, 0, 0.68))
    bm_cyl(t["wood_dark:0.2:0.7"], 0.03, 0.03, 0.17, (0, 0, 0.79), seg=6)
    bm_ellipsoid(t[GOLD], (0, 0, 0.9), (0.055, 0.055, 0.055), u=6, v=3)


def t_stack(t):
    """Coins, stacked (and one fallen off)."""
    for i in range(5):
        bm_cyl(t[GOLD], 0.088, 0.088, 0.034, (0.012 * math.sin(i * 2.4), 0.012 * math.cos(i * 1.7), 0.02 + 0.04 * i), rot=(0, 0, 25 * i), seg=7)
    for i in range(3):
        bm_cyl(t[GOLD], 0.088, 0.088, 0.034, (0.2 + 0.01 * i, 0.03, 0.02 + 0.04 * i), rot=(0, 0, 40 * i), seg=7)
    bm_cyl(t[GOLD], 0.088, 0.088, 0.034, (0.1, -0.17, 0.03), rot=(24, 10, 0), seg=7)


def t_bars(t):
    """Gold bars: three side by side, two laid across them."""
    for x in (-0.15, 0.0, 0.15):
        bm_frustum(t[GOLD], (x, 0), 0.066, 0.17, 0.0, 0.08, top=0.72)
    for y in (-0.08, 0.08):
        bm_frustum(t[GOLD], (0, y), 0.17, 0.066, 0.082, 0.162, top=0.72)


def t_chest(t):
    """An open chest (its front is +Y), full to the brim, the lid thrown back: lined in the team's color."""
    w, d, h = 0.64, 0.44, 0.3
    bm_box(t["wood_red:0.25:0.9"], (w, d, h), (0, 0, h / 2))
    for x in (-w * 0.33, w * 0.33):
        bm_box(t["gold:0.0:0.6"], (0.075, d + 0.03, h + 0.012), (x, 0, h / 2))
    bm_box(t["gold:0.0:0.6"], (0.11, 0.04, 0.13), (0, d / 2 + 0.008, h * 0.72))
    bm_ellipsoid(t[GOLD], (0, 0, h - 0.01), (w * 0.44, d * 0.42, 0.11), u=8, v=4)
    for i, (x, y) in enumerate(((-0.17, 0.05), (0.02, -0.07), (0.18, 0.06), (-0.04, 0.11), (0.1, -0.02))):
        bm_coin(t["gold:0.0:0.5"], (x, y, h + 0.07 - 0.25 * (x * x + y * y)), (x * 0.9, y * 1.2 + 0.1, 1), 0.075, rot=i)
    t["gold:0.0:0.5"].normal_update()
    lid = Kit()                                             # hinged on the back edge, laid out shut (it reaches +Y)
    bm_box(lid["wood_red:0.25:0.9"], (w, d, 0.08), (0, d / 2, 0.04))
    bm_box(lid["wood_red:0.25:0.9"], (w, d * 0.66, 0.06), (0, d / 2, 0.105))
    for x in (-w * 0.33, w * 0.33):
        bm_box(lid["gold:0.0:0.6"], (0.075, d + 0.03, 0.092), (x, d / 2, 0.04))
        bm_box(lid["gold:0.0:0.6"], (0.075, d * 0.66 + 0.03, 0.07), (x, d / 2, 0.105))
    bm_box(lid[TEAM], (w - 0.09, d - 0.08, 0.03), (0, d / 2, -0.004))
    stamp(t, lid, (0, -d / 2, h + 0.005), (104, 0, 0))


def build_base():
    col = collection("Fat_dragon")
    root = empty("Fat_dragon", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(23)
    k = Kit()
    on_floor = lambda x, y: in_footprint(CELLS, x, y, 0.21)
    # ---- the lair's floor: a scorched slab, old paving showing round the gold
    prism(k["stone_dark:0.5:0.9"], outline(CELLS, 0.19), T - 0.03, T + 0.025)
    k.emit("Floor", col, root)
    bm_flagstones(k["stone_dark:0.05:0.6"], rnd, lambda x, y: on_floor(x, y) and hoard(x, y) < 0.1,
                  (-3.1, -3.6, 3.1, 2.8), T + 0.02, size=0.37, gap=0.045, h=0.045, keep=0.92)
    k.emit("Floor_Stones", col, root, vary=0.12, seed=5)
    # ---- the gold: a faceted surface following hoard(), left out under the dragon
    bm = k["gold:0.14:0.82"]
    s = 0.21
    x0, y0 = -3.1, -3.62
    cols, rows = int(6.2 / s) + 2, int(6.4 / (s * 0.866)) + 2
    hs, made = {}, {}
    for j in range(rows):
        for i in range(cols):
            x = x0 + i * s + (s * 0.5 if j % 2 else 0.0) + rnd.uniform(-0.045, 0.045)
            y = y0 + j * s * 0.866 + rnd.uniform(-0.045, 0.045)
            hs[(i, j)] = (x, y, hoard(x, y))

    def vert(key):
        if key not in made:
            x, y, h = hs[key]
            made[key] = bm.verts.new((x, y, T + h - 0.035 + (rnd.uniform(-0.03, 0.035) if h > 0.06 else 0.0)))
        return made[key]
    for j in range(rows - 1):
        for i in range(cols - 1):
            if j % 2 == 0:
                tris = (((i, j), (i + 1, j), (i, j + 1)), ((i + 1, j), (i + 1, j + 1), (i, j + 1)))
            else:
                tris = (((i, j), (i + 1, j), (i + 1, j + 1)), ((i, j), (i + 1, j + 1), (i, j + 1)))
            for tri in tris:
                if max(hs[q][2] for q in tri) < 0.035 or all(_under(hs[q][0], hs[q][1]) for q in tri):
                    continue
                bm.faces.new([vert(q) for q in tri])
    k.emit("Hoard", col, root)
    # ---- treasure, half sunk in it: (builder, x, y, sink, rot)
    t = Kit()
    pieces = [(t_chest, 0.1, -2.64, 0.05, (0, 0, 180)), (t_chest, 2.28, 0.7, 0.05, (0, 0, -150)),
              (t_shield, -2.05, 0.38, -0.03, "lay"), (t_shield, 2.3, 0.22, -0.03, "lay"), (t_sword, -2.6, 0.72, 0.12, (14, -20, 30)),
              (t_crown, -1.82, 1.22, 0.02, (10, 14, 0)), (t_goblet, 2.45, 1.15, 0.03, (0, 0, 0)), (t_goblet, 1.72, 1.36, 0.05, (72, 0, 200)),
              (t_urn, -0.38, -2.3, 0.1, (-16, -14, 0)), (t_stack, -2.5, 0.3, 0.0, (0, 0, 200)), (t_stack, 1.93, -0.02, 0.0, (0, 0, 80)),
              (t_bars, 0.16, -3.0, 0.02, (0, 0, 20)), (t_bars, -2.16, 1.42, 0.02, (8, 0, -30))]
    avoid = []
    for fn, x, y, sink, rot in pieces:
        if rot == "lay":                # lying on the heap's slope, face up
            gx, gy = (hoard(x + 0.2, y) - hoard(x - 0.2, y)) / 0.4, (hoard(x, y + 0.2) - hoard(x, y - 0.2)) / 0.4
            rot = (math.degrees(math.atan(gy)), math.degrees(math.atan(-gx)), 0)
        fn(t)
        stamp(k, t, gold_at(x, y, -sink), rot)
        avoid.append((x, y, 0.36 if fn is t_chest else 0.28))
    k.emit("Treasure", col, root)
    gems = (("teal:0.05:0.5", 1.96, 0.5, 0.1), ("red:0.05:0.5", 2.72, 0.7, 0.09), ("sky:0.05:0.5", -2.4, 1.3, 0.1), ("lime:0.05:0.5", -1.5, 1.52, 0.08),
            ("teal:0.05:0.5", 0.5, -2.3, 0.09), ("red:0.05:0.5", -0.12, -2.02, 0.1), ("red:0.05:0.5", -1.72, -0.12, 0.09))
    for sw, x, y, r in gems:
        bm_blob(k[sw], rnd, gold_at(x, y, r * 0.45), r, squash=(1, 1, 0.8), jitter=0.0, sub=1)
        avoid.append((x, y, r + 0.06))
    k.emit("Gems", col, root)
    # the lance of the last knight to try, still flying his colors
    bm_tube(k["wood:0.2:0.85"], [LANCE[0], LANCE[1]], 0.035, n=6)
    bm_crystal(k["iron:0.0:0.6"], LANCE[1] - Vector((0, 0, 0.02)), LANCE[1] + (LANCE[1] - LANCE[0]).normalized() * 0.3, 0.06, n=4, shoulder=0.3)
    k.emit("Lance", col, root)
    # ---- coins all over it, and a few spilled on the paving
    bm = k["gold:0.02:0.62"]
    n, tries = 0, 0
    while n < 200 and tries < 6000:
        tries += 1
        x, y = rnd.uniform(-3.0, 3.0), rnd.uniform(-3.5, 2.7)
        if edge_dist(x, y) < 0.27 or _under(x, y, 0.08):
            continue
        h = hoard(x, y)
        if h < 0.06 and rnd.random() > 0.1:
            continue
        if any((x - ax) ** 2 + (y - ay) ** 2 < ar * ar for ax, ay, ar in avoid):
            continue
        gx = (hoard(x + 0.05, y) - hoard(x - 0.05, y)) / 0.1
        gy = (hoard(x, y + 0.05) - hoard(x, y - 0.05)) / 0.1
        nrm = Vector((-gx, -gy, 1.0)).normalized() + Vector((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0))
        bm_coin(bm, gold_at(x, y, 0.035 if h > 0.06 else 0.02), nrm, rnd.uniform(0.07, 0.095), rot=rnd.uniform(0, 1))
        n += 1
    k.emit("Hoard_Coins", col, root, vary=0.14, seed=9)
    empty("Head", col, root, (0, 0, 0), 0.5, "SINGLE_ARROW")
    return root


def _paw(k, w, d, r, length):
    """A paw lying on the gold from the wrist w along d, with three claws."""
    d = Vector(d).normalized()
    side = Vector((d.y, -d.x, 0))
    pts = []
    for t_, rr in ((-0.15, 0.85), (0.25, 1.0), (0.65, 0.95), (0.95, 0.6)):
        q = w + d * (length * t_)
        g = gold_at(q.x, q.y, r * rr * 0.72)
        pts.append(Vector((q.x, q.y, w.z if t_ < 0 else g.z)))
    bm_tube(k[RED], pts, [r * 0.85, r, r * 0.95, r * 0.6], n=7, squash=1.25)
    for i in (-1, 0, 1):
        b = pts[-1] + side * (i * r * 0.62) - d * (0.03 + 0.04 * abs(i)) - Vector((0, 0, r * 0.15))
        bm_crystal(k[CLAW], b, b + d * (r * 1.2) + side * (i * 0.04) - Vector((0, 0, r * 0.3)), r * 0.32, n=4, shoulder=0.3)


def build_head():
    col = collection("Fat_dragon")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    rnd = random.Random(7)
    k = Kit()

    def soft(objs, bones, power=7.0):
        for o in objs:
            skin_soft(o, rig, bones, power=power)
        return objs

    # ---- the back: one red loft from rump to neck, rows of darker scales lying on it, the spine's plates
    bm_loft(k[RED], [sec_ring(s, 14) for s in BACK])
    soft(k.emit("Head_Back", col, rig=rig, bones=TORSO), TORSO)
    for row, (a, y0, y1, n) in enumerate(((30, -1.0, 1.0, 8), (52, -1.1, 1.2, 9), (72, -1.0, 1.3, 9))):
        for i in range(n):
            y = y0 + (y1 - y0) * (i + 0.5 * (row % 2)) / n
            for sx in (1, -1):
                p, o = surf(BACK, y, a if sx > 0 else 180 - a)
                q, _ = surf(BACK, y - 0.25, (a - 4) if sx > 0 else (184 - a), 0.03)
                bm_beam(k[DARK], p + o * 0.008, q, 0.3, 0.05, w1=0.15, h1=0.02, up=o)
    for y, h in ((1.62, 0.2), (1.38, 0.27), (1.12, 0.34), (0.8, 0.42), (0.44, 0.48), (0.06, 0.5), (-0.32, 0.47), (-0.68, 0.41), (-1.0, 0.35),
                 (-1.28, 0.3)):
        p, _ = surf(BACK, y, 90, -0.02)
        bm_fin(k[TEAM], p, (0, 1, 0), (0, 0, 1), h * 0.95, h * 0.46, h)
    soft(k.emit("Head_Scales", col, rig=rig, bones=TORSO), TORSO)
    # ---- the belly: pale scutes bulging out from under the back, the fire inside them hidden until it breathes
    rings = []
    for i, y in enumerate(SCUTE_Y):
        if i > 0:
            rings.append(sec_ring(_grown(sec_at(BELLY, y - 0.05), 1.045), 14))
        rings.append(sec_ring(_grown(sec_at(BELLY, y), 0.985), 14))
        if i < SCUTES:
            rings.append(sec_ring(_grown(sec_at(BELLY, y + 0.05), 1.045), 14))
    bm_loft(k[PALE], rings)
    soft(k.emit("Head_Belly", col, rig=rig, bones=TORSO), TORSO)
    bm_loft(k[HOT], [sec_ring(_grown(sec_at(BELLY, y), 0.962), 14) for y in SCUTE_Y if y > -0.75], cap0=False, cap1=False)
    soft(k.emit("Head_Heat", col, rig=rig, bones=HEAT), HEAT)
    # ---- legs (planted: they stay put while the body breathes): forepaws beside the chin, hind feet up on the heaps
    for s, sx in (("L", -1), ("R", 1)):
        el = gold_at(sx * 1.36, 1.26, 0.27 * 0.8)
        wr = gold_at(sx * 0.94, 1.70, 0.2 * 0.85)
        bm_tube(k[RED], [(sx * 0.55, 0.9, T + 0.8), (sx * 0.92, 1.0, T + 0.7), el, wr], [0.3, 0.34, 0.27, 0.2], n=8)
        _paw(k, wr, (-sx * 0.18, 0.36, 0), 0.19, 0.42)
        kn = gold_at(sx * 1.42, -0.06, 0.34 * 0.8)
        an = gold_at(sx * 1.66, 0.42, 0.23 * 0.55)
        bm_tube(k[RED], [(sx * 0.4, -0.5, T + 0.85), (sx * 0.72, -0.42, T + 0.78), kn, an], [0.4, 0.46, 0.34, 0.23], n=8)
        _paw(k, an, (-sx * 0.03, 0.5, 0), 0.22, 0.48)
        k.emit("Head_Legs" + s, col, rig=rig, bone="root")
    # ---- the head: skull to snout in one loft, heavy brows, horns, nostrils, fangs over the lip
    bm_loft(k[RED], [sec_ring(s, 12) for s in SKULL])
    for sx in (-1, 1):
        bm_ellipsoid(k[RED], (sx * 0.15, 2.55, T + 0.655), (0.085, 0.1, 0.06), u=6, v=4)                    # nostril bumps
    skull = k.emit("Head_Skull", col, rig=rig, bone="head")[0]
    paint_faces(skull, "tan", lambda c, n: n.z < -0.55, lo=0.1, hi=0.75)
    for s, sx in (("L", -1), ("R", 1)):
        bm_beam(k[DARK], (sx * 0.1, 2.24, T + 0.82), (sx * 0.52, 1.98, T + 0.96), 0.2, 0.13, w1=0.17, h1=0.11)             # brow
        bm_ellipsoid(k["black:0.3:0.7"], (sx * 0.16, 2.62, T + 0.67), (0.04, 0.035, 0.032), u=6, v=4)                      # nostril
        bm_tube(k[HORN], [(sx * 0.27, 1.86, T + 0.86), (sx * 0.44, 1.62, T + 1.2), (sx * 0.52, 1.45, T + 1.52), (sx * 0.5, 1.4, T + 1.82)],
                [0.14, 0.115, 0.075, 0.0], n=6)
        bm_tube(k[HORN], [(sx * 0.48, 1.86, T + 0.52), (sx * 0.72, 1.66, T + 0.58), (sx * 0.86, 1.5, T + 0.7)], [0.09, 0.065, 0.0], n=5)
        bm_tube(k[HORN], [(sx * 0.44, 1.9, T + 0.36), (sx * 0.62, 1.72, T + 0.36), (sx * 0.72, 1.58, T + 0.42)], [0.07, 0.05, 0.0], n=5)
        for y, r in ((2.24, 0.036), (2.36, 0.042), (2.48, 0.036)):
            sc = sec_at(SKULL, y)
            bm_cyl(k[HORN], r, 0.0, 0.13, (sx * (sc[2] - 0.045), y, sc[1] - sc[4] * 0.5 - 0.065), rot=(180, 0, 0), seg=5)
        bm_cyl(k[HORN], 0.046, 0.0, 0.17, (sx * 0.16, 2.63, T + 0.255), rot=(180, 0, 0), seg=5)                            # front fangs
        e = Vector((sx * EYE_C.x, EYE_C.y, EYE_C.z))
        bm_ellipsoid(k[EYE], tuple(e), (0.1, 0.1, 0.09), u=8, v=5)
        bm_box(k["black:0.3:0.6"], (0.045, 0.03, 0.15), tuple(e + Vector((sx * 0.68, 0.73, 0)) * 0.086), (0, 0, -sx * 43))    # the slit
        k.emit("Head_Face" + s, col, rig=rig, bone="head")
        bm_ellipsoid(k[DARK], tuple(e + Vector((sx * 0.012, 0.012, 0))), (0.12, 0.12, 0.108), u=8, v=5)
        k.emit("Head_Lid" + s, col, rig=rig, bone="lid." + s)
    bm_tube(k[HORN], [(0, 2.5, T + 0.66), (0, 2.5, T + 0.8), (0, 2.44, T + 0.95)], [0.075, 0.06, 0.0], n=5)                 # nose horn
    k.emit("Head_NoseHorn", col, rig=rig, bone="head")
    bm_ellipsoid(k[FIRE], (0, 1.98, T + 0.33), (0.3, 0.24, 0.05), u=8, v=4)                                   # the glow down its throat
    k.emit("Head_Throat", col, rig=rig, bone="head")
    bm_loft(k[PALE], [sec_ring(s, 10) for s in JAW])
    for sx in (-1, 1):
        for y in (2.2, 2.36, 2.5):
            sc = sec_at(JAW, y)
            bm_cyl(k[HORN], 0.03, 0.0, 0.09, (sx * (sc[2] - 0.06), y, sc[1] + sc[3] + 0.02), seg=5)
    bm_box(k["salmon:0.3:0.8"], (0.3, 0.62, 0.03), (0, 2.16, T + 0.335))                                      # tongue
    k.emit("Head_Jaw", col, rig=rig, bone="jaw")
    # ---- the flame (scaled from nothing when it breathes) and the smoke from its nostrils
    c = MOUTH
    bm_loft(k[FIRE], [oval(c + Vector((0, y, 0)), (1, 0, 0), (0, 0, 1), r, r * 0.8, 8) for y, r in ((0.0, 0.1), (0.3, 0.3), (0.8, 0.42), (1.3, 0.32))],
            tip1=c + Vector((0, 1.85, 0.04)))
    for i in range(8):
        a = math.radians(45 * i + rnd.uniform(-12, 12))
        y = rnd.uniform(0.35, 1.2)
        o = Vector((math.cos(a), 0, math.sin(a) * 0.8))
        p = c + Vector((0, y, 0)) + o * 0.3
        bm_crystal(k[FIRE], p - o * 0.1, p + o * rnd.uniform(0.14, 0.24) + Vector((0, rnd.uniform(0.3, 0.5), 0)), 0.12, n=4, shoulder=0.25)
    bm_loft(k[HOT], [oval(c + Vector((0, y, 0)), (1, 0, 0), (0, 0, 1), r, r * 0.8, 6) for y, r in ((1.2, 0.3), (1.6, 0.26), (1.95, 0.14))],
            tip1=c + Vector((0, 2.3, 0.04)))
    k.emit("Head_Flame", col, rig=rig, bone="flame")
    for i in range(3):
        for sx in (-1, 1):
            bm_blob(k["white:0.0:0.45"], rnd, NOSE + Vector((sx * 0.14, 0.02, 0.03)), 0.17 + 0.035 * i, jitter=0.12, sub=1)
        k.emit("Head_Smoke%d" % (i + 1), col, rig=rig, bone="smoke.%d" % (i + 1))
    # ---- two little wings, standing on its shoulders (far too small for it)
    for s, sx in (("L", -1), ("R", 1)):
        mir = lambda v: Vector((v[0] * sx, v[1], v[2]))
        r_, w_ = mir(WING_R), mir(WING_W)
        a_, b_, c_ = w_ + mir((0.62, -0.18, 0.10)), w_ + mir((0.55, -0.50, -0.42)), w_ + mir((0.16, -0.66, -0.60))
        d_ = mir((0.44, 0.19, T + 1.6))
        bm_tube(k[RED], [r_ - (w_ - r_) * 0.3, r_, w_], [0.1, 0.1, 0.065], n=6)
        for tip in (a_, b_, c_):
            bm_tube(k[RED], [w_, w_.lerp(tip, 0.55) + Vector((0, 0, 0.04)), tip], [0.055, 0.04, 0.0], n=5)
        bm_crystal(k[HORN], w_, w_ + mir((0.03, 0.1, 0.17)), 0.045, n=4, shoulder=0.25)
        pull = lambda p, q: (p + q) * 0.4 + w_ * 0.2
        bm_sheet(k[TEAM], [w_, a_, pull(a_, b_), b_, pull(b_, c_), c_, pull(c_, d_), d_, r_])
        k.emit("Head_Wing" + s, col, rig=rig, bone="wing." + s)
    # ---- the tail, curling round the back heap: plates down it, the spade lying on the gold
    tb = ["hips"] + ["tail.%d" % i for i in range(1, 6)]
    bm_tube(k[RED], TAIL, TAIL_R, n=8)
    for i in range(1, 10):
        f = (TAIL[i - 1] - TAIL[i + 1]).normalized()
        h = 0.3 - 0.022 * i
        bm_fin(k[TEAM], TAIL[i] + Vector((0, 0, TAIL_R[i] * 0.9)), f, (0, 0, 1), h * 0.95, h * 0.46, h)
    bm_spade(k[TEAM], TAIL[-1], TAIL[-1] - TAIL[-2], 0.42, 0.52)
    soft(k.emit("Head_Tail", col, rig=rig, bones=tb), tb, power=5.0)
    flag_part("Head_Flag", col, rig, "flag", LANCE[1] - Vector((0, 0, 0.1)), FLAG_DIR, FLAG_LEN, 0.36, segs=3, swatch="team!", tail="swallow")
    empty("Muzzle", col, head, tuple(MOUTH), 0.25, "SPHERE")
    return rig


IDLE_LEN = 120
FIRE_LEN = 28


def pose(rig, breathe=0.0, swell=0.0, heat=0.0, lift=0.0, nod=0.0, jaw=0.0, flame=0.0, eye_l=0.0, eye_r=0.0, wings=0.0, flap=0.0, swish=0.0,
         flick=0.0, puffs=(None, None, None), flag=0.0, gust=1.0):
    pb = rig.pose.bones
    rest_pose(rig)
    s = 1.0 + breathe + 0.06 * swell
    kh = 1.0 + 0.085 * heat
    scale_arm(pb, "belly", (s, 1, s))
    scale_arm(pb, "ribs", (s, 1, s))
    scale_arm(pb, "heat.b", (s * kh, 1, s * kh))
    scale_arm(pb, "heat.r", (s * kh, 1, s * kh))
    scale_arm(pb, "heat.n", (1.0 + 0.1 * heat, 1, 1.0 + 0.1 * heat))
    turn(pb, "neck.1", x=20 * lift + nod)
    turn(pb, "neck.2", x=6 * lift)
    turn(pb, "head", x=-10 * lift)
    turn(pb, "jaw", x=-34 * jaw)
    fl = max(flame, 0.001)
    pb["flame"].scale = (fl, fl, fl)
    turn(pb, "flame", x=-16 * lift)                     # the breath runs level
    pb["lid.L"].scale = (1, 1.0 - 0.8 * max(eye_l, 0.3), 1)
    pb["lid.R"].scale = (1, 1.0 - 0.8 * max(eye_r, 0.3), 1)
    for sname, sx in (("L", -1), ("R", 1)):
        turn(pb, "wing." + sname, x=14 * wings + flap, y=sx * (28 * wings + flap * 0.8))
    turn(pb, "tail.3", z=5 * swish)
    turn(pb, "tail.4", z=9 * swish + 6 * flick)
    turn(pb, "tail.5", z=14 * swish + 22 * flick, x=-10 * abs(flick))
    for i, u in enumerate(puffs):
        b = pb["smoke.%d" % (i + 1)]
        if u is None or u <= 0.0 or u >= 1.0:
            b.scale = (0.001, 0.001, 0.001)
        else:
            g = math.sin(math.pi * u) ** 0.6 * (0.7 + 0.5 * u)
            b.scale = (g, g, g)
            b.location = arm_space_loc(b, (0.06 * math.sin(6 * u + 2 * i), -0.3 * u, 0.95 * u))
    wave_flag(rig, "flag", flag, amp=gust)


def _idle(rig, f):
    t = f / IDLE_LEN
    ph = 2 * math.pi * t
    c = (2 * t) % 1.0                                   # two breaths a loop; out from c = 0.25, a trail of puffs with each
    pose(rig, breathe=0.05 * math.sin(ph * 2), nod=1.2 * math.sin(ph * 2), jaw=0.07 * max(0.0, -math.cos(ph * 2)) * (1 if c > 0.25 else 0),
         eye_r=track(f, [(0, 0), (36, 0), (46, 0.75), (80, 0.75), (90, 0), (IDLE_LEN, 0)]),
         flap=3 * math.sin(ph * 2) + 8 * bump(f, 100, 10) * math.sin(f * 1.3), swish=math.sin(ph),
         flick=bump(f, 62, 11) * math.sin((f - 51) * 0.6), puffs=[(c - 0.25 - 0.1 * i) / 0.52 for i in range(3)], flag=3.0 * t)


def _fire(rig, f):
    lift = track(f, [(0, 0), (4, 1), (15, 1), (26, 0)])
    wings = track(f, [(0, 0), (4, 1), (14, 0.85), (26, 0)])
    eyes = track(f, [(0, 0), (2, 1), (17, 1), (26, 0)])
    pose(rig, swell=track(f, [(0, 0), (3, 1), (9, 0.5), (16, 0.3), (26, 0)]), heat=track(f, [(0, 0), (3, 1), (13, 1), (24, 0)]), lift=lift,
         jaw=track(f, [(0, 0), (2, 0.3), (5, 1), (15, 1), (22, 0)]),
         flame=track(f, [(2, 0), (5, 1), (14, 1), (18, 0)]) * (1.0 + 0.07 * math.sin(f * 2.1)), eye_l=eyes, eye_r=eyes, wings=wings,
         flap=4 * math.sin(f * 1.4) * wings, flick=track(f, [(0, 0), (5, 1), (16, 0.6), (26, 0)]) * math.sin(f * 0.7),
         puffs=[(f - 13 - i) / (FIRE_LEN - 13.5 - i) for i in range(3)], flag=3.0 * f / FIRE_LEN, gust=1.0 + 0.8 * bump(f, 10, 9))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        _idle(rig, f)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        _fire(rig, f)
        key_pose(rig, f)
    # the shot leaves where the mouth is mid-breath
    bpy.context.scene.frame_set(8)
    bpy.context.view_layer.update()
    mouth = rig.matrix_world @ rig.pose.bones["flame"].head
    bpy.data.objects["Muzzle"].location = bpy.data.objects["Head"].matrix_world.inverted() @ mouth
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, -0.3, 0.9), "dist": 13.0, "yaw": 150, "pitch": 22, "anim_target": (0, 1.2, 1.1), "anim_dist": 7.2,
           "frames": [("idle", 0), ("idle", 30), ("idle", 64), ("fire", 3), ("fire", 9), ("fire", 20)],
           "extra": [{"yaw": 152, "pitch": 9, "dist": 4.4, "target": (0.1, 2.05, 0.95)},
                     {"yaw": 20, "pitch": 34, "dist": 6.6, "target": (0, -2.2, 0.6)},
                     {"yaw": 212, "pitch": 28, "dist": 7.4, "target": (-1.3, 0.6, 0.9)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
