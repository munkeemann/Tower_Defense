extends SceneTree
## Dev tool: paints the animated particle textures (flipbooks) procedurally, so every frame is clean and they cost
## nothing to make. Each sheet is 8 x 8 frames of 64 px, read left to right, top to bottom, once over a particle's life.
##   fb_smoke:     a billowing puff that grows, thins and breaks up
##   fb_fire:      a flame tongue that flickers up, peaks and dies down
##   fb_explosion: a fireball that bursts out, then rolls into smoke
##   fx_glow:      a soft round glow (single frame)
## RGB is brightness (white core, darker edges, which particles tint), alpha is coverage.
## Godot --headless --path . --script res://tools/fx_flipbooks.gd -- --scratch

const DST := "res://assets/fx/"
const N := 8          # frames per side
const PX := 64        # frame size


func _init() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(DST))
	_sheet("fb_smoke", _smoke)
	_sheet("fb_fire", _fire)
	_sheet("fb_explosion", _explosion)
	_glow()
	quit()


func _noise(seed_: int, freq: float, octaves := 4) -> FastNoiseLite:
	var n := FastNoiseLite.new()
	n.seed = seed_
	n.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	n.frequency = freq
	n.fractal_type = FastNoiseLite.FRACTAL_FBM
	n.fractal_octaves = octaves
	return n


func _sheet(name: String, painter: Callable) -> void:
	var img := Image.create(N * PX, N * PX, false, Image.FORMAT_RGBA8)
	for i in N * N:
		var f := float(i) / float(N * N - 1)   # 0 = first frame, 1 = last
		var ox := (i % N) * PX
		var oy := (i / N) * PX
		for y in PX:
			for x in PX:
				var c: Color = painter.call(x, y, f, i)
				# keep a clear border so frames never bleed into each other
				var e := minf(minf(x, PX - 1 - x), minf(y, PX - 1 - y)) / 4.0
				c.a *= clampf(e, 0.0, 1.0)
				img.set_pixel(ox + x, oy + y, c)
	img.save_png(ProjectSettings.globalize_path(DST + name + ".png"))
	print("FLIPBOOK ", name)


var _n_smoke := _noise(11, 0.035, 3)
var _n_smoke2 := _noise(12, 0.07, 2)


func _smoke(x: int, y: int, f: float, _i: int) -> Color:
	var u := (x - PX * 0.5 + 0.5) / (PX * 0.5)
	var v := (y - PX * 0.5 + 0.5) / (PX * 0.5)
	var d := sqrt(u * u + v * v)
	var n := _n_smoke.get_noise_3d(x * 1.0, y * 1.0, f * 60.0) * 0.5 + 0.5
	var n2 := _n_smoke2.get_noise_3d(x * 1.0, y * 1.0, f * 90.0 + 40.0) * 0.5 + 0.5
	var r := 0.5 + 0.38 * sqrt(f)                        # grows
	var edge := d + (n - 0.5) * 0.5 + (n2 - 0.5) * 0.1
	var body := 1.0 - smoothstep(r - 0.35, r, edge)
	var erode := f * 0.75                                # thins and breaks up
	var dens := clampf((body * (0.72 + 0.28 * n) - erode * 0.6) / maxf(1.0 - erode * 0.6, 0.01), 0.0, 1.0)
	dens *= smoothstep(0.0, 0.08, f + 0.02) * (1.0 - smoothstep(0.7, 1.0, f))
	# lit from the top left, a little darker in the folds
	var light := clampf(0.74 + 0.26 * (-(u * 0.5 + v * 0.85)) + (n - 0.5) * 0.2, 0.5, 1.0)
	return Color(light, light, light, dens)


var _n_fire := _noise(21, 0.07)


func _fire(x: int, y: int, f: float, _i: int) -> Color:
	var u := (x - PX * 0.5 + 0.5) / (PX * 0.5)          # -1..1 across
	var v := 1.0 - (y + 0.5) / PX                         # 0 at the bottom, 1 at the top
	var life := sin(clampf(f * 1.15, 0.0, 1.0) * PI)     # flares up then dies down
	var n := _n_fire.get_noise_3d(x * 1.0, y * 1.0 + f * 260.0, f * 30.0) * 0.5 + 0.5
	var sway := (n - 0.5) * 0.7 * v
	var height := 0.45 + 0.5 * life
	var h := v / maxf(height, 0.05)                       # 0..1 up the flame
	var width := 0.62 * pow(clampf(1.0 - h, 0.0, 1.0), 0.6) * (0.55 + 0.45 * life) * smoothstep(0.0, 0.18, h + 0.05)
	var dx := absf(u - sway) / maxf(width, 0.01)
	var heat := clampf(1.0 - dx, 0.0, 1.0) * (0.75 + 0.5 * n) * clampf(1.0 - h * 0.85, 0.0, 1.0)
	heat = clampf(heat * 1.4, 0.0, 1.0)
	var a := smoothstep(0.05, 0.35, heat) * (1.0 - smoothstep(0.85, 1.0, f))
	var b := clampf(0.35 + heat * 0.9, 0.0, 1.0)         # white-hot core, darker rim
	return Color(b, b, b, a)


var _n_boom := _noise(31, 0.038, 3)
var _n_boom2 := _noise(32, 0.08, 2)


func _explosion(x: int, y: int, f: float, _i: int) -> Color:
	var u := (x - PX * 0.5 + 0.5) / (PX * 0.5)
	var v := (y - PX * 0.5 + 0.5) / (PX * 0.5)
	var d := sqrt(u * u + v * v)
	var n := _n_boom.get_noise_3d(x * 1.0, y * 1.0, f * 45.0) * 0.5 + 0.5
	var n2 := _n_boom2.get_noise_3d(x * 1.0, y * 1.0, f * 70.0) * 0.5 + 0.5
	var r := 0.42 + 0.5 * pow(f, 0.35)                    # bursts out fast, then slows
	var edge := d + (n - 0.5) * 0.45
	var body := 1.0 - smoothstep(r - 0.28, r, edge)
	var dens := clampf(body * (0.85 + 0.15 * n) - maxf(0.0, f - 0.5) * 1.3 * (1.0 - n2 * 0.6), 0.0, 1.0)
	dens *= 1.0 - smoothstep(0.8, 1.0, f)
	# hot and bright early (the particle's color ramp turns it to fire), dim smoke later
	var hot := clampf(1.1 - f * 1.5 + (n - 0.5) * 0.5 - d * 0.35, 0.0, 1.0)
	var b := clampf(0.35 + 0.65 * hot + (n2 - 0.5) * 0.1, 0.25, 1.0)
	return Color(b, b, b, dens)


func _glow() -> void:
	var s := 128
	var img := Image.create(s, s, false, Image.FORMAT_RGBA8)
	for y in s:
		for x in s:
			var u := (x - s * 0.5 + 0.5) / (s * 0.5)
			var v := (y - s * 0.5 + 0.5) / (s * 0.5)
			var d2 := u * u + v * v
			var a := exp(-d2 * 5.0) * (1.0 - smoothstep(0.8, 1.0, sqrt(d2)))
			img.set_pixel(x, y, Color(1, 1, 1, a))
	img.save_png(ProjectSettings.globalize_path(DST + "fx_glow.png"))
	print("FLIPBOOK fx_glow")
