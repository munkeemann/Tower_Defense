extends SceneTree
## Dev tool: turns the raw particle sprites from Meshy (white on black, assets/custom/fx_raw/) into small tintable
## textures for scripts/vfx.gd (assets/fx/<name>.png): cropped square around the sprite, brightness becomes
## alpha over pure white (so tinted particles never get dark fringes), an edge fade keeps the border clear.
## Godot --headless --path . --script res://tools/fx_textures.gd

const SRC := "res://assets/custom/fx_raw/"
const DST := "res://assets/fx/"
const SIZES := {"fx_rune": 512}   # everything else is 256 px
const BLACK := 0.05               # the backgrounds aren't perfectly black


func _init() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(DST))
	for f in DirAccess.get_files_at(SRC):
		if not f.ends_with(".png"):
			continue
		var img := Image.load_from_file(ProjectSettings.globalize_path(SRC + f))
		if img == null:
			continue
		img.convert(Image.FORMAT_RGBA8)
		var name := f.get_basename()
		# work at 512, then crop to the sprite and scale to the final size
		img.resize(512, 512, Image.INTERPOLATE_LANCZOS)
		var lo := Vector2i(512, 512)
		var hi := Vector2i(-1, -1)
		for y in 512:
			for x in 512:
				var c := img.get_pixel(x, y)
				if maxf(c.r, maxf(c.g, c.b)) > BLACK + 0.03:
					lo = Vector2i(mini(lo.x, x), mini(lo.y, y))
					hi = Vector2i(maxi(hi.x, x), maxi(hi.y, y))
		if hi.x < 0:
			continue
		var ctr := (lo + hi) / 2
		var half := int(maxi(hi.x - lo.x, hi.y - lo.y) * 0.56) + 2
		var r := Rect2i(ctr - Vector2i(half, half), Vector2i(half * 2, half * 2)).intersection(Rect2i(0, 0, 512, 512))
		var sq := img.get_region(r)
		var out_px: int = SIZES.get(name, 256)
		sq.resize(out_px, out_px, Image.INTERPOLATE_LANCZOS)
		var brightest := 0.01
		for y in out_px:
			for x in out_px:
				var c := sq.get_pixel(x, y)
				brightest = maxf(brightest, maxf(c.r, maxf(c.g, c.b)))
		var out := Image.create(out_px, out_px, false, Image.FORMAT_RGBA8)
		for y in out_px:
			for x in out_px:
				var c := sq.get_pixel(x, y)
				var lum := clampf((maxf(c.r, maxf(c.g, c.b)) - BLACK) / maxf(brightest - BLACK, 0.01), 0.0, 1.0)
				# fade out in the outer 8% so no sprite ever shows a square edge
				var e := minf(minf(x, out_px - 1 - x), minf(y, out_px - 1 - y)) / (out_px * 0.08)
				var a := pow(lum, 1.15) * clampf(e, 0.0, 1.0)
				out.set_pixel(x, y, Color(1, 1, 1, a))
		out.save_png(ProjectSettings.globalize_path(DST + name + ".png"))
		print("FX ", name, " ", out_px, "px")
	quit()
