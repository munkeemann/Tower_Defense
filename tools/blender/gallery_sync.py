"""Adds every tower source that isn't in the gallery yet to assets/towers/src/gallery.blend (the file that links all
the towers side by side for a look in Blender), and saves it:

    blender -b assets/towers/src/gallery.blend --python tools/blender/gallery_sync.py

The gallery links each tower's collection from src/<id>.blend, so rebuilt towers show their new version as soon as
the gallery is opened again (or its libraries are reloaded). This only handles towers with no instance yet: they go
in a row of their own ("Row_Shared", above the Crown's row), each as a `Gallery_<Collection>` instance with a
`Label_<Collection>` under it, like the rest. Strike models (src/<id>_strike.blend) are left out.
"""
import bpy, os, glob

SRC = os.path.dirname(bpy.data.filepath)
ROW_Y = 13.0
STEP = 9.0
scn = bpy.context.scene

have = {o.name[len("Gallery_"):] for o in bpy.data.objects if o.name.startswith("Gallery_")}
ids = sorted(os.path.basename(p)[:-6] for p in glob.glob(os.path.join(SRC, "*.blend")))
new = [t for t in ids if t != "gallery" and not t.endswith("_strike") and t.capitalize() not in have]
ref_label = next((o for o in bpy.data.objects if o.name.startswith("Label_") and o.type == "FONT"), None)
ref_row = next((o for o in bpy.data.objects if o.name.startswith("Row_") and o.type == "FONT"), None)
x = max([o.location.x for o in bpy.data.objects if o.name.startswith("Gallery_") and abs(o.location.y - ROW_Y) < 1.0 and o.instance_collection],
        default=-STEP) + STEP


def text_like(ref, name, body, loc):
    o = ref.copy()
    o.data = ref.data.copy()
    o.data.body = body
    o.name = name
    o.location = loc
    for c in ref.users_collection:
        c.objects.link(o)
    return o


if new and ref_row and bpy.data.objects.get("Row_Shared") is None:
    text_like(ref_row, "Row_Shared", "SHARED", (ref_row.location.x, ROW_Y, ref_row.location.z))
for tid in new:
    coll = tid.capitalize()
    with bpy.data.libraries.load(os.path.join(SRC, tid + ".blend"), link=True, relative=True) as (src, dst):
        dst.collections = [coll] if coll in src.collections else []
    if not dst.collections:
        print("GALLERY skip", tid, "(no collection", coll + ")")
        continue
    o = bpy.data.objects.new("Gallery_" + coll, None)
    o.instance_type = "COLLECTION"
    o.instance_collection = dst.collections[0]
    o.location = (x, ROW_Y, 0.0)
    scn.collection.objects.link(o)
    if ref_label:
        dy = -4.2
        text_like(ref_label, "Label_" + coll, tid.replace("_", " ").title(), (x, ROW_Y + dy, ref_label.location.z))
    print("GALLERY added", tid, "at", (x, ROW_Y))
    x += STEP
if new:
    bpy.ops.wm.save_mainfile()
print("GALLERY", len(have), "towers were in it;", len(new), "new:", new)
