"""Builds the Archer Tower (footprint "single": one hex), the Crown's tier I tower and the commonest in the game.

    python tools/blender/build.py archer --out <preview dir>

A proper archer's tower: a round shaft of coursed stone on a stepped, flared foot, an arched door at the front, cross
slits, a ring of corbels, and on top a jettied octagonal fighting platform of timber (joists, braces, a boarded
parapet with crenels). A pepper-pot bartizan with a team-tiled cap clings to the back-left corner, the team's banners
hang over the parapet front and back and its shields at the sides. The top stays open: the game stands a Ranger with a
bow at Crew, in the middle of the platform.
The Head is the archer's stand (it turns to aim): a low round dais with a team rim, a tub of arrows, a fire basket
for fire arrows and a pennant on a pole. Clips: idle (the pennant flies, the fire flickers), fire (a twitch: the
pennant snaps, the flames jump, the arrows rattle; the shot itself is the archer's own animation).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "siege_common.py"), encoding="utf-8").read())

TID = "archer"
CELLS = [(0, 0)]
MID = footprint_mid(CELLS)
C = hex_to_world(0, 0, MID)
TOP = 0.34
PLAT = TOP + 1.46           # the platform's floor
APO = 0.93                  # the platform's apothem: an octagon, flats to the front, back and sides
RAD = APO / math.cos(math.radians(22.5))
DAIS = 0.05
BART_A, BART_R = 225.0, 0.84
PAR = 0.42                  # the parapet's height


def build_base():
    col = collection("Archer")
    root = empty("Archer", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    rnd = random.Random(7)
    k = Kit()
    c0 = Vector((C.x, C.y, 0))
    # ---- the foot: three stepped courses flaring out, the door's bay left open
    for i, (r, n, ph) in enumerate(((0.81, 12, 0.5), (0.75, 11, 0.25), (0.69, 10, 0.0))):
        bm_block_course(k["stone:0.2:0.88"], rnd, c0, r, T + 0.13 * i, 0.13, n, depth=0.22, phase=ph, skip=lambda a: ang_off(a, 90) < 12)
    bm_cyl(k["stone_dark:0.3:0.9"], 0.6, 0.6, 0.4, (C.x, C.y, T + 0.2), seg=14)
    # ---- the shaft, a band of corbels under the platform
    round_tower(k, rnd, c0, 0.64, 0.59, T + 0.39, PLAT - 0.2, courses=5, n=10, depth=0.16, skip=lambda kk, a: kk == 0 and ang_off(a, 90) < 12)
    bm_block_course(k["stone:0.05:0.6"], rnd, c0, 0.7, PLAT - 0.2, 0.12, 12, depth=0.3)
    k.emit("Shaft", col, root, vary=0.08)
    # ---- the door: an arch of warm stone, an iron-bound leaf, a step
    bm_arch(k["stone_warm:0.1:0.7"], (C.x, C.y + 0.68, T), (1, 0, 0), 0.36, 0.34, th=0.11, depth=0.26, n=7)
    bm_box(k["stone_warm:0.2:0.8"], (0.62, 0.2, 0.06), (C.x, C.y + 0.86, T + 0.025))
    k.emit("Door_Arch", col, root, bevel=0.01, vary=0.07)
    bm_box(k["wood_dark:0.25:0.8"], (0.38, 0.06, 0.53), (C.x, C.y + 0.63, T + 0.265))
    for z in (0.13, 0.36):
        bm_box(k["iron:0.1:0.5"], (0.36, 0.02, 0.045), (C.x, C.y + 0.665, T + z))
    ring(k["gold:0.1:0.5"], (C.x + 0.09, C.y + 0.675, T + 0.25), 0.04, 0.022, -0.008, 0.008, seg=8, axis="Y")
    k.emit("Door", col, root)
    # ---- cross slits
    for a, z in ((22, 0.9), (158, 0.9), (270, 0.82), (322, 0.95)):
        p = polar(c0, a, 0.595, T + z)
        bm_box(k["black:0.3:0.7"], (0.055, 0.06, 0.26), tuple(p), (0, 0, a - 90))
        bm_box(k["black:0.3:0.7"], (0.17, 0.06, 0.05), (p.x, p.y, p.z + 0.02), (0, 0, a - 90))
        q = polar(c0, a, 0.62, T + z - 0.16)
        bm_box(k["stone:0.0:0.4"], (0.15, 0.07, 0.035), tuple(q), (0, 0, a - 90))
    # a shuttered window, and a lantern on a bracket by the door
    a = 47
    p = polar(c0, a, 0.595, T + 1.0)
    bm_box(k["black:0.3:0.7"], (0.15, 0.06, 0.22), tuple(p), (0, 0, a - 90))
    for dz, w in ((-0.135, 0.26), (0.135, 0.22)):
        bm_box(k["stone:0.0:0.4"], (w, 0.08, 0.045), tuple(polar(c0, a, 0.62, T + 1.0 + dz)), (0, 0, a - 90))
    for s in (-1, 1):
        q = polar(c0, a, 0.625, T + 1.0) + radial(a + 90) * (s * 0.125)
        bm_box(k["wood_red:0.2:0.7"], (0.085, 0.035, 0.22), tuple(q), (0, 0, a - 90 - s * 14))
    k.emit("Slits", col, root)
    la = 62
    bm_beam(k["iron:0.1:0.5"], polar(c0, la, 0.6, T + 0.72), polar(c0, la, 0.84, T + 0.75), 0.03, 0.03)
    lp = polar(c0, la, 0.82, T + 0.64)
    bm_cyl(k["iron:0.1:0.5"], 0.05, 0.02, 0.04, (lp.x, lp.y, lp.z + 0.07), seg=6)
    bm_cyl(k["iron:0.1:0.5"], 0.045, 0.045, 0.02, (lp.x, lp.y, lp.z - 0.06), seg=6)
    bm_cyl(k["glow:1.0,0.72,0.3,1.0"], 0.036, 0.036, 0.1, tuple(lp), seg=6)
    k.emit("Lantern", col, root)
    # ---- the jetty: joists out to the eight corners, a brace under each, a kerb round the edge
    corners = [polar(c0, 22.5 + 45 * i, RAD) for i in range(8)]
    for i, p in enumerate(corners):
        o = (p - c0).normalized()
        bm_beam(k["wood_dark:0.2:0.75"], c0 + o * 0.3 + Vector((0, 0, PLAT - 0.105)), p - o * 0.02 + Vector((0, 0, PLAT - 0.105)), 0.1, 0.09)
        bm_beam(k["wood_dark:0.2:0.75"], c0 + o * 0.6 + Vector((0, 0, PLAT - 0.62)), p - o * 0.1 + Vector((0, 0, PLAT - 0.15)), 0.075, 0.075)
    k.emit("Jetty", col, root)
    bm_deck(k["wood:0.2:0.75"], rnd, (C.x, C.y, 0), octagon_half(APO - 0.03), -APO + 0.03, APO - 0.03, PLAT, pw=0.155, th=0.06)
    k.emit("Deck", col, root, vary=0.09)
    for i in range(8):
        a, b = corners[i], corners[(i + 1) % 8]
        bm_beam(k["wood_dark:0.15:0.7"], (a.x, a.y, PLAT - 0.03), (b.x, b.y, PLAT - 0.03), 0.1, 0.13)
    # ---- the parapet: a post at each corner, boarded bays between (the diagonal bays lower: crenels to shoot from)
    for i, p in enumerate(corners):
        bm_box(k["wood_dark:0.15:0.7"], (0.11, 0.11, PAR + 0.2), (p.x, p.y, PLAT + (PAR + 0.2) / 2 - 0.1), (0, 0, 22.5 + 45 * i))
        bm_cyl(k["gold:0.1:0.55"], 0.07, 0.0, 0.09, (p.x, p.y, PLAT + PAR + 0.145), rot=(0, 0, 22.5 + 45 * i + 45), seg=4)
    k.emit("Parapet_Posts", col, root)
    side = 2 * APO * math.tan(math.radians(22.5)) - 0.1
    for i in range(8):
        m = 45.0 * (i + 1)
        if ang_off(m, BART_A) < 10:
            continue
        o = radial(m)
        t = o.cross(Vector((0, 0, 1)))
        h = PAR if i % 2 == 1 else PAR * 0.6
        s0 = c0 + o * (APO + 0.02) - t * (side / 2) + Vector((0, 0, PLAT + 0.035))
        bm_planks(k["wood:0.25:0.8"], rnd, s0, (0, 0, h), t * side, 4, th=0.05, gap=0.012)
        e0, e1 = c0 + o * (APO - 0.005) - t * (side / 2 + 0.03), c0 + o * (APO - 0.005) + t * (side / 2 + 0.03)
        bm_beam(k["wood_dark:0.15:0.7"], (e0.x, e0.y, PLAT + 0.035 + h + 0.02), (e1.x, e1.y, PLAT + 0.035 + h + 0.02), 0.1, 0.045)
    k.emit("Parapet", col, root, vary=0.09)
    # ---- heraldry: banners over the parapet front and back, shields on the sides
    for m in (90, 270):
        o = radial(m)
        bm_banner(k, c0 + o * (APO + 0.075) + Vector((0, 0, PLAT + PAR + 0.03)), o, w=0.44, h=0.95, lean=0.03)
    for m in (0, 180):
        o = radial(m)
        bm_shield(k, c0 + o * (APO + 0.045) + Vector((0, 0, PLAT + 0.035 + PAR * 0.5)), o, w=0.32, h=0.36)
    k.emit("Heraldry", col, root)
    # ---- the bartizan: corbelled out of the shaft, a slit, a tiled cap in the team's color, a gilt finial
    B = polar(c0, BART_A, BART_R)
    bo = radial(BART_A)
    zb = PLAT - 0.5
    for r1, r2, z1, z2 in ((0.06, 0.16, zb - 0.3, zb - 0.16), (0.16, 0.23, zb - 0.16, zb - 0.06), (0.23, 0.29, zb - 0.06, zb + 0.03)):
        bm_cyl(k["stone:0.2:0.8"], r1, r2, z2 - z1, (B.x - bo.x * 0.04, B.y - bo.y * 0.04, (z1 + z2) / 2), seg=9)
    bz = PLAT + 0.36
    round_tower(k, rnd, B, 0.27, 0.27, zb + 0.03, bz, courses=5, n=7, depth=0.1)
    bm_block_course(k["stone:0.05:0.55"], rnd, B, 0.31, bz, 0.07, 8, depth=0.14)
    k.emit("Bartizan", col, root, vary=0.08)
    p = B + bo * 0.262 + Vector((0, 0, PLAT + 0.08))
    bm_box(k["black:0.3:0.7"], (0.05, 0.05, 0.22), tuple(p), (0, 0, BART_A - 90))
    p = B - bo * 0.262 + Vector((0, 0, PLAT + 0.17))
    bm_box(k["black:0.3:0.7"], (0.17, 0.05, 0.3), tuple(p), (0, 0, BART_A - 90))
    k.emit("Bartizan_Dark", col, root)
    bm_cyl(k["wood_dark:0.4:0.9"], 0.33, 0.03, 0.46, (B.x, B.y, bz + 0.07 + 0.22), seg=10)
    bm_tile_cone(k["team!:0.08:0.7"], rnd, (B.x, B.y, 0), 0.34, bz + 0.07, 0.5, rows=4, n=9, th=0.035, flare=0.04, top=0.04)
    k.emit("Bartizan_Roof", col, root, vary=0.08)
    bm_ellipsoid(k["gold:0.05:0.5"], (B.x, B.y, bz + 0.61), (0.055, 0.055, 0.055), u=7, v=5)
    bm_cyl(k["gold:0.05:0.5"], 0.022, 0.0, 0.16, (B.x, B.y, bz + 0.73), seg=5)
    k.emit("Bartizan_Finial", col, root)
    # ---- ground: paving at the door and in the hex's corners, a tub of spare arrows up top, a bush, a rock
    def paved(x, y):
        return in_footprint(CELLS, x, y, 0.19) and (x - C.x) ** 2 + (y - C.y) ** 2 > 0.8 ** 2
    bm_flagstones(k["stone2:0.15:0.7"], rnd, paved, (C.x - 1.2, C.y - 1.1, C.x + 1.2, C.y + 1.1), T, size=0.2, keep=0.9)
    k.emit("Paving", col, root, vary=0.09)
    bm_boulder(k["stone:0.2:0.9"], rnd, (C.x + 0.92, C.y - 0.2, T - 0.02), 0.17, n=10)
    bm_boulder(k["stone:0.2:0.9"], rnd, (C.x - 0.95, C.y + 0.12, T - 0.02), 0.13, n=9)
    k.emit("Rocks", col, root, vary=0.07)
    for i, (rel, loc, rot, sc) in enumerate((("forest/Bush_1_C_Color1", (C.x - 0.93, C.y - 0.14, T - 0.02), 30, 0.22),
                                             ("forest/Grass_1_B_Color1", (C.x + 0.9, C.y + 0.16, T - 0.02), 80, 0.42))):
        kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d" % i)
    empty("Head", col, root, (C.x, C.y, PLAT + DAIS), 0.5, "SINGLE_ARROW")
    return root


# ---- the archer's stand, in the head's space (+Y forward; z = 0 is where the archer's feet are)
QUIVER = Vector((0.4, 0.06, 0.0))
FIREPOT = Vector((-0.41, -0.04, 0.0))
POLE = Vector((0.27, -0.33, 0.0))
PEN_Z = 1.22
BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "quiver": (tuple(QUIVER), (QUIVER.x, QUIVER.y, 0.3), "root"),
         "flame.1": ((FIREPOT.x, FIREPOT.y, 0.36), (FIREPOT.x, FIREPOT.y, 0.56), "root"),
         "flame.2": ((FIREPOT.x + 0.03, FIREPOT.y - 0.02, 0.38), (FIREPOT.x + 0.03, FIREPOT.y - 0.02, 0.52), "root")}
flag_bones(BONES, "pen", (POLE.x, POLE.y, PEN_Z), (1, 0, 0), 0.46, segs=3)


def build_head():
    col = collection("Archer")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    rnd = random.Random(3)
    k = Kit()
    # the dais: a turning round of planks with a rim in the team's color
    bm_deck(k["sand:0.35:0.85"], rnd, (0, 0, 0), circle_half(0.5), -0.5, 0.5, 0.0, pw=0.125, th=DAIS + 0.01, turn=90)
    ring(k["team!:0.1:0.6"], (0, 0, 0), 0.55, 0.47, -DAIS - 0.012, 0.012, seg=16)
    for i in range(8):
        p = polar((0, 0, 0), 22.5 + 45 * i, 0.51, 0.014)
        bm_cyl(k["gold:0.1:0.5"], 0.022, 0.022, 0.012, tuple(p), seg=6)
    k.emit("Head_Dais", col, rig=rig, bone="root", vary=0.07)
    # the pennant's pole
    bm_cyl(k["wood_dark:0.2:0.7"], 0.02, 0.016, PEN_Z + 0.04, (POLE.x, POLE.y, (PEN_Z + 0.04) / 2), seg=6)
    bm_cyl(k["gold:0.05:0.5"], 0.035, 0.0, 0.1, (POLE.x, POLE.y, PEN_Z + 0.09), seg=5)
    bm_cyl(k["wood_dark:0.2:0.7"], 0.05, 0.035, 0.05, (POLE.x, POLE.y, 0.025), seg=6)
    k.emit("Head_Pole", col, rig=rig, bone="root")
    flag_part("Head_Pennant", col, rig, "pen", (POLE.x, POLE.y, PEN_Z), (1, 0, 0), 0.46, 0.23, segs=3, tail="swallow")
    # the fire basket (fire arrows): coals on the root, two flames of their own
    fb = bm_brazier(k, FIREPOT, r=0.11, h=0.33, turn=30)
    k.emit("Head_Firepot", col, rig=rig, bone="root")
    bm_flame(k[FIRE], (FIREPOT.x, FIREPOT.y, 0.34), h=0.2, r=0.07)
    k.emit("Head_Flame1", col, rig=rig, bone="flame.1")
    bm_flame(k["glow:1.0,0.8,0.25,1.0"], (FIREPOT.x + 0.03, FIREPOT.y - 0.02, 0.35), h=0.13, r=0.045)
    k.emit("Head_Flame2", col, rig=rig, bone="flame.2")
    # the tub of arrows
    bm_cyl(k["wood:0.25:0.8"], 0.085, 0.105, 0.26, (QUIVER.x, QUIVER.y, 0.13), seg=8)
    for z in (0.06, 0.21):
        ring(k["iron:0.1:0.5"], (QUIVER.x, QUIVER.y, z), 0.112, 0.08, -0.015, 0.015, seg=8)
    for i in range(7):
        a = math.radians(360 * i / 7 + rnd.uniform(-15, 15))
        r = rnd.uniform(0.02, 0.06)
        b = Vector((QUIVER.x + math.cos(a) * r, QUIVER.y + math.sin(a) * r, 0.12))
        tip = b + Vector((math.cos(a) * r * 1.6, math.sin(a) * r * 1.6, rnd.uniform(0.36, 0.44)))
        bm_beam(k["sand:0.2:0.6"], b, tip, 0.014, 0.014)
        d = (tip - b).normalized()
        for q in range(2):
            sd = Vector((math.cos(a + q * 1.57), math.sin(a + q * 1.57), 0))
            bm_beam(k["team!:0.1:0.6"], tip - d * 0.1 - sd * 0.022, tip - d * 0.1 + sd * 0.022, 0.006, 0.11, up=tuple(d))
    k.emit("Head_Quiver", col, rig=rig, bone="quiver")
    empty("Muzzle", col, head, (0, 0.35, 0.75), 0.2, "SPHERE")
    crew = empty("Crew", col, head, (0, 0, 0), 0.3, "SINGLE_ARROW")
    mannequin(col, crew, 1.15, "archer")
    return rig


IDLE_LEN = 60
FIRE_LEN = 12


def pose(rig, wave=0.0, amp=1.0, flick=0.0, flare=0.0, rattle=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    wave_flag(rig, "pen", wave, amp=amp, segs=3)
    f1, f2 = pb["flame.1"], pb["flame.2"]
    s1 = 1.0 + 0.16 * math.sin(2 * math.pi * flick * 5) + 0.9 * flare
    s2 = 1.0 + 0.22 * math.sin(2 * math.pi * flick * 7 + 1.3) + 1.1 * flare
    f1.scale = (1.0 + 0.1 * math.sin(2 * math.pi * flick * 3) + 0.3 * flare, s1, 1.0 + 0.1 * math.cos(2 * math.pi * flick * 3) + 0.3 * flare)
    f2.scale = (1.0 + 0.25 * flare, s2, 1.0 + 0.25 * flare)
    f1.rotation_quaternion = arm_space_quat(f1, (1, 0, 0), 9 * math.sin(2 * math.pi * flick * 4)) @ arm_space_quat(f1, (0, 1, 0), 7 * math.sin(2 * math.pi * flick * 6 + 0.7))
    f2.rotation_quaternion = arm_space_quat(f2, (0, 0, 1), 360 * flick) @ arm_space_quat(f2, (1, 0, 0), 10)
    qv = pb["quiver"]
    qv.location = arm_space_loc(qv, (0, 0, 0.035 * rattle))
    qv.rotation_quaternion = arm_space_quat(qv, (1, 0, 0), -9 * rattle)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        pose(rig, wave=f / IDLE_LEN, flick=f / IDLE_LEN)
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        # the loose: the pennant snaps, the flames jump, the arrows rattle in their tub
        kick = smooth(f / 2.0) * (1 - smooth((f - 2) / 9.0))
        pose(rig, wave=f / FIRE_LEN, amp=1.0 + 1.6 * kick, flick=f / FIRE_LEN, flare=kick,
             rattle=math.sin(math.pi * min(f / 5.0, 1.0)) * (1 - smooth((f - 3) / 4.0)))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 1.35), "dist": 7.6, "yaw": 150, "pitch": 20, "anim_target": (0, 0, PLAT + 0.55), "anim_dist": 4.2,
           "frames": [("idle", 0), ("idle", 20), ("fire", 2), ("fire", 5)],
           "extra": [{"yaw": 180, "pitch": 12, "dist": 5.2, "target": (0, 0, 1.15)},
                     {"yaw": 0, "pitch": 57, "dist": 5.0, "target": (0, 0, PLAT + 0.35)},
                     {"yaw": 320, "pitch": 24, "dist": 4.6, "target": (-0.3, -0.3, PLAT)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
