"""Builds the Trebuchet (footprint "arrow5": [0,0] the tip in front, [1,0] / [-1,1] flanking just behind it, [0,1] and
[0,2] trailing straight back), the Crown's tier III siege engine: boulders lobbed across the map.

    python tools/blender/build.py trebuchet --out <preview dir>

One great counterweight trebuchet on a turntable of heavy planks, bedded in a ring of masonry in the middle of the
footprint (the Head: the whole engine turns within its 120 degree arc). Two A-frame trestles with king posts and raking
side struts carry the axle; the long throwing arm is drawn down to the rear by a windlass with two big spoked wheels,
its sling laid forward in the trough with a boulder in the pouch; the counterweight, a team-painted chest of stones,
hangs high at the front. The rest of the footprint is the engine's yard: a log crib of boulders with loading skids on
the left flank, a rack of firepots under a team awning and a pitch kettle on the right, a palisade of sharpened stakes
round the front, and a plank walk back to the crew's tiled shelter on the last hex.
Clips: idle (the counterweight sways, the arm creaks against its rope, the pennant flies), fire (the counterweight
drops, the arm whips over, the sling lets go at the top (frame 6), then follow-through and rocking), reload (the
windlass hauls the arm down, the sling is laid out, a new boulder drops into the pouch).
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "siege_common.py"), encoding="utf-8").read())

TID = "trebuchet"
CELLS = [(0, 0), (1, 0), (-1, 1), (0, 1), (0, 2)]
MID = footprint_mid(CELLS)
TIPC = hex_to_world(0, 0, MID)
FR = hex_to_world(1, 0, MID)
FL = hex_to_world(-1, 1, MID)
MIDC = hex_to_world(0, 1, MID)
BACK = hex_to_world(0, 2, MID)
TOP = 0.34
PIV = Vector((0.0, (TIPC.y + MIDC.y) * 0.5, 0.0))      # the turntable's pivot: where the four front hexes meet
RING_R = 1.42
DECK_R = 1.2
ES = 1.16                       # the engine is laid out at 1.0 and built this much bigger (the turntable keeps its size)
DECK_Z = TOP + 0.24

# ---- the engine, in the head's space (+Y forward, z = 0 the deck's top)
AXLE = Vector((0, 0.2, 1.5))
COCK = 36.0                     # the long arm's angle below level when it's drawn down
LA, SA, RPL = 1.75, 0.58, 1.45  # long arm, short arm, where the windlass rope is made fast
TX = 0.4                        # the trestles stand this far either side
U0 = Vector((0, -math.cos(math.radians(COCK)), -math.sin(math.radians(COCK))))
TIP0 = AXLE + U0 * LA
PIN0 = AXLE - U0 * SA
POUCH0 = Vector((0, -0.15, 0.2))
SL = (POUCH0 - TIP0).length
S0 = (POUCH0 - TIP0).normalized()
WINCH = Vector((0, -0.7, 0.5))
DRUM_R = 0.065
ROPE0 = WINCH + Vector((0, 0, DRUM_R + 0.012))
RP0 = AXLE + U0 * RPL
TH_UP = -(90.0 + COCK)          # the arm's turn from drawn to straight up
TH_REL, PSI_REL = TH_UP - 14.0, -285.0     # arm and sling at the moment the sling lets go
D0 = math.degrees(math.atan2(S0.z, S0.y))  # the sling's own angle when it lies in the trough
PSI_HANG = -90.0 - D0           # the sling hanging straight down from the arm's tip
POLE = Vector((TX, AXLE.y, AXLE.z + 0.12))
PEN_Z = AXLE.z + 0.95


def rotx(v, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return Vector((v.x, v.y * c - v.z * s, v.y * s + v.z * c))


def arm_tip(th):
    return AXLE + rotx(U0, th) * LA


MUZZLE = arm_tip(TH_REL) + rotx(S0, PSI_REL) * SL


def build_base():
    col = collection("Trebuchet")
    root = empty("Trebuchet", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    rnd = random.Random(11)
    k = Kit()
    inner = outline(CELLS, 0.22)
    P = Vector((PIV.x, PIV.y, 0))
    # ---- the turntable's bed: a ring of masonry with an iron rail, a dark pit inside
    bm_block_course(k["stone:0.1:0.7"], rnd, P, RING_R, T - 0.02, 0.17, 22, depth=0.26)
    bm_cyl(k["stone_dark:0.3:0.8"], RING_R - 0.2, RING_R - 0.2, 0.08, (P.x, P.y, T + 0.03), seg=22)
    k.emit("Bed", col, root, vary=0.08)
    ring(k["iron:0.1:0.5"], (P.x, P.y, 0), RING_R - 0.07, RING_R - 0.15, T + 0.14, T + 0.175, seg=20)
    k.emit("Bed_Rail", col, root)
    # ---- paving round the bed ties the hexes together
    shed = (BACK.x, BACK.y)

    def paved(x, y):
        if not inside(inner, x, y):
            return False
        d = math.hypot(x - P.x, y - P.y)
        if d < RING_R + 0.04:
            return False
        if abs(x - shed[0]) < 0.86 and abs(y - shed[1]) < 0.6:
            return False
        return d < 2.02 or y < -0.3
    bm_flagstones(k["stone2:0.15:0.7"], rnd, paved, (-3.0, -3.6, 3.0, 2.8), T, size=0.3, keep=0.93)
    k.emit("Paving", col, root, vary=0.09)
    # ---- the plank walk from the bed back to the shelter
    y = P.y - RING_R - 0.02
    while y - 0.17 > BACK.y + 0.5:
        w = 0.66 + rnd.uniform(-0.03, 0.03)
        bm_box(k["wood:0.3:0.85"], (w, 0.16, 0.05), (rnd.uniform(-0.02, 0.02), y - 0.085, T + 0.04), (0, 0, rnd.uniform(-2.5, 2.5)))
        y -= 0.175
    for sx in (-1, 1):
        bm_beam(k["wood_dark:0.3:0.8"], (sx * 0.27, P.y - RING_R + 0.05, T + 0.012), (sx * 0.27, BACK.y + 0.5, T + 0.012), 0.07, 0.03)
    k.emit("Walk", col, root, vary=0.09)
    # ---- the palisade: sharpened stakes leaning out along the whole front, lashed to a rail of logs
    front = [Vector((-2.34, -0.2, 0)), Vector((-2.8, 0.62, 0)), Vector((-2.36, 1.52, 0)), Vector((-1.22, 1.52, 0)), Vector((-0.56, 2.5, 0)),
             Vector((0.56, 2.5, 0)), Vector((1.22, 1.52, 0)), Vector((2.36, 1.52, 0)), Vector((2.8, 0.62, 0)), Vector((2.34, -0.2, 0))]
    for a, b in zip(front, front[1:]):
        d = (b - a)
        n = max(2, int(round(d.length / 0.25)))
        out = Vector((d.y, -d.x, 0)).normalized()
        if out.dot((a + b) * 0.5 - P) < 0:
            out = -out
        for i in range(n):
            p = a.lerp(b, (i + 0.5) / n) + out * rnd.uniform(-0.02, 0.02)
            lean = (Vector((0, 0, 1)) + out * rnd.uniform(0.22, 0.38) + d.normalized() * rnd.uniform(-0.08, 0.08)).normalized()
            bm_stake(k["wood:0.15:0.9"], (p.x, p.y, T - 0.04), lean, rnd.uniform(0.56, 0.69), r=rnd.uniform(0.055, 0.068), n=5)
        bm_tube(k["wood_dark:0.2:0.8"], [(a.x + out.x * 0.07, a.y + out.y * 0.07, T + 0.3), (b.x + out.x * 0.07, b.y + out.y * 0.07, T + 0.3)], 0.045, n=5)
    k.emit("Palisade", col, root, vary=0.1)
    for p, o in ((Vector((0, 2.62, 0)), Vector((0, 1, 0))), (Vector((-1.8, 1.66, 0)), Vector((0, 1, 0))), (Vector((1.8, 1.66, 0)), Vector((0, 1, 0)))):
        bm_shield(k, (p.x, p.y, T + 0.42), (o.x, o.y + 0.0, 0.42), w=0.34, h=0.4)
    k.emit("Palisade_Shields", col, root)
    # ---- left flank: the boulder stockpile in a crib of logs, skids up onto the bed
    cx0, cx1, cy0, cy1 = -2.42, -1.66, 0.2, 1.2
    for lvl in range(3):
        z = T + 0.07 + lvl * 0.13
        if lvl % 2 == 0:
            for yy in (cy0, cy1):
                bm_tube(k["wood:0.2:0.85"], [(cx0 - 0.1, yy, z), (cx1 + 0.1, yy, z)], 0.07, n=7)
        else:
            bm_tube(k["wood:0.2:0.85"], [(cx0, cy0 - 0.1, z), (cx0, cy1 + 0.1, z)], 0.07, n=7)
            bm_tube(k["wood:0.2:0.85"], [(cx1, cy0 - 0.1, z), (cx1, cy0 + 0.22, z)], 0.07, n=7)
            bm_tube(k["wood:0.2:0.85"], [(cx1, cy1 - 0.22, z), (cx1, cy1 + 0.1, z)], 0.07, n=7)
    for x, yy in ((cx0, cy0), (cx0, cy1), (cx1, cy0), (cx1, cy1)):
        bm_stake(k["wood_dark:0.2:0.8"], (x, yy, T - 0.02), (0, 0, 1), 0.62, r=0.055, n=6, point=0.2)
    k.emit("Crib", col, root, vary=0.09)
    for dx, dy, r, dz in ((0.2, 0.22, 0.24, 0), (0.55, 0.26, 0.22, 0), (0.22, 0.6, 0.23, 0), (0.56, 0.72, 0.25, 0), (0.36, 0.44, 0.22, 0.3), (0.2, 0.84, 0.19, 0.0),
                          (0.5, 0.5, 0.2, 0.26)):
        bm_boulder(k["stone:0.1:0.85"], rnd, (cx0 + dx, cy0 + dy, T + dz), r, squash=(1, 1, 0.92), n=12, sink=0.08)
    bm_boulder(k["stone:0.1:0.85"], rnd, (cx1 + 0.24, 0.62, T + 0.1), 0.2, squash=(1, 1, 0.95), n=12, sink=0.0)     # one on the skids
    k.emit("Boulders", col, root, vary=0.08, seed=4)
    for yy in (0.5, 0.76):
        bm_beam(k["wood_red:0.2:0.8"], (cx1 - 0.05, yy, T + 0.05), (P.x - RING_R + 0.1, yy, T + 0.19), 0.12, 0.05)
    bm_beam(k["wood_dark:0.2:0.8"], (cx1 + 0.08, 0.4, T + 0.03), (cx1 + 0.08, 0.86, T + 0.03), 0.07, 0.07)
    k.emit("Skids", col, root)
    # ---- right flank: firepots racked under an awning in the team's color, pitch warming on the coals
    rx, ry0, ry1 = 2.3, 0.28, 1.2
    for yy in (ry0, ry1):
        bm_box(k["wood_dark:0.2:0.8"], (0.08, 0.08, 0.95), (rx + 0.18, yy, T + 0.475))
        bm_box(k["wood_dark:0.2:0.8"], (0.08, 0.08, 0.68), (rx - 0.2, yy, T + 0.34))
        bm_beam(k["wood_dark:0.2:0.8"], (rx + 0.18, yy, T + 0.93), (rx - 0.36, yy, T + 0.6), 0.06, 0.06)
    for z, dx in ((0.2, -0.02), (0.5, 0.06)):
        bm_box(k["wood:0.25:0.8"], (0.3, ry1 - ry0 + 0.1, 0.04), (rx + dx, (ry0 + ry1) / 2, T + z))
    k.emit("Rack", col, root)
    for z, dx, n in ((0.22, -0.02, 4), (0.52, 0.06, 3)):
        for i in range(n):
            yy = ry0 + 0.12 + (ry1 - ry0 - 0.24) * (i + 0.5 * (4 - n)) / 3.0
            bm_ellipsoid(k["roof:0.1:0.8"], (rx + dx, yy, T + z + 0.1), (0.105, 0.105, 0.1), u=6, v=4)
            bm_cyl(k["roof:0.2:0.9"], 0.05, 0.04, 0.05, (rx + dx, yy, T + z + 0.21), seg=7)
            bm_cyl(k["cream:0.2:0.7"], 0.03, 0.02, 0.04, (rx + dx, yy, T + z + 0.25), seg=5)
    k.emit("Firepots", col, root, vary=0.06)
    aw = [Vector((rx + 0.26, ry0 - 0.12, T + 0.96)), Vector((rx + 0.26, ry1 + 0.12, T + 0.96)), Vector((rx - 0.44, ry1 + 0.12, T + 0.56)), Vector((rx - 0.44, ry0 - 0.12, T + 0.56))]
    bm = k["team!:0.1:0.7"]
    nrm = (aw[1] - aw[0]).cross(aw[3] - aw[0]).normalized()
    if nrm.z < 0:
        nrm = -nrm
    cuts = 4
    for i in range(cuts):                                       # the awning: strips of canvas, sagging a little between
        t0, t1 = i / cuts, (i + 1) / cuts
        q = [aw[0].lerp(aw[1], t0), aw[0].lerp(aw[1], t1), aw[3].lerp(aw[2], t1), aw[3].lerp(aw[2], t0)]
        mid0, mid1 = (q[0] + q[3]) * 0.5 - Vector((0, 0, 0.035)), (q[1] + q[2]) * 0.5 - Vector((0, 0, 0.035))
        for quad in ((q[0], q[1], mid1, mid0), (mid0, mid1, q[2], q[3])):
            vs = [bm.verts.new(p + nrm * 0.012) for p in quad] + [bm.verts.new(p - nrm * 0.012) for p in quad]
            fs = [bm.faces.new(vs[:4]), bm.faces.new(list(reversed(vs[4:])))]
            for a in range(4):
                b = (a + 1) % 4
                fs.append(bm.faces.new((vs[b], vs[a], vs[4 + a], vs[4 + b])))
            bmesh.ops.recalc_face_normals(bm, faces=fs)
    k.emit("Awning", col, root, vary=0.05)
    K = Vector((1.72, 0.0, 0))                                  # the pitch kettle on its ring of stones
    for i in range(7):
        p = polar(K, 360 * i / 7 + 12, 0.2)
        bm_boulder(k["stone:0.2:0.9"], rnd, (p.x, p.y, T - 0.01), 0.075, n=8)
    bm_cyl(k[EMBERS], 0.15, 0.12, 0.05, (K.x, K.y, T + 0.045), seg=8)
    for i in range(3):
        bm_beam(k["iron:0.1:0.6"], polar(K, 120 * i + 40, 0.23, T), polar(K, 120 * i + 40, 0.12, T + 0.2), 0.03, 0.03)
    bm_cyl(k["iron:0.0:0.5"], 0.11, 0.17, 0.17, (K.x, K.y, T + 0.26), seg=9)
    ring(k["iron:0.0:0.4"], (K.x, K.y, T + 0.345), 0.185, 0.14, -0.02, 0.02, seg=9)
    bm_cyl(k["black:0.4:0.8"], 0.15, 0.15, 0.02, (K.x, K.y, T + 0.335), seg=9)
    k.emit("Kettle", col, root, vary=0.05)
    # ---- the crew's shelter on the last hex: posts, boarded back and sides, a tiled roof in the team's color
    S = Vector((BACK.x, BACK.y, 0))
    w, d, ez = 1.5, 0.96, T + 0.72
    for sx in (-1, 1):
        for sy in (-1, 1):
            bm_box(k["wood_dark:0.2:0.8"], (0.1, 0.1, ez - T + 0.02), (S.x + sx * (w / 2 - 0.05), S.y + sy * (d / 2 - 0.05), (T + ez) / 2))
        bm_beam(k["wood_dark:0.2:0.8"], (S.x + sx * (w / 2 - 0.05), S.y - d / 2, ez), (S.x + sx * (w / 2 - 0.05), S.y + d / 2, ez), 0.09, 0.09)
        bm_box(k["wood_dark:0.2:0.8"], (0.08, 0.08, 0.34), (S.x + sx * (w / 2 - 0.05), S.y, ez + 0.19))
    bm_beam(k["wood_dark:0.2:0.8"], (S.x - w / 2, S.y + d / 2 - 0.05, ez), (S.x + w / 2, S.y + d / 2 - 0.05, ez), 0.09, 0.09)
    k.emit("Shelter_Frame", col, root)
    bm_planks(k["wood:0.3:0.85"], rnd, (S.x + w / 2 - 0.08, S.y - d / 2 + 0.03, T), (0, 0, ez - T), (-(w - 0.16), 0, 0), 8, th=0.045)
    for sx in (-1, 1):
        bm_planks(k["wood:0.3:0.85"], rnd, (S.x + sx * (w / 2 - 0.03), S.y + sx * (d / 2 - 0.1), T), (0, 0, 0.42), (0, -sx * (d - 0.2), 0), 5, th=0.045)
    k.emit("Shelter_Walls", col, root, vary=0.09)
    bm_gable_roof(k, rnd, (S.x, S.y, 0), w, d, ez + 0.03, 0.38, rows=4, cols=5, over=0.13)
    k.emit("Shelter_Roof", col, root, vary=0.08)
    bm_box(k["wood_red:0.2:0.8"], (0.95, 0.3, 0.05), (S.x - 0.1, S.y - d / 2 + 0.24, T + 0.38))                  # the bench
    for sx in (-1, 1):
        bm_box(k["wood_red:0.2:0.8"], (0.06, 0.26, 0.36), (S.x - 0.1 + sx * 0.4, S.y - d / 2 + 0.24, T + 0.18))
    bm_rope_coil(k["sand:0.3:0.7"], (S.x - 0.3, S.y - d / 2 + 0.24, T + 0.405), r=0.12, th=0.03, turns=2)
    bm_cyl(k["iron:0.1:0.5"], 0.012, 0.012, 0.22, (S.x + 0.2, S.y + d / 2 - 0.05, ez - 0.14), seg=4)              # a lantern on the tie beam
    bm_cyl(k["iron:0.1:0.5"], 0.055, 0.02, 0.04, (S.x + 0.2, S.y + d / 2 - 0.05, ez - 0.24), seg=6)
    bm_cyl(k["glow:1.0,0.72,0.3,1.0"], 0.04, 0.04, 0.1, (S.x + 0.2, S.y + d / 2 - 0.05, ez - 0.31), seg=6)
    bm_cyl(k["iron:0.1:0.5"], 0.05, 0.05, 0.02, (S.x + 0.2, S.y + d / 2 - 0.05, ez - 0.37), seg=6)
    k.emit("Shelter_Kit", col, root)
    for i, (rel, loc, rot, sc) in enumerate((("hex/hammer", (S.x + 0.12, S.y - d / 2 + 0.26, T + 0.405), 70, 1.6),
                                             ("forest/Bush_1_C_Color1", (0.95, BACK.y - 0.1, T - 0.02), 40, 0.22),
                                             ("forest/Grass_1_B_Color1", (-0.92, BACK.y - 0.05, T - 0.02), 120, 0.42))):
        for o in kk_import(rel, col, root, loc, rot, sc, name="Prop_KK_%d" % i):
            for c in [o] + list(o.children_recursive):
                if c.type == "MESH":
                    teamify(c)
    empty("Head", col, root, (PIV.x, PIV.y, DECK_Z), 0.5, "SINGLE_ARROW")
    return root


BONES = {"root": ((0, 0, 0), (0, 0, 0.2), None),
         "frame": ((0, 0, 0), (0, 0.3, 0), "root"),
         "arm": (tuple(AXLE), tuple(AXLE + U0 * 0.4), "frame"),
         "cw": (tuple(PIN0), (PIN0.x, PIN0.y, PIN0.z - 0.3), "arm"),
         "sling": (tuple(TIP0), tuple(POUCH0), "arm"),
         "boulder": (tuple(POUCH0), (POUCH0.x, POUCH0.y, POUCH0.z + 0.2), "sling"),
         "winch": (tuple(WINCH), (WINCH.x + 0.3, WINCH.y, WINCH.z), "frame"),
         "rope": (tuple(ROPE0), tuple(RP0), "frame")}
flag_bones(BONES, "pen", (POLE.x, POLE.y, PEN_Z), (1, 0, 0), 0.6, segs=3, parent="frame")


def _arm_wh(t):
    """The arm's width and depth, t along the long arm from the axle."""
    u = min(max((t - 0.25) / (LA - 0.25), 0.0), 1.0)
    return 0.17 - 0.085 * u, 0.22 - 0.115 * u


def build_head():
    col = collection("Trebuchet")
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES, scale=ES)
    rnd = random.Random(5)
    k = Kit()
    # ---- the turntable: planks on crossed sleepers that ride the bed's rail, an iron tyre with studs
    bm_deck(k["wood:0.3:0.85"], rnd, (0, 0, 0), circle_half(DECK_R), -DECK_R, DECK_R, 0.0, pw=0.165, th=0.07, turn=90)
    k.emit("Head_Deck", col, rig=rig, bone="root", vary=0.09)
    for a in (45, 135):
        o = radial(a)
        bm_beam(k["wood_dark:0.3:0.85"], o * -(DECK_R + 0.12) + Vector((0, 0, -0.105)), o * (DECK_R + 0.12) + Vector((0, 0, -0.105)), 0.2, 0.09)
    ring(k["iron:0.1:0.55"], (0, 0, 0), DECK_R + 0.025, DECK_R - 0.06, -0.08, 0.012, seg=20)
    for i in range(8):
        p = polar((0, 0, 0), 45 * i + 22.5, DECK_R - 0.02, 0.014)
        bm_cyl(k["iron:0.0:0.4"], 0.03, 0.03, 0.014, tuple(p), seg=6)
    k.emit("Head_DeckIron", col, rig=rig, bone="root")
    # ---- the frame: sole beams, cross beams, the sling's trough
    W, WD = "wood:0.2:0.8", "wood_dark:0.2:0.8"
    for sx in (-1, 1):
        bm_beam(k[WD], (sx * TX, -1.02, 0.065), (sx * TX, 1.0, 0.065), 0.16, 0.13)
        bm_beam(k[W], (sx * 0.17, -0.5, 0.035), (sx * 0.17, 0.74, 0.035), 0.05, 0.07)
    for y in (-0.98, AXLE.y, 0.94):
        bm_beam(k[WD], (-TX, y, 0.055), (TX, y, 0.055), 0.13, 0.11)
    bm_box(k["sand:0.4:0.8"], (0.3, 1.24, 0.02), (0, 0.12, 0.012))
    # ---- two A-frame trestles: legs, a king post, a collar; a raking strut out to the turntable's edge on each side
    for sx in (-1, 1):
        x = sx * TX
        for sy in (-1, 1):
            bm_beam(k[W], (x, AXLE.y + sy * 0.8, 0.1), (x, AXLE.y + sy * 0.035, AXLE.z + 0.05), 0.125, 0.125)
        bm_beam(k[W], (x, AXLE.y, 0.12), (x, AXLE.y, AXLE.z - 0.1), 0.11, 0.11)
        bm_beam(k[WD], (sx * (TX + 0.085), AXLE.y - 0.55, 0.6), (sx * (TX + 0.085), AXLE.y + 0.55, 0.6), 0.06, 0.11)
        bm_box(k[WD], (0.18, 0.32, 0.25), (x, AXLE.y, AXLE.z))
        bm_beam(k[WD], (sx * (TX - 0.05), AXLE.y, 0.05), (sx * 1.04, AXLE.y, 0.05), 0.15, 0.1)
        bm_beam(k[W], (sx * 0.99, AXLE.y, 0.08), (sx * (TX + 0.05), AXLE.y, AXLE.z - 0.2), 0.1, 0.1)
        bm_box(k[WD], (0.11, 0.18, 0.52), (x, WINCH.y, 0.13 + 0.25))                                              # the windlass's cheeks
    k.emit("Head_Frame", col, rig=rig, bone="frame", bevel=0.01, scale=ES)
    bm_cyl(k["iron:0.1:0.5"], 0.055, 0.055, 2 * TX + 0.3, tuple(AXLE), rot=(0, 90, 0), seg=8)
    for sx in (-1, 1):
        bm_cyl(k["iron:0.0:0.4"], 0.09, 0.09, 0.05, (sx * (TX + 0.115), AXLE.y, AXLE.z), rot=(0, 90, 0), seg=8)
        for sy in (-1, 1):                                                                                       # shoes on the legs' feet
            bm_box(k["iron:0.1:0.5"], (0.15, 0.1, 0.06), (sx * TX, AXLE.y + sy * 0.76, 0.15))
        bm_box(k["iron:0.1:0.5"], (0.07, 0.12, 0.08), (sx * 1.0, AXLE.y, 0.1))
    k.emit("Head_FrameIron", col, rig=rig, bone="frame", scale=ES)
    # the pennant's pole on the right trestle
    bm_cyl(k["wood_dark:0.2:0.7"], 0.024, 0.018, PEN_Z + 0.05 - POLE.z, (POLE.x, POLE.y, (PEN_Z + 0.05 + POLE.z) / 2), seg=6)
    bm_cyl(k["gold:0.05:0.5"], 0.04, 0.0, 0.11, (POLE.x, POLE.y, PEN_Z + 0.105), seg=5)
    k.emit("Head_Pole", col, rig=rig, bone="frame", scale=ES)
    flag_part("Head_Pennant", col, rig, "pen", (POLE.x, POLE.y, PEN_Z), (1, 0, 0), 0.6, 0.3, segs=3, tail="swallow", scale=ES)
    # ---- the throwing arm: a tapering beam with a yoke at the axle, iron bands, a painted band, the sling's prong
    bm_beam(k[W], AXLE - U0 * (SA + 0.09), AXLE + U0 * 0.25, 0.17, 0.22)
    bm_beam(k[W], AXLE + U0 * 0.25, TIP0, 0.17, 0.22, w1=0.085, h1=0.105)
    bm_beam(k[WD], AXLE - U0 * 0.24, AXLE + U0 * 0.3, 0.215, 0.275)
    k.emit("Head_Arm", col, rig=rig, bone="arm", bevel=0.01, scale=ES)
    for t in (0.62, 1.05, RPL):
        w, h = _arm_wh(t)
        bm_beam(k["iron:0.1:0.5"], AXLE + U0 * (t - 0.03), AXLE + U0 * (t + 0.03), w + 0.022, h + 0.022)
    bm_beam(k["iron:0.1:0.5"], AXLE - U0 * (SA - 0.06), AXLE - U0 * (SA + 0.1), 0.195, 0.245)
    bm_cyl(k["iron:0.0:0.4"], 0.035, 0.035, 0.64, tuple(PIN0), rot=(0, 90, 0), seg=6)
    up0 = rotx(U0, -90)
    bm_beam(k["iron:0.0:0.4"], TIP0 - U0 * 0.05, TIP0 + U0 * 0.14 + up0 * 0.04, 0.03, 0.03)
    for t in (LA - 0.2, LA - 0.12):
        w, h = _arm_wh(t)
        bm_beam(k["sand:0.3:0.7"], AXLE + U0 * (t - 0.025), AXLE + U0 * (t + 0.025), w + 0.02, h + 0.02)
    k.emit("Head_ArmIron", col, rig=rig, bone="arm", scale=ES)
    w, h = _arm_wh(0.42)
    bm_beam(k["team!:0.15:0.6"], AXLE + U0 * 0.33, AXLE + U0 * 0.55, w + 0.014, h + 0.014)
    k.emit("Head_ArmBand", col, rig=rig, bone="arm", scale=ES)
    # ---- the counterweight: a framed chest painted in the team's color, heaped with stones, hung from the short end
    bc = PIN0 + Vector((0, 0, -0.5))
    bw, bd, bh = 0.56, 0.52, 0.48
    for sx in (-1, 1):
        for sy in (-1, 1):
            bm_box(k[WD], (0.075, 0.075, bh + 0.04), (bc.x + sx * (bw / 2 - 0.03), bc.y + sy * (bd / 2 - 0.03), bc.z))
        for z in (-bh / 2 + 0.02, bh / 2 - 0.01):
            bm_box(k[WD], (0.06, bd - 0.1, 0.07), (bc.x + sx * (bw / 2 - 0.03), bc.y, bc.z + z))
            bm_box(k[WD], (bw - 0.1, 0.06, 0.07), (bc.x, bc.y + sx * (bd / 2 - 0.03), bc.z + z))
    bm_box(k[WD], (bw - 0.08, bd - 0.08, 0.05), (bc.x, bc.y, bc.z - bh / 2 + 0.03))
    k.emit("Head_CwFrame", col, rig=rig, bone="cw", scale=ES)
    for sx in (-1, 1):
        bm_box(k["team!:0.1:0.7"], (0.03, bd - 0.12, bh - 0.1), (bc.x + sx * (bw / 2 - 0.045), bc.y, bc.z))
        bm_box(k["team!:0.1:0.7"], (bw - 0.12, 0.03, bh - 0.1), (bc.x, bc.y + sx * (bd / 2 - 0.045), bc.z))
    k.emit("Head_CwPanels", col, rig=rig, bone="cw", scale=ES)
    for sy in (-1, 1):
        bm_plate(k["gold:0.05:0.5"], crown_pts(0.24, 0.15), (bc.x, bc.y + sy * (bd / 2 - 0.025), bc.z), (-sy, 0, 0), (0, 0, 1), 0.016)
        for sx in (-1, 1):                                                                                       # the hangers: an inverted V each side
            bm_beam(k["iron:0.0:0.45"], (sx * 0.295, PIN0.y, PIN0.z + 0.02), (sx * 0.295, bc.y + sy * (bd / 2 - 0.06), bc.z + bh / 2), 0.035, 0.06)
    for sx in (-1, 1):
        for sy in (-1, 1):
            for z in (-bh / 2 + 0.02, bh / 2 - 0.01):
                bm_box(k["gold:0.1:0.55"], (0.09, 0.09, 0.04), (bc.x + sx * (bw / 2 - 0.03), bc.y + sy * (bd / 2 - 0.03), bc.z + z))
    k.emit("Head_CwIron", col, rig=rig, bone="cw", scale=ES)
    for dx, dy, r in ((-0.12, -0.1, 0.14), (0.13, -0.08, 0.13), (0.0, 0.12, 0.15), (-0.15, 0.13, 0.1), (0.15, 0.14, 0.11), (0.0, -0.02, 0.12)):
        bm_boulder(k["stone:0.1:0.8"], rnd, (bc.x + dx, bc.y + dy, bc.z + bh / 2 - 0.12 + (0.08 if dx == 0.0 and dy < 0 else 0)), r, n=10, sink=0.0)
    k.emit("Head_CwStones", col, rig=rig, bone="cw", vary=0.08, scale=ES)
    # ---- the sling: two ropes from the arm's tip to a leather pouch; the boulder on a bone of its own
    for sx in (-1, 1):
        bm_tube(k["sand:0.3:0.7"], [TIP0 + U0 * 0.08, POUCH0 + Vector((sx * 0.14, -0.16, -0.06)), POUCH0 + Vector((sx * 0.15, 0.12, -0.1))], 0.018, n=4)
    bm_box(k["tan:0.3:0.8"], (0.32, 0.36, 0.035), (POUCH0.x, POUCH0.y, POUCH0.z - 0.165))
    bm_box(k["tan:0.3:0.8"], (0.3, 0.035, 0.16), (POUCH0.x, POUCH0.y + 0.185, POUCH0.z - 0.1), (-18, 0, 0))
    for sx in (-1, 1):
        bm_box(k["tan:0.3:0.8"], (0.035, 0.32, 0.1), (POUCH0.x + sx * 0.165, POUCH0.y, POUCH0.z - 0.13), (0, sx * 18, 0))
    k.emit("Head_Sling", col, rig=rig, bone="sling", scale=ES)
    bm_boulder(k["stone:0.05:0.8"], rnd, (POUCH0.x, POUCH0.y, POUCH0.z - 0.165), 0.2, squash=(1, 1, 0.95), n=13, sink=0.0)
    k.emit("Head_Boulder", col, rig=rig, bone="boulder", vary=0.05, scale=ES)
    # ---- the windlass: a drum between the cheeks, a spoked wheel either side, the rope up to the arm
    bm_cyl(k["wood_red:0.2:0.7"], DRUM_R, DRUM_R, 2 * TX - 0.1, tuple(WINCH), rot=(0, 90, 0), seg=8)
    bm_cyl(k["sand:0.3:0.7"], DRUM_R + 0.022, DRUM_R + 0.022, 0.26, tuple(WINCH), rot=(0, 90, 0), seg=8)
    bm_cyl(k["iron:0.1:0.5"], 0.03, 0.03, 2 * TX + 0.36, tuple(WINCH), rot=(0, 90, 0), seg=6)
    k.emit("Head_Winch", col, rig=rig, bone="winch", scale=ES)
    for sx in (-1, 1):
        wc = Vector((sx * (TX + 0.14), WINCH.y, WINCH.z))
        ring(k["wood_red:0.2:0.7"], tuple(wc), 0.34, 0.275, -0.03, 0.03, seg=10, axis="X")
        bm_cyl(k["wood_red:0.2:0.7"], 0.07, 0.07, 0.09, tuple(wc), rot=(0, 90, 0), seg=8)
        for i in range(6):
            a = math.radians(60 * i + 15)
            dv = Vector((0, math.cos(a), math.sin(a)))
            bm_beam(k["wood:0.2:0.7"], wc + dv * 0.04, wc + dv * 0.42, 0.04, 0.04, w1=0.03, h1=0.03)
    k.emit("Head_WinchWheels", col, rig=rig, bone="winch", scale=ES)
    bm_beam(k["sand:0.3:0.7"], ROPE0, RP0, 0.03, 0.03)
    k.emit("Head_Rope", col, rig=rig, bone="rope", scale=ES)
    # ---- markers
    empty("Muzzle", col, head, tuple(MUZZLE * ES), 0.25, "SPHERE")
    spot = Vector((1.02, -0.58, 0.0))
    crew = empty("Crew", col, head, tuple(spot), 0.3, "SINGLE_ARROW")
    to = Vector((TX + 0.14, WINCH.y, 0)) * ES - spot
    crew.rotation_euler = (0, 0, math.atan2(-to.x, to.y))        # its +Y (the character's front) faces the windlass wheel
    mannequin(col, crew, 1.15, "engineer")
    return rig


IDLE_LEN = 80
FIRE_LEN = 24
RELOAD_LEN = 54


def keys(f, pts):
    """Piecewise-linear value at frame f through (frame, value) points."""
    if f <= pts[0][0]:
        return pts[0][1]
    for (f0, v0), (f1, v1) in zip(pts, pts[1:]):
        if f <= f1:
            return v0 + (v1 - v0) * (f - f0) / float(f1 - f0)
    return pts[-1][1]


def pose(rig, th=0.0, psi=0.0, sig=0.0, rock=0.0, ball=1.0, drop=0.0, wave=0.0, amp=1.0, crank=0.0):
    """th: the arm's turn from drawn (0) toward straight up (TH_UP); psi: the sling's own turn from lying in the trough;
    sig: the counterweight's swing off plumb; rock: the frame's pitch; ball: the boulder's size (0 = gone);
    drop: how far above the pouch a new boulder is; crank: extra turn of the windlass."""
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    pb["frame"].rotation_quaternion = q(pb["frame"], (1, 0, 0), rock)
    pb["arm"].rotation_quaternion = q(pb["arm"], (1, 0, 0), th)
    pb["cw"].rotation_quaternion = q(pb["cw"], (1, 0, 0), -th + sig)
    pb["sling"].rotation_quaternion = q(pb["sling"], (1, 0, 0), psi - th)
    pb["boulder"].scale = (max(ball, 0.001),) * 3
    pb["boulder"].location = arm_space_loc(pb["boulder"], (0, 0, drop))
    rp = AXLE + rotx(U0, th) * RPL
    d, d0 = rp - ROPE0, RP0 - ROPE0
    pb["rope"].rotation_quaternion = q(pb["rope"], (1, 0, 0), math.degrees(math.atan2(d.z, d.y) - math.atan2(d0.z, d0.y)))
    pb["rope"].scale = (1.0, d.length / d0.length, 1.0)
    pb["winch"].rotation_quaternion = q(pb["winch"], (1, 0, 0), -(d.length - d0.length) * 240.0 + crank)
    wave_flag(rig, "pen", wave, amp=amp, segs=3)


def drag_psi(th):
    """The sling's turn while its pouch trails on the trough behind the arm's tip (or hangs, once the tip is high)."""
    s = (arm_tip(th).z - POUCH0.z) / SL
    return -math.degrees(math.asin(min(max(s, -1.0), 1.0))) - D0


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        ph = 2 * math.pi * f / IDLE_LEN
        th = -0.5 - 0.5 * math.sin(ph * 2)                       # the arm strains against its rope
        pose(rig, th=th, psi=drag_psi(th), sig=2.2 * math.sin(ph), rock=0.12 * math.sin(ph * 2), wave=f / IDLE_LEN)
        key_pose(rig, f)
    th0 = -0.5
    # ---- fire: the hook slips, the counterweight drops, the arm whips over and the sling lets go at the top (frame 6)
    TH = [(0, th0), (1, 1.0), (2, -22), (3, -58), (4, -96), (5, -124), (6, TH_REL), (7, TH_REL - 12), (9, TH_UP - 14), (11, TH_UP + 8), (13, TH_UP + 13),
          (16, TH_UP + 2), (19, TH_UP - 5), (22, TH_UP - 1), (24, TH_UP)]
    PSI = [(0, drag_psi(th0)), (1, drag_psi(1.0)), (2, -50), (3, -112), (4, -178), (5, -238), (6, PSI_REL), (8, -360), (10, -418), (12, -452), (14, -448),
           (17, PSI_HANG - 360 + 12), (20, PSI_HANG - 360 - 6), (24, PSI_HANG - 360)]
    SIG = [(0, 0), (2, -10), (4, -24), (6, -8), (8, 22), (10, 30), (13, 6), (16, -15), (19, -5), (22, 4), (24, 0)]
    ROCK = [(0, 0), (1, 0.8), (4, -2.6), (7, 2.0), (10, -1.3), (13, 0.8), (16, -0.4), (20, 0.15), (24, 0)]
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        pose(rig, th=keys(f, TH), psi=keys(f, PSI), sig=keys(f, SIG), rock=keys(f, ROCK), ball=1.0 if f < 6 else 0.0,
             wave=f / FIRE_LEN, amp=1.0 + 1.4 * smooth(f / 4.0) * (1 - smooth((f - 6) / 14.0)))
        key_pose(rig, f)
    # ---- reload: the windlass hauls the arm down, the sling trails into the trough, a new boulder drops in
    new_action(rig, "reload", RELOAD_LEN)
    for f in range(RELOAD_LEN + 1):
        p = smooth((f - 3) / 37.0)
        th = TH_UP + (th0 - TH_UP) * p
        hang = smooth((arm_tip(th).z - POUCH0.z - SL) / 0.5)
        psi = drag_psi(th) + hang * 9 * math.sin(f * 0.5) * (1 - 0.6 * p)
        ball = smooth((f - 41) / 3.0)
        drop = 0.55 * (1 - smooth((f - 41) / 7.0)) ** 2
        heave = math.sin(2 * math.pi * f / 9.0) * (1 - smooth((f - 38) / 6.0)) * smooth(f / 4.0)
        pose(rig, th=th, psi=psi, sig=3.0 * math.sin(f * 0.45) * (1 - p), rock=0.35 * heave - 0.5 * smooth((f - 46) / 2.0) * (1 - smooth((f - 48) / 5.0)),
             ball=ball, drop=drop, wave=f / RELOAD_LEN, crank=14 * heave)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.0, 1.3), "dist": 13.5, "yaw": 150, "pitch": 20, "anim_target": (PIV.x, PIV.y + 0.2, 2.6), "anim_dist": 11.5,
           "frames": [("idle", 0), ("fire", 3), ("fire", 6), ("fire", 10), ("reload", 24)],
           "extra": [{"yaw": 125, "pitch": 16, "dist": 6.2, "target": (PIV.x, PIV.y, 1.4)},
                     {"yaw": 0, "pitch": 57, "dist": 7.5, "target": (PIV.x, PIV.y - 0.3, 0.9)},
                     {"yaw": 215, "pitch": 22, "dist": 6.0, "target": (-1.6, 0.8, 0.6)},
                     {"yaw": 40, "pitch": 24, "dist": 6.0, "target": (0.7, -1.6, 0.6)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
    tri_report("Trebuchet")
