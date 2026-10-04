"""Tiles PNGs into one sheet with a background Blender (for reviewing several tower previews at once):

    blender -b --factory-startup --python tools/blender/contact.py -- out.png cols tile_px a.png b.png ...
"""
import bpy, sys
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:]
out, cols, tile = argv[0], int(argv[1]), int(argv[2])
files = argv[3:]
rows = (len(files) + cols - 1) // cols
sheet = np.zeros((rows * tile, cols * tile, 4), dtype=np.float32)
sheet[..., 3] = 1.0
for i, f in enumerate(files):
    im = bpy.data.images.load(f, check_existing=False)
    im.scale(tile, tile)
    px = np.array(im.pixels[:], dtype=np.float32).reshape(tile, tile, 4)
    r, c = i // cols, i % cols
    y0 = (rows - 1 - r) * tile          # pixel rows run bottom-up
    sheet[y0:y0 + tile, c * tile:(c + 1) * tile] = px
    bpy.data.images.remove(im)
img = bpy.data.images.new("contact", cols * tile, rows * tile)
img.pixels = sheet.ravel()
img.filepath_raw = out
img.file_format = "PNG"
img.save()
print("CONTACT saved", out)
