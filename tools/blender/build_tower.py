"""Builds one tower with a background Blender (no window, no add-ons), so it never touches an open Blender:

    blender -b --factory-startup --python tools/blender/build_tower.py -- <tower id> [preview dir]

Runs kk_helpers.py and <id>_build.py, makes the scene (start_tower), builds it (build_all), saves
assets/towers/src/<id>.blend, exports assets/towers/<id>.glb, and renders previews (three-quarter view, the game
camera's view, and a strip of animation frames) into the preview dir when one is given.
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
bpy.ops.wm.save_mainfile()
coll = g["TID"].capitalize()
glb = g["export_tower"](coll, os.path.join(g["TOWERS_DIR"], g["TID"] + ".glb"))
bpy.ops.wm.save_mainfile()
print("BUILD saved", bpy.data.filepath, "exported", glb, os.path.getsize(glb))
if out:
    os.makedirs(out, exist_ok=True)
    rp = g["render_preview"]
    look = g.get("PREVIEW", {})
    tgt = look.get("target", (0, 0, 0.9))
    rp(os.path.join(out, tid + "_34.png"), yaw=look.get("yaw", 150), pitch=look.get("pitch", 26), dist=look.get("dist", 10),
       target=tgt, size=(800, 800))
    rp(os.path.join(out, tid + "_game.png"), yaw=0, pitch=57, dist=look.get("dist", 10) * 1.1, target=tgt, size=(600, 600))
    rig = bpy.data.objects.get("Rig")
    if rig and rig.animation_data:
        import numpy as np
        shots = look.get("frames", [("idle", 0), ("fire", 3), ("fire", 8)])
        tiles = []
        for act, f in shots:
            if act not in bpy.data.actions:
                continue
            rig.animation_data.action = bpy.data.actions[act]
            p = os.path.join(out, "_tile.png")
            rp(p, yaw=look.get("yaw", 150), pitch=look.get("pitch", 26) + 6, dist=look.get("anim_dist", 7), target=look.get("anim_target", tgt),
               size=(420, 420), frame=f)
            im = bpy.data.images.load(p, check_existing=False)
            tiles.append(np.array(im.pixels[:]).reshape(420, 420, 4).copy())
            bpy.data.images.remove(im)
        if tiles:
            sheet = np.concatenate(tiles, axis=1)
            img = bpy.data.images.new("anim_sheet", sheet.shape[1], sheet.shape[0])
            img.pixels = sheet.ravel()
            img.filepath_raw = os.path.join(out, tid + "_anim.png")
            img.file_format = "PNG"
            img.save()
        rig.animation_data.action = bpy.data.actions.get("idle")
        bpy.context.scene.frame_set(0)
        bpy.ops.wm.save_mainfile()
    print("BUILD previews in", out)
