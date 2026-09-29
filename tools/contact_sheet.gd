extends SceneTree
## Dev tool: tiles images into one sheet (in the given order) for quick review.
## Godot --headless --path . --script res://tools/contact_sheet.gd -- <out.png> <cols> <thumb_px> <img1> <img2> ...


func _init() -> void:
	var a := OS.get_cmdline_user_args()
	var out := a[0]
	var cols := int(a[1])
	var px := int(a[2])
	var files := a.slice(3)
	var rows := int(ceil(files.size() / float(cols)))
	var sheet := Image.create(cols * px, rows * px, false, Image.FORMAT_RGBA8)
	sheet.fill(Color(0.2, 0.2, 0.22))
	for i in files.size():
		var img := Image.load_from_file(files[i])
		if img == null:
			continue
		img.convert(Image.FORMAT_RGBA8)
		img.resize(px - 8, px - 8, Image.INTERPOLATE_BILINEAR)
		var bg := Image.create(px - 8, px - 8, false, Image.FORMAT_RGBA8)
		bg.fill(Color(1, 1, 1))
		bg.blend_rect(img, Rect2i(Vector2i.ZERO, img.get_size()), Vector2i.ZERO)
		sheet.blit_rect(bg, Rect2i(Vector2i.ZERO, bg.get_size()), Vector2i((i % cols) * px + 4, (i / cols) * px + 4))
	sheet.save_png(out)
	print("SHEET ", out, " ", files.size(), " images")
	quit()
