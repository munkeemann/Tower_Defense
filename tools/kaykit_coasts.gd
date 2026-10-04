extends SceneTree
## Dev tool: works out which sides of our hex grid are grass on each KayKit coast tile, in each of its 6 turns, and
## prints the lookup Board uses (mask of Hex.E side indices that are land -> [tile, turns]). Each side is tested just
## inside its midpoint: the tile's top surface there is found from the mesh's triangles and its texture color read
## at that spot; it's land when that's grass at the tile's top height (water and beach sit lower or aren't green).
## Godot --headless --path . --script res://tools/kaykit_coasts.gd -- --scratch

const TILES := ["hex_coast_A", "hex_coast_B", "hex_coast_C", "hex_coast_D"]


func _init() -> void:
	Hex.setup()
	var table := {}
	var apothem := Hex.SQ3 * 0.5 * Hex.R
	for t in TILES:
		var mi: Array = KayKit.hex_mesh(t)
		var mesh: Mesh = mi[0]
		var xf: Transform3D = mi[1]
		var mat := mesh.surface_get_material(0) as BaseMaterial3D
		var img := mat.albedo_texture.get_image()
		if img.is_compressed():
			img.decompress()
		var arr := mesh.surface_get_arrays(0)
		var vs: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var uvs: PackedVector2Array = arr[Mesh.ARRAY_TEX_UV]
		var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
		for k in 6:
			var basis := Basis(Vector3.UP, deg_to_rad(Board.KK_BASE_YAW + 60.0 * k)).scaled(Vector3(Board.KK_SCALE, 1.0, Board.KK_SCALE))
			var mask := 0
			for i in 6:
				var q := Hex.dir_world(i) * apothem * 0.8
				var top := -INF
				var col := Color.BLACK
				for n in range(0, idx.size(), 3):
					var a: Vector3 = basis * (xf * vs[idx[n]])
					var b: Vector3 = basis * (xf * vs[idx[n + 1]])
					var c: Vector3 = basis * (xf * vs[idx[n + 2]])
					var den := (b.z - c.z) * (a.x - c.x) + (c.x - b.x) * (a.z - c.z)
					if absf(den) < 1e-9:
						continue
					var w0 := ((b.z - c.z) * (q.x - c.x) + (c.x - b.x) * (q.z - c.z)) / den
					var w1 := ((c.z - a.z) * (q.x - c.x) + (a.x - c.x) * (q.z - c.z)) / den
					var w2 := 1.0 - w0 - w1
					if w0 < 0.0 or w1 < 0.0 or w2 < 0.0:
						continue
					var y := w0 * a.y + w1 * b.y + w2 * c.y
					if y > top:
						top = y
						var uv: Vector2 = uvs[idx[n]] * w0 + uvs[idx[n + 1]] * w1 + uvs[idx[n + 2]] * w2
						col = img.get_pixel(clampi(int(uv.x * img.get_width()), 0, img.get_width() - 1), clampi(int(uv.y * img.get_height()), 0, img.get_height() - 1))
				# the pack's yellow-green grass (sand is redder, water bluer and lower)
				if top > -0.06 and col.g >= col.r - 0.01 and col.g > col.b + 0.25:
					mask |= 1 << i
			if not table.has(mask):
				table[mask] = [t, k]
			if k == 0:
				print("TILE %s land sides at turn 0: %s" % [t, _bits(mask)])
	var keys := table.keys()
	keys.sort()
	var lines: PackedStringArray = []
	for m in keys:
		lines.append("%d: [\"%s\", %d]" % [m, table[m][0], table[m][1]])
	print("KK_COASTS := {" + ", ".join(lines) + "}")
	print("masks covered: ", keys.size())
	quit()


func _bits(m: int) -> String:
	var s := ""
	for i in 6:
		s += "1" if m & (1 << i) else "0"
	return s
