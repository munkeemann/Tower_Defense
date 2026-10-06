"""Builds one tower with a background Blender (no window, no add-ons), so it never touches an open Blender:

    blender -b --factory-startup --python tools/blender/build_tower.py -- <tower id> [preview dir]
    (or: python tools/blender/build.py <tower id> ... which runs this at low priority and checks the result)

Runs kk_helpers.py and <id>_build.py, makes the scene (start_tower), builds it (build_all), finishes it
(finalize_tower: bevels applied, contact shade baked into vertex colors), saves assets/towers/src/<id>.blend and
exports assets/towers/<id>.glb. If the script has build_strike() (a model the game plays on the enemy a melee tower
hits), that's built, saved as src/<id>_strike.blend and exported to <id>_strike.glb the same way.

With a preview dir it renders:
    <id>_sheet.png   one sheet to judge the tower by: the front three-quarter view, the game camera's view (from
                     behind and above, as the player sees it), a back three-quarter view, then a strip of animation
                     frames (and the strike's frames)
    <id>_34.png      the front three-quarter view alone, larger
The script's PREVIEW dict tunes them: target, dist, yaw, pitch (the 3/4 view), anim_target, anim_dist, frames
[(action, frame), ...], and extra [{"yaw", "pitch", "dist", "target"}, ...] for more views on the sheet (close-ups).
"""
import bpy, os, sys, math
HERE = os.path.dirname(os.path.abspath(__file__))
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
tid = argv[0]
out = argv[1] if len(argv) > 1 else ""
g = {"__name__": "kk", "__file__": os.path.join(HERE, "kk_helpers.py")}
exec(open(os.path.join(HERE, "kk_helpers.py"), encoding="utf-8").read(), g)
exec(open(os.path.join(HERE, tid + "_build.py"), encoding="utf-8").read(), g)
g["start_tower"](g["TID"], g["CELLS"])
g["build_all"]()
coll = g["TID"].capitalize()
tris = g["finalize_tower"](coll)      # bevels applied, contact shade baked into vertex colors
bpy.ops.wm.save_mainfile()
glb = g["export_tower"](coll, os.path.join(g["TOWERS_DIR"], g["TID"] + ".glb"))
bpy.ops.wm.save_mainfile()

rp = g["render_preview"]
look = g.get("PREVIEW", {})
tgt = look.get("target", (0, 0, 0.9))
tmp = os.path.join(out, "_%s_tile.png" % tid) if out else ""


def tile(size, **kw):
    """Renders one view and returns its pixels (rows bottom-up, as Blender keeps them)."""
    import numpy as np
    rp(tmp, size=(size, size), **kw)
    im = bpy.data.images.load(tmp, check_existing=False)
    px = np.array(im.pixels[:]).reshape(size, size, 4).copy()
    bpy.data.images.remove(im)
    return px


def save_sheet(rows, path):
    import numpy as np
    width = max(sum(t.shape[1] for t in r) for r in rows)
    bands = []
    for r in rows:
        band = np.concatenate(r, axis=1)
        if band.shape[1] < width:
            pad = np.zeros((band.shape[0], width - band.shape[1], 4))
            pad[:, :, 3] = 1.0
            band = np.concatenate([band, pad], axis=1)
        bands.append(band)
    sheet = np.concatenate(list(reversed(bands)), axis=0)      # (the first row ends up on top)
    img = bpy.data.images.new("sheet", sheet.shape[1], sheet.shape[0])
    img.pixels = sheet.ravel()
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


rows = []
if out:
    os.makedirs(out, exist_ok=True)
    rig0 = bpy.data.objects.get("Rig")
    if rig0 and rig0.animation_data and "idle" in bpy.data.actions:     # (the export leaves the rig in its rest pose)
        rig0.animation_data.action = bpy.data.actions["idle"]
    bpy.context.scene.frame_set(0)
    main = dict(yaw=look.get("yaw", 150), pitch=look.get("pitch", 26), dist=look.get("dist", 10), target=tgt)
    rp(os.path.join(out, tid + "_34.png"), size=(800, 800), **main)
    views = [main, dict(yaw=0, pitch=57, dist=look.get("dist", 10) * 1.1, target=tgt),
             dict(yaw=35, pitch=28, dist=look.get("dist", 10), target=tgt)]
    rows.append([tile(640, **v) for v in views])
    extra = [tile(480, **v) for v in look.get("extra", [])]
    rig = bpy.data.objects.get("Rig")
    strip = []
    if rig and rig.animation_data:
        for act, f in look.get("frames", [("idle", 0), ("fire", 3), ("fire", 8)]):
            if act not in bpy.data.actions:
                continue
            rig.animation_data.action = bpy.data.actions[act]
            strip.append(tile(384, yaw=look.get("yaw", 150), pitch=look.get("pitch", 26) + 6, dist=look.get("anim_dist", 7),
                              target=look.get("anim_target", tgt), frame=f))
        rig.animation_data.action = bpy.data.actions.get("idle")
        bpy.context.scene.frame_set(0)
        bpy.ops.wm.save_mainfile()
    if strip:
        rows.append(strip[:5])
    if extra:
        rows.append(extra[:4])
print("BUILD saved", bpy.data.filepath, "exported", glb, os.path.getsize(glb), "tris", tris)

# ---- the strike: a small animated model of its own (roots bursting up, a tentacle, a spectral hammer)
if "build_strike" in g:
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    g["start_tower"](g["TID"] + "_strike", [(0, 0)])
    g["build_strike"]()
    sname = (g["TID"] + "_strike").capitalize()
    stris = g["finalize_tower"](sname)
    bpy.ops.wm.save_mainfile()
    sglb = g["export_tower"](sname, os.path.join(g["TOWERS_DIR"], g["TID"] + "_strike.glb"))
    bpy.ops.wm.save_mainfile()
    print("STRIKE saved", bpy.data.filepath, "exported", sglb, os.path.getsize(sglb), "tris", stris)
    if out:
        rig = bpy.data.objects.get("Rig")
        sl = g.get("STRIKE_PREVIEW", {})
        strip = []
        if rig and "strike" in bpy.data.actions:
            rig.animation_data.action = bpy.data.actions["strike"]
            for f in sl.get("frames", [2, 6, 10, 16, 24]):
                strip.append(tile(384, yaw=sl.get("yaw", 150), pitch=sl.get("pitch", 24), dist=sl.get("dist", 6),
                                  target=sl.get("target", (0, 0, 0.8)), frame=f))
        if strip:
            rows.append(strip[:5])
if out and rows:
    save_sheet(rows, os.path.join(out, tid + "_sheet.png"))
    if os.path.exists(tmp):
        os.remove(tmp)
    print("BUILD previews in", out)
