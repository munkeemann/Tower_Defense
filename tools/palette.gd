extends SceneTree
## Dev tool: lists the swatches in a Kenney colormap, or recolors one swatch.
## List:    Godot --headless --path . --script res://tools/palette.gd -- list <png>
## Recolor: Godot --headless --path . --script res://tools/palette.gd -- recolor <png> <from_hex> <to_hex> [tolerance]


func _init() -> void:
	var args := OS.get_cmdline_user_args()
	var path := ProjectSettings.globalize_path(args[1])
	var img := Image.load_from_file(path)
	img.convert(Image.FORMAT_RGBA8)
	if args[0] == "list":
		var counts := {}
		for y in img.get_height():
			for x in img.get_width():
				var h := img.get_pixel(x, y).to_html(false)
				counts[h] = counts.get(h, 0) + 1
		var keys := counts.keys()
		keys.sort_custom(func(a, b): return counts[a] > counts[b])
		for k in keys.slice(0, 400):
			var c := Color(k)
			print("SWATCH %s count=%d h=%.2f s=%.2f v=%.2f" % [k, counts[k], c.h, c.s, c.v])
	elif args[0] == "crop":
		# crop <png> <x> <y> <w> <h>: keep a region (fractions 0..1 of the image), saved over the file
		var w := img.get_width()
		var h := img.get_height()
		var r := Rect2i(int(float(args[2]) * w), int(float(args[3]) * h), int(float(args[4]) * w), int(float(args[5]) * h))
		img.get_region(r).save_png(path)
		print("CROPPED ", r)
	elif args[0] == "seamless":
		# seamless <png> [size]: cross-fade the image with a half-offset copy of itself so it tiles
		var sz := int(args[2]) if args.size() > 2 else 512
		img.resize(sz, sz, Image.INTERPOLATE_LANCZOS)
		var out := Image.create(sz, sz, false, Image.FORMAT_RGBA8)
		var half := sz / 2
		for y in sz:
			var wy := 1.0 - absf(float(y) - half) / half   # 1 in the middle, 0 at the edges
			for x in sz:
				var wx := 1.0 - absf(float(x) - half) / half
				var w := clampf(minf(wx, wy) * 2.2, 0.0, 1.0)
				var a := img.get_pixel(x, y)
				var b := img.get_pixel((x + half) % sz, (y + half) % sz)
				out.set_pixel(x, y, b.lerp(a, w))
		out.generate_mipmaps()
		out.save_png(path)
		print("SEAMLESS ", path)
	elif args[0] == "sample":
		for i in range(2, args.size(), 2):
			var p := img.get_pixel(int(args[i]), int(args[i + 1]))
			print("SAMPLE %s,%s = %s" % [args[i], args[i + 1], p.to_html(false)])
	elif args[0] == "hueshift":
		# hueshift <png> <hue_min> <hue_max> <shift> [sat_mult]
		var h0 := float(args[2])
		var h1 := float(args[3])
		var shift := float(args[4])
		var smul := float(args[5]) if args.size() > 5 else 1.0
		var n := 0
		for y in img.get_height():
			for x in img.get_width():
				var p := img.get_pixel(x, y)
				if p.s > 0.3 and p.h >= h0 and p.h <= h1:
					img.set_pixel(x, y, Color.from_hsv(p.h + shift, clamp(p.s * smul, 0.0, 1.0), p.v, p.a))
					n += 1
		img.save_png(path)
		print("SHIFTED %d pixels" % n)
	elif args[0] == "recolor":
		var from := Color(args[2])
		var to := Color(args[3])
		var tol := float(args[4]) if args.size() > 4 else 0.02
		var n := 0
		for y in img.get_height():
			for x in img.get_width():
				var p := img.get_pixel(x, y)
				if abs(p.r - from.r) < tol and abs(p.g - from.g) < tol and abs(p.b - from.b) < tol:
					# keep the pixel's shading relative to the swatch
					img.set_pixel(x, y, Color(to.r + (p.r - from.r), to.g + (p.g - from.g), to.b + (p.b - from.b), p.a))
					n += 1
		img.save_png(path)
		print("RECOLORED %d pixels" % n)
	quit()
