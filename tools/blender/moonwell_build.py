"""Builds the Moonwell (footprint "single"), a Verdant support tower (nearby towers attack faster).

    python tools/blender/build.py moonwell --out <preview dir>

One shrine on a round stone step: a well of coursed white stone, its rim inlaid with the team's color and glowing
runes, brimming with moon-blue water (lily pads, the moon's reflection, ripples running out to the rim). A tall crescent
moon of pale carved stone grows out of a pedestal built against the well and leans over the water; a crystal hangs in
its embrace on a chain, a flowering vine climbs it, and two ribbons in the team's color fly from its horn.
A druid tends it (Crew, in front of the well, facing the water).
idle (its only clip, 4 s): ripples spread over the water, the reflection shimmers, the lily pads bob, motes of light
rise in a spiral through the crescent and fade, the crystal turns and sways with a ring of light circling it, the
ribbons stream.
"""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "wildwood_common.py"), encoding="utf-8").read())

TID = "moonwell"
CELLS = [(0, 0)]
MID = footprint_mid(CELLS)
TOP = 0.34
T = TOP + 0.05                    # the turf plinth's top
P_TOP = T + 0.1                   # the round step everything stands on
STEP_TOP = P_TOP + 0.07           # the well's own base step
RIM_Z0 = STEP_TOP + 0.36          # top of the wall's three courses
RIM_TOP = RIM_Z0 + 0.08
WATER = RIM_TOP - 0.025
W = Vector((-0.12, 0.06, 0))      # the well's middle
DEEP = "glow:0.13,0.36,0.9,0.7"   # the water
PALE = "glow:0.5,0.78,1.0,0.85"   # ripples, runes, motes
LIGHT = "glow:0.72,0.9,1.0,1.0"   # the crystal, the reflection
# ---- the crescent: an arc in a plane that leans forward over the well
FOOT = Vector((0.5, -0.25, P_TOP))
LEAN = math.radians(14)
UP = Vector((0, math.sin(LEAN), math.cos(LEAN)))
NRM = Vector((0, math.cos(LEAN), -math.sin(LEAN)))      # the crescent's front face looks this way
CX, CU, CR = W.x - FOOT.x, 1.28, 0.85                   # its circle: middle (across, up the lean) and radius
PH0, PH1 = -62.0, 175.0                                 # from the pedestal round over the top to the horn's tip
WID = [(0.0, 0.17), (0.3, 0.21), (0.62, 0.185), (0.86, 0.1), (1.0, 0.012)]     # half width along the arc
DEP = [(0.0, 0.125), (0.5, 0.12), (0.86, 0.075), (1.0, 0.02)]                  # half thickness


def cres(phi, off=0.0, out=0.0):
    """A point of the crescent: phi degrees round its circle, `off` out from the middle line, `out` off its face."""
    a = math.radians(phi)
    r = CR + off
    return FOOT + Vector((CX + r * math.cos(a), 0, 0)) + UP * (CU + r * math.sin(a)) + NRM * out


def cres_t(t):
    return PH0 + (PH1 - PH0) * t


HANG = cres(90, -ramp(WID, (90 - PH0) / (PH1 - PH0)) + 0.03)          # where the crystal's chain is fixed
CRYSTAL = HANG - Vector((0, 0, 0.62))                                  # the crystal's middle
TIP = cres(PH1 - 6, 0.0)                                               # the horn's tip: the ribbons fly from here
CREW = Vector((0.14, 0.72, P_TOP))
PIER = (306.0, 372.0)             # the pier: this stretch of the well's wall (degrees round the well)


def build_base():
    col = collection("Moonwell")
    root = empty("Moonwell", col, None, (0, 0, 0), 0.6, "ARROWS")
    plinth(CELLS, col, root, TOP, turf=True)
    rnd = random.Random(3)
    k = Kit()
    # ---- the round step: long radial slabs, worn
    bm_block_course(k["stone2:0.08:0.7"], rnd, (0, 0, 0), 0.83, T - 0.03, 0.135, 17, depth=0.38, gap=0.022, jit=0.014)
    k.emit("Step", col, root, bevel=0.014, vary=0.09, seed=2)
    # ---- the well: a base step, three courses of white blocks over a dark core, a broad coping
    bm_block_course(k["white:0.25:0.85"], rnd, W, 0.67, P_TOP - 0.012, 0.085, 14, depth=0.17, phase=0.3)
    round_tower(k, rnd, W, 0.555, 0.53, STEP_TOP - 0.006, RIM_Z0, courses=3, n=11, depth=0.15, stone="white:0.12:0.8",
                core="stone_dark:0.3:0.9")
    bm_block_course(k["white:0.0:0.4"], rnd, W, 0.605, RIM_Z0, 0.085, 12, depth=0.185, gap=0.014, jit=0.006)
    k.emit("Well", col, root, bevel=0.012, vary=0.06, seed=5)
    # the rim's inlay: a ring of glazed tiles in the team's color, a glowing rune set in every other one
    for i in range(12):
        a0, a1 = 2 * math.pi * (i + 0.09) / 12, 2 * math.pi * (i + 0.91) / 12
        _wedge(k["team!:0.1:0.6"], W, a0, a1, 0.455, 0.575, RIM_TOP - 0.02, RIM_TOP + 0.012)
        if i % 2 == 0:
            am = (a0 + a1) * 0.5
            c = W + Vector((math.cos(am) * 0.515, math.sin(am) * 0.515, RIM_TOP + 0.016))
            bm_box(k[PALE], (0.07, 0.07, 0.014), tuple(c), (0, 0, math.degrees(am) + 45))
    # runes cut into the wall's middle course
    for a in (205, 262, 318, 20, 95, 150):
        ar = math.radians(a)
        d = Vector((math.cos(ar), math.sin(ar), 0))
        c = W + d * 0.548 + Vector((0, 0, STEP_TOP + 0.18))
        bm_box(k[PALE], (0.022, 0.02, 0.1), tuple(c), (0, 0, a + 90))
        bm_box(k[PALE], (0.05, 0.02, 0.05), tuple(c + Vector((0, 0, 0.012))), (0, 45, a + 90))
    k.emit("Well_Inlay", col, root)
    # ---- the pier the crescent grows from: the well's own wall, thicker and taller on one side
    def in_pier(a):
        return a >= PIER[0] or a <= PIER[1] - 360.0
    for c_ in range(5):
        z0 = P_TOP - 0.012 + c_ * 0.128
        bm_block_course(k["white:0.18:0.9"], rnd, W, 0.8 - 0.012 * c_, z0, 0.128, 15, depth=0.385 - 0.012 * c_, phase=0.5 * (c_ % 2), skip=lambda a: not in_pier(a))
    bm_block_course(k["white:0.0:0.4"], rnd, W, 0.83, P_TOP + 0.628, 0.075, 15, depth=0.44, phase=0.5, skip=lambda a: not in_pier(a))
    k.emit("Pier", col, root, bevel=0.012, vary=0.07, seed=9)
    for a in (318, 345):
        ar = math.radians(a)
        d = Vector((math.cos(ar), math.sin(ar), 0))
        c = W + d * 0.795 + Vector((0, 0, P_TOP + 0.36))
        bm_box(k[PALE], (0.024, 0.02, 0.15), tuple(c), (0, 0, a + 90))
        bm_box(k[PALE], (0.075, 0.02, 0.075), tuple(c + Vector((0, 0, 0.02))), (0, 45, a + 90))
    k.emit("Pier_Runes", col, root)
    # ---- the crescent: wedge stones along the arc, a raised silver band down both edges, runes on both faces
    N = 17
    trim = Kit()
    for i in range(N):
        ta, tb = i / N, (i + 1) / N
        pa, pb = cres_t(ta) + 0.5, cres_t(tb) - (0.5 if i < N - 1 else 0.0)
        pts, band_in, band_out = [], [], []
        for ph, t in ((pa, ta), (pb, tb)):
            w, d = ramp(WID, t), ramp(DEP, t)
            for off in (-w, w):
                for sg in (-1, 1):
                    pts.append(cres(ph, off, sg * d))
            for sg in (-1, 1):
                band_in.extend((cres(ph, -w - 0.014, sg * (d + 0.014)), cres(ph, -w + min(0.05, w * 0.5), sg * (d + 0.014))))
                band_out.extend((cres(ph, w + 0.014, sg * (d + 0.014)), cres(ph, w - min(0.05, w * 0.5), sg * (d + 0.014))))
        bm_hull(k["white:0.1:0.85"], pts)
        if i < N - 1:
            bm_hull(trim["white:0.0:0.3"], band_in)
            bm_hull(trim["white:0.0:0.3"], band_out)
        if i % 2 == 1 and i < N - 2:
            tm = (ta + tb) * 0.5
            pm = cres_t(tm)
            tan = (cres(pm + 1) - cres(pm - 1)).normalized()
            rad = (cres(pm, 0.1) - cres(pm)).normalized()
            s = min(1.0, ramp(WID, tm) / 0.17)
            for sg in (-1, 1):
                c = cres(pm, 0.0, sg * (ramp(DEP, tm) + 0.006))
                bm_hull(k[PALE], [c + tan * 0.05 * s, c - tan * 0.05 * s, c + rad * 0.085 * s, c - rad * 0.085 * s, c + NRM * sg * 0.012,
                                  c - NRM * sg * 0.004])
    k.emit("Crescent", col, root, bevel=0.01, vary=0.05, seed=7)
    trim.emit("Crescent_Trim", col, root)
    # moss where the rain sits: along the crescent's back, on the pier
    for ph, sz in ((38, 0.11), (61, 0.08), (118, 0.1), (143, 0.07)):
        t = (ph - PH0) / (PH1 - PH0)
        bm_blob(k["grass:0.25:0.8"], rnd, cres(ph, ramp(WID, t) + 0.01, rnd.uniform(-0.04, 0.04)), sz, squash=(1.5, 1.2, 0.5), jitter=0.14)
    for a, r, sz in ((312, 0.66, 0.12), (352, 0.72, 0.09)):
        ar = math.radians(a)
        bm_blob(k["grass:0.25:0.8"], rnd, W + Vector((math.cos(ar) * r, math.sin(ar) * r, P_TOP + 0.71)), sz, squash=(1.3, 1.3, 0.4), jitter=0.14)
    k.emit("Moss", col, root)
    # a silver cap on the horn's tip, a ring where the chain hangs
    bm_crystal(k["white:0.0:0.3"], cres(PH1 - 5, 0.0), cres(PH1 + 9, -0.03), 0.045, n=5, shoulder=0.3, foot=1.0)
    bm_cyl(k["white:0.0:0.3"], 0.05, 0.035, 0.06, tuple(HANG + Vector((0, 0, 0.02))), seg=6)
    k.emit("Crescent_Silver", col, root)
    # ---- a flowering vine winding up the crescent from the pedestal, leaves and blossoms in the team's color
    vine, turns = [], 3.5
    for i in range(46):
        t = 0.0 + 0.62 * i / 45
        ps = 2 * math.pi * turns * i / 45 + 0.8
        w, d = ramp(WID, t) + 0.035, ramp(DEP, t) + 0.035
        vine.append(cres(cres_t(t), math.cos(ps) * w, math.sin(ps) * d))
    vine = [Vector((FOOT.x + 0.22, FOOT.y - 0.3, T - 0.02)), Vector((FOOT.x + 0.2, FOOT.y - 0.22, P_TOP + 0.36))] + vine
    bm_tube(k["teal:0.2:0.8"], vine, [0.055, 0.048] + [0.04 - 0.018 * i / 45 for i in range(46)], n=5)
    for i in range(4, len(vine) - 1, 2):
        p = vine[i]
        mid_ = cres(cres_t(0.62 * (i - 2) / 45))
        out = (p - mid_).normalized()
        along = (vine[i + 1] - vine[i - 1]).normalized()
        side = out.cross(along).normalized() * (1 if (i // 2) % 2 else -1)
        dr = (out * 0.6 + side * 0.8 + Vector((0, 0, -0.25))).normalized()
        leaf(k["grass:0.1:0.8"], [p, p + dr * 0.09 + out * 0.03, p + dr * 0.2], 0.12, th=0.014, n=4, up=tuple(out))
        if i % 6 == 4:
            bm_star(k["team!:0.05:0.6"], p + out * 0.055, out, 0.125, r_in=0.5, h=0.35, turn=i)
            bm_cyl(k["gold:0.1:0.5"], 0.04, 0.016, 0.045, tuple(p + out * 0.075), rot=rot_deg(out), seg=5)
    # a second, shorter vine spilling over the well's back rim and down its wall
    for a0, da, n_fl in ((236, 26, 2), (120, -22, 2), (192, 12, 1)):
        pts = []
        for j, (rr, z) in enumerate(((0.5, RIM_TOP + 0.02), (0.615, RIM_TOP + 0.03), (0.625, RIM_Z0 - 0.1), (0.6, STEP_TOP + 0.12), (0.7, STEP_TOP + 0.02),
                                     (0.78, P_TOP + 0.02))):
            ar = math.radians(a0 + da * j / 5)
            pts.append(W + Vector((math.cos(ar) * rr, math.sin(ar) * rr, z)))
        bm_tube(k["teal:0.2:0.8"], pts, [0.03, 0.036, 0.034, 0.03, 0.024, 0.0], n=5)
        for j in range(1, 5):
            p = pts[j]
            out = Vector((p.x - W.x, p.y - W.y, 0)).normalized()
            side = out.cross(Vector((0, 0, 1))) * (1 if j % 2 else -1)
            dr = (side + Vector((0, 0, -0.5)) + out * 0.3).normalized()
            leaf(k["grass:0.1:0.8"], [p, p + dr * 0.09 + out * 0.03, p + dr * 0.19], 0.12, th=0.014, n=4, up=tuple(out))
            if j <= n_fl:
                bm_star(k["team!:0.05:0.6"], p + out * 0.05 - side * 0.06, out + Vector((0, 0, 0.4)), 0.115, r_in=0.5, h=0.35, turn=j)
                bm_cyl(k["gold:0.1:0.5"], 0.038, 0.015, 0.045, tuple(p + out * 0.07 - side * 0.06), rot=rot_deg(out + Vector((0, 0, 0.4))), seg=5)
    k.emit("Vines", col, root)
    # ---- the corners of the hex: mossy stones, ferns, a few moon-white flowers
    for a, r, s, moss in ((182, 0.93, 0.15, True), (243, 0.9, 0.2, True), (300, 0.93, 0.13, False), (121, 0.95, 0.11, False), (58, 0.95, 0.12, True),
                          (228, 0.99, 0.09, False)):
        ar = math.radians(a)
        r = hex_r(ar, 0.19 + s * 0.9)
        p = Vector((math.cos(ar) * r, math.sin(ar) * r, T - 0.03))
        bm_boulder(k["stone2:0.1:0.85"], rnd, tuple(p), s, squash=(1, 1, 0.85), n=11)
        if moss:
            bm_blob(k["grass:0.3:0.8"], rnd, (p.x * 0.97, p.y * 0.97, T + s * 0.95), s * 0.62, squash=(1, 1, 0.38), jitter=0.12)
    for a, r in ((170, 0.9), (196, 0.95), (112, 0.92), (64, 0.86), (290, 0.9)):
        ar = math.radians(a)
        r = hex_r(ar, 0.25)
        p = Vector((math.cos(ar) * r, math.sin(ar) * r, T))
        bm_tube(k["grass:0.3:0.8"], [p, p + Vector((0, 0, 0.1))], [0.012, 0.01], n=4)
        bm_star(k["white:0.0:0.3"], p + Vector((0, 0, 0.11)), (0, 0, 1), 0.06, r_in=0.5, h=0.4, turn=a)
        bm_cyl(k[PALE], 0.02, 0.008, 0.03, (p.x, p.y, p.z + 0.125), seg=5)
    k.emit("Corners", col, root, vary=0.07)
    for i, (rel, a, r, sc) in enumerate((("forest/Bush_1_E_Color1", 255, 1.0, 0.22), ("forest/Grass_2_A_Color1", 72, 1.0, 0.36),
                                         ("forest/Grass_1_B_Color1", 132, 1.0, 0.4), ("forest/Grass_2_A_Color1", 315, 1.0, 0.34))):
        ar = math.radians(a)
        r = hex_r(ar, 0.3) * r
        kk_import(rel, col, root, (math.cos(ar) * r, math.sin(ar) * r, T - 0.02), rnd.uniform(0, 360), sc, name="Prop_KK_%d" % i)
    crew = empty("Crew", col, root, tuple(CREW), 0.3, "SINGLE_ARROW")
    to = W - CREW
    crew.rotation_euler = (0, 0, math.atan2(-to.x, to.y))
    empty("Head", col, root, (W.x, W.y, WATER), 0.5, "SINGLE_ARROW")
    return root


MOTES = 7
WC = Vector((W.x, W.y + 0.06, WATER))        # where the water's light gathers: under the crystal
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "water": ((W.x, W.y, WATER), (W.x, W.y + 0.2, WATER), "root"),
    "moon": (tuple(WC), (WC.x, WC.y + 0.2, WC.z), "root"),
    "lily": ((W.x, W.y, WATER), (W.x + 0.2, W.y, WATER), "root"),
    "crystal": (tuple(HANG), tuple(HANG + Vector((0, 0, 0.2))), "root"),
    "halo": (tuple(CRYSTAL), tuple(CRYSTAL + Vector((0, 0, 0.2))), "crystal"),
}
for _i in range(3):
    BONES["ripple.%d" % _i] = ((W.x, W.y, WATER), (W.x, W.y + 0.15, WATER), "root")
for _i in range(MOTES):
    BONES["mote.%d" % _i] = ((W.x, W.y, WATER + 0.3), (W.x, W.y, WATER + 0.4), "root")
flag_bones(BONES, "rib1", TIP + Vector((0.03, 0, -0.02)), (0, 0, -1), 0.62, segs=3)
flag_bones(BONES, "rib2", TIP + Vector((0.2, 0, 0.02)), (0, 0, -1), 0.46, segs=3)


def build_head():
    col = collection("Moonwell")
    root = bpy.data.objects["Moonwell"]
    rig = make_rig(col, root, BONES)
    k = BoneKit()
    # ---- the water: deep blue to the brim, the crescent's reflection lying on it, ripples running out under the coping
    k.bone("water")
    bm_cyl(k[DEEP], 0.45, 0.45, 0.05, (W.x, W.y, WATER - 0.025), seg=18)
    k.bone("moon")
    bm = k[LIGHT]
    n, r_mid = 12, 0.15
    for i in range(n):
        strip = []
        for j in (i, i + 1):
            a = math.radians(-50 + 280 * j / n)
            hw = 0.006 + 0.05 * math.sin(math.pi * j / n) ** 0.8
            strip.append((bm.verts.new((WC.x + math.cos(a) * (r_mid - hw), WC.y + math.sin(a) * (r_mid - hw), WATER + 0.004)),
                          bm.verts.new((WC.x + math.cos(a) * (r_mid + hw), WC.y + math.sin(a) * (r_mid + hw), WATER + 0.004))))
        bm.faces.new((strip[0][0], strip[0][1], strip[1][1], strip[1][0]))
    for i in range(3):
        k.bone("ripple.%d" % i)
        ring(k[PALE], (W.x, W.y, 0), 0.4, 0.372, WATER + 0.001, WATER + 0.007, seg=18)
    # ---- lily pads and a lotus, drifting
    k.bone("lily")
    for dx, dy, r, turn in ((0.28, -0.2, 0.12, 40), (-0.33, -0.02, 0.095, 200), (0.2, 0.28, 0.07, 300), (-0.17, -0.3, 0.07, 120)):
        c = Vector((W.x + dx, W.y + dy, 0))
        pts = [c] + [c + Vector((math.cos(math.radians(turn + 310 * j / 8)) * r, math.sin(math.radians(turn + 310 * j / 8)) * r, 0)) for j in range(9)]
        prism(k["grass:0.25:0.7"], pts, WATER - 0.004, WATER + 0.014)
    lc = Vector((W.x + 0.28, W.y - 0.2, WATER + 0.014))
    for j in range(6):
        a = math.radians(60 * j + 15)
        d = Vector((math.cos(a), math.sin(a), 0))
        bm_crystal(k["cream:0.0:0.35"], lc + d * 0.015, lc + d * 0.075 + Vector((0, 0, 0.07)), 0.032, n=4, shoulder=0.45, foot=0.6)
    bm_cyl(k["gold:0.1:0.4"], 0.024, 0.012, 0.05, (lc.x, lc.y, lc.z + 0.03), seg=5)
    # ---- the crystal on its chain, a silver cap, a ring of light round it
    k.bone("crystal")
    bm_tube(k["stone2:0.0:0.4"], [HANG, CRYSTAL + Vector((0, 0, 0.2))], 0.014, n=4)
    bm_cyl(k["white:0.0:0.35"], 0.035, 0.085, 0.1, tuple(CRYSTAL + Vector((0, 0, 0.19))), seg=6)
    bm_crystal(k[LIGHT], CRYSTAL + Vector((0, 0, 0.15)), CRYSTAL - Vector((0, 0, 0.36)), 0.135, n=6, shoulder=0.3, foot=0.55)
    k.bone("halo")
    hb = bmesh.new()
    ring(hb, (0, 0, 0), 0.285, 0.255, -0.012, 0.012, seg=16)
    bmesh.ops.transform(hb, matrix=Matrix.Translation(CRYSTAL - Vector((0, 0, 0.08))) @ Matrix.Rotation(math.radians(24), 4, "X"), verts=hb.verts)
    me = bpy.data.meshes.new("_halo")
    hb.to_mesh(me)
    hb.free()
    k[PALE].from_mesh(me)
    bpy.data.meshes.remove(me)
    # ---- motes of light
    for i in range(MOTES):
        k.bone("mote.%d" % i)
        h = Vector(BONES["mote.%d" % i][0])
        bm_crystal(k[PALE], h - Vector((0, 0, 0.075)), h + Vector((0, 0, 0.095)), 0.062, n=4, shoulder=0.45, foot=0.0)
    k.emit_bones("Head_Magic", col, rig)
    # ---- two ribbons in the team's color streaming from the horn
    flag_part("Head_Ribbon1", col, rig, "rib1", TIP + Vector((0.03, 0, -0.02)), (0, 0, -1), 0.62, 0.17, segs=3, tail="swallow", hang=(1, 0, 0))
    flag_part("Head_Ribbon2", col, rig, "rib2", TIP + Vector((0.2, 0, 0.02)), (0, 0, -1), 0.46, 0.13, segs=3, tail="point", hang=(1, 0, 0))
    head = bpy.data.objects["Head"]
    empty("Muzzle", col, head, tuple(CRYSTAL - Vector((W.x, W.y, WATER))), 0.2, "SPHERE")
    return rig


IDLE_LEN = 120
RIPPLE = 60          # frames from the middle of the water to the rim


def build_anims():
    rig = bpy.data.objects["Rig"]
    pb = rig.pose.bones
    q = arm_space_quat
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1):
        ph = 2 * math.pi * f / IDLE_LEN
        rest_pose(rig)
        sw = 1.0 + 0.012 * math.sin(ph * 2)
        pb["water"].scale = (sw, sw, 1.0)
        pb["water"].location = arm_space_loc(pb["water"], (0, 0, 0.006 * math.sin(ph * 2)))
        ms = 1.0 + 0.16 * math.sin(ph * 3) * math.sin(ph)
        pb["moon"].scale = (ms, ms, 1.0)
        pb["moon"].rotation_quaternion = q(pb["moon"], (0, 0, 1), 9 * math.sin(ph))
        for i in range(3):
            t = ((f + i * RIPPLE / 3.0) % RIPPLE) / RIPPLE
            b = pb["ripple.%d" % i]
            hidden = t < 0.04 or t > 0.96           # (it jumps back to the middle sunk under the water)
            s = 0.07 + 1.12 * t
            b.scale = (s, s, 1.0)
            b.location = arm_space_loc(b, (0, 0, -0.06 if hidden else 0.0))
        pb["lily"].location = arm_space_loc(pb["lily"], (0, 0, 0.007 * math.sin(ph * 2 + 0.6)))
        pb["lily"].rotation_quaternion = q(pb["lily"], (0, 0, 1), 7 * math.sin(ph))
        c = pb["crystal"]
        c.rotation_quaternion = q(c, (1, 0, 0), 3.5 * math.sin(ph)) @ q(c, (0, 1, 0), 2.5 * math.sin(ph * 2 + 1)) @ q(c, (0, 0, 1), 180.0 * f / IDLE_LEN)
        c.location = arm_space_loc(c, (0, 0, 0.025 * math.sin(ph * 2)))
        pb["halo"].rotation_quaternion = q(pb["halo"], (0, 0, 1), 540.0 * f / IDLE_LEN)
        hs = 1.0 + 0.07 * math.sin(ph * 4)
        pb["halo"].scale = (hs, hs, hs)
        for i in range(MOTES):
            mote_pose(pb, "mote.%d" % i, f / IDLE_LEN + i / MOTES + 0.13 * (i % 2), (WC.x, WC.y, WATER + 0.05), 1.42, 0.36, 0.1, 1.3,
                      i * 2.4, size=0.8 + 0.4 * ((i * 7) % 3) / 2)
        wave_flag(rig, "rib1", f / 60.0, amp=1.5, segs=3, axis=(0, 1, 0))
        wave_flag(rig, "rib2", f / 40.0 + 0.3, amp=1.7, segs=3, axis=(0, 1, 0))
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0, 1.4), "dist": 7.6, "yaw": 150, "pitch": 20, "anim_target": (0, 0.1, 1.5), "anim_dist": 6.0,
           "frames": [("idle", 0), ("idle", 24), ("idle", 48), ("idle", 72), ("idle", 96)],
           "extra": [{"yaw": 0, "pitch": 50, "dist": 3.6, "target": (W.x, W.y, 1.0)},
                     {"yaw": 200, "pitch": 14, "dist": 4.2, "target": (0, 0, 1.9)},
                     {"yaw": 120, "pitch": 26, "dist": 3.8, "target": (0, 0, 0.8)},
                     {"yaw": 90, "pitch": 6, "dist": 6.5, "target": (0, 0, 1.4)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
