"""Builds the Runic Hammer (footprint "arrow3": [0,0] front, [1,0] back-right, [-1,1] back-left), a Forge tower: a
rune-powered drop hammer whose blow lands, as a spectral hammer, on the enemies beside it (GameData.STRIKES "erupt").

    python tools/blender/build.py dwarf_hammer --out <preview dir>

One machine on one paved floor. Front hex: a towering timber-and-iron frame (two guide posts on stone footings, raking
struts out to the flank hexes, an iron-strapped crosshead with the hoisting sheave) over the great anvil stone, an
octagon of rune-carved blocks under an iron plate; between the posts hangs the hammer, a colossal banded block with
glowing runes and the team's color on its crown. Back-right: the engine that hoists it (a riveted boiler on a stone
firebox, a winch drum on timber stands, a great gear and its pinion), its chain running up to the sheave.
Back-left: the forge store under a lean-to roofed in the team's color (ingots, spare hammer faces) and a stone quench
trough. Banners in the team's color hang down the backs of the posts; a pennant flies from the frame.
The machine doesn't turn: the Head is a bare marker at the hammer (Muzzle at the anvil), the Rig hangs off the root.
idle: the hammer hangs breathing on its chain, embers drift up off the anvil's runes, the boiler smokes, the pennant
flies. fire (0.6 s): the hammer drops (it meets the anvil 0.23 s in, as the strike lands), sparks burst, a ring of
light flashes across the floor, it bounces and settles. reload (1.07 s): the winch turns and the chain hauls it up.

build_strike(): the blow itself. A spectral rune hammer appears over the enemy, smashes straight down (0.25 s in),
a rune ring flashes on the ground, shards of stone jump, and it all fades by 0.8 s.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "forgeworks_common.py"), encoding="utf-8").read())

TID = "dwarf_hammer"
CELLS = [(0, 0), (1, 0), (-1, 1)]
MID = footprint_mid(CELLS)
F = hex_to_world(0, 0, MID)
BR = hex_to_world(1, 0, MID)
BL = hex_to_world(-1, 1, MID)
TOP = 0.34
T = TOP
Z = Vector((0, 0, 1))
X = Vector((1, 0, 0))
Y = Vector((0, 1, 0))
ANVIL_TOP = T + 0.76                 # the anvil plate's top: where the hammer lands
DROP = 0.85                          # how far the hammer falls
UP_Z = ANVIL_TOP + DROP - T          # the hammer's face at rest, above the plinth (the old script's name)
HZ = ANVIL_TOP + DROP                # ... in world height
H_TALL = 0.8                         # the hammer's height
POST_X = 0.72                        # the guide posts stand this far either side of the anvil
POST_TOP = 3.18
BEAM_Z = 2.86                        # the crosshead's underside
# the engine on the back-right hex, laid out in its own frame (X: the winch's axle, +Y: toward the frame)
WINCH = Vector((1.66, -0.22, 0))
_d = Vector((WINCH.x - F.x, WINCH.y - F.y, 0)).normalized()          # from the hammer toward the winch, on the ground
SHEAVE_R = 0.2
SHEAVE = Vector((F.x, F.y, BEAM_Z + 0.2)) + _d * SHEAVE_R
EM = Matrix.Translation((WINCH.x, WINCH.y, T)) @ Matrix.Rotation(math.atan2(_d.x, -_d.y), 4, "Z")
AXLE = (EM.to_3x3() @ X).normalized()
DRUM_C = EM @ Vector((0, 0, 0.8))
PINION_C = EM @ Vector((0.5, -0.71, 0.66))
BOILER = EM @ Vector((-0.05, -0.86, 0))
STACK_TOP = Vector((BOILER.x, BOILER.y, T + 2.02))
LINKS = 8
LINK = 0.125


def _rect(z, hx, hy, c=None):
    c = c or Vector((F.x, F.y, 0))
    return [Vector((c.x + sx * hx, c.y + sy * hy, z)) for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1))]


def build_base():
    fw_reset()
    col = collection("Dwarf_hammer")
    root = empty("Dwarf_hammer", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(8)
    k = Kit()
    # ---- one paved floor under the whole machine
    fw_bed(k["stone_dark:0.35:0.85"], CELLS, T)
    fw_emit(k, "Bed", col, root, tag="no_refine")
    fw_paving(k[STONE], rnd, CELLS, T, sx=0.5, sy=0.32, skip=lambda x, y: (x - F.x) ** 2 + (y - F.y) ** 2 < 0.62 ** 2)
    fw_emit(k, "Floor", col, root, vary=0.09)
    # ---- the anvil stone: a wide footing course, an octagon of two courses of big blocks, an iron plate on top
    A = Vector((F.x, F.y, 0))
    bm_block_course(k["stone:0.3:0.9"], rnd, A, 0.86, T, 0.16, 8, depth=0.4, phase=0.5)
    round_tower(k, rnd, A, 0.68, 0.62, T + 0.16, T + 0.64, courses=2, n=8, depth=0.32, stone="stone:0.1:0.8")
    fw_emit(k, "Anvil_Stone", col, root, vary=0.08, bevel=0.014)
    fw_lathe(k[CAST], (A.x, A.y, T + 0.62), Z, [(0.6, 0.0), (0.6, 0.07), (0.52, 0.14), (0.0, 0.14)], n=8, phase=0.5, cap0=False)
    fw_hoop(k[BRASS], (A.x, A.y, T + 0.655), Z, 0.6, w=0.05, th=0.02, n=8, phase=0.5)
    fw_emit(k, "Anvil_Plate", col, root)
    # its runes: one on each block of the upper course, a sigil on the plate, a ring let into the floor round its foot
    for i in range(8):
        a = math.radians(45 * i + 22.5)
        d = Vector((math.cos(a), math.sin(a), 0))
        fw_rune(k[RUNE], A + d * 0.632 + Vector((0, 0, T + 0.52)), d.cross(Z) * -1.0, Z, 0.11, i)
    fw_ring(k[RUNE], (A.x, A.y, ANVIL_TOP - 0.004), Z, 0.3, 0.36, 0.012, n=8, phase=0.5)
    fw_rune(k[RUNE], (A.x, A.y, ANVIL_TOP + 0.004), X, Y, 0.2, "tiwaz", stroke=0.2)
    for i in range(12):
        a0, a1 = math.radians(30 * i + 4), math.radians(30 * i + 26)
        bm_beam(k[RUNE], A + Vector((math.cos(a0) * 1.0, math.sin(a0) * 1.0, T + 0.052)), A + Vector((math.cos(a1) * 1.0, math.sin(a1) * 1.0, T + 0.052)),
                0.05, 0.02)
    fw_emit(k, "Anvil_Runes", col, root)
    # ---- the frame: two guide posts on stone footings, iron-shod and banded, with iron rails down their inner faces
    for sx in (-1, 1):
        px = F.x + sx * POST_X
        bm_box(k["stone:0.15:0.8"], (0.54, 0.6, 0.3), (px + sx * 0.04, F.y, T + 0.15))
        bm_box(k[TIMBER], (0.26, 0.32, POST_TOP - T - 0.2), (px, F.y, (POST_TOP + T + 0.2) / 2))
        bm_box(k[IRON], (0.035, 0.12, HZ + H_TALL - ANVIL_TOP + 0.1), (px - sx * 0.14, F.y, (HZ + H_TALL + ANVIL_TOP + 0.1) / 2))
        for z, sw in ((T + 0.42, IRON), (1.6, BRASS), (2.5, BRASS)):
            bm_box(k[sw], (0.3, 0.36, 0.1 if sw == BRASS else 0.22), (px, F.y, z))
        bm_cyl(k[BRASS], 0.11, 0.0, 0.2, (px, F.y, POST_TOP + 0.08), seg=4, rot=(0, 0, 45))
        # raking struts: one forward inside the front hex, one out and back onto the flank hex
        for top, foot in (((px, F.y + 0.12, 2.1), (F.x + sx * 0.62, F.y + 0.76, T + 0.12)),
                          ((px + sx * 0.1, F.y - 0.1, 2.3), (F.x + sx * 1.28, F.y - 0.74, T + 0.12))):
            bm_beam(k[TIMBER], top, foot, 0.16, 0.16)
            bm_box(k["stone:0.15:0.8"], (0.36, 0.36, 0.22), (foot[0], foot[1], T + 0.11))
    # the crosshead: a great beam let into the fronts of the posts, iron-strapped; the sheave hangs in a bracket behind it
    bm_box(k[TIMBER], (2.1, 0.22, 0.3), (F.x, F.y + 0.14, BEAM_Z + 0.15))
    bm_box(k[TIMBER], (1.2, 0.16, 0.16), (F.x, F.y + 0.14, BEAM_Z + 0.38))
    for sx in (-1, 1):
        bm_box(k[IRON], (0.1, 0.26, 0.34), (F.x + sx * 0.98, F.y + 0.14, BEAM_Z + 0.15))
        bm_box(k[IRON], (0.34, 0.26, 0.1), (F.x + sx * POST_X, F.y + 0.14, BEAM_Z + 0.15))
        bm_beam(k[TIMBER], (F.x + sx * (POST_X - 0.1), F.y + 0.14, BEAM_Z - 0.42), (F.x + sx * 0.28, F.y + 0.14, BEAM_Z + 0.02), 0.12, 0.12, up=(0, 1, 0))
    side = Vector((-_d.y, _d.x, 0))
    for sg in (-1, 1):
        fw_prism(k[IRON], [SHEAVE + side * (sg * 0.09) + Vector(p) for p in ((-0.1 * _d.x, -0.1 * _d.y, -0.3), (0.12 * _d.x, 0.12 * _d.y, -0.3),
                                                                             (0.1 * _d.x, 0.1 * _d.y, 0.1), (-0.08 * _d.x, -0.08 * _d.y, 0.1))], side * (sg * 0.03))
    bm_box(k[IRON], (0.5, 0.3, 0.07), (F.x + 0.1, F.y - 0.02, BEAM_Z + 0.02))
    fw_emit(k, "Frame", col, root, bevel=0.012, vary=0.05)
    # ---- the engine (laid out in its own frame, set down by EM): timber stands for the winch, the boiler on its firebox
    for x in (-0.34, 0.3):
        for sy in (-1, 1):
            bm_beam(k[TIMBER], (x, sy * 0.36, 0.0), (x, sy * 0.05, 0.9), 0.12, 0.12, up=(1, 0, 0))
        bm_box(k[TIMBER], (0.12, 0.6, 0.1), (x, 0, 0.3))
        bm_box(k[BRASS], (0.16, 0.2, 0.14), (x, 0, 0.82))
    bm_box(k["stone:0.2:0.8"], (0.9, 0.98, 0.07), (-0.02, 0, 0.035))
    bx, by = -0.05, -0.86
    bm_block_course(k["stone:0.15:0.8"], rnd, (bx, by, 0), 0.5, 0.0, 0.17, 7, depth=0.24, skip=lambda a: 245 < a < 295)
    bm_block_course(k["stone:0.15:0.8"], rnd, (bx, by, 0), 0.47, 0.17, 0.17, 7, depth=0.24, phase=0.5, skip=lambda a: 250 < a < 290)
    bm_cyl(k["stone_dark:0.3:0.9"], 0.34, 0.34, 0.34, (bx, by, 0.17), seg=10)
    fw_place(k, m=EM)
    fw_emit(k, "Engine_Frame", col, root, bevel=0.01, vary=0.06)
    fw_lathe(k[CAST], (bx, by, 0.34), Z, [(0.4, 0.0), (0.4, 0.86), (0.33, 1.0), (0.12, 1.08), (0.1, 1.2), (0.1, 1.62), (0.15, 1.66), (0.15, 1.72), (0.09, 1.72), (0.09, 1.6)],
             n=10, cap0=False, cap1=False)
    for z in (0.44, 0.78, 1.12):
        fw_hoop(k[BRASS], (bx, by, z), Z, 0.4, w=0.07, th=0.022, n=10)
        fw_studs_round(k[IRON], (bx, by, z), Z, 0.422, 10, sr=0.024, h=0.02)
    fw_hoop(k[BRASS], (bx, by, 1.74), Z, 0.1, w=0.06, th=0.02, n=10)
    # a pipe from the boiler's shoulder to the pinion's engine block
    bm_tube(k[BRASS], [(bx + 0.3, by, 1.22), (bx + 0.52, by, 1.2), (bx + 0.55, by + 0.02, 0.86)], 0.055, n=6)
    bm_box(k[CAST], (0.26, 0.3, 0.36), (0.42, -0.74, 0.66))
    bm_box(k["stone:0.2:0.8"], (0.34, 0.4, 0.5), (0.42, -0.74, 0.25))
    fw_place(k, m=EM)
    fw_emit(k, "Engine_Boiler", col, root)
    bm_box(k[FIRE], (0.3, 0.05, 0.22), (bx, by - 0.3, 0.18))
    fw_rune(k[RUNE], (bx, by - 0.405, 0.95), X, Z, 0.11, "othala")
    fw_place(k, m=EM)
    fw_emit(k, "Engine_Glow", col, root)
    # the chain from the sheave down to the winch (it only hangs there: the links on the hammer's side move)
    c0 = SHEAVE + _d * (SHEAVE_R * 0.7) + Vector((0, 0, SHEAVE_R * 0.72))
    c1 = DRUM_C - _d * 0.05 + Vector((0, 0, 0.24))
    fw_chain(k[IRON], c0, c1, size=0.11, up=tuple(side), slack=0.05)
    fw_emit(k, "Chain_Run", col, root)
    # ---- the forge store on the back-left hex: a lean-to on four posts, its roof in the team's tiles
    sx0, sx1, sy0, sy1 = BL.x - 0.6, BL.x + 0.3, BL.y - 0.62, BL.y + 0.2
    for x, y, h in ((sx0, sy0, 0.7), (sx1, sy0, 0.7), (sx0, sy1, 1.3), (sx1, sy1, 1.3)):
        bm_box(k[TIMBER], (0.12, 0.12, h), (x, y, T + h / 2))
        bm_box(k["stone:0.2:0.8"], (0.22, 0.22, 0.1), (x, y, T + 0.05))
    for x in (sx0, sx1):
        bm_beam(k[TIMBER], (x, sy0 - 0.16, T + 0.6), (x, sy1 + 0.14, T + 1.34), 0.1, 0.1)
    bm_beam(k[TIMBER], (sx0, sy1, T + 1.26), (sx1, sy1, T + 1.26), 0.1, 0.1)
    bm_beam(k[TIMBER], (sx0, sy0, T + 0.66), (sx1, sy0, T + 0.66), 0.1, 0.1)
    bm_block_wall(k["stone:0.2:0.85"], rnd, (sx0, sy0 + 0.06), (sx0, sy1 - 0.06), T, T + 0.5, th=0.16, course=0.17, block=0.3)
    fw_emit(k, "Store", col, root, bevel=0.01, vary=0.07)
    bm_tile_slope(k["team!:0.1:0.7"], rnd, (sx0 - 0.14, sy0 - 0.2, T + 0.6), (sx1 + 0.14, sy0 - 0.2, T + 0.6),
                  (sx0 - 0.14, sy1 + 0.16, T + 1.42), (sx1 + 0.14, sy1 + 0.16, T + 1.42), rows=5, cols=4, th=0.05)
    fw_emit(k, "Store_Roof", col, root, vary=0.08)
    # the quench trough: a stone tank of water between the store and the anvil; a spare hammer face on skids
    q = Vector((BL.x + 0.86, BL.y - 0.12, 0))
    for dx, dy, w, d in ((0, 0.19, 0.74, 0.1), (0, -0.19, 0.74, 0.1), (0.32, 0, 0.1, 0.28), (-0.32, 0, 0.1, 0.28)):
        bm_box(k["stone:0.15:0.8"], (w, d, 0.3), (q.x + dx, q.y + dy, T + 0.15), (0, 0, 0))
    bm_box(k["stone_dark:0.3:0.8"], (0.6, 0.3, 0.06), (q.x, q.y, T + 0.05))
    fw_place(k, m=Matrix.Translation(q) @ Matrix.Rotation(math.radians(-30), 4, "Z") @ Matrix.Translation(-q))
    fw_emit(k, "Trough", col, root, bevel=0.012, vary=0.07)
    bm_box(k["water"], (0.56, 0.28, 0.04), (q.x, q.y, T + 0.23))
    fw_place(k, m=Matrix.Translation(q) @ Matrix.Rotation(math.radians(-30), 4, "Z") @ Matrix.Translation(-q))
    fw_emit(k, "Trough_Water", col, root)
    kk = [("resources/Iron_Bars_Stack_Medium", (BL.x - 0.3, BL.y - 0.38, T + 0.03), 90, 0.52),
          ("resources/Gold_Bars_Stack_Small", (BL.x + 0.02, BL.y - 0.05, T + 0.03), 20, 0.5),
          ("resources/Iron_Bars_Stack_Small", (BL.x - 0.36, BL.y + 0.0, T + 0.03), 0, 0.5)]
    for i, (rel, loc, rot, sc) in enumerate(kk):
        kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d" % i)
    head = empty("Head", col, root, (F.x, F.y, T + UP_Z), 0.5, "SINGLE_ARROW")
    empty("Muzzle", col, head, (0, 0, -UP_Z + 0.82), 0.2, "SPHERE")
    return root


BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "hammer": ((F.x, F.y, HZ), (F.x, F.y, HZ + 0.4), "root"),
    "sheave": (tuple(SHEAVE), tuple(SHEAVE + Vector((-_d.y, _d.x, 0)) * 0.2), "root"),
    "drum": (tuple(DRUM_C), tuple(DRUM_C + AXLE * 0.3), "root"),
    "pinion": (tuple(PINION_C), tuple(PINION_C + AXLE * 0.2), "root"),
    "sparks": ((F.x, F.y, ANVIL_TOP), (F.x, F.y, ANVIL_TOP + 0.2), "root"),
    "flash": ((F.x, F.y, T + 0.06), (F.x, F.y, T + 0.26), "root"),
}
for _i in range(LINKS):
    _z = HZ + H_TALL + 0.12 + _i * LINK
    BONES["link.%d" % _i] = ((F.x, F.y, _z), (F.x, F.y, _z + 0.1), "hammer")
fw_puff_bones(BONES, "puff", STACK_TOP, 3, "root")
fw_puff_bones(BONES, "mote", (F.x, F.y, ANVIL_TOP + 0.05), 4, "root")
PEN = Vector((F.x - POST_X, F.y, POST_TOP + 0.62))
flag_bones(BONES, "flag", tuple(PEN), (-1, -0.25, 0), 0.62, segs=3)
for _s, _sx in (("L", -1), ("R", 1)):
    flag_bones(BONES, "ban" + _s, (F.x + _sx * POST_X, F.y - 0.175, 2.52), (0, 0, -1), 0.9, segs=3)


def _hammer(k, glow=RUNE, body=CAST, face=IRON, band=BRASS, crown="team!:0.1:0.6", c=None, z0=0.0, runes=True):
    """The hammer head, its face at z0 over c: a striking face, a banded block with runes fore and aft, sloped
    shoulders, a crown plate. Shared by the tower and the strike (which casts it in light)."""
    c = c or Vector((F.x, F.y, 0))

    def box(key, size, z):
        bm_box(k[key], size, (c.x, c.y, z0 + z))
    box(face, (0.98, 0.76, 0.14), 0.07)
    box(body, (0.86, 0.66, 0.44), 0.36)
    box(band, (0.9, 0.7, 0.06), 0.2)
    box(band, (0.9, 0.7, 0.06), 0.52)
    bm_loft(k[body], [_rect(z0 + 0.58, 0.43, 0.33, c), _rect(z0 + 0.72, 0.27, 0.22, c)])
    box(face, (0.56, 0.46, 0.06), 0.74)
    box(crown, (0.46, 0.36, 0.03), 0.785)
    for sx in (-1, 1):
        for sy in (-1, 1):
            fw_stud(k[band], (c.x + sx * 0.36, c.y + sy * 0.332, z0 + 0.36), (0, sy, 0), r=0.04, h=0.03)
    if runes:
        for sy in (-1, 1):
            for i, x in enumerate((-0.17, 0.17)):
                fw_rune(k[glow], (c.x + x, c.y + sy * 0.334, z0 + 0.36), (-sy, 0, 0), Z, 0.1, i + (2 if sy > 0 else 0), stroke=0.2)


def build_head():
    col = collection("Dwarf_hammer")
    root = bpy.data.objects["Dwarf_hammer"]
    rig = make_rig(col, root, BONES)
    k = Kit()
    rnd = random.Random(9)
    # ---- the hammer: the head, brass guide shoes that ride the posts' rails, the shackle its chain hangs from
    _hammer(k, z0=HZ)
    for sx in (-1, 1):
        bm_box(k[BRASS], (0.2, 0.34, 0.26), (F.x + sx * 0.49, F.y, HZ + 0.36))
    fw_ring(k[IRON], (F.x, F.y - 0.03, HZ + H_TALL + 0.07), Y, 0.05, 0.1, 0.06, n=8)
    fw_emit(k, "Head_Hammer", col, rig=rig, bone="hammer", bevel=0.014)
    for i in range(LINKS):
        z = HZ + H_TALL + 0.12 + i * LINK
        a, b = Vector((F.x, F.y, z - LINK * 0.14)), Vector((F.x, F.y, z + LINK * 1.14))
        if i % 2:
            bm_beam(k[IRON], a, b, 0.07, 0.026, up=(0, 1, 0))
        else:
            bm_beam(k[IRON], a, b, 0.026, 0.07, up=(0, 1, 0))
        fw_emit(k, "Head_Link%d" % i, col, rig=rig, bone="link.%d" % i)
    # ---- the sheave, the winch drum with its great gear, the pinion
    side = Vector((-_d.y, _d.x, 0))
    fw_lathe(k[BRASS], SHEAVE - side * 0.05, side, [(0.06, 0.0), (SHEAVE_R, 0.0), (SHEAVE_R, 0.03), (SHEAVE_R - 0.05, 0.05), (SHEAVE_R, 0.07), (SHEAVE_R, 0.1), (0.06, 0.1)], n=10)
    for i in range(4):
        a = math.radians(90 * i + 20)
        dd = _d * math.cos(a) + Z * math.sin(a)
        bm_box(k[IRON], (0.03, 0.03, 0.03), tuple(SHEAVE + dd * 0.12 + side * 0.052))
    fw_emit(k, "Head_Sheave", col, rig=rig, bone="sheave")
    fw_lathe(k["wood:0.2:0.8"], (-0.26, 0, 0.8), X, [(0.2, 0.0), (0.2, 0.5)], n=10)
    for x in (-0.27, 0.22):
        fw_lathe(k[IRON], (x, 0, 0.8), X, [(0.3, 0.0), (0.3, 0.04)], n=10)
    fw_lathe(k[IRON], (-0.2, 0, 0.8), X, [(0.235, 0.0), (0.235, 0.34)], n=10, cap0=False, cap1=False)
    fw_lathe(k[IRON], (-0.46, 0, 0.8), X, [(0.05, 0.0), (0.05, 1.1)], n=6)
    fw_gear(k["gold:0.2:0.85"], (0.5, 0, 0.8), X, 0.5, teeth=14, w=0.11, tooth=0.09, hub=0.26, spokes=4, rim=0.2)
    fw_place(k, m=EM)
    fw_emit(k, "Head_Drum", col, rig=rig, bone="drum")
    fw_gear(k[CAST], (0.5, -0.71, 0.66), X, 0.16, teeth=6, w=0.13, tooth=0.08, hub=0.5, spokes=0, rim=0.5)
    fw_lathe(k[IRON], (0.3, -0.71, 0.66), X, [(0.045, 0.0), (0.045, 0.3)], n=6)
    fw_place(k, m=EM)
    fw_emit(k, "Head_Pinion", col, rig=rig, bone="pinion")
    # ---- the blow: sparks flying off the anvil, a ring of light racing over the floor (both hidden until it lands)
    for i in range(12):
        a = 2 * math.pi * i / 12 + rnd.uniform(-0.2, 0.2)
        dd = Vector((math.cos(a), math.sin(a), rnd.uniform(0.25, 1.0))).normalized()
        p = Vector((F.x, F.y, ANVIL_TOP)) + dd * rnd.uniform(0.5, 0.75)
        bm_crystal(k[HOT], p - dd * 0.1, p + dd * rnd.uniform(0.1, 0.2), 0.035, n=3, shoulder=0.4, foot=0.2)
    fw_fx(fw_emit(k, "Head_Sparks", col, rig=rig, bone="sparks"))
    fw_ring(k[HOT], (F.x, F.y, T + 0.062), Z, 0.86, 1.0, 0.03, n=16)
    for i in range(8):
        a = math.radians(45 * i + 22.5)
        dd = Vector((math.cos(a), math.sin(a), 0))
        fw_rune(k[HOT], Vector((F.x, F.y, T + 0.07)) + dd * 1.16, dd.cross(Z), dd, 0.09, i + 3)
    fw_fx(fw_emit(k, "Head_Flash", col, rig=rig, bone="flash"))
    # embers drifting up off the anvil's runes, smoke from the boiler's stack
    for i in range(4):
        a = math.radians(90 * i + 30)
        bm_blob(k[HOT], rnd, Vector((F.x + math.cos(a) * 0.42, F.y + math.sin(a) * 0.42, ANVIL_TOP + 0.05)), 0.045, jitter=0.2)
        fw_fx(fw_emit(k, "Head_Mote%d" % i, col, rig=rig, bone="mote.%d" % i))
    fw_puffs("Head_Puff", col, rig, "puff", STACK_TOP, 3, r=0.16)
    # ---- the team's colors: a pennant on the left post, a banner down the back of each post
    bm_box(k[TIMBER], (0.04, 0.04, 0.72), (PEN.x, PEN.y, POST_TOP + 0.36))
    fw_emit(k, "Pennant_Pole", col, root)
    flag_part("Pennant", col, rig, "flag", tuple(PEN), (-1, -0.25, 0), 0.62, 0.3, segs=3, tail="swallow")
    for s, sx in (("L", -1), ("R", 1)):
        flag_part("Banner" + s, col, rig, "ban" + s, (F.x + sx * POST_X - 0.11, F.y - 0.175, 2.52), (0, 0, -1), 0.9, 0.22, segs=3,
                  tail="point", hang=(1, 0, 0))
        bm_box(k[BRASS], (0.3, 0.05, 0.05), (F.x + sx * POST_X, F.y - 0.185, 2.54))
    fw_emit(k, "Banner_Rods", col, root)
    return rig


IDLE_LEN = 60
FIRE_LEN = 18
RELOAD_LEN = 32
HIT_F = 7                     # the frame the hammer meets the anvil (0.233 s; the strike's blow is at 0.25 s)
TURN = math.degrees(DROP / 0.22)        # how far the winch turns to pay the chain out


def pose(rig, down=0.0, sparks=0.0, flash=0.0, t=0.0, wave=0.0, breathe=0.0, gust=1.0):
    """down: 0 hanging ready .. 1 on the anvil; sparks / flash: the burst's size (0 = hidden); t: time through the
    idle loop (smoke, embers); wave: the pennant's phase."""
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    drop = down * DROP - breathe
    pb["hammer"].location = arm_space_loc(pb["hammer"], (0, 0, -drop))
    for i in range(LINKS):
        z = HZ + H_TALL + 0.12 + (i + 1.0) * LINK - drop
        pb["link.%d" % i].scale = (1, 1, 1) if z < SHEAVE.z - SHEAVE_R * 0.3 else (0.001, 0.001, 0.001)
    pb["sheave"].rotation_quaternion = q(pb["sheave"], (-_d.y, _d.x, 0), -math.degrees(drop / SHEAVE_R))
    pb["drum"].rotation_quaternion = q(pb["drum"], tuple(AXLE), down * TURN)
    pb["pinion"].rotation_quaternion = q(pb["pinion"], tuple(AXLE), -down * TURN * 14 / 6.0)
    pb["sparks"].scale = (max(sparks, 0.001),) * 3
    pb["flash"].scale = (max(flash, 0.001), 1.0 if flash > 0.01 else 0.001, max(flash, 0.001))      # (across, up, across): the bone stands upright
    fw_puff_pose(rig, "puff", 3, t * 2, rise=0.8, drift=(0.25, -0.1), size=(0.5, 1.5))
    fw_puff_pose(rig, "mote", 4, t * 3, rise=0.75, drift=(0.0, 0.0), size=(1.0, 0.5))
    wave_flag(rig, "flag", wave, amp=gust)
    for s in ("L", "R"):
        wave_flag(rig, "ban" + s, wave + (0.3 if s == "R" else 0.0), amp=0.35 * gust, axis=(1, 0, 0))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        pose(rig, t=t, wave=t * 2, breathe=0.012 * math.sin(2 * math.pi * t))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    bounce = {8: 0.925, 9: 0.9, 10: 0.925, 11: 1.0, 12: 0.985, 13: 1.0}
    for f in range(FIRE_LEN + 1):
        if f <= 1:
            down = -0.03 * f                               # the latch lifts it a hair
        elif f <= HIT_F:
            down = -0.03 + 1.03 * ((f - 1) / float(HIT_F - 1)) ** 2
        else:
            down = bounce.get(f, 1.0)
        k = f - HIT_F
        sparks = 0.0 if k < 0 or k > 6 else (0.55, 1.0, 1.35, 1.6, 1.75, 1.85, 1.9)[k]
        flash = 0.0 if k < 0 or k > 7 else (0.55, 0.85, 1.05, 1.2, 1.3, 1.38, 1.44, 1.48)[k]
        pose(rig, down=down, sparks=sparks, flash=flash, t=f / IDLE_LEN, wave=f / IDLE_LEN * 2, gust=1.0 + (1.2 if 0 <= k < 6 else 0.0))
        if 0 <= k <= 6:                                    # the sparks thin out as they fly
            thin = 1.0 - k / 7.0
            rig.pose.bones["sparks"].scale = (sparks, sparks * (0.5 + 0.5 * thin), sparks)
        key_pose(rig, f)
    new_action(rig, "reload", RELOAD_LEN)
    for f in range(RELOAD_LEN + 1):
        up = smooth((f - 3) / 24.0)
        over = 0.02 * math.sin(math.pi * min(max((f - 27) / 5.0, 0.0), 1.0))
        pose(rig, down=1.0 - up - over, t=(FIRE_LEN + f) / IDLE_LEN, wave=(FIRE_LEN + f) / IDLE_LEN * 2)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.1, 1.5), "dist": 11.0, "yaw": 150, "pitch": 20, "anim_target": (F.x, F.y, 1.7), "anim_dist": 7.0,
           "frames": [("idle", 0), ("fire", 5), ("fire", 8), ("fire", 11), ("reload", 16)],
           "extra": [{"yaw": 170, "pitch": 12, "dist": 5.0, "target": (F.x, F.y, 1.6)},
                     {"yaw": 20, "pitch": 30, "dist": 5.5, "target": (BR.x, BR.y, 0.9)},
                     {"yaw": -25, "pitch": 30, "dist": 5.5, "target": (BL.x, BL.y, 0.8)}]}


def build_all():
    build_base()
    build_head()
    build_anims()


# ---------------------------------------------------------------------------------------------- the strike
# What the game plays on the enemy the hammer hits (Strike, GameData.STRIKES "erupt"): the hammer's ghost, cast in
# forge-light, bursts into being over the enemy, hangs a beat and smashes straight down on it (the blow: frame 7,
# 0.23 s), a shockwave and a wheel of runes flash across the ground, chips of stone and embers jump, and the ghost
# thins away upward. The model stands on the enemy's spot on the road; +Y points away from the tower.
STRIKE_LEN = 25
S_HIT = 7
S_HIGH, S_LOW = 1.42, 0.4            # the ghost's striking face: where it appears, where the blow stops
S_SHARDS = 9
GHOST = "glow:1.0,0.4,0.05,0.62"            # its body: deep forge orange
GHOST_HI = "glow:1.0,0.68,0.16,0.95"        # its face, bands, the shockwave
GHOST_RUNE = "glow:1.0,0.92,0.5,1.15"       # its runes, the flash


def build_strike():
    fw_reset()
    col = collection("Dwarf_hammer_strike")
    root = empty("Dwarf_hammer_strike", col, None, (0, 0, 0), 0.5, "ARROWS")
    rnd = random.Random(12)
    O = Vector((0, 0, 0))
    bones = {"root": ((0, 0, 0), (0, 0, 0.2), None),
             "hammer": ((0, 0, S_HIGH), (0, 0, S_HIGH + 0.4), "root"),
             "trail": ((0, 0, S_HIGH + 0.78), (0, 0, S_HIGH + 1.18), "hammer"),
             "ring_in": ((0, 0, 0.05), (0, 0, 0.25), "root"),
             "ring_out": ((0, 0, 0.05), (0, 0, 0.25), "root"),
             "runes": ((0, 0, 0.05), (0, 0, 0.25), "root"),
             "flash": ((0, 0, S_LOW), (0, 0, S_LOW + 0.2), "root")}
    fly = []
    for i in range(S_SHARDS):
        a = 2 * math.pi * (i + 0.5 + rnd.uniform(-0.2, 0.2)) / S_SHARDS
        d = Vector((math.cos(a), math.sin(a), 0))
        fly.append((d, rnd.uniform(0.9, 1.45), rnd.uniform(1.3, 2.2), rnd.uniform(0.1, 0.16)))
        bones["shard%d" % i] = (tuple(d * 0.5 + Vector((0, 0, 0.12))), tuple(d * 0.5 + Vector((0, 0, 0.32))), "root")
    rig = make_rig(col, root, bones)
    k = Kit()
    # the ghost of the hammer, and the streak of light it falls down
    _hammer(k, glow=GHOST_RUNE, body=GHOST, face=GHOST_HI, band=GHOST_HI, crown=GHOST_RUNE, c=O, z0=S_HIGH)
    for sx in (-1, 1):
        fw_rune(k[GHOST_RUNE], (sx * 0.434, 0, S_HIGH + 0.36), (0, sx, 0), Z, 0.1, "tiwaz" if sx > 0 else "othala", stroke=0.2)
    fw_fx(fw_emit(k, "Strike_Hammer", col, rig=rig, bone="hammer"))
    for x, y, r, h in ((0, 0, 0.2, 1.5), (0.3, 0.2, 0.08, 1.0), (-0.32, -0.16, 0.08, 1.15), (0.26, -0.24, 0.06, 0.8), (-0.24, 0.25, 0.06, 0.9)):
        fw_lathe(k[GHOST_HI], (x, y, S_HIGH + 0.78), Z, [(r, 0.0), (r * 0.7, h * 0.45), (0.0, h)], n=4, phase=0.5)
    fw_fx(fw_emit(k, "Strike_Trail", col, rig=rig, bone="trail"))
    # the shockwave: a band of light whose inner and outer edges ride two bones, so it can widen and thin away
    fw_ring(k[GHOST_HI], (0, 0, 0.04), Z, 0.8, 1.0, 0.035, n=20)
    for o in fw_fx(fw_emit(k, "Strike_Wave", col, rig=rig, bone="ring_out")):
        fw_skin(o, rig, lambda co: {"ring_in": 1.0} if math.hypot(co.x, co.y) < 0.9 else {"ring_out": 1.0})
    # the wheel of runes
    fw_ring(k[GHOST_RUNE], (0, 0, 0.045), Z, 0.4, 0.45, 0.02, n=16)
    for i in range(8):
        a = math.radians(45 * i)
        d = Vector((math.cos(a), math.sin(a), 0))
        fw_rune(k[GHOST_RUNE], d * 0.66 + Vector((0, 0, 0.05)), d.cross(Z), d, 0.13, i, stroke=0.2)
        a2 = a + math.radians(22.5)
        bm_crystal(k[GHOST_HI], Vector((math.cos(a2) * 0.5, math.sin(a2) * 0.5, 0.05)), Vector((math.cos(a2) * 0.86, math.sin(a2) * 0.86, 0.05)),
                   0.035, n=4, shoulder=0.3, foot=0.3)
    fw_fx(fw_emit(k, "Strike_Runes", col, rig=rig, bone="runes"))
    # the flash of the blow: a burst of spikes of light from under the face
    for i in range(10):
        a = 2 * math.pi * i / 10 + rnd.uniform(-0.15, 0.15)
        d = Vector((math.cos(a), math.sin(a), rnd.uniform(0.05, 0.6))).normalized()
        p = Vector((0, 0, S_LOW)) + d * 0.5
        bm_crystal(k[GHOST_RUNE], p, p + d * rnd.uniform(0.45, 0.8), 0.07, n=4, shoulder=0.25, foot=0.3)
    fw_fx(fw_emit(k, "Strike_Flash", col, rig=rig, bone="flash"))
    # chips of the road and embers, thrown out by the blow
    for i, (d, _, _, r) in enumerate(fly):
        c = d * 0.5 + Vector((0, 0, 0.12))
        if i % 3 == 2:
            bm_blob(k[GHOST_RUNE], rnd, c, r * 0.6, jitter=0.2)
            fw_fx(fw_emit(k, "Strike_Shard%d" % i, col, rig=rig, bone="shard%d" % i))
        else:
            bm_boulder(k["stone:0.15:0.9"], rnd, c - Vector((0, 0, r * 0.6)), r, squash=(1.2, 0.8, 0.8), n=8, sink=0.0)
            fw_emit(k, "Strike_Shard%d" % i, col, rig=rig, bone="shard%d" % i)
    new_action(rig, "strike", STRIKE_LEN)
    pb = rig.pose.bones
    bounce = {8: 0.09, 9: 0.15, 10: 0.11, 11: 0.03, 12: 0.0, 13: 0.02}
    squash = {7: (1.14, 0.78), 8: (0.95, 1.08), 9: (1.0, 1.0)}
    for f in range(STRIKE_LEN + 1):
        rest_pose(rig)
        if f <= 3:                                         # it bursts into being overhead and rears a little
            z = S_HIGH + 0.14 * smooth(f / 3.0)
        elif f <= S_HIT:                                   # ... and falls
            z = S_HIGH + 0.14 - (S_HIGH + 0.14 - S_LOW) * ((f - 3) / float(S_HIT - 3)) ** 2
        else:
            z = S_LOW + bounce.get(f, 0.0)
        gone = smooth((f - 14) / 9.0)
        s = max(0.02, smooth(f / 2.0) * (1.0 - gone))
        sq = squash.get(f, (1.0, 1.0))
        h = pb["hammer"]
        h.location = arm_space_loc(h, (0, 0, z - S_HIGH + 0.7 * gone))
        h.scale = (s * sq[0], s * sq[1] * (1.0 + 0.9 * gone), s * sq[0])          # upright bones: (across, up, across)
        tr = {4: 0.45, 5: 0.9, 6: 1.25, 7: 1.0, 8: 0.45, 9: 0.15}.get(f, 0.0)
        pb["trail"].scale = (1.0, tr, 1.0) if tr > 0.0 else (0.001, 0.001, 0.001)
        u = (f - S_HIT) / 13.0
        if 0.0 <= u < 1.0:
            R = 0.42 + 1.2 * (1.0 - (1.0 - u) ** 2)
            w = 0.36 * (1.0 - u) ** 1.3
            pb["ring_out"].scale = (R, 1.0, R)
            pb["ring_in"].scale = (max(R - w, 0.01) / 0.8, 1.0, max(R - w, 0.01) / 0.8)
        else:
            pb["ring_out"].scale = pb["ring_in"].scale = (0.001, 0.001, 0.001)
        rs = {S_HIT: 0.55, S_HIT + 1: 0.95, S_HIT + 2: 1.08}.get(f, 1.0) * (1.0 - smooth((f - 17) / 7.0)) if f >= S_HIT else 0.0
        pb["runes"].scale = (max(rs, 0.001), 1.0 if rs > 0.01 else 0.001, max(rs, 0.001))
        pb["runes"].rotation_quaternion = arm_space_quat(pb["runes"], (0, 0, 1), 3.5 * (f - S_HIT))
        fl = {S_HIT: 0.75, S_HIT + 1: 1.25, S_HIT + 2: 1.0, S_HIT + 3: 0.5}.get(f, 0.0)
        pb["flash"].scale = (max(fl, 0.001),) * 3
        for i, (d, reach, vz, r) in enumerate(fly):        # thrown out and up, tumbling, gone as they land
            t = min(max((f - S_HIT + 0.5) / 13.0, 0.0), 1.0)
            b = pb["shard%d" % i]
            b.location = arm_space_loc(b, tuple(d * (reach * t) + Vector((0, 0, vz * t * (1.0 - t) * 1.6))))
            b.rotation_quaternion = arm_space_quat(b, (d.y, -d.x, 0), -400 * t)
            b.scale = (max(0.001, smooth(t / 0.1) * (1.0 - smooth((t - 0.75) / 0.25))),) * 3
        key_pose(rig, f)
    bpy.context.scene.frame_set(0)


STRIKE_PREVIEW = {"frames": [2, 5, 7, 9, 13, 19], "dist": 7.0, "target": (0, 0, 1.0)}
