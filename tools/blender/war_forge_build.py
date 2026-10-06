"""Builds the Forge of Ages (footprint "fan4": [0,0] back, [-1,0] left, [0,-1] front, [1,-1] right), the Forge's
Tier IV support tower: a grand dwarven forge whose idle is the show (it never aims or fires).

    python tools/blender/build.py war_forge --out <preview dir>

One forge on one paved floor. Front hex: the furnace hall, a stone house with crow-stepped gables under a roof of the
team's heavy tiles, its great arched mouth glowing toward the player, a massive round chimney stack rising through
the roof behind. From the mouth a channel of molten metal runs straight back across the middle to the casting pit on
the back hex, where a greatsword and ingots glow in their moulds. Left hex: the hammer works: a giant anvil on its
block, two trip hammers on a timber frame beating the blade on it in turn, driven by a cam shaft and a rune-hubbed
cog. Right hex: the great bellows pumping into the hall's flank, a quench trough steaming beside the channel, the rack
of finished weapons and shields. Rune pillars stand at the four corners where the hexes meet.
idle (2 s, loops): the hammers rise and fall alternately (sparks at each blow), the cam shaft and cog turn, the
bellows pump, the fire flickers, metal flows down the channel and pulses in the mould, the chimney smokes and throws
embers, the trough steams, the pennant flies.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "forgeworks_common.py"), encoding="utf-8").read())

TID = "war_forge"
CELLS = [(0, 0), (-1, 0), (0, -1), (1, -1)]
MID = footprint_mid(CELLS)
BK = hex_to_world(0, 0, MID)          # (0, -1.04)
LF = hex_to_world(-1, 0, MID)         # (-1.8, 0)
FC = hex_to_world(0, -1, MID)         # (0, 1.04)
RT = hex_to_world(1, -1, MID)         # (1.8, 0)
TOP = 0.34
T = TOP
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
WALL = "stone:0.2:0.88"
TEAM = "team!:0.1:0.72"
# the hall
HW, HY0, HY1, WT = 0.8, 0.3, 1.42, 0.2            # half width, front (mouth) and back walls, wall thickness
WH, RIDGE = 1.5, 2.4                               # the walls' top and the ridge above the floor
MOUTH_W, SPRING = 0.84, 0.48                       # the mouth: its width, the height its arch springs from
FY = HY0 + WT / 2
CHIM = Vector((0, 1.5, 0))
CHIM_TOP = T + 3.5
# the anvil and the hammers
ANV = Vector((-1.02, 0, 0))
ANV_TOP = T + 0.74
PIV_X, PIV_Z = -1.95, T + 1.0                      # the hammers' pivot
HAM_Y = {"A": 0.2, "B": -0.2}
SHAFT = Vector((-2.4, 0, T + 1.2))                 # the cam shaft
# the channel and the casting pit
CH_Y0, CH_Y1 = HY0 - 0.02, -0.78
PIT = Vector((0, -1.2, 0))
# the bellows and the trough
B_HINGE = Vector((1.12, 0.5, T + 0.56))
B_BACK = Vector((0.9, -0.44, 0)).normalized()
B_LEN, B_WIDE, B_OPEN = 1.1, 0.66, 24.0
TROUGH = Vector((0.72, -0.2, 0))
PILLARS = [(sx * 0.98, sy * 0.8) for sy in (1, -1) for sx in (-1, 1)]
FLAG_TOP = Vector((0, FY, T + RIDGE + 0.74))
FLAG_DIR = (-1, -0.25, 0)
BAN_TOP = Vector((-0.26, FY - 0.135, T + WH + 0.98))     # the great banner down the front gable
BAN_LEN = 1.22
_BEL = {}


def _sq(x, y, z, h):
    return [Vector((x - h, y - h, z)), Vector((x + h, y - h, z)), Vector((x + h, y + h, z)), Vector((x - h, y + h, z))]


def _arch_pts(w, s, y, z0, n=8):
    r = w / 2
    pts = [(-r, y, z0), (r, y, z0), (r, y, z0 + s)]
    for i in range(1, n):
        a = math.pi * i / n
        pts.append((r * math.cos(a), y, z0 + s + r * math.sin(a)))
    pts.append((-r, y, z0 + s))
    return pts


def _kite(k, c, w, h):
    """A kite shield in the team's color standing in the XZ plane at c, its face toward -Y, a brass boss."""
    pts = [(-w / 2, h * 0.55), (w / 2, h * 0.55), (w * 0.44, h * 0.1), (0.0, -h * 0.45), (-w * 0.44, h * 0.1)]
    fw_prism(k[TEAM], [Vector((c.x + x, c.y, c.z + z)) for x, z in pts], Vector((0, 0.035, 0)))
    fw_stud(k[BRASS], (c.x, c.y - 0.002, c.z + h * 0.12), (0, -1, 0), r=0.05, h=0.03)
    bm_box(k[BRASS], (0.025, 0.012, h * 0.85), (c.x, c.y - 0.004, c.z + h * 0.07))


def _round_shield(k, c, r):
    fw_lathe(k[TEAM], c, (0, -1, 0), [(0.0, 0.0), (r, 0.0), (r, 0.035), (0.0, 0.035)], n=8, phase=0.5)
    fw_stud(k[BRASS], c + Vector((0, -0.037, 0)), (0, -1, 0), r=r * 0.3, h=0.035)
    fw_hoop(k[IRON], c + Vector((0, -0.018, 0)), (0, -1, 0), r, w=0.03, th=0.012, n=8, phase=0.5)


def build_base():
    fw_reset()
    col = collection("War_forge")
    root = empty("War_forge", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(23)
    k = Kit()
    # ---- one paved floor, the hall and the pit left out of it
    fw_bed(k["stone_dark:0.35:0.85"], CELLS, T)
    fw_emit(k, "Bed", col, root, tag="no_refine")

    def skip(x, y):
        return (-HW - 0.04 < x < HW + 0.04 and HY0 - 0.04 < y < HY1 + 0.04) or (abs(x - PIT.x) < 0.46 and abs(y - PIT.y) < 0.44) \
            or (x - CHIM.x) ** 2 + (y - CHIM.y) ** 2 < 0.38 ** 2
    fw_paving(k[STONE], rnd, CELLS, T, sx=0.5, sy=0.32, skip=skip)
    fw_emit(k, "Floor", col, root, vary=0.09)
    # ---- the hall: coursed walls, the wall over the mouth, crow-stepped gables front and back
    for sx in (-1, 1):
        bm_block_wall(k[WALL], rnd, (sx * (HW - WT / 2), HY0), (sx * (HW - WT / 2), HY1), T, T + WH, th=WT, course=0.3, block=0.56)
    bm_block_wall(k[WALL], rnd, (-HW + WT, HY1 - WT / 2), (HW - WT, HY1 - WT / 2), T, T + WH, th=WT, course=0.3, block=0.6)
    bm_block_wall(k[WALL], rnd, (-HW + WT, FY), (HW - WT, FY), T + SPRING + MOUTH_W / 2 + 0.1, T + WH, th=WT, course=0.25, block=0.4)
    for sx in (-1, 1):
        bm_box(k[WALL], (0.22, WT, 0.3), (sx * 0.49, FY, T + SPRING + MOUTH_W / 2 - 0.03))
    STEPS = [(0.0, 0.3, 0.86), (0.3, 0.6, 0.62), (0.6, 0.9, 0.38), (0.9, 1.1, 0.16)]
    for gy in (FY, HY1 - WT / 2):
        for z0, z1, hw in STEPS:
            bm_block_wall(k[WALL], rnd, (-hw, gy), (hw, gy), T + WH + z0, T + WH + z1, th=WT + 0.02, course=z1 - z0, block=0.36)
            bm_box(k["stone:0.0:0.55"], (2 * hw + 0.1, WT + 0.1, 0.05), (0, gy, T + WH + z1 + 0.025))
    fw_emit(k, "Hall_Walls", col, root, vary=0.08)
    bm_arch(k["stone_warm:0.15:0.75"], (0, FY, T), (1, 0, 0), MOUTH_W, SPRING, th=0.14, depth=0.3, n=7)
    fw_emit(k, "Hall_Arch", col, root, vary=0.06)
    bm_box(k[BRASS], (0.17, 0.34, 0.2), (0, FY, T + SPRING + MOUTH_W / 2 + 0.07))
    fw_emit(k, "Hall_Keystone", col, root, bevel=0.01)
    fw_rune(k[RUNE], (0, FY - 0.173, T + SPRING + MOUTH_W / 2 + 0.07), (1, 0, 0), Z, 0.08, "dagaz", stroke=0.2)
    for sx in (-1, 1):
        fw_rune(k[RUNE], (sx * 0.5, FY - 0.115, T + WH + 0.14), (1, 0, 0), Z, 0.08, 2 + sx, stroke=0.2)
        fw_rune(k[RUNE], (sx * 0.5, HY1 - WT / 2 + 0.115, T + WH + 0.14), (-1, 0, 0), Z, 0.08, 5 + sx, stroke=0.2)
    fw_fx(fw_emit(k, "Hall_Runes", col, root))
    bm_box(k["stone_dark:0.3:0.9"], (2 * HW - 0.12, HY1 - HY0 - 0.5, WH - 0.02), (0, (HY0 + 0.44 + HY1 - 0.06) / 2, T + WH / 2))
    fw_prism(k["stone_dark:0.3:0.9"], [Vector((-HW + 0.06, HY0 + 0.24, T + WH - 0.02)), Vector((HW - 0.06, HY0 + 0.24, T + WH - 0.02)),
                                        Vector((0, HY0 + 0.24, T + RIDGE - 0.1))], Vector((0, HY1 - HY0 - 0.48, 0)))
    fw_emit(k, "Hall_Core", col, root, tag="no_refine")
    # the firebox behind the mouth: a dark hearth, the fire's glow, coals
    bm_box(k["black:0.3:0.8"], (1.1, 0.06, 0.95), (0, HY0 + 0.46, T + 0.47))
    bm_box(k["stone_dark:0.4:0.9"], (1.1, 0.5, 0.04), (0, HY0 + 0.25, T + 0.02))
    fw_emit(k, "Hall_Hearth", col, root)
    fw_face(k[FIRE], _arch_pts(MOUTH_W - 0.02, SPRING, HY0 + 0.36, T + 0.02), toward=(0, -1, 0))
    fw_face(k[HOT], _arch_pts(MOUTH_W * 0.56, SPRING * 0.55, HY0 + 0.34, T + 0.02), toward=(0, -1, 0))
    for i in range(6):
        bm_blob(k[HOT if i % 2 else FIRE], rnd, (-0.33 + 0.13 * i, HY0 + 0.2 + 0.05 * (i % 2), T + 0.06), 0.085, jitter=0.2)
    for sx in (-1, 1):                                       # slit windows glowing in the side walls
        bm_box(k[FIRE], (0.03, 0.08, 0.3), (sx * (HW + 0.004), 0.95, T + 0.95))
    fw_fx(fw_emit(k, "Hall_Fire", col, root))
    for sx in (-1, 1):
        bm_box(k[IRON], (0.03, 0.03, 0.34), (sx * (HW + 0.012), 0.95, T + 0.95))
    bm_box(k["stone_dark:0.2:0.7"], (0.16, 0.3, 0.36), (HW + 0.06, 0.63, T + 0.56))        # the tuyere block the bellows feed
    bm_box(k[TIMBER], (0.04, 0.04, 0.76), (0, FY, T + RIDGE + 0.36))                         # the pennant's pole
    bm_box(k[BRASS], (0.62, 0.05, 0.05), (0, FY - 0.13, BAN_TOP.z + 0.02))                   # the great banner's rod
    bm_cyl(k[BRASS], 0.035, 0.0, 0.08, (0, FY, T + RIDGE + 0.78), seg=5)
    fw_emit(k, "Hall_Fittings", col, root)
    # the roof of the team's tiles between the gables, its ridge iron, eave beams
    ya, yb = HY0 + 0.2, HY1 - 0.2
    for sx in (-1, 1):
        bm_tile_slope(k[TEAM], rnd, (sx * (HW + 0.16), ya, T + WH - 0.08), (sx * (HW + 0.16), yb, T + WH - 0.08),
                      (0, ya, T + RIDGE - 0.02), (0, yb, T + RIDGE - 0.02), rows=5, cols=4, th=0.06)
    fw_emit(k, "Hall_Roof", col, root, vary=0.08)
    bm_beam(k[IRON], (0, ya - 0.02, T + RIDGE + 0.03), (0, yb + 0.02, T + RIDGE + 0.03), 0.12, 0.08)
    for sx in (-1, 1):
        bm_beam(k[TIMBER], (sx * (HW + 0.1), ya - 0.02, T + WH - 0.14), (sx * (HW + 0.1), yb + 0.02, T + WH - 0.14), 0.1, 0.1)
    fw_emit(k, "Hall_Trim", col, root)
    # the chimney stack: coursed, banded, a crown, the glow in its throat
    round_tower(k, rnd, (CHIM.x, CHIM.y, 0), 0.4, 0.3, T, CHIM_TOP - 0.28, courses=9, n=7, depth=0.15, stone="stone:0.1:0.85")
    bm_block_course(k["stone:0.0:0.6"], rnd, CHIM, 0.37, CHIM_TOP - 0.28, 0.24, 7, depth=0.18, phase=0.5)
    fw_emit(k, "Chimney", col, root, vary=0.08)
    fw_hoop(k[IRON], (CHIM.x, CHIM.y, CHIM_TOP - 0.34), Z, 0.305, w=0.08, th=0.025, n=7)
    fw_hoop(k[BRASS], (CHIM.x, CHIM.y, T + 1.9), Z, 0.345, w=0.1, th=0.025, n=7)
    fw_studs_round(k[IRON], (CHIM.x, CHIM.y, T + 1.9), Z, 0.372, 7, sr=0.025, h=0.02, phase=0.5)
    fw_emit(k, "Chimney_Bands", col, root)
    bm_cyl(k[FIRE], 0.22, 0.22, 0.03, (CHIM.x, CHIM.y, CHIM_TOP - 0.05), seg=7)
    fw_fx(fw_emit(k, "Chimney_Glow", col, root))
    # ---- the rune pillars at the corners
    for i, (px, py) in enumerate(PILLARS):
        bm_box(k["stone:0.2:0.85"], (0.34, 0.34, 0.12), (px, py, T + 0.06))
        bm_loft(k["stone:0.1:0.8"], [_sq(px, py, T + 0.12, 0.14), _sq(px, py, T + 1.35, 0.1)])
        bm_box(k[IRON], (0.27, 0.27, 0.05), (px, py, T + 0.8))
        bm_cyl(k[BRASS], 0.15, 0.0, 0.2, (px, py, T + 1.45), seg=4, rot=(0, 0, 45))
    fw_emit(k, "Pillars", col, root, bevel=0.012, vary=0.05)
    for i, (px, py) in enumerate(PILLARS):
        for sy in (-1, 1):
            for j, z in enumerate((0.42, 0.62, 1.0, 1.2)):
                hw = 0.14 - 0.04 * (z - 0.12) / 1.23
                fw_rune(k[RUNE], (px, py + sy * (hw + 0.004), T + z), (-sy, 0, 0), Z, 0.07, i * 4 + j, stroke=0.2)
    fw_fx(fw_emit(k, "Pillar_Runes", col, root))
    # ---- the giant anvil on its block, the blade being forged on it
    bm_box(k["stone:0.15:0.8"], (0.6, 0.9, 0.34), (ANV.x, 0, T + 0.17))
    fw_emit(k, "Anvil_Block", col, root, bevel=0.016, vary=0.0)
    bm_box(k[CAST], (0.34, 0.52, 0.09), (ANV.x, 0, T + 0.385))
    bm_box(k[CAST], (0.2, 0.34, 0.15), (ANV.x, 0, T + 0.5))
    bm_box(k[CAST], (0.34, 0.7, 0.17), (ANV.x, 0, T + 0.655))
    fw_lathe(k[CAST], (ANV.x, -0.35, T + 0.655), (0, -1, 0), [(0.11, 0.0), (0.08, 0.16), (0.0, 0.34)], n=6)
    bm_box(k[CAST], (0.3, 0.14, 0.1), (ANV.x, 0.41, T + 0.69))
    fw_emit(k, "Anvil", col, root, bevel=0.014)
    bm_box(k[HOT], (0.08, 0.56, 0.028), (ANV.x, 0, ANV_TOP + 0.014))
    fw_fx(fw_emit(k, "Anvil_Work", col, root))
    # ---- the hammer works' frame: the pivot posts and the shaft posts, braced, the hammers' axle
    for sy in (-1, 1):
        bm_box(k[TIMBER], (0.14, 0.14, 1.32), (PIV_X, sy * 0.46, T + 0.66))
        bm_box(k["stone:0.2:0.8"], (0.26, 0.26, 0.1), (PIV_X, sy * 0.46, T + 0.05))
        bm_box(k[TIMBER], (0.14, 0.14, 1.26), (SHAFT.x, sy * 0.52, T + 0.63))
        bm_box(k[BRASS], (0.18, 0.16, 0.15), (SHAFT.x, sy * 0.52, SHAFT.z))
        bm_box(k["stone:0.2:0.8"], (0.26, 0.26, 0.1), (SHAFT.x, sy * 0.52, T + 0.05))
        bm_beam(k[TIMBER], (PIV_X, sy * 0.46, T + 1.3), (SHAFT.x, sy * 0.52, T + 1.26), 0.09, 0.09)
    bm_box(k[TIMBER], (0.14, 1.08, 0.12), (PIV_X, 0, T + 1.38))
    bm_box(k[TIMBER], (0.14, 1.2, 0.1), (SHAFT.x, 0, T + 1.31))
    fw_lathe(k[IRON], (PIV_X, -0.53, PIV_Z), Y, [(0.04, 0.0), (0.04, 1.06)], n=6)
    fw_emit(k, "Works_Frame", col, root)
    # ---- the channel of molten metal, from the mouth's sill back to the pit
    for sx in (-1, 1):
        bm_block_wall(k["stone:0.25:0.9"], rnd, (sx * 0.15, CH_Y0), (sx * 0.15, CH_Y1), T, T + 0.13, th=0.09, course=0.13, block=0.3)
    bm_box(k["stone_dark:0.4:0.9"], (0.22, CH_Y0 - CH_Y1, 0.04), (0, (CH_Y0 + CH_Y1) / 2, T + 0.02))
    bm_box(k["stone:0.1:0.7"], (0.5, 0.16, 0.1), (0, HY0 + 0.02, T + 0.05))
    fw_emit(k, "Channel", col, root, vary=0.08)
    bm_box(k[FIRE], (0.2, CH_Y0 - CH_Y1 + 0.1, 0.03), (0, (CH_Y0 + CH_Y1) / 2 - 0.05, T + 0.055))
    fw_fx(fw_emit(k, "Channel_Metal", col, root))
    # ---- the casting pit: a stone curb round a bed of sand, the greatsword and ingots in their moulds
    px0, px1, py0, py1 = -0.48, 0.48, PIT.y - 0.45, PIT.y + 0.45
    for a, b in (((px0, py0), (px1, py0)), ((px1, py0), (px1, py1)), ((px0, py1), (px0, py0)), ((px0, py1), (-0.17, py1)), ((0.17, py1), (px1, py1))):
        bm_block_wall(k["stone:0.2:0.85"], rnd, a, b, T, T + 0.17, th=0.13, course=0.17, block=0.32)
    bm_box(k["taupe_dark:0.3:0.9"], (0.8, 0.74, 0.08), (PIT.x, PIT.y, T + 0.04))
    fw_emit(k, "Pit", col, root, vary=0.08)
    zs = T + 0.085
    bm_box(k[FIRE], (0.1, 0.08, 0.02), (0, PIT.y + 0.37, zs))
    bm_box(k[FIRE], (0.05, 0.16, 0.02), (0, PIT.y + 0.26, zs))
    bm_box(k[FIRE], (0.36, 0.06, 0.02), (0, PIT.y + 0.17, zs))
    bm_beam(k[FIRE], (0, PIT.y + 0.15, zs), (0, PIT.y - 0.28, zs), 0.14, 0.02, w1=0.11, h1=0.02)
    bm_beam(k[FIRE], (0, PIT.y - 0.28, zs), (0, PIT.y - 0.41, zs), 0.11, 0.02, w1=0.012, h1=0.02)
    for sx in (-1, 1):
        for yy in (0.2, -0.18):
            bm_box(k[FIRE], (0.1, 0.26, 0.02), (sx * 0.3, PIT.y + yy, zs))
    fw_fx(fw_emit(k, "Pit_Metal", col, root))
    # ---- the bellows' stand and bottom board (the top and the leather are on the rig)
    _BEL.update(fw_bellows(B_HINGE, B_BACK, B_LEN, B_WIDE, B_OPEN, leather="wood_red:0.2:0.95"))
    side = B_BACK.cross(Z)
    for s in (0.3, 0.8):
        p = B_HINGE + B_BACK * (s * B_LEN)
        bm_beam(k[TIMBER], p - side * 0.4 - Z * 0.09, p + side * 0.4 - Z * 0.09, 0.1, 0.08)
        for sg in (-1, 1):
            q = p + side * (sg * 0.36)
            bm_beam(k[TIMBER], (q.x, q.y, T), (q.x, q.y, B_HINGE.z - 0.1), 0.09, 0.09)
    fw_emit(k, "Bellows_Stand", col, root)
    fw_emit(_BEL["bottom"], "Bellows_Bottom", col, root)
    # ---- the quench trough beside the channel
    tr = TROUGH
    for dx, dy, w, d in ((0, 0.42, 0.5, 0.1), (0, -0.42, 0.5, 0.1), (0.2, 0, 0.1, 0.94), (-0.2, 0, 0.1, 0.94)):
        bm_box(k["stone:0.15:0.8"], (w, d, 0.3), (tr.x + dx, tr.y + dy, T + 0.15))
    bm_box(k["stone_dark:0.3:0.8"], (0.4, 0.84, 0.06), (tr.x, tr.y, T + 0.04))
    fw_emit(k, "Trough", col, root, bevel=0.012, vary=0.06)
    bm_box(k["water"], (0.32, 0.76, 0.03), (tr.x, tr.y, T + 0.22))
    fw_emit(k, "Trough_Water", col, root)
    bm_beam(k[IRON], (tr.x + 0.12, tr.y - 0.3, T + 0.2), (tr.x + 0.3, tr.y - 0.5, T + 0.62), 0.03, 0.03)       # tongs
    bm_beam(k[IRON], (tr.x + 0.06, tr.y - 0.32, T + 0.2), (tr.x + 0.25, tr.y - 0.5, T + 0.62), 0.03, 0.03)
    bm_box(k[HOT], (0.05, 0.2, 0.02), (tr.x - 0.05, tr.y + 0.1, T + 0.235))                                  # a blade cooling
    fw_emit(k, "Trough_Bits", col, root)
    # ---- the racks: weapons and round shields on the right, kite shields on the left
    ry = -0.66
    for x in (1.42, 2.18):
        bm_box(k[TIMBER], (0.1, 0.1, 0.95), (x, ry, T + 0.475))
    for z in (0.3, 0.8):
        bm_box(k[TIMBER], (0.86, 0.08, 0.07), (1.8, ry, T + z))
    bm_beam(k[IRON], (1.6, ry - 0.07, T + 0.28), (1.6, ry - 0.08, T + 1.06), 0.1, 0.02, w1=0.06, h1=0.02)          # a greatsword
    bm_beam(k[IRON], (1.6, ry - 0.08, T + 1.06), (1.6, ry - 0.085, T + 1.2), 0.06, 0.02, w1=0.01, h1=0.02)
    bm_box(k[BRASS], (0.28, 0.05, 0.05), (1.6, ry - 0.07, T + 0.27))
    bm_box(k[TEAM], (0.05, 0.05, 0.18), (1.6, ry - 0.07, T + 0.16))
    bm_cyl(k[BRASS], 0.04, 0.04, 0.04, (1.6, ry - 0.07, T + 0.05), seg=6)
    bm_box(k[TIMBER], (0.05, 0.05, 1.0), (1.8, ry - 0.08, T + 0.5))                                             # a great axe
    fw_prism(k[IRON], [Vector((1.8 + x, ry - 0.11, T + z)) for x, z in ((0.03, 0.7), (0.22, 0.62), (0.26, 0.86), (0.22, 1.08), (0.03, 1.0))], Vector((0, 0.06, 0)))
    bm_box(k[TEAM], (0.07, 0.07, 0.16), (1.8, ry - 0.08, T + 0.62))
    bm_box(k[TIMBER], (0.05, 0.05, 0.96), (2.0, ry - 0.08, T + 0.48))                                            # a war hammer
    bm_box(k[IRON], (0.16, 0.13, 0.26), (2.0, ry - 0.08, T + 0.94))
    for z in (0.85, 1.03):
        bm_box(k[BRASS], (0.18, 0.15, 0.03), (2.0, ry - 0.08, T + z))
    for x in (1.42, 2.18):
        _round_shield(k, Vector((x, ry - 0.09, T + 0.6)), 0.2)
    fw_emit(k, "Rack_Weapons", col, root)
    sy_ = 0.78
    for x in (-2.3, -1.6):
        bm_box(k[TIMBER], (0.1, 0.1, 0.92), (x, sy_, T + 0.46))
    bm_box(k[TIMBER], (0.8, 0.08, 0.07), (-1.95, sy_, T + 0.82))
    for i, x in enumerate((-2.3, -1.95, -1.6)):
        _kite(k, Vector((x, sy_ - 0.06, T + 0.5)), 0.32, 0.56)
    fw_emit(k, "Rack_Shields", col, root)
    for i, (rel, loc, rot, sc) in enumerate((("resources/Iron_Bars_Stack_Medium", (-1.55, -0.72, T + 0.03), 20, 0.5),
                                             ("resources/Gold_Bars_Stack_Small", (-2.05, -0.62, T + 0.03), 70, 0.5))):
        kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d" % i)
    head = empty("Head", col, root, (ANV.x, 0, ANV_TOP), 0.5, "SINGLE_ARROW")
    empty("Muzzle", col, head, (0, 0, 0.3), 0.2, "SPHERE")
    return root


BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "shaft": ((SHAFT.x, -0.3, SHAFT.z), (SHAFT.x, 0.0, SHAFT.z), "root"),
    "bellows": (tuple(B_HINGE), tuple(B_HINGE + B_BACK * 0.4), "root"),
    "glow": ((PIT.x, PIT.y, T + 0.09), (PIT.x, PIT.y, T + 0.29), "root"),
}
for _n, _hy in HAM_Y.items():
    BONES["ham." + _n] = ((PIV_X, _hy, PIV_Z), (PIV_X, _hy + 0.2, PIV_Z), "root")
    BONES["sparks." + _n] = ((ANV.x, _hy, ANV_TOP), (ANV.x, _hy, ANV_TOP + 0.2), "root")
for _i in range(3):
    BONES["flame.%d" % _i] = ((-0.22 + 0.23 * _i, HY0 + 0.24, T + 0.08), (-0.22 + 0.23 * _i, HY0 + 0.24, T + 0.4), "root")
    BONES["flow.%d" % _i] = ((0, CH_Y0 - 0.1, T + 0.07), (0, CH_Y0 - 0.3, T + 0.07), "root")
fw_puff_bones(BONES, "puff", (CHIM.x, CHIM.y, CHIM_TOP - 0.02), 4, "root")
fw_puff_bones(BONES, "mote", (CHIM.x, CHIM.y, CHIM_TOP), 4, "root")
fw_puff_bones(BONES, "steam", (TROUGH.x, TROUGH.y + 0.1, T + 0.24), 2, "root")
flag_bones(BONES, "flag", tuple(FLAG_TOP), FLAG_DIR, 0.62, segs=3)
flag_bones(BONES, "ban", tuple(BAN_TOP), (0, 0, -1), BAN_LEN, segs=3)
FLOW_LEN = (CH_Y0 - 0.1) - (CH_Y1 + 0.05)


def build_rig():
    col = collection("War_forge")
    root = bpy.data.objects["War_forge"]
    rig = make_rig(col, root, BONES)
    rnd = random.Random(31)
    k = Kit()
    # ---- the trip hammers: a helve through an iron collar on the axle, the tail's striking plate, the great head
    for n, hy in HAM_Y.items():
        bm_beam(k[TIMBER], (PIV_X - 0.47, hy, PIV_Z), (ANV.x + 0.1, hy, PIV_Z), 0.11, 0.13)
        bm_box(k[IRON], (0.14, 0.15, 0.17), (PIV_X, hy, PIV_Z))
        bm_box(k[IRON], (0.14, 0.15, 0.16), (PIV_X - 0.42, hy, PIV_Z))
        bm_box(k[CAST], (0.26, 0.28, 0.4), (ANV.x, hy, T + 0.968))
        for z in (0.82, 1.12):
            bm_box(k[BRASS], (0.28, 0.3, 0.05), (ANV.x, hy, T + z))
        for sx in (-1, 1):
            fw_rune(k[RUNE], (ANV.x + sx * 0.131, hy, T + 0.968), (0, sx, 0), Z, 0.08, "tiwaz" if n == "A" else "algiz", stroke=0.2)
        fw_emit(k, "Hammer_" + n, col, rig=rig, bone="ham." + n, bevel=0.012)
        for i in range(9):
            a = 2 * math.pi * i / 9 + rnd.uniform(-0.2, 0.2)
            d = Vector((math.cos(a), math.sin(a), rnd.uniform(0.3, 1.0))).normalized()
            p = Vector((ANV.x, hy, ANV_TOP)) + d * rnd.uniform(0.3, 0.5)
            bm_crystal(k[HOT], p - d * 0.08, p + d * rnd.uniform(0.08, 0.16), 0.03, n=3, shoulder=0.4, foot=0.2)
        fw_fx(fw_emit(k, "Sparks_" + n, col, rig=rig, bone="sparks." + n))
    # ---- the cam shaft with its two cams (a quarter turn apart) and the rune-hubbed cog between them
    fw_lathe(k[IRON], (SHAFT.x, -0.6, SHAFT.z), Y, [(0.055, 0.0), (0.055, 1.2)], n=8)
    bm_box(k[IRON], (0.5, 0.1, 0.11), (SHAFT.x, HAM_Y["A"], SHAFT.z))
    bm_box(k[IRON], (0.11, 0.1, 0.5), (SHAFT.x, HAM_Y["B"], SHAFT.z))
    for sx in (-1, 1):
        bm_box(k[BRASS], (0.06, 0.11, 0.12), (SHAFT.x + sx * 0.23, HAM_Y["A"], SHAFT.z))
        bm_box(k[BRASS], (0.12, 0.11, 0.06), (SHAFT.x, HAM_Y["B"], SHAFT.z + sx * 0.23))
    fw_gear(k["gold:0.2:0.85"], (SHAFT.x, 0, SHAFT.z), Y, 0.32, teeth=12, w=0.1, tooth=0.07, hub=0.3, spokes=4, rim=0.22)
    for sy in (-1, 1):
        fw_rune(k[RUNE], (SHAFT.x, sy * 0.07, SHAFT.z), (-sy, 0, 0), Z, 0.08, "sowil", stroke=0.2)
    fw_emit(k, "Shaft", col, rig=rig, bone="shaft")
    # ---- the bellows' top board and its leather
    fw_emit(_BEL["top"], "Bellows_Top", col, rig=rig, bone="bellows")
    for o in fw_emit(_BEL["leather"], "Bellows_Leather", col, rig=rig, bone="root"):
        fw_skin(o, rig, lambda co: {"bellows": _BEL["frac"](co), "root": 1.0 - _BEL["frac"](co)})
    # ---- the fire's tongues in the mouth, the metal flowing down the channel, the pulse in the mould
    for i, (h, dx) in enumerate(((0.5, 0.05), (0.64, -0.04), (0.46, 0.06))):
        base = Vector(BONES["flame.%d" % i][0])
        bm_crystal(k[HOT], base, base + Vector((dx, 0, h)), 0.1, n=4, shoulder=0.3, foot=0.8)
        bm_crystal(k[FIRE], base + Vector((0.07, -0.02, 0)), base + Vector((dx + 0.1, -0.02, h * 0.7)), 0.07, n=4, shoulder=0.3, foot=0.7)
        fw_fx(fw_emit(k, "Flame%d" % i, col, rig=rig, bone="flame.%d" % i))
    for i in range(3):
        bm_box(k[HOT], (0.12, 0.22, 0.02), (0, CH_Y0 - 0.1, T + 0.072))
        fw_fx(fw_emit(k, "Flow%d" % i, col, rig=rig, bone="flow.%d" % i))
    zs2 = T + 0.09
    bm_beam(k[HOT], (0, PIT.y + 0.14, zs2), (0, PIT.y - 0.3, zs2), 0.07, 0.02, w1=0.05, h1=0.02)
    bm_box(k[HOT], (0.26, 0.03, 0.02), (0, PIT.y + 0.17, zs2))
    for sx in (-1, 1):
        for yy in (0.2, -0.18):
            bm_box(k[HOT], (0.05, 0.2, 0.02), (sx * 0.3, PIT.y + yy, zs2))
    fw_fx(fw_emit(k, "Pit_Glow", col, rig=rig, bone="glow"))
    # ---- smoke and embers from the chimney, steam off the trough, the pennant
    fw_puffs("Puff", col, rig, "puff", (CHIM.x, CHIM.y, CHIM_TOP - 0.02), 4, r=0.2)
    for i in range(4):
        bm_blob(k[HOT], rnd, Vector((CHIM.x + rnd.uniform(-0.1, 0.1), CHIM.y + rnd.uniform(-0.1, 0.1), CHIM_TOP)), 0.045, jitter=0.2)
        fw_fx(fw_emit(k, "Mote%d" % i, col, rig=rig, bone="mote.%d" % i))
    fw_puffs("Steam", col, rig, "steam", (TROUGH.x, TROUGH.y + 0.1, T + 0.24), 2, r=0.11, swatch="white:0.0:0.3", seed=5)
    flag_part("Pennant", col, rig, "flag", tuple(FLAG_TOP), FLAG_DIR, 0.62, 0.3, segs=3, tail="swallow")
    flag_part("Banner", col, rig, "ban", tuple(BAN_TOP), (0, 0, -1), BAN_LEN, 0.52, segs=3, tail="point", hang=(1, 0, 0))
    return rig


IDLE_LEN = 60


def pose(rig, t):
    """One moment of the loop (t = 0..1): hammer A is tripped at t = 0.3 and 0.8, B at 0.05 and 0.55."""
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    f = t * IDLE_LEN
    for n, off in (("A", 0.0), ("B", 15.0)):
        u = ((f - off) % 30.0) / 30.0
        if u < 0.5:
            lift = smooth(u / 0.5)
        elif u < 0.6:
            lift = 1.0 - ((u - 0.5) / 0.1) ** 2
        elif u < 0.72:
            lift = 0.07 * math.sin(math.pi * (u - 0.6) / 0.12)
        else:
            lift = 0.0
        pb["ham." + n].rotation_quaternion = q(pb["ham." + n], (0, 1, 0), -27.0 * lift)
        s = 0.0
        if 0.6 <= u < 0.8:
            kk = (u - 0.6) / 0.2
            s = 1.4 * math.sin(math.pi * kk) ** 0.6 * (0.6 + 0.6 * kk)
        pb["sparks." + n].scale = (max(s, 0.001),) * 3
    pb["shaft"].rotation_quaternion = q(pb["shaft"], (0, 1, 0), 360.0 * t)
    fw_bellows_pose(rig, "bellows", _BEL["axis"], 15.0 * (0.5 - 0.5 * math.cos(4 * math.pi * t)))
    for i in range(3):
        fl = 0.78 + 0.28 * math.sin(2 * math.pi * (3 * t + i * 0.37)) + 0.12 * math.sin(2 * math.pi * (5 * t + i * 0.7))
        pb["flame.%d" % i].scale = (1.0 + 0.15 * (1.0 - fl), fl, 1.0 + 0.15 * (1.0 - fl))
    for i in range(3):
        u = (t + i / 3.0) % 1.0
        b = pb["flow.%d" % i]
        b.location = arm_space_loc(b, (0, -u * FLOW_LEN, 0))
        s = max(0.001, math.sin(math.pi * u) ** 0.5)
        b.scale = (s, 1.0, s)
    g = 1.0 + 0.2 * math.sin(2 * math.pi * 2 * t)
    pb["glow"].scale = (g, 1.0, g)
    fw_puff_pose(rig, "puff", 4, 2 * t, rise=1.1, drift=(0.2, -0.1), size=(0.5, 1.6))
    fw_puff_pose(rig, "mote", 4, 3 * t, rise=1.4, drift=(0.35, 0.15), size=(1.0, 0.4))
    fw_puff_pose(rig, "steam", 2, 2 * t, rise=0.55, drift=(0.05, 0.0), size=(0.3, 1.1))
    wave_flag(rig, "flag", 2 * t)
    wave_flag(rig, "ban", 2 * t + 0.3, amp=0.3, axis=(1, 0, 0))


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1):
        pose(rig, f / IDLE_LEN)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.2, 1.4), "dist": 11.5, "yaw": -35, "pitch": 20, "anim_target": (-0.6, -0.1, 1.0), "anim_dist": 6.5,
           "frames": [("idle", 0), ("idle", 10), ("idle", 18), ("idle", 33), ("idle", 48)],
           "extra": [{"yaw": 10, "pitch": 18, "dist": 6.0, "target": (0, 0.2, 1.0)},
                     {"yaw": -40, "pitch": 28, "dist": 6.0, "target": (-1.6, 0, 0.8)},
                     {"yaw": 35, "pitch": 28, "dist": 6.0, "target": (1.4, 0, 0.7)}]}


def build_all():
    build_base()
    build_rig()
    build_anims()
