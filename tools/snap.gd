extends RefCounted
## Dev helper: a small software rasterizer, so headless runs can draw models to PNG with no window and no GPU.
## Triangles are flat shaded; each takes its color from its texture at the triangle's middle (KayKit and Kenney
## models use palette textures, so that's the true color). Skinned meshes are drawn in their current pose.
## Use: var S := preload("res://tools/snap.gd"); var img := S.draw(node, 256, view_dir)

const LIGHT := Vector3(0.45, 1.0, 0.65)

static var _imgs := {}


static func _tex_image(t: Texture2D) -> Image:
	if t == null:
		return null
	if not _imgs.has(t):
		var im := t.get_image()
		if im and im.is_compressed():
			im.decompress()
		_imgs[t] = im
	return _imgs[t]


## Every visible triangle under `root` in world space: Array of [a, b, c, color].
static func triangles(root: Node) -> Array:
	var out: Array = []
	for node in root.find_children("*", "MeshInstance3D", true, false):
		var m := node as MeshInstance3D
		if not m.is_visible_in_tree() or m.mesh == null:
			continue
		var skel: Skeleton3D = null
		if m.skin and m.skeleton != NodePath():
			skel = m.get_node_or_null(m.skeleton) as Skeleton3D
		var binds: Array = []
		if skel:
			for i in m.skin.get_bind_count():
				var bi := m.skin.get_bind_bone(i)
				if bi < 0:
					bi = skel.find_bone(m.skin.get_bind_name(i))
				binds.append(skel.global_transform * skel.get_bone_global_pose(maxi(bi, 0)) * m.skin.get_bind_pose(i))
		var xf := m.global_transform
		for s in m.mesh.get_surface_count():
			var arr := m.mesh.surface_get_arrays(s)
			var vs: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
			if vs.is_empty():
				continue
			var uvs: PackedVector2Array = arr[Mesh.ARRAY_TEX_UV] if arr[Mesh.ARRAY_TEX_UV] != null else PackedVector2Array()
			var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX] if arr[Mesh.ARRAY_INDEX] != null else PackedInt32Array()
			var mat := m.get_active_material(s) as BaseMaterial3D
			var shm := m.get_active_material(s) as ShaderMaterial
			var base := mat.albedo_color if mat else Color(0.8, 0.8, 0.8)
			var img := _tex_image(mat.albedo_texture) if mat else null
			if shm and shm.get_shader_parameter("atlas") is Texture2D:
				img = _tex_image(shm.get_shader_parameter("atlas"))   # (patterned ground: drawn without its pattern)
				base = Color.WHITE
			var vcols = arr[Mesh.ARRAY_COLOR] if (mat and mat.vertex_color_use_as_albedo) else null
			var uv_scale := Vector2(mat.uv1_scale.x, mat.uv1_scale.y) if mat else Vector2.ONE
			var uv_off := Vector2(mat.uv1_offset.x, mat.uv1_offset.y) if mat else Vector2.ZERO
			var wv := PackedVector3Array()
			wv.resize(vs.size())
			var bones = arr[Mesh.ARRAY_BONES]
			if skel and bones != null and (bones as PackedInt32Array).size() > 0:
				var wts: PackedFloat32Array = arr[Mesh.ARRAY_WEIGHTS]
				var per: int = (bones as PackedInt32Array).size() / vs.size()
				for i in vs.size():
					var p := Vector3.ZERO
					for k in per:
						var w := wts[i * per + k]
						if w > 0.0:
							p += ((binds[bones[i * per + k]] as Transform3D) * vs[i]) * w
					wv[i] = p
			else:
				for i in vs.size():
					wv[i] = xf * vs[i]
			var n := idx.size() if idx.size() > 0 else vs.size()
			for t in range(0, n - 2, 3):
				var i0 := idx[t] if idx.size() > 0 else t
				var i1 := idx[t + 1] if idx.size() > 0 else t + 1
				var i2 := idx[t + 2] if idx.size() > 0 else t + 2
				var col := base
				if img and uvs.size() > 0:
					var uv := (uvs[i0] + uvs[i1] + uvs[i2]) / 3.0 * uv_scale + uv_off
					uv = Vector2(fposmod(uv.x, 1.0), fposmod(uv.y, 1.0))
					col = base * img.get_pixel(clampi(int(uv.x * img.get_width()), 0, img.get_width() - 1), clampi(int(uv.y * img.get_height()), 0, img.get_height() - 1))
				if vcols != null and (vcols as PackedColorArray).size() > i0:
					col = col * vcols[i0]
				out.append([wv[i0], wv[i1], wv[i2], col])
	return out


## Draws `root` (already in the tree, posed) seen from direction `view` (pointing from the model toward the
## camera), orthographic. `world_px` > 0 fixes the scale in pixels per world unit (else it's fitted); `center`
## is the world point drawn at the image's middle when the scale is fixed.
static func draw(root: Node, size := 256, view := Vector3(0.55, 0.75, 1.0), world_px := 0.0, center := Vector3.ZERO, bg := Color(0.13, 0.14, 0.16)) -> Image:
	return draw_tris(triangles(root), size, view, world_px, center, bg)


static func draw_tris(tris: Array, size := 256, view := Vector3(0.55, 0.75, 1.0), world_px := 0.0, center := Vector3.ZERO, bg := Color(0.13, 0.14, 0.16)) -> Image:
	var img := Image.create(size, size, false, Image.FORMAT_RGB8)
	img.fill(bg)
	if tris.is_empty():
		return img
	var c := view.normalized()
	var fwd := -c
	var right := fwd.cross(Vector3.UP).normalized()
	var up := right.cross(fwd).normalized()
	var L := LIGHT.normalized()
	# project
	var lo := Vector2(INF, INF)
	var hi := Vector2(-INF, -INF)
	var proj: Array = []
	for t in tris:
		var q: Array = []
		for k in 3:
			var p: Vector3 = t[k]
			var s := Vector3(p.dot(right), p.dot(up), p.dot(c))
			lo = Vector2(minf(lo.x, s.x), minf(lo.y, s.y))
			hi = Vector2(maxf(hi.x, s.x), maxf(hi.y, s.y))
			q.append(s)
		proj.append(q)
	var scale := world_px
	var mid := (lo + hi) * 0.5
	if scale <= 0.0:
		scale = (size * 0.9) / maxf(hi.x - lo.x, hi.y - lo.y)
	else:
		mid = Vector2(center.dot(right), center.dot(up))
	var zb := PackedFloat32Array()
	zb.resize(size * size)
	zb.fill(-INF)
	for ti in tris.size():
		var t: Array = tris[ti]
		var q: Array = proj[ti]
		var nrm: Vector3 = ((t[1] as Vector3) - (t[0] as Vector3)).cross((t[2] as Vector3) - (t[0] as Vector3))
		if nrm.length_squared() < 1e-12:
			continue
		nrm = nrm.normalized()
		if nrm.dot(c) < 0.0:
			nrm = -nrm
		var shade := 0.55 + 0.45 * maxf(0.0, nrm.dot(L))
		var col: Color = t[3]
		col = Color(col.r * shade, col.g * shade, col.b * shade)
		var a := _px(q[0], mid, scale, size)
		var b := _px(q[1], mid, scale, size)
		var d := _px(q[2], mid, scale, size)
		var area := (b.x - a.x) * (d.y - a.y) - (b.y - a.y) * (d.x - a.x)
		if absf(area) < 1e-9:
			continue
		var x0 := maxi(0, int(floor(minf(a.x, minf(b.x, d.x)))))
		var x1 := mini(size - 1, int(ceil(maxf(a.x, maxf(b.x, d.x)))))
		var y0 := maxi(0, int(floor(minf(a.y, minf(b.y, d.y)))))
		var y1 := mini(size - 1, int(ceil(maxf(a.y, maxf(b.y, d.y)))))
		for y in range(y0, y1 + 1):
			for x in range(x0, x1 + 1):
				var px := x + 0.5
				var py := y + 0.5
				var w0 := ((b.x - px) * (d.y - py) - (b.y - py) * (d.x - px)) / area
				var w1 := ((d.x - px) * (a.y - py) - (d.y - py) * (a.x - px)) / area
				var w2 := 1.0 - w0 - w1
				if w0 < -0.001 or w1 < -0.001 or w2 < -0.001:
					continue
				var z: float = w0 * a.z + w1 * b.z + w2 * d.z
				var k := y * size + x
				if z > zb[k]:
					zb[k] = z
					img.set_pixel(x, y, col)
	return img


static func _px(s: Vector3, mid: Vector2, scale: float, size: int) -> Vector3:
	return Vector3((s.x - mid.x) * scale + size * 0.5, size * 0.5 - (s.y - mid.y) * scale, s.z)


## Lays images out in a grid (cols wide) on one sheet.
static func sheet(imgs: Array, cols: int) -> Image:
	var w := (imgs[0] as Image).get_width()
	var rows := int(ceil(float(imgs.size()) / cols))
	var out := Image.create(w * cols, w * rows, false, Image.FORMAT_RGB8)
	out.fill(Color(0.05, 0.05, 0.06))
	for i in imgs.size():
		out.blit_rect(imgs[i], Rect2i(0, 0, w, w), Vector2i((i % cols) * w, (i / cols) * w))
	return out
