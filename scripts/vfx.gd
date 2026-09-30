class_name VFX
extends RefCounted
## GPU particle effects built on the sprites in assets/fx (made by tools/fx_textures.gd from Meshy images).
## Fire-and-forget: every call makes a one-shot emitter that frees itself when it's done. Materials are cached per
## preset and tint, so making emitters is cheap; VFX.warmup() compiles them all up front so nothing hitches mid-wave.
## Without the textures (or on a headless run) calls quietly do nothing.

const TEX := "res://assets/fx/"

## Presets. tex: sprite; add: additive blend (glows) instead of alpha; amount; life (s); explode: 1 = all at once,
## 0 = spread over the lifetime (a stream); speed [min, max]; spread (degrees around dir); gravity (y, + = rises);
## size [start, end] (world units); ramp: colors over the particle's life (multiplied by the call's tint);
## radius: emission sphere; ring: emit from a flat ring of this radius instead; spin (deg/s, random either way);
## look: "cam" (billboard), "y" (upright billboard, for beams) or "flat" (lying on the ground); tall: quad height factor;
## damp: slows particles down; reach: how far the effect can extend (for culling).
const PRESETS := {
	"death_smoke": {"tex": "fx_smoke", "add": false, "amount": 6, "life": 0.7, "speed": [0.6, 1.6], "spread": 180.0,
		"gravity": 0.9, "size": [0.5, 1.3], "ramp": [Color(1, 1, 1, 0.75), Color(0.8, 0.8, 0.8, 0.0)], "radius": 0.3, "spin": 60.0},
	"death_sparks": {"tex": "fx_spark", "add": true, "amount": 5, "life": 0.4, "speed": [2.0, 4.0], "spread": 180.0,
		"gravity": -4.0, "size": [0.4, 0.05], "ramp": [Color(1, 1, 1, 1), Color(1, 1, 1, 0.0)], "spin": 180.0},
	"blast_smoke": {"tex": "fx_smoke", "add": false, "amount": 8, "life": 0.9, "speed": [1.0, 3.0], "spread": 70.0,
		"gravity": 0.6, "size": [0.8, 2.0], "ramp": [Color(0.62, 0.58, 0.52, 0.7), Color(0.5, 0.48, 0.45, 0.0)], "radius": 0.4, "spin": 45.0, "damp": 2.0},
	"blast_debris": {"tex": "fx_debris", "add": false, "amount": 7, "life": 0.8, "speed": [3.0, 6.0], "spread": 50.0,
		"gravity": -12.0, "size": [0.35, 0.25], "ramp": [Color(0.62, 0.55, 0.45, 1), Color(0.5, 0.45, 0.38, 1)], "spin": 400.0},
	"blast_flash": {"tex": "fx_flame", "add": true, "amount": 6, "life": 0.3, "speed": [1.5, 3.0], "spread": 180.0,
		"gravity": 1.0, "size": [1.0, 1.7], "ramp": [Color(1, 0.95, 0.7, 1), Color(1, 0.55, 0.15, 0.7), Color(0.6, 0.15, 0.05, 0.0)]},
	"embers": {"tex": "fx_spark", "add": true, "amount": 10, "life": 0.9, "speed": [2.0, 5.0], "spread": 60.0,
		"gravity": -3.0, "size": [0.2, 0.05], "ramp": [Color(1, 0.9, 0.5, 1), Color(1, 0.45, 0.1, 0.9), Color(0.7, 0.1, 0.0, 0.0)], "spin": 200.0},
	"dust_ring": {"tex": "fx_dust", "add": false, "amount": 1, "life": 0.6, "speed": [0.0, 0.0], "spread": 0.0,
		"gravity": 0.0, "size": [0.6, 2.6], "ramp": [Color(0.8, 0.72, 0.6, 0.7), Color(0.75, 0.68, 0.58, 0.0)], "look": "flat", "spin": 30.0},
	"breath": {"tex": "fx_flame", "add": true, "amount": 44, "life": 0.6, "explode": 0.0, "speed": [22.0, 26.0], "spread": 6.0,
		"gravity": 1.5, "size": [0.6, 2.4], "ramp": [Color(1, 0.97, 0.8, 1), Color(1, 0.7, 0.2, 1), Color(0.95, 0.3, 0.05, 0.7), Color(0.3, 0.05, 0.0, 0.0)],
		"spin": 120.0, "reach": 16.0},
	"breath_smoke": {"tex": "fx_smoke", "add": false, "amount": 12, "life": 1.0, "explode": 0.0, "speed": [11.0, 14.0], "spread": 9.0,
		"gravity": 1.8, "size": [1.0, 2.6], "ramp": [Color(0.2, 0.18, 0.16, 0.0), Color(0.22, 0.2, 0.18, 0.45), Color(0.3, 0.28, 0.26, 0.0)],
		"spin": 50.0, "damp": 3.0, "reach": 16.0},
	"cone": {"tex": "fx_flame", "add": true, "amount": 22, "life": 0.45, "explode": 0.2, "speed": [9.0, 12.0], "spread": 28.0,
		"gravity": 1.5, "size": [0.4, 1.4], "ramp": [Color(1, 0.95, 0.75, 1), Color(1, 0.6, 0.15, 0.9), Color(0.5, 0.1, 0.0, 0.0)],
		"spin": 120.0, "reach": 8.0},
	"smite_ray": {"tex": "fx_ray", "add": true, "amount": 1, "life": 0.55, "speed": [0.0, 0.0], "spread": 0.0,
		"gravity": 0.0, "size": [1.6, 0.8], "tall": 5.0, "ramp": [Color(1, 1, 1, 1), Color(1, 0.9, 0.55, 0.9), Color(1, 0.85, 0.4, 0.0)],
		"look": "y", "reach": 10.0},
	"holy_sparks": {"tex": "fx_spark", "add": true, "amount": 14, "life": 0.8, "speed": [1.5, 4.0], "spread": 180.0,
		"gravity": 1.2, "size": [0.35, 0.05], "ramp": [Color(1, 1, 1, 1), Color(1, 0.85, 0.4, 0.8), Color(1, 0.8, 0.3, 0.0)], "spin": 180.0},
	"rune": {"tex": "fx_rune", "add": true, "amount": 1, "life": 0.8, "speed": [0.0, 0.0], "spread": 0.0, "gravity": 0.0,
		"size": [1.0, 2.6], "ramp": [Color(1, 1, 1, 0.95), Color(1, 1, 1, 0.0)], "look": "flat", "spin": 90.0},
	"splash": {"tex": "fx_splash", "add": true, "amount": 3, "life": 0.5, "speed": [0.5, 1.0], "spread": 60.0,
		"gravity": 0.0, "size": [0.8, 1.9], "ramp": [Color(0.85, 0.95, 1, 0.9), Color(0.5, 0.8, 1, 0.0)], "spin": 90.0},
	"bubbles": {"tex": "fx_bubble", "add": false, "amount": 8, "life": 0.9, "speed": [0.8, 2.0], "spread": 70.0,
		"gravity": 1.2, "size": [0.2, 0.38], "ramp": [Color(1, 1, 1, 0.9), Color(1, 1, 1, 0.0)], "radius": 0.5},
	"poison_cloud": {"tex": "fx_smoke", "add": false, "amount": 5, "life": 1.2, "speed": [0.3, 1.0], "spread": 90.0,
		"gravity": 0.4, "size": [1.0, 2.3], "ramp": [Color(1, 1, 1, 0.5), Color(1, 1, 1, 0.0)], "radius": 0.5, "spin": 40.0},
	"wisps": {"tex": "fx_wisp", "add": true, "amount": 4, "life": 1.2, "speed": [1.0, 2.0], "spread": 25.0,
		"gravity": 1.5, "size": [0.5, 0.9], "ramp": [Color(1, 1, 1, 0.0), Color(1, 1, 1, 0.9), Color(1, 1, 1, 0.0)], "radius": 0.4, "spin": 60.0},
	"dirt": {"tex": "fx_debris", "add": false, "amount": 6, "life": 0.7, "speed": [1.5, 3.5], "spread": 45.0,
		"gravity": -10.0, "size": [0.22, 0.16], "ramp": [Color(0.45, 0.36, 0.26, 1), Color(0.4, 0.32, 0.24, 1)], "spin": 400.0},
	"bones": {"tex": "fx_debris", "add": false, "amount": 6, "life": 0.7, "speed": [1.5, 3.0], "spread": 70.0,
		"gravity": -9.0, "size": [0.2, 0.12], "ramp": [Color(0.92, 0.9, 0.8, 1), Color(0.85, 0.83, 0.75, 1)], "spin": 400.0},
	"magic": {"tex": "fx_magic", "add": true, "amount": 2, "life": 0.45, "speed": [0.0, 0.3], "spread": 180.0,
		"gravity": 0.0, "size": [0.4, 1.5], "ramp": [Color(1, 1, 1, 1), Color(1, 1, 1, 0.0)], "spin": 360.0},
	"sparks": {"tex": "fx_spark", "add": true, "amount": 6, "life": 0.35, "speed": [2.0, 4.5], "spread": 180.0,
		"gravity": -2.0, "size": [0.3, 0.05], "ramp": [Color(1, 1, 1, 1), Color(1, 1, 1, 0.0)], "spin": 200.0},
	"rise_sparks": {"tex": "fx_spark", "add": true, "amount": 16, "life": 1.0, "speed": [0.6, 1.6], "spread": 25.0,
		"gravity": 2.2, "size": [0.3, 0.05], "ramp": [Color(1, 1, 1, 1), Color(1, 1, 1, 0.0)], "ring": 1.0, "spin": 180.0},
	"ring_dust": {"tex": "fx_smoke", "add": false, "amount": 10, "life": 0.8, "speed": [1.0, 2.0], "spread": 80.0,
		"gravity": 0.3, "size": [0.5, 1.4], "ramp": [Color(0.8, 0.74, 0.64, 0.6), Color(0.75, 0.7, 0.62, 0.0)], "ring": 1.0, "spin": 40.0, "damp": 2.0},
}

static var _ok := -1
static var _proc := {}
static var _draw := {}


static func available() -> bool:
	if _ok == -1:
		_ok = 1 if (DisplayServer.get_name() != "headless" and ResourceLoader.exists(TEX + "fx_smoke.png")) else 0
	return _ok == 1


## One effect: preset at pos, tinted, scaled (size, speed and reach together), aimed along dir (the direction
## particles fly; flat effects ignore it).
static func play(parent: Node, preset: String, pos: Vector3, tint := Color.WHITE, scale := 1.0, dir := Vector3.UP) -> void:
	if not available() or parent == null:
		return
	var p: Dictionary = PRESETS[preset]
	var e := GPUParticles3D.new()
	e.one_shot = true
	e.amount = int(p["amount"])
	e.lifetime = float(p["life"])
	e.explosiveness = float(p.get("explode", 1.0))
	e.local_coords = false
	e.process_material = _process_mat(preset, tint)
	e.draw_pass_1 = _draw_mesh(preset)
	e.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var reach := float(p.get("reach", 5.0))
	e.visibility_aabb = AABB(Vector3.ONE * -reach, Vector3.ONE * reach * 2.0)
	parent.add_child(e)
	e.global_position = pos
	# the process material shoots along +Y; turn the emitter so +Y is dir
	var d := dir.normalized()
	if absf(d.dot(Vector3.UP)) < 0.999:
		e.global_basis = Basis(Quaternion(Vector3.UP, d))
	elif d.y < 0.0:
		e.global_basis = Basis(Vector3.RIGHT, PI)
	if scale != 1.0:
		e.scale = Vector3.ONE * scale
	e.emitting = true
	# freed once its last particle is gone (a timer, not the finished signal, so it can't be missed); the timer
	# pauses with the game
	var ttl := e.lifetime * (2.0 - e.explosiveness) + 0.3
	e.get_tree().create_timer(ttl, false).timeout.connect(e.queue_free)


static func _process_mat(preset: String, tint: Color) -> ParticleProcessMaterial:
	var key := preset + "|" + tint.to_html()
	if _proc.has(key):
		return _proc[key]
	var p: Dictionary = PRESETS[preset]
	var m := ParticleProcessMaterial.new()
	m.direction = Vector3.UP
	m.spread = float(p["spread"])
	m.initial_velocity_min = float(p["speed"][0])
	m.initial_velocity_max = float(p["speed"][1])
	m.gravity = Vector3(0, float(p["gravity"]), 0)
	if p.has("damp"):
		m.damping_min = float(p["damp"]) * 0.7
		m.damping_max = float(p["damp"])
	if p.has("ring"):
		m.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_RING
		m.emission_ring_axis = Vector3.UP
		m.emission_ring_radius = float(p["ring"])
		m.emission_ring_inner_radius = float(p["ring"]) * 0.8
		m.emission_ring_height = 0.1
	elif p.has("radius"):
		m.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
		m.emission_sphere_radius = float(p["radius"])
	# size over life: the quad is 1 unit, scaled from size[0] to size[1]
	var s0 := float(p["size"][0])
	var s1 := float(p["size"][1])
	var top := maxf(s0, s1)
	m.scale_min = top * 0.85
	m.scale_max = top * 1.15
	var curve := Curve.new()
	curve.add_point(Vector2(0, s0 / top))
	curve.add_point(Vector2(1, s1 / top))
	var ct := CurveTexture.new()
	ct.curve = curve
	m.scale_curve = ct
	var g := Gradient.new()
	var ramp: Array = p["ramp"]
	var offs := PackedFloat32Array()
	var cols := PackedColorArray()
	for i in ramp.size():
		var c: Color = ramp[i]
		offs.append(float(i) / maxf(1.0, ramp.size() - 1))
		cols.append(Color(c.r * tint.r, c.g * tint.g, c.b * tint.b, c.a * tint.a))
	g.offsets = offs
	g.colors = cols
	var gt := GradientTexture1D.new()
	gt.gradient = g
	m.color_ramp = gt
	if p.has("spin"):
		m.angle_min = -180.0
		m.angle_max = 180.0
		m.angular_velocity_min = -float(p["spin"])
		m.angular_velocity_max = float(p["spin"])
	if String(p.get("look", "cam")) == "flat":
		m.particle_flag_rotate_y = true
	_proc[key] = m
	return m


static func _draw_mesh(preset: String) -> QuadMesh:
	if _draw.has(preset):
		return _draw[preset]
	var p: Dictionary = PRESETS[preset]
	var look := String(p.get("look", "cam"))
	var q := QuadMesh.new()
	q.size = Vector2(1.0, float(p.get("tall", 1.0)))
	if look == "flat":
		q.orientation = PlaneMesh.FACE_Y
	elif look == "y":
		q.center_offset = Vector3(0, q.size.y * 0.5, 0)   # beams stand on the spot
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD if p["add"] else BaseMaterial3D.BLEND_MODE_MIX
	mat.vertex_color_use_as_albedo = true
	mat.albedo_texture = load(TEX + String(p["tex"]) + ".png")
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.disable_receive_shadows = true
	if look == "cam":
		mat.billboard_mode = BaseMaterial3D.BILLBOARD_PARTICLES
	elif look == "y":
		mat.billboard_mode = BaseMaterial3D.BILLBOARD_FIXED_Y
		mat.billboard_keep_scale = true
	q.material = mat
	_draw[preset] = q
	return q


## Plays every preset once just under the castle (in view, but hidden by the ground), so their shaders compile at
## load time instead of mid-wave.
static func warmup(parent: Node) -> void:
	if not available():
		return
	for k in PRESETS:
		play(parent, k, Vector3(0, -4.0, 0), Color.WHITE, 0.3)


# ------------------------------------------------------------------ composed effects

static func death(parent: Node, pos: Vector3, col: Color, big := false) -> void:
	var s := 2.2 if big else 1.0
	play(parent, "death_smoke", pos, col.lerp(Color(0.85, 0.85, 0.85), 0.5), s)
	play(parent, "death_sparks", pos, col.lightened(0.3), s)


## A boulder, shell or bomb landing: flash, stones, dust and smoke, sized by the splash radius (world units).
static func blast(parent: Node, pos: Vector3, splash: float, fiery := false) -> void:
	var s := clampf(splash / 2.2, 0.6, 2.2)
	play(parent, "blast_flash", pos + Vector3(0, 0.3, 0), Color.WHITE, s)
	play(parent, "blast_debris", pos, Color.WHITE, s)
	play(parent, "blast_smoke", pos, Color.WHITE, s)
	play(parent, "dust_ring", pos + Vector3(0, 0.08, 0), Color.WHITE, s * 1.2)
	if fiery:
		play(parent, "embers", pos + Vector3(0, 0.3, 0), Color.WHITE, s)


static func poison(parent: Node, pos: Vector3, col: Color, splash: float) -> void:
	var s := clampf(splash / 2.4, 0.6, 1.8)
	play(parent, "bubbles", pos + Vector3(0, 0.2, 0), col.lightened(0.2), s)
	play(parent, "poison_cloud", pos + Vector3(0, 0.3, 0), col, s)


## A slam, stomp or maul on the ground.
static func stomp(parent: Node, pos: Vector3, radius: float) -> void:
	var s := clampf(radius / 2.2, 0.5, 2.5)
	play(parent, "dust_ring", pos + Vector3(0, 0.08, 0), Color.WHITE, s * 1.3)
	play(parent, "ring_dust", pos, Color.WHITE, s)
	play(parent, "dirt", pos, Color.WHITE, s)


## The Fat Dragon's fire, from its mouth along dir for about length world units.
static func breath(parent: Node, mouth: Vector3, dir: Vector3, length: float) -> void:
	var s := clampf(length / 14.0, 0.5, 2.0)
	play(parent, "breath", mouth, Color.WHITE, s, dir)
	play(parent, "breath_smoke", mouth + Vector3(0, 0.4, 0), Color.WHITE, s, dir)


static func smite(parent: Node, ground: Vector3, col: Color) -> void:
	play(parent, "smite_ray", ground, Color.WHITE, 1.0)
	play(parent, "holy_sparks", ground + Vector3(0, 0.6, 0), Color.WHITE, 1.0)
	play(parent, "rune", ground + Vector3(0, 0.1, 0), col, 1.0)


static func splash(parent: Node, pos: Vector3, col: Color) -> void:
	play(parent, "splash", pos, col.lightened(0.4), 1.0)
	play(parent, "bubbles", pos, col.lightened(0.5), 0.8)


static func raise(parent: Node, ground: Vector3) -> void:
	var green := Color(0.5, 1.0, 0.4)
	play(parent, "rune", ground + Vector3(0, 0.1, 0), green, 0.8)
	play(parent, "wisps", ground + Vector3(0, 0.3, 0), green, 1.0)
	play(parent, "dirt", ground, Color.WHITE, 0.8)


static func crumble(parent: Node, pos: Vector3) -> void:
	play(parent, "bones", pos + Vector3(0, 0.5, 0), Color.WHITE, 1.0)
	play(parent, "death_smoke", pos + Vector3(0, 0.3, 0), Color(0.7, 0.8, 0.6), 0.8)


static func magic_hit(parent: Node, pos: Vector3, col: Color, big := false) -> void:
	play(parent, "magic", pos, col.lightened(0.3), 1.4 if big else 1.0)
	play(parent, "sparks", pos, col.lightened(0.4), 1.0)


static func build(parent: Node, center: Vector3, cells: int) -> void:
	var s := sqrt(float(cells))
	play(parent, "ring_dust", center, Color.WHITE, s)
	play(parent, "dust_ring", center + Vector3(0, 0.08, 0), Color.WHITE, s * 1.2)


static func upgrade(parent: Node, center: Vector3, col: Color, cells: int) -> void:
	var s := sqrt(float(cells))
	play(parent, "rise_sparks", center + Vector3(0, 0.2, 0), col.lerp(Color(1, 0.9, 0.5), 0.5), s)
	play(parent, "rune", center + Vector3(0, 0.1, 0), Color(1, 0.85, 0.4), s * 1.1)
