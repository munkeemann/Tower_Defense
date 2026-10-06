"""Builds the Siege Mortar (footprint "fan4": [0,0] back, [-1,0] left, [0,-1] front, [1,-1] right), a Forge tower:
a colossal stubby mortar that lobs a huge bomb to very long range, all round.

    python tools/blender/build.py dwarf_mortar --out <preview dir>

One emplacement on one paved floor. Where the four hexes meet: a pit ringed by a wall of great stone blocks (a brass
traverse ring and runes on its coping), and in it a timber turntable carrying the mortar: a fat bronze barrel, iron
banded, on trunnions in a massive timber-and-iron bed, with the team's color round its chase and on the bed's cheeks.
The turntable is the Head: bed, barrel, the loading derrick stepped on its rim (jib, rope, a bomb hanging over its
cradle, the team's pennant) and the Crew's place by the breech all turn with the aim.
Front hex: a stone revetment with a capped pier at each corner. Left hex: the supply ramp up
to the wall, a bomb truck on it hauled by a capstan. Right hex: the store, a lean-to roofed in the team's tiles over
the powder kegs, a pyramid of bombs beside it. Back: the steps up to the pit.
idle: the hanging bomb sways, the gunner trims the elevation, a wisp of smoke curls from the bore, the pennant flies.
fire (0.8 s): the blast at frame 1: muzzle flash, a smoke ring rolling away up the line of fire, billowing smoke, the
barrel rocks and the bed slams back on its rails, the bomb on the derrick swings. reload (1.6 s): the barrel tips up,
the derrick swings its bomb over the muzzle and lowers it in, swings back, picks the next one out of the cradle.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "forgeworks_common.py"), encoding="utf-8").read())

TID = "dwarf_mortar"
CELLS = [(0, 0), (-1, 0), (0, -1), (1, -1)]
MID = footprint_mid(CELLS)
BK = hex_to_world(0, 0, MID)          # (0, -1.04)
LF = hex_to_world(-1, 0, MID)         # (-1.8, 0)
FC = hex_to_world(0, -1, MID)         # (0, 1.04)
RT = hex_to_world(1, -1, MID)         # (1.8, 0)
TOP = 0.34
T = TOP
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
O = Vector((0, 0, 0))
RING_R, RING_IN, RING_H = 1.42, 1.17, 0.38     # the pit's wall: outer and inner radius, height above the floor
DECK = T + 0.22                                 # the turntable's top: the Head stands here
TURN_R = 1.13
BOMB_R = 0.22
BRONZE = "gold:0.25:0.92"
PLANK = "wood:0.22:0.85"
ROPE = "sand:0.3:0.75"
SMOKE = "stone:0.0:0.4"

# ---- the mortar, in the Head's space (the deck is z = 0, +Y is the line of fire)
P = Vector((0, -0.12, 0.52))                    # the trunnions' axis
ELEV, LOAD_ELEV = 58.0, 80.0


def _axis(e):
    return Vector((0, math.cos(math.radians(e)), math.sin(math.radians(e))))


A = _axis(ELEV)
BL = 1.3                                        # from the trunnions to the muzzle
MUZ = P + A * BL
POST = Vector((0.62, -0.82, 0))                 # the derrick's post, on the turntable's rim behind the bed
TIPZ = 2.7                                     # the jib's tip, where the rope hangs from
_load = P + _axis(LOAD_ELEV) * BL               # the muzzle when the barrel is tipped up to load
REACH = math.hypot(_load.x - POST.x, _load.y - POST.y)
PHI_LOAD = math.degrees(math.atan2(_load.y - POST.y, _load.x - POST.x))
PHI_REST = 75.0                                 # the jib's bearing at rest: along the bed's right side
SLEW = PHI_LOAD - PHI_REST
TIP = Vector((POST.x + math.cos(math.radians(PHI_REST)) * REACH, POST.y + math.sin(math.radians(PHI_REST)) * REACH, TIPZ))
L0 = 0.2                                        # the rope as modelled; it's stretched to the lengths below
SLING = 0.1
L_REST, L_HIGH, L_IN = 0.8, 0.2, 1.0           # hanging at rest, hoisted to clear the muzzle, lowered into the bore
L_DECK = TIPZ - SLING - BOMB_R - (BOMB_R + 0.05)    # with the bomb set down in its cradle
SR, Sr = 0.4, 0.13                              # the smoke ring as modelled: its radius, its thickness


def _bomb(k, c, r=BOMB_R, turn=0.0, eye=True):
    """A mortar bomb: a cast-iron ball, a brass fuse plug off its crown, a lifting eye on top."""
    c = Vector(c)
    bm_ellipsoid(k[CAST], tuple(c), (r, r, r), u=10 if eye else 8, v=6 if eye else 5)
    up = Vector((0.5 * math.cos(math.radians(turn)), 0.5 * math.sin(math.radians(turn)), 0.86)).normalized()
    fw_lathe(k[BRASS], c + up * (r * 0.9), up, [(r * 0.3, 0.0), (r * 0.3, r * 0.2), (r * 0.15, r * 0.3), (0.0, r * 0.3)], n=6, cap0=False)
    if eye:
        fw_ring(k[IRON], c + Z * (r * 1.16) - Y * 0.015, Y, r * 0.12, r * 0.27, 0.03, n=8)


def build_base():
    fw_reset()
    col = collection("Dwarf_mortar")
    root = empty("Dwarf_mortar", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(14)
    k = Kit()
    # ---- one paved floor under the whole emplacement
    fw_bed(k["stone_dark:0.35:0.85"], CELLS, T)
    fw_emit(k, "Bed", col, root, tag="no_refine")
    fw_paving(k[STONE], rnd, CELLS, T, sx=0.5, sy=0.32, skip=lambda x, y: x * x + y * y < (RING_R - 0.06) ** 2)
    fw_emit(k, "Floor", col, root, vary=0.09)
    # ---- the pit: a wall of two courses of great blocks, the brass traverse ring and runes on its coping
    bm_block_course(k["stone:0.25:0.9"], rnd, O, RING_R + 0.035, T, 0.2, 16, depth=RING_R + 0.035 - RING_IN)
    fw_emit(k, "Pit_Foot", col, root, vary=0.08)
    bm_block_course(k["stone:0.08:0.78"], rnd, O, RING_R, T + 0.2, RING_H - 0.2, 16, depth=RING_R - RING_IN, phase=0.5)
    fw_emit(k, "Pit_Wall", col, root, vary=0.08, bevel=0.014)
    fw_ring(k["stone_dark:0.3:0.9"], (0, 0, T), Z, RING_IN + 0.03, RING_R - 0.05, RING_H - 0.03, n=16)
    fw_emit(k, "Pit_Core", col, root, tag="no_refine")
    fw_ring(k[BRASS], (0, 0, T + RING_H - 0.014), Z, RING_IN - 0.004, RING_IN + 0.06, 0.03, n=24)
    for i in range(8):
        a = math.radians(45 * i)
        fw_stud(k[IRON], (math.cos(a) * (RING_IN + 0.028), math.sin(a) * (RING_IN + 0.028), T + RING_H + 0.016), Z, r=0.02, h=0.012)
    fw_emit(k, "Pit_Scale", col, root)
    for i in range(8):
        a = math.radians(45 * i + 11.25)
        d = Vector((math.cos(a), math.sin(a), 0))
        fw_rune(k[RUNE], d * (RING_R - 0.085) + Z * (T + RING_H - 0.006), d.cross(Z), d, 0.08, i * 3, stroke=0.2)
    fw_emit(k, "Pit_Runes", col, root)
    # ---- the steps up to the pit at the back
    bm_box(k["stone:0.2:0.85"], (1.02, 0.46, 0.13), (0, -RING_R - 0.2, T + 0.065))
    bm_box(k["stone:0.1:0.8"], (0.86, 0.26, 0.13), (0, -RING_R - 0.1, T + 0.195))
    fw_emit(k, "Steps", col, root, bevel=0.014, vary=0.06)
    # ---- the revetment round the front: a thick wall hugging the pit, a capped pier at each corner, the team's banner down its face
    wall = [(-0.70, 1.30), (-0.415, 1.77), (0.415, 1.77), (0.70, 1.30)]
    for a, b in zip(wall, wall[1:]):
        bm_block_wall(k["stone:0.2:0.88"], rnd, a, b, T, T + 0.64, th=0.3, course=0.21, block=0.4)
        bm_block_wall(k["stone:0.05:0.65"], rnd, a, b, T + 0.64, T + 0.79, th=0.37, course=0.15, block=0.45)
    fw_emit(k, "Revetment", col, root, vary=0.08, bevel=0.012)
    for sx in (-1, 1):
        round_tower(k, rnd, (sx * 0.415, 1.77, 0), 0.25, 0.23, T, T + 0.96, courses=3, n=6, depth=0.13, stone="stone:0.1:0.8")
        bm_cyl(k["stone:0.0:0.6"], 0.28, 0.28, 0.07, (sx * 0.415, 1.77, T + 0.99), seg=6)
    fw_emit(k, "Piers", col, root, vary=0.08)
    for sx in (-1, 1):
        bm_tile_cone(k["team!:0.1:0.7"], rnd, (sx * 0.415, 1.77, 0), 0.3, T + 1.02, 0.36, rows=2, n=6, th=0.045, top=0.03)
    fw_emit(k, "Pier_Caps", col, root, vary=0.08)
    for sx in (-1, 1):
        bm_cyl(k[BRASS], 0.04, 0.0, 0.14, (sx * 0.415, 1.77, T + 1.42), seg=5)
    bm_box(k[BRASS], (0.5, 0.04, 0.04), (0, 1.95, T + 0.6))
    fw_emit(k, "Pier_Spikes", col, root)
    bm = k["team!:0.1:0.75"]                                 # the banner down the wall's face (both sides)
    for yy, flip in ((1.942, False), (1.93, True)):
        vs = [bm.verts.new((px, yy, T + pz)) for px, pz in ((0.2, 0.6), (-0.2, 0.6), (-0.2, 0.2), (0.0, 0.08), (0.2, 0.2))]
        bm.faces.new(list(reversed(vs)) if flip else vs)
    fw_emit(k, "Banner", col, root)
    # ---- left hex: the supply ramp up to the wall's top, the bomb truck on it, the capstan that hauls it
    x0, x1, hw = -2.6, -(RING_R - 0.05), 0.37
    rise = RING_H - 0.02
    for sy in (-1, 1):
        fw_wedge(k[TIMBER], (x0, sy * hw, T), (x1, sy * hw, T), 0.1, 0.035, rise)
        bm_beam(k[TIMBER], (x0 + 0.04, sy * (hw - 0.015), T + 0.085), (x1, sy * (hw - 0.015), T + 0.085 + rise), 0.07, 0.07)
    for t in (0.42, 0.8):
        x = x0 + (x1 - x0) * t
        bm_box(k[TIMBER], (0.1, 2 * hw + 0.1, rise * t), (x, 0, T + rise * t / 2))
    fw_emit(k, "Ramp_Frame", col, root)
    bm_planks(k[PLANK], rnd, (x0, -hw - 0.03, T + 0.04), (0, 2 * hw + 0.06, 0), (x1 - x0, 0, rise), 9, th=0.045)
    fw_emit(k, "Ramp_Planks", col, root, vary=0.09)
    slope = math.atan2(rise, x1 - x0)
    tc = 0.66
    kc = Kit()                                              # the truck, laid out level (+X up the ramp), then set on the slope
    for sx in (-1, 1):
        for sy in (-1, 1):
            fw_lathe(kc[TIMBER], (sx * 0.17, sy * 0.21 - 0.03, 0.1), Y, [(0.1, 0.0), (0.1, 0.06)], n=8)
            fw_hoop(kc[IRON], (sx * 0.17, sy * 0.21, 0.1), Y, 0.1, w=0.07, th=0.012, n=8)
            fw_lathe(kc[BRASS], (sx * 0.17, sy * 0.21 + sy * 0.03, 0.1), (0, sy, 0), [(0.035, 0.0), (0.02, 0.025)], n=6, cap0=False)
    bm_box(kc[PLANK], (0.58, 0.34, 0.06), (0, 0, 0.21))
    for sy in (-1, 1):
        bm_box(kc["team!:0.15:0.7"], (0.58, 0.035, 0.13), (0, sy * 0.175, 0.3))
    for sx in (-1, 1):
        bm_box(kc[TIMBER], (0.04, 0.38, 0.12), (sx * 0.29, 0, 0.295))
    _bomb(kc, (0, 0, 0.24 + BOMB_R - 0.03), turn=200)
    fw_ring(kc[IRON], (0.31, -0.012, 0.3), Y, 0.025, 0.05, 0.024, n=6)
    cart_m = Matrix.Translation((x0 + (x1 - x0) * tc, 0, T + 0.045 + rise * tc)) @ Matrix.Rotation(-slope, 4, "Y")
    fw_place(kc, m=cart_m)
    fw_emit(kc, "Truck", col, root)
    for sy in (-1, 1):                                      # chocks behind its wheels
        fw_wedge(k[TIMBER], cart_m @ Vector((-0.36, sy * 0.21, 0.0)), cart_m @ Vector((-0.24, sy * 0.21, 0.0)), 0.1, 0.02, 0.09,
                 up=cart_m.to_3x3() @ Z)
    bolt = Vector((x1 + 0.12, 0.0, T + RING_H))
    bm_tube(k[ROPE], [bolt + Z * 0.05, cart_m @ Vector((0.33, 0, 0.3))], 0.016, n=4)
    fw_ring(k[IRON], bolt - Y * 0.015, Y, 0.03, 0.065, 0.03, n=6)
    fw_emit(k, "Truck_Rope", col, root)
    by = -0.7                                               # bombs waiting by the ramp, on the near side
    for i, (bx, bz, tn) in enumerate(((-2.2, 0.0, 40), (-1.78, 0.0, 250), (-1.99, 0.34, 130))):
        _bomb(k, (bx, by, T + 0.05 + BOMB_R + bz), turn=tn, eye=False)
    for sy in (-1, 1):
        bm_box(k[TIMBER], (0.92, 0.06, 0.08), (-1.99, by + sy * 0.15, T + 0.04))
    for sx in (-1, 1):
        bm_box(k[TIMBER], (0.06, 0.4, 0.1), (-1.99 + sx * 0.43, by, T + 0.05))
    fw_emit(k, "Ramp_Bombs", col, root)
    ry = 0.72                                               # the rammer and the sponge on their rack, on the far side
    for x in (-2.28, -1.72):
        bm_box(k[TIMBER], (0.08, 0.08, 0.5), (x, ry, T + 0.25))
        bm_box(k[TIMBER], (0.08, 0.3, 0.06), (x, ry, T + 0.5))
        for dy in (-0.14, 0.14):
            bm_box(k[TIMBER], (0.06, 0.05, 0.12), (x, ry + dy, T + 0.57))
    bm_beam(k["wood:0.15:0.7"], (-2.46, ry - 0.07, T + 0.57), (-1.4, ry - 0.07, T + 0.57), 0.05, 0.05)
    fw_lathe(k[TIMBER], (-1.42, ry - 0.07, T + 0.57), X, [(0.1, 0.0), (0.1, 0.18)], n=8)
    bm_beam(k["wood:0.15:0.7"], (-2.42, ry + 0.07, T + 0.57), (-1.5, ry + 0.07, T + 0.57), 0.05, 0.05)
    bm_blob(k["cream:0.1:0.8"], rnd, (-2.46, ry + 0.07, T + 0.57), 0.12, squash=(1.3, 1.0, 1.0), jitter=0.1)
    fw_emit(k, "Tools", col, root)
    # ---- right hex: the store, a lean-to over the powder kegs, and a pyramid of bombs in its garland
    sx0, sx1, sy0, sy1 = RT.x - 0.02, RT.x + 0.62, -0.08, 0.72
    for x, y, h in ((sx0, sy0, 0.78), (sx0, sy1, 0.78), (sx1, sy0, 1.3), (sx1, sy1, 1.3)):
        bm_box(k[TIMBER], (0.11, 0.11, h), (x, y, T + h / 2))
        bm_box(k["stone:0.2:0.8"], (0.2, 0.2, 0.09), (x, y, T + 0.045))
    for y in (sy0, sy1):
        bm_beam(k[TIMBER], (sx0 - 0.2, y, T + 0.7), (sx1 + 0.12, y, T + 1.36), 0.09, 0.09)
        bm_beam(k[TIMBER], (sx0, y, T + 0.45), (sx0 + 0.24, y, T + 0.86), 0.06, 0.06)
    for x, z in ((sx0, T + 0.78), (sx1, T + 1.28)):
        bm_beam(k[TIMBER], (x, sy0 - 0.1, z), (x, sy1 + 0.1, z), 0.09, 0.09)
    bm_block_wall(k["stone:0.2:0.88"], rnd, (sx1, sy0 + 0.06), (sx1, sy1 - 0.06), T, T + 0.86, th=0.16, course=0.17, block=0.3)
    bm_block_wall(k["stone:0.2:0.88"], rnd, (sx0 + 0.08, sy1), (sx1 - 0.08, sy1), T, T + 0.52, th=0.14, course=0.17, block=0.3)
    fw_emit(k, "Store", col, root, vary=0.07)
    bm_tile_slope(k["team!:0.1:0.7"], rnd, (sx0 - 0.22, sy0 - 0.16, T + 0.7), (sx0 - 0.22, sy1 + 0.1, T + 0.7),
                  (sx1 + 0.14, sy0 - 0.16, T + 1.42), (sx1 + 0.14, sy1 + 0.1, T + 1.42), rows=5, cols=4, th=0.05)
    fw_emit(k, "Store_Roof", col, root, vary=0.08)
    kx = sx0 + 0.36
    for ky, kz in ((0.14, 0.0), (0.5, 0.0), (0.32, 0.3)):
        fw_keg(k, (kx, ky, T + 0.19 + kz), X, 0.17, 0.42)
    for ky in (-0.03, 0.67):
        fw_wedge(k[TIMBER], (kx, ky, T), (kx, ky + (0.09 if ky < 0.3 else -0.09), T), 0.4, 0.1, 0.02)
    fw_emit(k, "Store_Kegs", col, root, vary=0.05)
    pyr = Vector((RT.x + 0.1, -0.5, 0))
    for i, (dx, dy, dz, tn) in enumerate(((-0.21, 0.14, 0.0, 30), (0.21, 0.14, 0.0, 160), (0.0, -0.22, 0.0, 280), (0.0, 0.02, 0.34, 80))):
        _bomb(k, (pyr.x + dx, pyr.y + dy, T + 0.05 + BOMB_R + dz), turn=tn, eye=False)
    tri = [pyr + Vector((-0.5, 0.33, 0)), pyr + Vector((0.5, 0.33, 0)), pyr + Vector((0.0, -0.53, 0))]
    for i in range(3):
        a, b = tri[i], tri[(i + 1) % 3]
        bm_beam(k[TIMBER], (a.x, a.y, T + 0.05), (b.x, b.y, T + 0.05), 0.07, 0.1)
    fw_emit(k, "Store_Bombs", col, root)
    head = empty("Head", col, root, (0, 0, DECK), 0.5, "SINGLE_ARROW")
    return root


BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "bed": ((0, -0.5, 0.1), (0, -0.2, 0.1), "root"),
    "barrel": (tuple(P), tuple(P + A * 0.4), "bed"),
    "crane": ((POST.x, POST.y, 0.1), (POST.x, POST.y, 0.5), "root"),
    "rope": (tuple(TIP), tuple(TIP - Z * 0.2), "crane"),
    "hook": (tuple(TIP - Z * L0), tuple(TIP - Z * (L0 + 0.15)), "crane"),
    "bomb": (tuple(TIP - Z * (L0 + SLING + BOMB_R)), tuple(TIP - Z * (L0 + SLING + BOMB_R) + Y * 0.15), "hook"),
    "ring_in": (tuple(MUZ), tuple(MUZ + A * 0.2), "root"),
    "ring_out": (tuple(MUZ), tuple(MUZ + A * 0.2), "root"),
    "flash": (tuple(MUZ), tuple(MUZ + A * 0.2), "root"),
}
fw_puff_bones(BONES, "puff", tuple(MUZ + A * 0.05), 3, "root")
FLAG_TOP = Vector((POST.x, POST.y, 2.98))
FLAG_DIR = (-1, -0.2, 0)
flag_bones(BONES, "flag", tuple(FLAG_TOP), FLAG_DIR, 0.62, segs=3, parent="crane")
CHEEK = [(-0.58, 0.02), (0.84, 0.02), (0.84, 0.42), (0.64, 0.8), (0.42, 0.8), (0.16, 0.54), (-0.4, 0.54), (-0.58, 0.3)]
PANEL = [(-0.46, 0.14), (0.74, 0.14), (0.74, 0.4), (0.3, 0.46), (-0.46, 0.42)]
BARREL = [(0.0, -0.36), (0.18, -0.35), (0.34, -0.28), (0.5, -0.16), (0.56, -0.02), (0.56, 0.42), (0.51, 0.46), (0.49, 0.96), (0.53, 1.0),
          (0.6, 1.1), (0.6, 1.24), (0.54, BL), (0.4, BL)]


def build_head():
    col = collection("Dwarf_mortar")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    rnd = random.Random(5)
    k = Kit()
    # ---- the turntable: a wheel of plank wedges in an iron tyre, the rails the bed slides on, the derrick's step,
    # the cradle the next bomb waits in
    bm_block_course(k[PLANK], rnd, O, TURN_R, -0.1, 0.1, 20, depth=TURN_R - 0.2, gap=0.016, jit=0.006)
    bm_cyl(k["wood_dark:0.4:0.9"], 0.26, 0.26, 0.09, (0, 0, -0.055), seg=8)
    fw_emit(k, "Head_Deck", col, rig=rig, bone="root", vary=0.09)
    fw_ring(k[IRON], (0, 0, -0.1), Z, TURN_R - 0.07, TURN_R + 0.012, 0.112, n=20)
    for i in range(10):
        a = 2 * math.pi * (i + 0.5) / 10
        fw_stud(k[BRASS], (math.cos(a) * (TURN_R - 0.03), math.sin(a) * (TURN_R - 0.03), 0.012), Z, r=0.028, h=0.016)
    for sx in (-1, 1):
        bm_box(k[IRON], (0.07, 1.66, 0.035), (sx * 0.645, 0.1, 0.012))
    fw_ring(k[IRON], (POST.x, POST.y, 0.0), Z, 0.07, 0.18, 0.13, n=8)
    for dx in (-0.16, 0.16):
        bm_box(k[TIMBER], (0.06, 0.52, 0.1), (TIP.x + dx, TIP.y, 0.05))
    for dy in (-0.2, 0.2):
        bm_box(k[TIMBER], (0.4, 0.06, 0.07), (TIP.x, TIP.y + dy, 0.035))
    fw_emit(k, "Head_Turntable", col, rig=rig, bone="root")
    # ---- the bed: two cheeks of baulk timber shod and strapped in iron, the team's panel on each, transoms, the quoin
    ki = Kit()
    for sx in (-1, 1):
        fw_prism(k[TIMBER], [Vector((sx * 0.58, y, z)) for y, z in CHEEK], Vector((sx * 0.13, 0, 0)))
        bm_box(ki[IRON], (0.15, 1.46, 0.06), (sx * 0.645, 0.13, 0.045))
        top = CHEEK[2:]
        for (ya, za), (yb, zb) in zip(top, top[1:]):
            bm_beam(ki[IRON], (sx * 0.645, ya, za + 0.006), (sx * 0.645, yb, zb + 0.006), 0.15, 0.03)
        bm_box(ki[IRON], (0.15, 0.03, 0.42), (sx * 0.645, 0.845, 0.22))
        fw_prism(k["team!:0.15:0.7"], [Vector((sx * 0.71, y, z)) for y, z in PANEL], Vector((sx * 0.012, 0, 0)))
        fw_rune(k[RUNE], (sx * 0.726, 0.14, 0.29), (0, sx, 0), Z, 0.1, "tiwaz" if sx > 0 else "othala", stroke=0.2)
        for yy in (-0.3, 0.52):
            fw_stud(ki[BRASS], (sx * 0.722, yy, 0.29), (sx, 0, 0), r=0.035, h=0.02)
        # the cap square over the trunnion
        bm_box(ki[BRASS], (0.16, 0.44, 0.07), (sx * 0.645, P.y, P.z + 0.17))
        for dy in (-0.19, 0.19):
            bm_box(ki[BRASS], (0.16, 0.07, 0.16), (sx * 0.645, P.y + dy, P.z + 0.085))
    bm_box(k[TIMBER], (1.1, 0.14, 0.17), (0, -0.5, 0.115))
    bm_box(k[TIMBER], (1.1, 0.18, 0.4), (0, 0.75, 0.24))
    fw_prism(k["wood:0.3:0.9"], [Vector((-0.52, y, z)) for y, z in ((0.3, 0.04), (0.68, 0.04), (0.68, 0.73), (0.6, 0.73), (0.36, 0.22))], Vector((1.04, 0, 0)))
    fw_emit(k, "Head_Bed", col, rig=rig, bone="bed", bevel=0.012, vary=0.04)
    fw_emit(ki, "Head_BedIron", col, rig=rig, bone="bed")
    # ---- the barrel: bronze, iron hoops, a brass muzzle ring, the team's band round the chase, runes round the breech
    fw_lathe(k[BRONZE], P, A, BARREL, n=12, cap0=False, cap1=False)
    fw_lathe(k["black:0.3:0.9"], P, A, [(0.4, BL), (0.39, 0.62), (0.0, 0.62)], n=12, cap0=False, cap1=False)
    for d, r, w in ((-0.02, 0.56, 0.1), (0.42, 0.56, 0.09), (0.98, 0.51, 0.07)):
        fw_hoop(k[IRON], P + A * d, A, r, w=w, th=0.028, n=12)
    fw_hoop(k[BRASS], P + A * 1.17, A, 0.6, w=0.12, th=0.024, n=12)
    fw_lathe(k["team!:0.1:0.65"], P, A, [(0.48, 0.52), (0.508, 0.52), (0.508, 0.92), (0.48, 0.92)], n=12, cap0=False, cap1=False)
    fw_lathe(k[CAST], P - X * 0.8, X, [(0.15, 0.0), (0.15, 1.6)], n=10)
    for sx in (-1, 1):
        fw_lathe(k[BRASS], P + X * (sx * 0.8), X * sx, [(0.1, 0.0), (0.07, 0.03), (0.0, 0.03)], n=8, cap0=False)
    a_, x_, y_ = fw_frame(A)
    g = 0
    for i in range(12):
        ang = 2 * math.pi * (i + 0.5) / 12
        dn = x_ * math.cos(ang) + y_ * math.sin(ang)
        if dn.z > 0.05 or dn.y < -0.3:                       # the facets you can see: up, and back toward the crew
            fw_rune(k[RUNE], P + A * 0.2 + dn * (0.56 * math.cos(math.pi / 12) + 0.003), A.cross(dn), A, 0.095, g * 2, stroke=0.2)
            g += 1
    fw_emit(k, "Head_Barrel", col, rig=rig, bone="barrel")
    # ---- the derrick (laid out with its jib along +Y, then turned to its bearing): post, jib and brace, a counterweight,
    # the block at the tip, a winch on the post, the pennant's pole
    kc = Kit()
    sl = (TIPZ - 2.2) / REACH
    bm_box(kc[TIMBER], (0.16, 0.16, 2.36), (0, 0, 1.18))
    for z in (0.42, 1.44, 2.2):
        bm_box(kc[IRON], (0.19, 0.19, 0.08), (0, 0, z))
    bm_beam(kc[TIMBER], (0, -0.36, 2.2 - 0.36 * sl + 0.1), (0, REACH + 0.08, TIPZ + 0.1 + 0.08 * sl), 0.11, 0.15)
    bm_beam(kc[TIMBER], (0, 0.06, 1.46), (0, REACH * 0.58, 2.2 + sl * REACH * 0.58 + 0.03), 0.09, 0.09)
    bm_box(kc[IRON], (0.14, 0.09, 0.2), (0, REACH * 0.58, 2.2 + sl * REACH * 0.58 + 0.08))
    bm_box(kc[CAST], (0.22, 0.2, 0.24), (0, -0.34, 1.9))
    bm_box(kc[IRON], (0.05, 0.05, 0.2), (0, -0.34, 2.08))
    fw_lathe(kc[BRASS], (-0.04, REACH, TIPZ + 0.02), X, [(0.03, 0.0), (0.09, 0.0), (0.09, 0.08), (0.03, 0.08)], n=8)
    for sx in (-1, 1):
        bm_box(kc[IRON], (0.02, 0.16, 0.24), (sx * 0.055, REACH, TIPZ + 0.06))
    fw_lathe(kc["wood:0.2:0.8"], (-0.14, 0.15, 0.95), X, [(0.075, 0.0), (0.075, 0.28)], n=8)
    for sx in (-1, 1):
        bm_box(kc[IRON], (0.03, 0.24, 0.12), (sx * 0.15, 0.09, 0.95))
    bm_beam(kc[IRON], (0.15, 0.15, 0.95), (0.25, 0.15, 0.95), 0.03, 0.03)
    bm_beam(kc[IRON], (0.24, 0.15, 0.95), (0.24, 0.15, 1.1), 0.03, 0.03)
    bm_beam(kc[TIMBER], (0.22, 0.15, 1.1), (0.34, 0.15, 1.1), 0.045, 0.045)
    bm_tube(kc[ROPE], [(0, 0.2, 1.0), (0, REACH - 0.06, TIPZ + 0.09)], 0.016, n=4)
    bm_cyl(kc[BRASS], 0.11, 0.0, 0.14, (0, 0, 2.43), seg=4, rot=(0, 0, 45))
    bm_box(kc[TIMBER], (0.035, 0.035, 0.6), (0, 0, 2.7))
    bm_cyl(kc[BRASS], 0.035, 0.0, 0.08, (0, 0, 3.03), seg=5)
    fw_place(kc, m=Matrix.Translation(POST) @ Matrix.Rotation(math.radians(PHI_REST - 90.0), 4, "Z"))
    fw_emit(kc, "Head_Crane", col, rig=rig, bone="crane")
    flag_part("Pennant", col, rig, "flag", tuple(FLAG_TOP), FLAG_DIR, 0.62, 0.3, segs=3, tail="swallow")
    # the rope (stretched by its bone), the hook, the bomb
    bm_tube(k[ROPE], [TIP + Z * 0.02, TIP - Z * L0], 0.018, n=5)
    fw_emit(k, "Head_Rope", col, rig=rig, bone="rope")
    hz = TIP - Z * L0
    bm_box(k[IRON], (0.06, 0.06, 0.06), tuple(hz - Z * 0.02))
    fw_ring(k[IRON], hz - Z * 0.075 - X * 0.014, X, 0.028, 0.055, 0.028, n=8)
    fw_emit(k, "Head_Hook", col, rig=rig, bone="hook")
    _bomb(k, TIP - Z * (L0 + SLING + BOMB_R), turn=150)
    fw_emit(k, "Head_Bomb", col, rig=rig, bone="bomb")
    # ---- the shot: a smoke ring (its inner and outer edge on two bones, so it can widen and thin away), the muzzle
    # flash, the smoke that billows after
    prof = [(SR + Sr * math.cos(math.radians(180 + 60 * i)), Sr * math.sin(math.radians(180 + 60 * i))) for i in range(7)]
    fw_lathe(k[SMOKE], MUZ, A, prof, n=12, cap0=False, cap1=False)
    for o in fw_fx(fw_emit(k, "Head_SmokeRing", col, rig=rig, bone="ring_out")):
        fw_skin(o, rig, lambda co: {"ring_in": 1.0} if ((co - MUZ) - A * (co - MUZ).dot(A)).length < SR else {"ring_out": 1.0})
    for i in range(9):
        ang = 2 * math.pi * i / 9
        side = x_ * math.cos(ang) + y_ * math.sin(ang)
        base = MUZ + side * 0.2
        bm_crystal(k[FIRE], base, base + (A + side * 0.8).normalized() * rnd.uniform(0.5, 0.85), 0.1, n=4, shoulder=0.3, foot=0.5)
    bm_crystal(k[HOT], MUZ - A * 0.1, MUZ + A * 1.0, 0.2, n=6, shoulder=0.3, foot=0.6)
    fw_fx(fw_emit(k, "Head_Flash", col, rig=rig, bone="flash"))
    fw_puffs("Head_Puff", col, rig, "puff", tuple(MUZ + A * 0.05), 3, r=0.2)
    empty("Muzzle", col, head, tuple(MUZ + A * 0.05), 0.2, "SPHERE")
    crew = empty("Crew", col, head, (-0.4, -0.86, 0.0), 0.3, "SINGLE_ARROW")       # by the breech, on the turntable
    crew.rotation_euler = (0, 0, math.radians(-35))
    return rig


IDLE_LEN = 80
FIRE_LEN = 24
RELOAD_LEN = 48


def _q(pb, quat):
    """An armature-space rotation as this bone's own pose rotation."""
    r = pb.bone.matrix_local.to_quaternion()
    return r.inverted() @ quat @ r


def pose(rig, elev=ELEV, back=0.0, rock=0.0, squash=0.0, slew=0.0, L=L_REST, sway=0.0, sway2=0.0, bomb=1.0, smoke=-1.0, flash=0.0,
         puff=0.0, burst=0.0, wave=0.0, gust=1.0):
    """elev: the barrel's elevation; back: the bed's slide; rock: the barrel's kick (degrees); slew: the jib's turn
    from its rest bearing; L: the rope's length; sway / sway2: the rope's swing; bomb: the hanging bomb's size
    (0 = gone); smoke: the smoke ring's life 0..1 (outside = hidden); puff: the smoke's phase; burst: its size."""
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    pb["bed"].location = arm_space_loc(pb["bed"], (0, -back, 0))
    pb["barrel"].rotation_quaternion = q(pb["barrel"], (1, 0, 0), elev - ELEV + rock)
    pb["barrel"].scale = (1.0 + squash * 0.5, 1.0 - squash, 1.0 + squash * 0.5)
    pb["crane"].rotation_quaternion = q(pb["crane"], (0, 0, 1), slew)
    sw = Quaternion((1, 0, 0), math.radians(sway)) @ Quaternion((0, 1, 0), math.radians(sway2))
    pb["rope"].rotation_quaternion = _q(pb["rope"], sw)
    pb["rope"].scale = (1.0, L / L0, 1.0)
    pb["hook"].rotation_quaternion = _q(pb["hook"], sw)
    pb["hook"].location = arm_space_loc(pb["hook"], tuple(sw @ Vector((0, 0, -L)) + Vector((0, 0, L0))))
    pb["bomb"].scale = (max(bomb, 0.001),) * 3
    if 0.0 <= smoke < 1.0:
        u = smoke
        s = 0.15 + 1.9 * (1.0 - (1.0 - u) ** 2)
        big = 0.36 + 0.55 * u
        rho = 0.16 * (1.0 - u) ** 0.8 * min(1.0, 0.4 + u * 6.0)
        for b, sc in (("ring_out", (big + rho) / (SR + Sr)), ("ring_in", max(big - rho, 0.01) / (SR - Sr))):
            pb[b].location = arm_space_loc(pb[b], tuple(A * s))
            pb[b].scale = (sc, max(rho / Sr, 0.01), sc)
    else:
        pb["ring_out"].scale = pb["ring_in"].scale = (0.001, 0.001, 0.001)
    pb["flash"].scale = (max(flash, 0.001), max(flash * 1.15, 0.001), max(flash, 0.001))
    fw_puff_pose(rig, "puff", 3, puff, rise=0.75 + 0.5 * min(burst, 1.0), drift=(0.0, 0.3), size=(0.2, 0.62), burst=burst)
    wave_flag(rig, "flag", wave, amp=gust)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        ph = 2 * math.pi * t
        pose(rig, elev=ELEV + 0.9 * math.sin(ph), slew=1.2 * math.sin(2 * ph), sway=3.5 * math.sin(ph), sway2=2.6 * math.sin(2 * ph),
             puff=2 * t, wave=2 * t)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        kick = smooth(f / 2.0) * (1.0 - smooth((f - 3) / 12.0))
        damp = math.exp(-max(f - 1, 0) / 5.0) * (1.0 - smooth((f - 17) / 7.0))
        swing = math.exp(-f / 10.0) * (1.0 - smooth((f - 17) / 7.0))
        pose(rig, back=0.1 * kick, rock=6.5 * damp * math.cos((f - 1) * 0.85) if f >= 1 else 0.0,
             squash={1: 0.1, 2: 0.06, 3: -0.03}.get(f, 0.0), slew=1.8 * damp * math.sin(f * 1.3),
             sway=-13 * swing * math.sin(f * 0.7), sway2=7 * swing * math.sin(f * 0.9),
             smoke=(f - 1) / 14.0 if f >= 1 else -1.0, flash={1: 0.9, 2: 1.3, 3: 0.85, 4: 0.4}.get(f, 0.0),
             puff=f / FIRE_LEN * 2 / 3.0, burst=3.2 * smooth((f - 1) / 3.0) * (1.0 - smooth((f - 9) / 14.0)),
             wave=f / FIRE_LEN, gust=1.0 + 1.4 * kick)
        key_pose(rig, f)
    new_action(rig, "reload", RELOAD_LEN)
    for f in range(RELOAD_LEN + 1):
        up = smooth(f / 10.0) - smooth((f - 30) / 12.0)               # the barrel tips up to load, and comes back down
        settle = -1.4 * math.sin(math.pi * min(max((f - 41) / 6.0, 0.0), 1.0))
        turn = smooth((f - 3) / 10.0) - smooth((f - 23) / 9.0)         # the jib swings in over the muzzle, and back
        if f <= 13:                                                   # the rope: hoist, down the bore, up, (swing back),
            L = L_REST + (L_HIGH - L_REST) * smooth(f / 6.0)          # down to the cradle, up to rest with the next bomb
        elif f <= 19:
            L = L_HIGH + (L_IN - L_HIGH) * smooth((f - 13) / 6.0)
        elif f <= 31:
            L = L_IN + (0.3 - L_IN) * smooth((f - 20) / 4.0)
        elif f <= 38:
            L = 0.3 + (L_DECK - 0.3) * smooth((f - 31) / 6.0)
        else:
            L = L_DECK + (L_REST - L_DECK) * smooth((f - 38) / 9.0)
        bomb = 1.0 if f <= 19 else (0.0 if f <= 36 else (0.55 if f == 37 else 1.0))
        lag = math.sin(math.pi * min(max((f - 3) / 10.0, 0.0), 1.0)) - 0.5 * math.sin(math.pi * min(max((f - 23) / 9.0, 0.0), 1.0))
        bob = math.sin(math.pi * min(max((f - 40) / 8.0, 0.0), 1.0)) * math.sin((f - 40) * 0.9)
        pose(rig, elev=ELEV + (LOAD_ELEV - ELEV) * up + settle, slew=SLEW * turn, L=L, sway=-7 * lag + 3 * bob, sway2=6 * lag,
             bomb=bomb, puff=f / RELOAD_LEN * 4 / 3.0, wave=f / RELOAD_LEN)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.0, 1.2), "dist": 11.0, "yaw": 150, "pitch": 20, "anim_target": (0.1, 0, 1.9), "anim_dist": 7.5,
           "frames": [("idle", 0), ("fire", 2), ("fire", 7), ("reload", 17), ("reload", 37)],
           "extra": [{"yaw": 160, "pitch": 15, "dist": 6.0, "target": (0, 0, 1.5)},
                     {"yaw": 35, "pitch": 30, "dist": 6.0, "target": (RT.x - 0.3, 0, 0.8)},
                     {"yaw": -35, "pitch": 30, "dist": 6.0, "target": (LF.x + 0.3, 0, 0.7)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
