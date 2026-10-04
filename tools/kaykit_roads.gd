extends SceneTree
## Dev tool: works out which sides of our hex grid each KayKit road tile connects, in each of its 6 turns, and prints
## the lookup Board uses (mask of Hex.E side indices -> [tile, turns]). Road vertices are found by the color of the
## texture under them (road is not green); a side counts as connected when road reaches its midpoint.
## Godot --headless --path . --script res://tools/kaykit_roads.gd -- --scratch

const TILES := ["hex_road_A", "hex_road_B", "hex_road_C", "hex_road_D", "hex_road_E", "hex_road_F", "hex_road_G",
	"hex_road_H", "hex_road_I", "hex_road_J", "hex_road_K", "hex_road_L", "hex_road_M"]


func _init() -> void:
	Hex.setup()
	var img: Image = null
	var table := {}
	var apothem := Hex.SQ3 * 0.5 * Hex.R
	for t in TILES:
		var mi: Array = KayKit.hex_mesh(t)
		var mesh: Mesh = mi[0]
		var xf: Transform3D = mi[1]
		if mesh == null:
			print("missing ", t)
			continue
		var road_pts: Array = []
		for s in mesh.get_surface_count():
			var mat := mesh.surface_get_material(s) as BaseMaterial3D
			if img == null and mat and mat.albedo_texture:
				img = mat.albedo_texture.get_image()
				if img.is_compressed():
					img.decompress()
			var arr := mesh.surface_get_arrays(s)
			var vs: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			var uvs: PackedVector2Array = arr[Mesh.ARRAY_TEX_UV]
			for i in vs.size():
				var uv := uvs[i]
				var c := img.get_pixel(clampi(int(uv.x * img.get_width()), 0, img.get_width() - 1), clampi(int(uv.y * img.get_height()), 0, img.get_height() - 1))
				var green := c.g > c.r + 0.06 and c.g > c.b + 0.06
				var p := xf * vs[i]
				if not green and p.y > -0.2:
					road_pts.append(p)
		for k in 6:
			var basis := Basis(Vector3.UP, deg_to_rad(Board.KK_BASE_YAW + 60.0 * k)).scaled(Vector3(Board.KK_SCALE, 1.0, Board.KK_SCALE))
			var mask := 0
			for i in 6:
				var mid := Hex.dir_world(i) * apothem
				for p in road_pts:
					var w: Vector3 = basis * p
					if Vector2(w.x - mid.x, w.z - mid.z).length() < 0.42:
						mask |= 1 << i
						break
			if not table.has(mask):
				table[mask] = [t, k]
		print("TILE %s road verts=%d base mask=%s" % [t, road_pts.size(), _bits(_mask_of(table, t))])
	var keys := table.keys()
	keys.sort()
	var lines: PackedStringArray = []
	for m in keys:
		lines.append("%d: [\"%s\", %d]" % [m, table[m][0], table[m][1]])
	print("KK_ROADS := {" + ", ".join(lines) + "}")
	print("masks covered: ", keys.size(), " of 63")
	quit()


func _mask_of(table: Dictionary, t: String) -> int:
	for m in table:
		if table[m][0] == t and table[m][1] == 0:
			return m
	return -1


func _bits(m: int) -> String:
	var s := ""
	for i in 6:
		s += "1" if m >= 0 and m & (1 << i) else "0"
	return s
