"""Builds the Bone Crypt (footprint "single"), a Bone Legion tower: a cheap skeleton crossbowman that hits air and
ground, 1.9 shots a second, all round.

    python tools/blender/build.py bone_crypt --out <preview dir>

One small mausoleum that is also a firing post. Thick walls of coursed blocks on a stepped footing, corner quoins, a
pointed-arch door with an iron gate and green soul-light behind it, lancet windows and arrow slits glowing the same
green, horned gargoyles under the cornice. Its flat roof is the fighting platform: flagstones, a trapdoor, and a
parapet of crossed bones and skulls between four posts with skull finials. The skeleton crossbowman stands in the
middle of it (Crew, on the Head: he turns to aim). A soul-fire lantern hangs off one side on an iron crook, the
team's tattered banner down the back wall, its pennant from a crooked pole on a corner post, a heap of bones against
one wall and a spare coffin against the other. Two soul-wisps circle the roof, one each way.
Clips: idle (wisps circle and bob, the lantern swings and flickers, the cloth stirs), fire (the wisps whirl once round
and flare: at 1.9 shots a second they never stop whirling while he shoots).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "grave_shrines_common.py"), encoding="utf-8").read())

TID = "bone_crypt"
CELLS = [(0, 0)]
TOP = 0.34
T = TOP
W, D = 0.56, 0.50             # the mausoleum's half width and half depth (outer wall faces)
WT = 0.15                     # wall thickness
Z0 = T + 0.10                 # the walls' foot (the footing's top)
COURSE = 0.23
Z1 = Z0 + 5 * COURSE          # the walls' top
ROOF = Z1 + 0.13              # the roof platform
EW, ED = W + 0.09, D + 0.09   # the cornice's (and the roof's) half sizes
DOOR_W, DOOR_SPRING, DOOR_K = 0.42, 0.40, 0.9
WIN_SILL, WIN_W, WIN_SPRING = Z0 + 2 * COURSE, 0.2, 0.2
POST = (EW - 0.085, ED - 0.085)                       # the corner posts' middles
POLE_FOOT = Vector((-POST[0], POST[1], ROOF + 0.4))   # the pennant's pole stands on the front-left post
POLE_TOP = POLE_FOOT + Vector((-0.2, 0.2, 1.25))
PEN = POLE_TOP + Vector((0.035, 0.0, -0.2))           # where the pennant leaves the pole
PEN_DIR = Vector((1.0, 0.08, -0.1)).normalized()
HOOK = Vector((EW + 0.25, 0.2, ROOF + 0.04))          # the lantern's hook
BAN_TOP = Vector((0.0, -(ED + 0.035), Z1 - 0.04))     # the banner's rod
LS = 0.8                                              # lantern scale
WISPS = ((0.72, 2.62, 1.0), (0.66, 2.9, -1.0))        # (orbit radius, height, direction)


def _yaw_to(dx, dy):
    """The yaw that turns +Y toward (dx, dy)."""
    return math.degrees(math.atan2(-dx, dy))


def build_base():
    col = collection("Bone_crypt")
    root = empty("Bone_crypt", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP)
    rnd = random.Random(11)
    k = Kit()
    # ---- the yard: worn flagstones round the crypt
    def yard(x, y):
        return in_footprint(CELLS, x, y, 0.22) and not (abs(x) < W + 0.04 and abs(y) < D + 0.04)
    bm_flagstones(k["stone:0.5:0.98"], rnd, yard, (-1.1, -1.0, 1.1, 1.0), T, size=0.27, keep=0.92)
    k.emit("Yard", col, root, vary=0.1)
    # ---- the footing and the door's steps
    gs_step(k, rnd, gs_rect(0, 0, W + 0.07, D + 0.07), T, Z0, stone="stone:0.4:0.9", block=0.4, th=0.22)
    bm_box(k["stone:0.4:0.9"], (0.7, 0.2, 0.05), (0, D + 0.17, T + 0.025))
    bm_box(k["stone:0.4:0.9"], (0.56, 0.12, 0.1), (0, D + 0.12, T + 0.05))
    k.emit("Footing", col, root, bevel=0.012, vary=0.08)
    # ---- the walls: coursed blocks cut to the door's arch, the lancets and the slits
    door = arch_hole(W, Z0, DOOR_W, DOOR_SPRING, DOOR_K)
    lancet = arch_hole(D - WT, WIN_SILL, WIN_W, WIN_SPRING, 1.0)

    def slits(z):
        if WIN_SILL <= z <= Z0 + 4 * COURSE:
            return [(W - 0.36 - 0.04, W - 0.36 + 0.04), (W + 0.36 - 0.04, W + 0.36 + 0.04)]
        return []
    wall = k["stone:0.38:1.0"]
    gs_block_wall(wall, rnd, (-W, D - WT / 2), (W, D - WT / 2), Z0, Z1, th=WT, course=COURSE, block=0.38, hole=door)
    gs_block_wall(wall, rnd, (-W, -(D - WT / 2)), (W, -(D - WT / 2)), Z0, Z1, th=WT, course=COURSE, block=0.38, hole=slits)
    for sx in (-1, 1):
        gs_block_wall(wall, rnd, (sx * (W - WT / 2), -(D - WT)), (sx * (W - WT / 2), D - WT), Z0, Z1, th=WT, course=COURSE, block=0.36,
                      hole=lancet)
    for sx in (-1, 1):                                          # quoins: long and short, turn about, a little proud
        for sy in (-1, 1):
            for c in range(5):
                lx, ly = (0.27, 0.19) if (c + (sx * sy > 0)) % 2 else (0.19, 0.27)
                bm_box(k["stone:0.1:0.75"], (lx, ly, COURSE - 0.022),
                       (sx * (W + 0.028 - lx / 2), sy * (D + 0.028 - ly / 2), Z0 + (c + 0.5) * COURSE))
    k.emit("Walls", col, root, bevel=0.012, vary=0.09)
    for sx in (-1, 1):                                          # stepped buttresses either side of each lancet
        for by in (-0.36, 0.36):
            gs_buttress(k, rnd, (sx * W, by), (sx, 0), Z0, [(0.68, 0.2), (0.42, 0.11)], width=0.17, stone="stone:0.3:0.95")
    k.emit("Buttresses", col, root, bevel=0.01, vary=0.08)
    # the dark inside (it shows in the joints and the openings), with a deep niche behind the door
    dk = k["black:0.3:0.9"]
    bm_box(dk, (2 * W - 0.24, 2 * D - 0.42, Z1 - Z0), (0, -0.09, (Z0 + Z1) / 2))
    for sx in (-1, 1):
        bm_box(dk, (W - 0.12 - 0.235, 0.18, Z1 - Z0), (sx * (0.235 + (W - 0.12 - 0.235) / 2), D - 0.21, (Z0 + Z1) / 2))
    bm_box(dk, (0.47, 0.18, Z1 - Z0 - 0.76), (0, D - 0.21, (Z0 + 0.76 + Z1) / 2))
    k.emit("Inside", col, root)
    # ---- the door: a pointed arch, a skull over its point, soul-light behind an iron gate
    gs_pointed_arch(k["stone:0.05:0.6"], (0, D - WT / 2 + 0.025, Z0), (1, 0, 0), DOOR_W, DOOR_SPRING, th=0.09, depth=WT + 0.07, n=3, k=DOOR_K,
                    key=False)
    k.emit("Door_Arch", col, root, bevel=0.008, vary=0.06)
    for sx in (-1, 1):
        gs_pointed_arch(k["stone:0.05:0.6"], (sx * (W - WT / 2 + 0.02), 0, WIN_SILL), (0, 1, 0), WIN_W, WIN_SPRING, th=0.06, depth=WT + 0.06,
                        n=3, k=1.0, sill=0.05)
    k.emit("Lancets", col, root, vary=0.06)
    gs_skull(k, place((0, D + 0.005, Z0 + 0.74), scale=0.27))
    k.emit("Door_Skull", col, root)
    g = k[glow(NECRO, 0.7)]
    pts = [Vector((-DOOR_W / 2, D - 0.295, Z0)), Vector((DOOR_W / 2, D - 0.295, Z0))]
    for i in range(13):
        x = DOOR_W / 2 - DOOR_W * i / 12.0
        h = Z0 + 0.0
        for hh in [DOOR_SPRING + 0.34 * j / 40.0 for j in range(41)]:
            hw = arch_half_width(DOOR_W, DOOR_SPRING, DOOR_K, hh)
            if hw is not None and hw >= abs(x) - 1e-6:
                h = Z0 + hh
        pts.append(Vector((x, D - 0.295, h)))
    f = g.faces.new([g.verts.new(p) for p in pts])
    f.normal_update()
    if f.normal.y < 0:
        f.normal_flip()
    for sx in (-1, 1):                                          # the lancets' and the slits' light
        bm_box(g, (0.012, WIN_W + 0.02, WIN_SPRING + 0.2), (sx * (W - 0.118), 0, WIN_SILL + (WIN_SPRING + 0.2) / 2))
        bm_box(g, (0.1, 0.012, 2 * COURSE), (sx * 0.36, -(D - 0.118), WIN_SILL + COURSE))
    k.emit("Soul_Light", col, root)
    ir = k[IRON]
    R = DOOR_W * DOOR_K
    xc = R - DOOR_W / 2
    for i in range(4):                                          # the gate's bars, spear-topped, following the arch
        x = (i - 1.5) * 0.09
        h = DOOR_SPRING + math.sqrt(R * R - (abs(x) + xc) ** 2) - 0.07
        bm_box(ir, (0.03, 0.03, h), (x, D - 0.1, Z0 + h / 2))
        bm_crystal(ir, (x, D - 0.1, Z0 + h - 0.01), (x, D - 0.1, Z0 + h + 0.075), 0.03, n=4, shoulder=0.3, foot=0.5)
    for z in (0.1, 0.4):
        bm_box(ir, (DOOR_W + 0.02, 0.025, 0.035), (0, D - 0.1, Z0 + z))
    bm_box(ir, (0.075, 0.04, 0.1), (0.0, D - 0.085, Z0 + 0.27))
    for sx in (-1, 1):
        for y in (-0.035, 0.035):
            bm_box(ir, (0.022, 0.022, WIN_SPRING + 0.12), (sx * (W - 0.07), y, WIN_SILL + (WIN_SPRING + 0.12) / 2))
    k.emit("Gate", col, root)
    # ---- the cornice: a row of corbels under a heavy course that carries the roof
    cb = k["stone:0.15:0.7"]
    for i in range(6):
        for sy in (-1, 1):
            bm_box(cb, (0.085, 0.08, 0.09), (-0.42 + 0.168 * i, sy * (D + 0.035), Z1 - 0.05))
    for i in range(5):
        for sx in (-1, 1):
            bm_box(cb, (0.08, 0.085, 0.09), (sx * (W + 0.035), -0.36 + 0.18 * i, Z1 - 0.05))
    k.emit("Corbels", col, root, vary=0.06)
    gs_step(k, rnd, gs_rect(0, 0, EW, ED), Z1, ROOF, stone="stone_dark:0.0:0.55", core="stone_dark:0.3:0.8", block=0.36, th=0.24)
    k.emit("Cornice", col, root, bevel=0.012, vary=0.06)
    for sx in (-1, 1):
        for sy in (-1, 1):
            gs_gargoyle(k, place((sx * (W - 0.06), sy * (D - 0.06), Z1 - 0.12), yaw=_yaw_to(sx, sy * 0.92), pitch=-9, scale=0.37),
                        stone="stone:0.2:0.85", eye=glow(NECRO, 0.8))
    k.emit("Gargoyles", col, root)
    # ---- the roof platform: flagstones, a trapdoor, the parapet of bones and skulls
    bm_flagstones(k["stone:0.2:0.7"], rnd, lambda x, y: abs(x) < EW - 0.2 and abs(y) < ED - 0.2, (-EW, -ED, EW, ED), ROOF - 0.012,
                  size=0.21, gap=0.03, h=0.035)
    k.emit("Roof", col, root, vary=0.1)
    ring(k["team!:0.15:0.6"], (0, 0, 0), 0.45, 0.31, ROOF + 0.027, ROOF + 0.036, seg=16)      # a ring in the team's color painted round his post
    k.emit("Roof_Ring", col, root)
    bm_planks(k["wood_dark:0.15:0.7"], rnd, (0.13, -0.4, ROOF + 0.045), (0.28, 0, 0), (0, 0.27, 0), 3, th=0.04)
    for y in (-0.34, -0.19):
        bm_box(k[IRON], (0.3, 0.035, 0.014), (0.27, y, ROOF + 0.052))
    ring(k[IRON], (0.36, -0.265, ROOF + 0.06), 0.04, 0.022, -0.008, 0.008, seg=6)
    k.emit("Trapdoor", col, root)
    gs_step(k, rnd, gs_rect(0, 0, EW, ED), ROOF, ROOF + 0.09, stone="stone:0.25:0.8", core=None, block=0.3, th=0.12)
    k.emit("Curb", col, root, vary=0.08)
    for sx in (-1, 1):
        for sy in (-1, 1):
            bm_box(k["stone:0.25:0.8"], (0.17, 0.17, 0.36), (sx * POST[0], sy * POST[1], ROOF + 0.18))
            bm_box(k["stone_dark:0.0:0.5"], (0.225, 0.225, 0.05), (sx * POST[0], sy * POST[1], ROOF + 0.375))
    k.emit("Posts", col, root, bevel=0.012, vary=0.08)
    zc, zr = ROOF + 0.09, ROOF + 0.33
    bn = k[BONE]
    for (ax, ay), (bx, by), (nx, ny) in (((-POST[0], ED - 0.06), (POST[0], ED - 0.06), (0, 1)), ((POST[0], -(ED - 0.06)), (-POST[0], -(ED - 0.06)), (0, -1)),
                                         ((EW - 0.06, POST[1]), (EW - 0.06, -POST[1]), (1, 0)), ((-(EW - 0.06), -POST[1]), (-(EW - 0.06), POST[1]), (-1, 0))):
        a, b, nv = Vector((ax, ay, 0)), Vector((bx, by, 0)), Vector((nx, ny, 0))
        c = (a + b) * 0.5
        u = (b - a).normalized()
        half = (b - a).length * 0.5
        gs_skull(k, place((c.x, c.y, zc - 0.012), yaw=_yaw_to(nx, ny), scale=0.2), n=6)
        for s in (-1, 1):
            p, q = c + u * (s * (half - 0.1)), c + u * (s * 0.115)            # from the post to the skull
            gs_bone(bn, p + nv * 0.022 + Vector((0, 0, zc + 0.03)), q + nv * 0.022 + Vector((0, 0, zr - 0.05)), r=0.026, knob=1.8, n=4)
            gs_bone(bn, p - nv * 0.022 + Vector((0, 0, zr - 0.05)), q - nv * 0.022 + Vector((0, 0, zc + 0.03)), r=0.026, knob=1.8, n=4)
            gs_bone(bn, p - u * (s * 0.03) + Vector((0, 0, zr)), c + u * (s * 0.012) + Vector((0, 0, zr)), r=0.03, knob=1.7, n=4)
    for sx in (-1, 1):
        for sy in (-1, 1):
            if (sx, sy) != (-1, 1):                              # (the fourth post carries the pennant's pole)
                gs_skull(k, place((sx * POST[0], sy * POST[1], ROOF + 0.395), yaw=_yaw_to(sx, sy), scale=0.22))
    k.emit("Parapet_Bones", col, root, vary=0.05)
    # ---- the pennant's pole on the back corner post: crooked, bound with bone, a skull on its tip
    bm_tube(k["wood_dark:0.2:0.85"], [POLE_FOOT - Vector((0, 0, 0.03)), POLE_FOOT.lerp(POLE_TOP, 0.5) + Vector((0.02, -0.02, 0)), POLE_TOP],
            [0.046, 0.038, 0.028], n=5)
    gs_bone(k[BONE], PEN + Vector((-0.1, 0.0, 0.16)), PEN + Vector((0.2, 0.02, 0.16)), r=0.02, n=4)
    gs_skull(k, place(tuple(POLE_TOP - Vector((0, 0, 0.02))), yaw=_yaw_to(0.2, 1), scale=0.15), n=6)
    k.emit("Pole", col, root)
    # ---- the banner's rod (a thigh bone on two iron hooks) and the lantern's crook
    gs_bone(k[BONE], BAN_TOP + Vector((-0.34, 0, 0.02)), BAN_TOP + Vector((0.34, 0, 0.02)), r=0.03)
    for sx in (-1, 1):
        bm_box(k[IRON], (0.03, 0.09, 0.03), (sx * 0.3, BAN_TOP.y + 0.035, BAN_TOP.z + 0.02))
    ir = k[IRON]
    crook = [Vector((EW - 0.04, HOOK.y, ROOF - 0.07)), Vector((EW + 0.1, HOOK.y, ROOF + 0.0)), Vector((EW + 0.2, HOOK.y, ROOF + 0.12)),
             Vector((HOOK.x + 0.02, HOOK.y, ROOF + 0.15)), Vector((HOOK.x + 0.06, HOOK.y, ROOF + 0.09)), Vector((HOOK.x, HOOK.y, HOOK.z))]
    bm_tube(ir, crook, [0.03, 0.028, 0.026, 0.024, 0.02, 0.014], n=4)
    bm_beam(ir, (EW - 0.02, HOOK.y, ROOF - 0.24), (EW + 0.15, HOOK.y, ROOF + 0.04), 0.022, 0.03)
    k.emit("Fittings", col, root)
    # ---- a heap of the crypt's overflow against the west wall, a spare coffin against the east
    H = Vector((-(W + 0.26), 0.02, T))
    for (dx, dy, dz, yaw, pitch, roll, s) in ((0.0, 0.08, 0.0, 100, -6, 8, 0.24), (-0.05, -0.14, 0.0, 60, 0, -20, 0.21), (0.1, -0.03, 0.17, 95, -18, 0, 0.2),
                                              (-0.16, 0.2, 0.0, 130, 10, 30, 0.18)):
        gs_skull(k, place((H.x + dx, H.y + dy, H.z + dz), yaw=yaw, pitch=pitch, roll=roll, scale=s), n=6)
    for (x0, y0, z0, x1, y1, z1) in ((-0.16, -0.27, 0.04, 0.1, 0.25, 0.05), (0.17, -0.22, 0.03, 0.2, 0.16, 0.42), (-0.22, 0.02, 0.04, -0.04, 0.3, 0.07),
                                     (0.1, -0.3, 0.04, -0.22, -0.12, 0.05), (0.02, 0.12, 0.05, 0.19, 0.25, 0.36)):
        gs_bone(k[BONE], (H.x + x0, H.y + y0, H.z + z0), (H.x + x1, H.y + y1, H.z + z1), r=0.03)
    k.emit("Bone_Heap", col, root, vary=0.06)
    for o in kk_import("halloween/coffin", col, root, (W + 0.17, 0.0, T + 0.3), 0, 0.2, name="Prop_KK_Coffin"):
        o.rotation_euler = (math.radians(77), 0, math.radians(90))
    ms = k["teal:0.45:0.95"]                                    # moss creeping up from the footing
    for (x, y, r) in ((-W - 0.03, 0.42, 0.09), (W + 0.03, 0.4, 0.08), (-0.3, -D - 0.04, 0.09), (0.46, -D - 0.03, 0.07), (-W - 0.02, -0.4, 0.07),
                      (0.42, D + 0.05, 0.06)):
        bm_blob(ms, rnd, (x, y, Z0 + r * 0.25), r, squash=(1.2, 1.2, 0.7), jitter=0.2)
    k.emit("Moss", col, root)
    head = empty("Head", col, root, (0, 0, ROOF + 0.02), 0.5, "SINGLE_ARROW")
    empty("Crew", col, head, (0, 0, 0), 0.3, "SINGLE_ARROW")
    empty("Muzzle", col, head, (0, 0.35, 0.6), 0.2, "SPHERE")
    gs_standin((0, 0, 0), parent=head, h=1.0)
    return root


BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "lantern": (tuple(HOOK), tuple(HOOK - Vector((0, 0, 0.3))), "root"),
         "fire": (tuple(HOOK - Vector((0, 0, 0.48 * LS))), tuple(HOOK - Vector((0, 0, 0.48 * LS - 0.12))), "lantern")}
for _i, (_r, _z, _d) in enumerate(WISPS):
    BONES["orbit.%d" % (_i + 1)] = ((0, 0, _z), (0, 0, _z + 0.2), "root")
    BONES["wisp.%d" % (_i + 1)] = ((_r, 0, _z), (_r, 0, _z + 0.15), "orbit.%d" % (_i + 1))
flag_bones(BONES, "ban", tuple(BAN_TOP), (0, 0, -1), 0.9, segs=3)
flag_bones(BONES, "pen", tuple(PEN), tuple(PEN_DIR), 0.62, segs=3)


def build_head():
    col = collection("Bone_crypt")
    root = bpy.data.objects["Bone_crypt"]
    rig = make_rig(col, root, BONES)
    k = Kit()
    rnd = random.Random(5)
    soul = glow(NECRO, 0.8)
    for i, (r, z, d) in enumerate(WISPS):                       # the wisps: a bright head, a tail streaming behind
        gs_wisp(k[soul], (r, 0, z), r=0.085, tail=(-0.3, -d, 0.0), length=0.46, curl=(-0.55, 0, 0.3), eyes=k["black:0.3:0.6"])
        for t, s in ((0.62, 0.035), (0.86, 0.025)):
            a = -d * t
            p = Vector((math.cos(a) * r * 0.93, math.sin(a) * r * 0.93, z + 0.1 * t))
            bm_crystal(k[soul], p - Vector((0, 0, s * 1.3)), p + Vector((0, 0, s * 1.6)), s, n=4, shoulder=0.45, foot=0.1)
        k.emit("Wisp%d" % (i + 1), col, rig=rig, bone="wisp.%d" % (i + 1))
    gs_lantern(k, place(tuple(HOOK), scale=LS))
    k.emit("Lantern", col, rig=rig, bone="lantern")
    gs_flame(k[glow(NECRO, 0.8)], tuple(HOOK - Vector((0, 0, 0.48 * LS))), h=0.2, r=0.06, rnd=rnd, tongues=2, n=5)
    k.emit("Lantern_Fire", col, rig=rig, bone="fire")
    gs_banner(k["team!:0.1:0.75"], tuple(BAN_TOP), (1, 0, 0), (0, 0, -1), 0.56, 0.9, rnd=rnd, cols=6, rows=4, tatter=0.3)
    k.emit("Banner", col, rig=rig, bones=["ban.1", "ban.2", "ban.3"])
    gs_skull(k, place((BAN_TOP.x, BAN_TOP.y - 0.012, BAN_TOP.z - 0.48), yaw=180, scale=0.24) @ Matrix.Diagonal((1.0, 0.28, 1.0, 1.0)), n=6)
    k.emit("Banner_Badge", col, rig=rig, bones=["ban.1", "ban.2", "ban.3"])
    gs_banner(k["team!:0.1:0.75"], tuple(PEN), (0, 0, 1), tuple(PEN_DIR), 0.32, 0.62, rnd=rnd, cols=4, rows=6, tatter=0.22, taper=0.5)
    k.emit("Pennant", col, rig=rig, bones=["pen.1", "pen.2", "pen.3"])
    return rig


IDLE_LEN = 72
FIRE_LEN = 14


def pose(rig, t=0.0, whirl=0.0, flare=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    for i, (r, z, d) in enumerate(WISPS):
        o, w = pb["orbit.%d" % (i + 1)], pb["wisp.%d" % (i + 1)]
        o.rotation_quaternion = q(o, (0, 0, 1), d * 360.0 * (t + whirl) + 180.0 * i)
        o.location = arm_space_loc(o, (0, 0, 0.09 * math.sin(2 * math.pi * (2 * t + 0.5 * i)) + 0.1 * flare))
        s = 1.0 + 0.1 * math.sin(2 * math.pi * (3 * t + 0.3 * i)) + 0.7 * flare
        w.scale = (s, s, s)
    pb["lantern"].rotation_quaternion = q(pb["lantern"], (1, 0, 0), 6.0 * math.sin(2 * math.pi * t) + 5.0 * flare) @ \
        q(pb["lantern"], (0, 1, 0), 3.0 * math.sin(2 * math.pi * (2 * t + 0.2)))
    f = 1.0 + 0.14 * math.sin(2 * math.pi * 6 * t) + 0.08 * math.sin(2 * math.pi * (11 * t + 0.3)) + 0.6 * flare
    pb["fire"].scale = (1.0 + 0.3 * (f - 1.0), f, 1.0 + 0.3 * (f - 1.0))          # (an upright bone: its own Y is the height)
    sway(rig, "ban", 2.2, segs=3, axis=(0, 1, 0), lag=0.14, phase=t)
    for kk in range(3):                                                           # ... and it lifts off the wall a little
        b = pb["ban.%d" % (kk + 1)]
        b.rotation_quaternion = b.rotation_quaternion @ q(b, (1, 0, 0), -(1.5 + 1.5 * math.sin(2 * math.pi * (t * 2 - 0.15 * kk)) + 4.0 * flare))
    wave_flag(rig, "pen", 2 * t + whirl, amp=1.0 + 0.5 * flare, segs=3)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(rig, t=f / IDLE_LEN)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        # the bolt leaves on frame 0: the wisps flare at once and whirl a full turn, back to where they started
        pose(rig, t=0.0, whirl=smooth(f / float(FIRE_LEN)), flare=smooth(f / 1.5) * (1 - smooth((f - 3) / 9.0)))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 1.45), "dist": 7.6, "yaw": 160, "pitch": 20, "anim_target": (0, 0, 1.7), "anim_dist": 6.4,
           "frames": [("idle", 0), ("idle", 24), ("fire", 3), ("fire", 8)],
           "extra": [{"yaw": 150, "pitch": 4, "dist": 2.6, "target": (0.2, 0.4, 1.5)},
                     {"yaw": 0, "pitch": 57, "dist": 4.6, "target": (0, 0, 1.75)},
                     {"yaw": 175, "pitch": 8, "dist": 3.6, "target": (0, 0.3, 1.0)},
                     {"yaw": 250, "pitch": 14, "dist": 4.2, "target": (0, 0, 1.4)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
