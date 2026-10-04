class_name FX
extends RefCounted
## Fire-and-forget visual effects.


static func _fade_mat(color: Color, alpha: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(color.r, color.g, color.b, alpha)
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	return m


static func burst(parent: Node, pos: Vector3, color: Color, radius := 0.6, dur := 0.25) -> void:
	var m := SphereMesh.new()
	m.radius = 1.0
	m.height = 2.0
	m.radial_segments = 12
	m.rings = 6
	var mi := MeshInstance3D.new()
	mi.mesh = m
	var mat := _fade_mat(color, 0.7)
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.scale = Vector3.ONE * radius * 0.3
	parent.add_child(mi)
	mi.global_position = pos
	var tw := mi.create_tween().set_parallel(true)
	tw.tween_property(mi, "scale", Vector3.ONE * max(radius, 0.1), dur)
	tw.tween_property(mat, "albedo_color:a", 0.0, dur)
	tw.chain().tween_callback(mi.queue_free)


static func ring(parent: Node, pos: Vector3, color: Color, radius := 2.0, dur := 0.4) -> void:
	var m := TorusMesh.new()
	m.inner_radius = 0.9
	m.outer_radius = 1.0
	m.rings = 32
	m.ring_segments = 4
	var mi := MeshInstance3D.new()
	mi.mesh = m
	var mat := _fade_mat(color, 0.8)
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	mi.scale = Vector3(0.2, 0.2, 0.2)
	parent.add_child(mi)
	mi.global_position = pos
	var tw := mi.create_tween().set_parallel(true)
	tw.tween_property(mi, "scale", Vector3(radius, 0.3, radius), dur).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_QUAD)
	tw.tween_property(mat, "albedo_color:a", 0.0, dur)
	tw.chain().tween_callback(mi.queue_free)


static func lightning(parent: Node, points: Array, color: Color) -> void:
	var holder := Node3D.new()
	parent.add_child(holder)
	var mat := _fade_mat(color.lightened(0.4), 1.0)
	for i in range(points.size() - 1):
		var a: Vector3 = points[i]
		var b: Vector3 = points[i + 1]
		# jag each hop into 3 pieces
		var prev := a
		for k in range(1, 4):
			var nxt := a.lerp(b, k / 3.0)
			if k < 3:
				nxt += Vector3(randf_range(-0.35, 0.35), randf_range(-0.35, 0.35), randf_range(-0.35, 0.35))
			var seg_len := prev.distance_to(nxt)
			if seg_len > 0.01:
				var bm := BoxMesh.new()
				bm.size = Vector3(0.09, 0.09, seg_len)
				var mi := MeshInstance3D.new()
				mi.mesh = bm
				mi.material_override = mat
				mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				holder.add_child(mi)
				mi.global_position = (prev + nxt) * 0.5
				mi.look_at(nxt, Vector3.UP if abs((nxt - prev).normalized().y) < 0.99 else Vector3.RIGHT)
			prev = nxt
	var tw := holder.create_tween()
	tw.tween_property(mat, "albedo_color:a", 0.0, 0.2)
	tw.tween_callback(holder.queue_free)


## A straight beam of light from a to b: a bright core in a colored glow, flaring then fading.
static func beam(parent: Node, a: Vector3, b: Vector3, color: Color, width := 0.4, dur := 0.35) -> void:
	var length := a.distance_to(b)
	if length < 0.05:
		return
	var holder := Node3D.new()
	parent.add_child(holder)
	var mats: Array = []
	for layer in [[width, color.lightened(0.15), 0.5], [width * 0.4, color.lightened(0.8), 0.95]]:
		var cm := CylinderMesh.new()
		cm.top_radius = float(layer[0]) * 0.5
		cm.bottom_radius = float(layer[0]) * 0.5
		cm.height = length
		cm.radial_segments = 10
		cm.rings = 1
		var mi := MeshInstance3D.new()
		mi.mesh = cm
		var m := _fade_mat(layer[1], layer[2])
		mats.append(m)
		mi.material_override = m
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		holder.add_child(mi)
	holder.global_position = (a + b) * 0.5
	holder.quaternion = Quaternion(Vector3.UP, (b - a).normalized())   # the cylinders run along Y
	var tw := holder.create_tween().set_parallel(true)
	for m in mats:
		tw.tween_property(m, "albedo_color:a", 0.0, dur)
	tw.tween_property(holder, "scale", Vector3(0.25, 1.0, 0.25), dur).set_ease(Tween.EASE_IN)
	tw.chain().tween_callback(holder.queue_free)


static func float_text(parent: Node, pos: Vector3, text: String, color: Color, size := 48) -> void:
	var l := Label3D.new()
	l.text = text
	l.modulate = color
	l.font_size = size
	l.outline_size = 10
	l.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	l.no_depth_test = true
	l.pixel_size = 0.01
	parent.add_child(l)
	l.global_position = pos
	var tw := l.create_tween().set_parallel(true)
	tw.tween_property(l, "global_position", pos + Vector3(0, 1.5, 0), 0.9)
	tw.tween_property(l, "modulate:a", 0.0, 0.9).set_delay(0.3)
	tw.chain().tween_callback(l.queue_free)
