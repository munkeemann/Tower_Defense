"""Builds the Flame Belcher (footprint "pair": [0,0] front, [0,1] back; a 90 degree cone of fire ahead), a Forge tower.

    python tools/blender/build.py dwarf_flame --out <preview dir>

One machine over both hexes. Front: a furnace-cannon cast as a roaring dragon's head (brass horns, teeth and muzzle, a
glowing maw, a team-colored saddle plate and crest, a stubby smoking chimney on its neck, the firebox door glowing at
the back) on a brass-toothed turntable over a drum of stone blocks. Back: the great leather-and-timber bellows that
blows it (its top board painted in the team's color), plugged into the drum by a riveted pipe, a rack of fuel kegs
with a hose to the pipe's funnel, a coal bin, and the Engineer who works it (Crew).
The Head is the turntable's pivot; the Rig hangs under it. Bones under "turret" turn with the dragon; the bellows
hangs on "base" (the game doesn't turn an aura's Head: if it ever does, counter-turn "base").
idle: the dragon sweeps a little from side to side, its jaw works, the flames in its mouth flicker, the bellows
breathe, the chimney smokes. fire (0.4 s, one pulse): the bellows slam shut, the jaw gapes, fire leaps out of the maw,
the cannon kicks back, the chimney belches.
"""
import bpy, bmesh, math, random, os
from mathutils import Vector, Matrix, Quaternion, Euler

exec(open(os.path.join(REPO, "tools", "blender", "forgeworks_common.py"), encoding="utf-8").read())

TID = "dwarf_flame"
CELLS = [(0, 0), (0, 1)]
MID = footprint_mid(CELLS)
FRONT = hex_to_world(0, 0, MID)
BACK = hex_to_world(0, 1, MID)
TOP = 0.34
DRUM_R, DRUM_H = 0.9, 0.5
PIV = Vector((FRONT.x, FRONT.y, TOP + DRUM_H + 0.05))       # the Head: the turntable's pivot, on the track ring
Z = Vector((0, 0, 1))
Y = Vector((0, 1, 0))
# the bellows (world space)
B_HINGE = Vector((0.1, -0.5, TOP + 0.52))
B_BACK = Vector((0, -1, 0.06)).normalized()
B_LEN, B_WIDE, B_OPEN = 1.2, 0.9, 24.0
# the dragon is laid out in its own space (+Y forward, the pivot at the origin) and set on the turntable by DSM
DS = 1.13
DISC = 0.085                                                 # the turntable disc's top
DSM = Matrix.Translation((0, 0, DISC)) @ Matrix.Scale(DS, 4) @ Matrix.Translation((0, -0.12, -DISC))
ZB, RB = 0.6, 0.4                                            # the furnace body's axis height and radius
BY = -0.74                                                   # its back end
JAW_HINGE = Vector((0, 0.02, 0.47))
JAW_OPEN = 12.0                                              # how far the jaw hangs open at rest
CHIM = Vector((0, -0.52, ZB + RB - 0.06))
FLARE = Vector((0, 0.6, 0.4))
# the skull's sections: (y, the lip line's height, half width, height above the lip); the jaw's hang below theirs
SKULL = [(-0.06, 0.50, 0.42, 0.46), (0.16, 0.50, 0.50, 0.52), (0.40, 0.505, 0.46, 0.42), (0.62, 0.51, 0.39, 0.32),
         (0.86, 0.52, 0.33, 0.26), (1.08, 0.53, 0.30, 0.23)]
JAW = [(0.0, 0.47, 0.41, 0.24), (0.32, 0.47, 0.41, 0.2), (0.66, 0.47, 0.35, 0.15), (1.0, 0.47, 0.3, 0.11)]


def DP(v):
    return DSM @ Vector(v)


def _dsect(y, z0, hw, h, n=6, power=3.4, down=False):
    """A cross-section at y with a flat side at z0: over the top (under, for the jaw) from +x round to -x."""
    pts = []
    e = 2.0 / power
    for i in range(n + 1):
        a = math.pi * i / n
        ca, sa = math.cos(a), math.sin(a)
        pts.append(Vector((math.copysign(abs(ca) ** e, ca) * hw, y, z0 + (-1 if down else 1) * (abs(sa) ** e) * h)))
    return pts


def _at(rows, y):
    for a, b in zip(rows, rows[1:]):
        if a[0] <= y <= b[0]:
            t = (y - a[0]) / (b[0] - a[0])
            return tuple(a[i] + (b[i] - a[i]) * t for i in (1, 2, 3))
    return rows[-1][1:]


def build_base():
    fw_reset()
    col = collection("Dwarf_flame")
    root = empty("Dwarf_flame", col, None, (0, 0, 0), 0.6, "ARROWS")
    T = plinth(CELLS, col, root, TOP)
    rnd = random.Random(4)
    k = Kit()
    C = Vector((PIV.x, PIV.y, 0))
    # ---- one stone floor over both hexes
    fw_bed(k["stone_dark:0.35:0.85"], CELLS, T)
    fw_emit(k, "Bed", col, root, tag="no_refine")
    fw_paving(k[STONE], rnd, CELLS, T, skip=lambda x, y: (x - C.x) ** 2 + (y - C.y) ** 2 < (DRUM_R - 0.14) ** 2)
    fw_emit(k, "Floor", col, root, vary=0.09)
    # ---- the emplacement: a drum of big stone blocks, a lip course, the toothed brass track the turntable rides
    round_tower(k, rnd, (C.x, C.y, 0), DRUM_R, DRUM_R - 0.05, T, T + DRUM_H - 0.08, courses=2, n=9, depth=0.26, stone="stone:0.15:0.85")
    bm_block_course(k["stone:0.05:0.6"], rnd, (C.x, C.y, 0), DRUM_R + 0.03, T + DRUM_H - 0.08, 0.1, 12, depth=0.3, phase=0.25)
    fw_emit(k, "Drum", col, root, vary=0.08, bevel=0.012)
    fw_gear(k["gold:0.3:0.9"], (C.x, C.y, T + DRUM_H + 0.015), Z, 0.86, teeth=24, w=0.07, tooth=0.06, hub=0.0, rim=0.3)
    fw_emit(k, "Track", col, root)
    # ---- the bellows' trestle: two sleepers on legs, a stretcher between them
    def under(s):                                        # the bottom board's underside, s along the bellows
        p = B_HINGE + B_BACK * s
        return Vector((p.x, p.y, p.z - 0.05))
    for s, half in ((0.3, 0.26), (0.98, 0.36)):
        p = under(s)
        bm_beam(k[TIMBER], (p.x - half - 0.08, p.y, p.z - 0.05), (p.x + half + 0.08, p.y, p.z - 0.05), 0.12, 0.1)
        for sx in (-1, 1):
            bm_beam(k[TIMBER], (p.x + sx * (half - 0.02), p.y, T), (p.x + sx * (half - 0.06), p.y, p.z - 0.08), 0.11, 0.11, up=(0, 1, 0))
            bm_box(k["stone:0.2:0.8"], (0.2, 0.22, 0.07), (p.x + sx * (half - 0.02), p.y, T + 0.035))
    a, b = under(0.3), under(0.98)
    bm_beam(k[TIMBER], (a.x, a.y, T + 0.2), (b.x, b.y, T + 0.2), 0.09, 0.09)
    for p in (a, b):
        bm_beam(k[TIMBER], (p.x, p.y, T + 0.2), (p.x, p.y, p.z - 0.08), 0.09, 0.09, up=(0, 1, 0))
    fw_emit(k, "Trestle", col, root, bevel=0.01)
    # ---- the pipe from the bellows' nozzle into the drum: riveted iron, brass flanges, a funnel for the fuel
    n0 = B_HINGE - B_BACK * 0.3
    p1 = Vector((0.02, C.y - DRUM_R + 0.1, T + 0.4))
    pipe = [n0 + Vector((0, -0.04, 0)), n0 + Vector((0, 0.1, -0.02)), p1 + Vector((0, -0.08, 0)), p1 + Vector((0, 0.1, 0))]
    bm_tube(k[CAST], pipe, 0.115, n=8)
    for p, d in ((pipe[1], pipe[1] - pipe[0]), (pipe[2], pipe[3] - pipe[2])):
        fw_hoop(k[BRASS], p, d, 0.115, w=0.07, th=0.035, n=8)
        fw_studs_round(k[IRON], p, d, 0.15, 6, sr=0.022, h=0.05)
    fun = pipe[1].lerp(pipe[2], 0.5)
    fw_lathe(k[BRASS], fun + Vector((0, 0, 0.08)), Z, [(0.05, 0.0), (0.05, 0.08), (0.13, 0.2), (0.1, 0.2)], n=8, cap0=False, cap1=True)
    fw_emit(k, "Pipe", col, root)
    # ---- the keg rack: two fuel kegs on a timber stand, a third on end behind it, a hose from the tap to the funnel
    R = Vector((-0.66, -1.0, 0))
    for sx in (-1, 1):
        for sy in (-1, 1):
            bm_box(k[TIMBER], (0.08, 0.08, 0.98), (R.x + sx * 0.23, R.y + sy * 0.22, T + 0.49))
    for z in (0.08, 0.5):
        for sy in (-1, 1):
            bm_box(k[TIMBER], (0.56, 0.07, 0.07), (R.x, R.y + sy * 0.22, T + z))
    for sx in (-1, 1):
        bm_box(k[TIMBER], (0.07, 0.56, 0.07), (R.x + sx * 0.23, R.y, T + 0.95))
    fw_emit(k, "Rack", col, root, bevel=0.008)
    fw_keg(k, (R.x, R.y, T + 0.29), (0, 1, 0), 0.2, 0.52)
    fw_keg(k, (R.x, R.y, T + 0.71), (0, 1, 0), 0.2, 0.52, hoop=BRASS)
    fw_keg(k, (R.x + 0.06, R.y - 0.52, T + 0.24), (0, 0, 1), 0.19, 0.46)
    tap = Vector((R.x, R.y + 0.27, T + 0.64))
    fw_lathe(k[BRASS], tap, (0, 1, 0), [(0.035, 0.0), (0.035, 0.09), (0.05, 0.09), (0.05, 0.13)], n=6)
    hose = [tap + Vector((0, 0.11, 0)), tap + Vector((0.14, 0.26, -0.2)), fun + Vector((-0.2, -0.05, 0.3)), fun + Vector((-0.02, 0, 0.28))]
    bm_tube(k["wood_dark:0.45:0.9"], hose, 0.032, n=5)
    fw_emit(k, "Kegs", col, root)
    # ---- the coal bin by the Engineer's feet
    cb = Vector((0.46, -0.5, 0))
    for sx in (-1, 1):
        bm_box(k[TIMBER], (0.05, 0.32, 0.2), (cb.x + sx * 0.15, cb.y, T + 0.14))
    for sy in (-1, 1):
        bm_box(k[TIMBER], (0.34, 0.05, 0.2), (cb.x, cb.y + sy * 0.15, T + 0.14))
    fw_emit(k, "Bin", col, root, bevel=0.008, vary=0.06)
    for dx, dy, r in ((0.0, 0.0, 0.13), (0.07, 0.07, 0.09), (-0.08, 0.05, 0.09), (0.03, -0.09, 0.1), (-0.06, -0.07, 0.08)):
        bm_boulder(k["iron:0.0:0.6"], rnd, (cb.x + dx, cb.y + dy, T + 0.12), r, n=9)
    fw_emit(k, "Coal", col, root, vary=0.08)
    for o in kk_import("hex/shovel", col, root, (cb.x + 0.22, cb.y + 0.1, T + 0.03), 30, 1.8, name="Prop_KK_shovel"):
        o.rotation_euler = (math.radians(-18), 0, math.radians(30))
    crew = empty("Crew", col, root, (0.9, -1.04, T + 0.045), 0.3, "SINGLE_ARROW")
    crew.rotation_euler = (0, 0, math.radians(90))      # faces the bellows (-X)
    empty("Head", col, root, tuple(PIV), 0.5, "SINGLE_ARROW")
    return root


PUFF_AT = DP(CHIM + Vector((0, 0, 0.44)))
BONES = {
    "root": ((0, 0, 0), (0, 0, 0.2), None),
    "base": ((0, 0, 0), (0, 0.2, 0), "root"),
    "turret": ((0, 0, 0.05), (0, 0.3, 0.05), "root"),
    "jaw": (tuple(DP(JAW_HINGE)), tuple(DP(JAW_HINGE + Vector((0, 0.5, -0.04)))), "turret"),
    "flare": (tuple(DP(FLARE)), tuple(DP(FLARE + Vector((0, 0.3, 0)))), "turret"),
    "bellows": (tuple(B_HINGE - PIV), tuple(B_HINGE - PIV + B_BACK * 0.4), "base"),
}
fw_puff_bones(BONES, "puff", PUFF_AT, 3, "turret")
BEL = {}


def build_head():
    col = collection("Dwarf_flame")
    root = bpy.data.objects["Dwarf_flame"]
    head = bpy.data.objects["Head"]
    rig = make_rig(col, head, BONES)
    k = Kit()

    def put(name, bone="turret", kit=None, **kw):
        """Sets a Kit laid out in the dragon's space on the turntable and emits it on a bone."""
        kit = kit or k
        fw_place(kit, m=DSM)
        return fw_emit(kit, name, col, rig=rig, bone=bone, **kw)
    # ---- the turntable's disc
    fw_lathe(k[CAST], (0, 0, 0), Z, [(0.76, 0.0), (0.76, 0.06), (0.68, DISC)], n=16, cap0=False, cap1=True)
    fw_studs_round(k[BRASS], (0, 0, 0.062), Z, 0.71, 8, sr=0.035, h=0.03)
    fw_emit(k, "Head_Disc", col, rig=rig, bone="turret")
    # ---- the carriage: two iron cheeks cradling the furnace, brass trunnion caps, a cross tie
    for sx in (-1, 1):
        fw_prism(k[CAST], [Vector((sx * 0.3, y, z)) for y, z in ((-0.5, DISC - 0.01), (0.4, DISC - 0.01), (0.24, 0.5), (-0.4, 0.5))], (sx * 0.09, 0, 0))
        fw_lathe(k[BRASS], (sx * 0.38, -0.08, 0.44), (sx, 0, 0), [(0.13, 0.0), (0.13, 0.04), (0.07, 0.07)], n=8)
        fw_studs(k[BRASS], (sx * 0.395, -0.4, 0.17), (sx * 0.395, 0.3, 0.17), 4, (sx, 0, 0), r=0.03, h=0.022)
    bm_box(k[CAST], (0.6, 0.12, 0.2), (0, -0.42, 0.18))
    put("Head_Carriage", bevel=0.01)
    # ---- the furnace: a fat iron body along the gun's axis, brass hoops, the firebox door glowing at the back
    fw_lathe(k[CAST], (0, BY, ZB), Y, [(0.31, 0.0), (RB, 0.08), (RB, 0.76)], n=10, phase=0.5, cap0=True, cap1=False)
    for d in (0.15, 0.66):
        fw_hoop(k[BRASS], (0, BY + d, ZB), Y, RB, w=0.08, th=0.025, n=10, phase=0.5)
        fw_studs_round(k[IRON], (0, BY + d, ZB), Y, RB + 0.025, 7, sr=0.026, h=0.02, arc=(165.0, 375.0), phase=0.5)
    fw_ring(k[BRASS], (0, BY + 0.005, ZB), -Y, 0.19, 0.28, 0.05, n=10, phase=0.5)
    for x in (-0.09, 0.0, 0.09):
        bm_box(k[IRON], (0.035, 0.035, 0.4 - abs(x) * 0.6), (x, BY - 0.035, ZB))
    bm_box(k[IRON], (0.1, 0.05, 0.08), (0.27, BY - 0.02, ZB))
    # the chimney on its neck
    fw_lathe(k[CAST], CHIM, Z, [(0.17, 0.0), (0.14, 0.26), (0.21, 0.33), (0.21, 0.42), (0.14, 0.42), (0.14, 0.3)], n=8, cap0=False, cap1=False)
    fw_hoop(k[BRASS], CHIM + Vector((0, 0, 0.13)), Z, 0.155, w=0.06, th=0.02, n=8)
    put("Head_Furnace")
    bm_cyl(k[FIRE], 0.2, 0.2, 0.02, (0, BY - 0.012, ZB), rot=(90, 0, 0), seg=10)
    bm_cyl(k[HOT], 0.13, 0.13, 0.02, CHIM + Vector((0, 0, 0.34)), seg=8)
    put("Head_FurnaceGlow")
    # the team's saddle plate over the body, brass-edged, and a crest of fins down the spine

    def arc(y, a0, a1, grow, n=6):
        o, i_ = [], []
        for q in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * q / n)
            o.append(Vector((math.cos(a) * (RB + grow), y, ZB + math.sin(a) * (RB + grow))))
            i_.append(Vector((math.cos(a) * (RB - 0.02), y, ZB + math.sin(a) * (RB - 0.02))))
        return o + list(reversed(i_))
    bm_loft(k["team!:0.1:0.7"], [arc(BY + 0.24, 22, 158, 0.035), arc(BY + 0.58, 22, 158, 0.035)])
    for y in (BY + 0.24, BY + 0.58):
        bm_loft(k[BRASS], [arc(y - 0.02, 20, 160, 0.05), arc(y + 0.02, 20, 160, 0.05)])
    for y, zs, h in ((BY + 0.43, ZB + RB + 0.02, 0.26), (0.03, 0.99, 0.3), (0.27, 1.0, 0.25)):
        fw_prism(k["team!:0.05:0.6"], [Vector((-0.035, y - 0.13, zs - 0.05)), Vector((-0.035, y + 0.12, zs - 0.05)), Vector((-0.035, y - 0.1, zs + h))], (0.07, 0, 0))
    put("Head_Saddle")
    # ---- the dragon's skull: one loft from the furnace to the snout, flat along the lip; its palate glows red
    bm_loft(k["stone_dark:0.0:0.55"], [_dsect(*s) for s in SKULL])
    skull = put("Head_Skull")[0]
    paint_faces(skull, "ember", lambda c, n: n.z < -0.6, lo=0.25, hi=0.9)
    # brow ridges running from the bridge of the nose out over the eyes and back to the horns; cheek spikes
    for sx in (-1, 1):
        bm_beam(k[IRON], (sx * 0.08, 0.8, 0.8), (sx * 0.37, 0.5, 0.845), 0.13, 0.1, w1=0.2, h1=0.14)
        bm_beam(k[IRON], (sx * 0.37, 0.52, 0.845), (sx * 0.41, 0.1, 0.955), 0.2, 0.14, w1=0.22, h1=0.16)
        bm_crystal(k[IRON], (sx * 0.4, 0.02, 0.7), (sx * 0.76, -0.24, 0.82), 0.1, n=4, shoulder=0.25)
        bm_crystal(k[IRON], (sx * 0.4, 0.06, 0.52), (sx * 0.68, -0.14, 0.46), 0.08, n=4, shoulder=0.25)
    bm_box(k[IRON], (0.1, 0.3, 0.06), (0, 0.72, 0.8), (-9, 0, 0))
    put("Head_Brow", bevel=0.012)
    # a brass nose horn and flared nostrils, studs along the lip, brass horns sweeping back over the furnace
    bm_crystal(k[BRASS], (0, 0.93, 0.74), (0, 1.06, 1.02), 0.1, n=4, shoulder=0.22)
    for sx in (-1, 1):
        fw_lathe(k[BRASS], (sx * 0.17, 1.0, 0.7), (sx * 0.5, 0.5, 0.75), [(0.07, 0.0), (0.07, 0.07), (0.04, 0.07)], n=6)
        for y in (0.42, 0.58, 0.74, 0.9, 1.04):
            z0, hw, _ = _at(SKULL, y)
            fw_stud(k[BRASS], (sx * hw, y, z0 + 0.07), (sx, 0, 0.2), r=0.03, h=0.02)
        bm_tube(k[BRASS], [(sx * 0.36, 0.14, 0.93), (sx * 0.58, -0.06, 1.08), (sx * 0.72, -0.32, 1.22), (sx * 0.72, -0.6, 1.4)],
                [0.13, 0.11, 0.07, 0.0], n=6)
        fw_hoop(k[IRON], (sx * 0.46, 0.05, 1.0), (sx * 0.22, -0.2, 0.15), 0.115, w=0.05, th=0.02, n=6)
        # teeth: a fang at the front, a row down the lip
        bm_crystal(k["gold:0.0:0.4"], (sx * 0.19, 1.04, 0.54), (sx * 0.19, 1.07, 0.27), 0.065, n=4, shoulder=0.2)
        for y in (0.5, 0.66, 0.82):
            z0, hw, _ = _at(SKULL, y)
            bm_crystal(k["gold:0.0:0.4"], (sx * (hw - 0.05), y, z0 + 0.02), (sx * (hw - 0.04), y + 0.01, z0 - 0.15), 0.05, n=4, shoulder=0.2)
    put("Head_Horns")
    # eyes under the brows, the glowing roof of the mouth
    for sx in (-1, 1):
        bm_box(k[HOT], (0.08, 0.17, 0.085), (sx * 0.365, 0.6, 0.725), (0, sx * -18, sx * -12))
    bm_box(k[FIRE], (0.5, 0.7, 0.02), (0, 0.5, 0.492))
    for sx in (-1, 1):                                   # gills: three glowing slots down each flank of the furnace
        for d in (0.3, 0.4, 0.5):
            bm_box(k[FIRE], (0.04, 0.05, 0.2), (sx * (RB - 0.005), BY + d, ZB - 0.02))
    put("Head_Eyes")
    # ---- the lower jaw (hanging open at rest): a loft with a brass chin, tusks and teeth, a bed of fire on its tongue
    kj = Kit()
    bm_loft(kj["stone_dark:0.0:0.55"], [_dsect(*s, down=True) for s in JAW])
    bm_box(kj[BRASS], (0.22, 0.06, 0.1), (0, 1.0, 0.41))
    for sx in (-1, 1):
        bm_crystal(kj["gold:0.0:0.4"], (sx * 0.31, 0.86, 0.45), (sx * 0.44, 0.92, 0.8), 0.07, n=4, shoulder=0.2)
        for y, x in ((0.46, 0.36), (0.64, 0.33)):
            bm_crystal(kj["gold:0.0:0.4"], (sx * x, y, 0.46), (sx * x, y, 0.6), 0.045, n=4, shoulder=0.2)
    bm_box(kj[FIRE], (0.46, 0.66, 0.02), (0, 0.46, 0.478))
    fw_place(kj, m=Matrix.Translation(JAW_HINGE) @ Matrix.Rotation(math.radians(-JAW_OPEN), 4, "X") @ Matrix.Translation(-JAW_HINGE))
    jaw = [o for o in put("Head_Jaw", bone="jaw", kit=kj) if o.name.endswith("stone_dark")][0]
    paint_faces(jaw, "ember", lambda c, n: n.z > 0.6, lo=0.3, hi=0.9)
    # ---- the fire in its throat: a knot of flame tongues (small at rest; fire throws them out past the snout)
    for i, (dx, dz, ln, r) in enumerate(((0.0, 0.0, 0.3, 0.08), (0.1, -0.01, 0.24, 0.06), (-0.1, -0.01, 0.25, 0.06), (0.05, 0.03, 0.2, 0.05),
                                         (-0.05, 0.03, 0.21, 0.05), (0.17, 0.0, 0.17, 0.045), (-0.17, 0.0, 0.18, 0.045))):
        bm_crystal(k[HOT if i in (0, 3, 4) else FIRE], FLARE + Vector((dx, -0.06, dz)), FLARE + Vector((dx * 1.4, ln, dz * 1.6 + 0.02)), r, n=4, shoulder=0.3, foot=0.6)
    fw_fx(put("Head_Flare", bone="flare"))
    # ---- the bellows: the bottom board is fixed on its trestle, the top board and the leather fold
    b = fw_bellows(B_HINGE - PIV, B_BACK, B_LEN, B_WIDE, B_OPEN, leather="wood_red:0.2:0.95")
    BEL.update(b)
    fw_place(b["bottom"], loc=tuple(PIV))
    fw_emit(b["bottom"], "Bellows_Bottom", col, root, bevel=0.008)
    fw_emit(b["top"], "Bellows_Top", col, rig=rig, bone="bellows")
    for o in fw_emit(b["leather"], "Bellows_Leather", col, rig=rig, bone="base"):
        fw_skin(o, rig, lambda co: {"bellows": b["frac"](co), "base": 1.0 - b["frac"](co)})
    fw_puffs("Head_Puff", col, rig, "puff", PUFF_AT, 3, r=0.17)
    empty("Muzzle", col, head, tuple(DP((0, 0.92, 0.42))), 0.2, "SPHERE")
    return rig


IDLE_LEN = 72
FIRE_LEN = 12


def pose(rig, puff=0.0, yaw=0.0, jaw=0.0, flare=1.0, reach=0.0, squeeze=0.0, recoil=0.0, pitch=0.0, burst=0.0):
    pb = rig.pose.bones
    rest_pose(rig)
    q = arm_space_quat
    pb["turret"].rotation_quaternion = q(pb["turret"], (0, 0, 1), yaw) @ q(pb["turret"], (1, 0, 0), pitch)
    pb["turret"].location = arm_space_loc(pb["turret"], (0, -recoil, 0))
    pb["jaw"].rotation_quaternion = q(pb["jaw"], (1, 0, 0), -jaw)
    pb["flare"].scale = (1.0 + (flare - 1.0) * 0.45, flare, 1.0 + (flare - 1.0) * 0.3)
    pb["flare"].location = arm_space_loc(pb["flare"], (0, reach, 0))
    fw_bellows_pose(rig, "bellows", BEL["axis"], squeeze)
    fw_puff_pose(rig, "puff", 3, puff, rise=0.8, drift=(0.0, -0.3), size=(0.5, 1.6), burst=burst)


def build_anims():
    rig = bpy.data.objects["Rig"]
    new_action(rig, "idle", IDLE_LEN)
    for f in range(0, IDLE_LEN + 1, 2):
        t = f / IDLE_LEN
        ph = 2 * math.pi * t
        pose(rig, puff=2 * t, yaw=7 * math.sin(ph), jaw=4 * math.sin(2 * ph), flare=1.0 + 0.3 * math.sin(5 * ph) * math.sin(2 * ph),
             squeeze=5 * (0.5 - 0.5 * math.cos(2 * ph)))
        key_pose(rig, f)
    new_action(rig, "fire", FIRE_LEN)
    for f in range(FIRE_LEN + 1):
        # the bellows slam (frame 2), the jaw gapes and the fire leaps (3-4), then it all eases back
        sq = smooth(f / 2.0) * (1 - smooth((f - 3) / 8.0))
        a = smooth((f - 0.5) / 2.5) * (1 - smooth((f - 4) / 7.0))
        pose(rig, puff=f / FIRE_LEN, jaw=28 * a, flare=1.0 + 2.6 * a, reach=0.22 * a, squeeze=17 * sq, recoil=0.08 * a, pitch=3.5 * a,
             burst=0.7 * a)
        key_pose(rig, f)
    rig.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)


PREVIEW = {"target": (0, 0.1, 1.15), "dist": 7.6, "yaw": 150, "pitch": 22, "anim_target": (0, 0.7, 1.3), "anim_dist": 5.6,
           "frames": [("idle", 0), ("fire", 2), ("fire", 4), ("fire", 8), ("idle", 18)],
           "extra": [{"yaw": 160, "pitch": 8, "dist": 3.8, "target": (0, 1.2, 1.5)},
                     {"yaw": 20, "pitch": 34, "dist": 4.6, "target": (0, -0.8, 0.8)},
                     {"yaw": 90, "pitch": 14, "dist": 6.5, "target": (0, 0.0, 1.0)}]}


def build_all():
    build_base()
    build_head()
    build_anims()
