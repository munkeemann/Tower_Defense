class_name VFX
extends RefCounted
## GPU particle effects. Textures live in assets/fx: animated flipbooks painted by tools/fx_flipbooks.gd (smoke, fire,
## explosion) and single sprites made from Meshy images by tools/fx_textures.gd (sparks, runes, splashes...), all
## white so particles tint them freely. Fire-and-forget: every call makes a one-shot emitter that frees itself.
## Materials are cached per preset and tint, and VFX.warmup() compiles them all at load so nothing hitches mid-wave.
## Without the textures (or on a headless run) calls quietly do nothing.

const TEX := "res://assets/fx/"

## Presets.
##   tex: texture (fb_* are 8x8 flipbooks played once over the particle's life); mesh: "chunk" draws little lit 3D
##   rocks instead of sprites. add: additive glow instead of alpha blend.
##   amount, life (s), explode (1 = all at once, 0 = a stream over the lifetime; default 0.85), speed [min, max],
##   spread (deg around the emit direction), gravity (y, + rises), damp (slows down), size [start, end] (world units),
##   ramp (colors over life, multiplied by the call's tint), fade_in (share of the life spent fading in, default 0.1),
##   radius (emission sphere) or ring (flat ring radius), spin (deg/s either way; 0 keeps sprites upright),
##   look: "cam" billboard (default), "y" upright billboard (beams), "flat" lying on the ground,
##   tall (quad height factor), soft (fade where it meets the ground, default true), reach (culling size).
const PRESETS := {
	# ---- smoke and dust
	"death_smoke": {"tex": "fb_smoke", "amount": 4, "life": 0.9, "speed": [0.5, 1.4], "spread": 180.0, "gravity": 0.9,
		"damp": 1.5, "size": [0.8, 1.6], "ramp": [Color(1, 1, 1, 0.85), Color(0.9, 0.9, 0.9, 0.6)], "radius": 0.3},
	"blast_smoke": {"tex": "fb_smoke", "amount": 6, "life": 1.4, "speed": [1.0, 2.6], "spread": 70.0, "gravity": 0.8,
		"damp": 2.2, "size": [1.2, 2.6], "ramp": [Color(0.72, 0.68, 0.62, 0.0), Color(0.62, 0.58, 0.54, 0.8), Color(0.55, 0.52, 0.5, 0.5)],
		"fade_in": 0.2, "radius": 0.5},
	"ring_dust": {"tex": "fb_smoke", "amount": 9, "life": 0.9, "speed": [1.2, 2.2], "spread": 80.0, "gravity": 0.3,
		"damp": 2.5, "size": [0.7, 1.5], "ramp": [Color(0.85, 0.78, 0.66, 0.75), Color(0.8, 0.74, 0.64, 0.5)], "ring": 1.0},
	"dust_ring": {"tex": "fx_dust", "amount": 1, "life": 0.6, "speed": [0.0, 0.0], "spread": 0.0, "gravity": 0.0,
		"size": [0.8, 2.8], "ramp": [Color(0.85, 0.78, 0.66, 0.7), Color(0.8, 0.74, 0.64, 0.0)], "look": "flat", "fade_in": 0.05},
	"poison_cloud": {"tex": "fb_smoke", "amount": 5, "life": 1.5, "speed": [0.3, 0.9], "spread": 90.0, "gravity": 0.35,
		"damp": 1.0, "size": [1.1, 2.2], "ramp": [Color(1, 1, 1, 0.75), Color(1, 1, 1, 0.5)], "radius": 0.5},
	"breath_smoke": {"tex": "fb_smoke", "amount": 14, "life": 1.1, "explode": 0.0, "speed": [10.0, 13.0], "spread": 9.0,
		"gravity": 1.8, "damp": 3.0, "size": [1.2, 2.8], "ramp": [Color(0.28, 0.25, 0.23, 0.0), Color(0.3, 0.27, 0.25, 0.55), Color(0.36, 0.34, 0.32, 0.3)],
		"fade_in": 0.3, "reach": 16.0},
	# ---- fire
	"blast_fire": {"tex": "fb_explosion", "amount": 4, "life": 0.75, "speed": [0.3, 1.2], "spread": 180.0, "gravity": 0.8,
		"size": [1.4, 2.4], "ramp": [Color(1, 0.97, 0.85, 1), Color(1, 0.72, 0.3, 1), Color(0.95, 0.4, 0.12, 1), Color(0.35, 0.3, 0.28, 1)],
		"radius": 0.45, "fade_in": 0.03},
	"breath": {"tex": "fb_fire", "amount": 46, "life": 0.62, "explode": 0.0, "speed": [22.0, 26.0], "spread": 5.0,
		"gravity": 1.2, "size": [0.9, 2.6], "ramp": [Color(1, 0.98, 0.85, 1), Color(1, 0.75, 0.3, 1), Color(0.98, 0.42, 0.1, 1), Color(0.6, 0.15, 0.05, 1)],
		"fade_in": 0.04, "soft": false, "reach": 16.0},
	"cone": {"tex": "fb_fire", "amount": 24, "life": 0.5, "explode": 0.25, "speed": [9.0, 12.0], "spread": 26.0,
		"gravity": 1.2, "size": [0.7, 1.7], "ramp": [Color(1, 0.96, 0.8, 1), Color(1, 0.65, 0.2, 1), Color(0.75, 0.2, 0.05, 1)],
		"fade_in": 0.05, "soft": false, "reach": 8.0},
	"embers": {"tex": "fx_glow", "add": true, "amount": 12, "life": 1.0, "speed": [2.0, 5.0], "spread": 65.0,
		"gravity": -3.0, "size": [0.22, 0.06], "ramp": [Color(1, 0.9, 0.55, 1), Color(1, 0.5, 0.12, 0.9), Color(0.8, 0.15, 0.0, 0.0)],
		"fade_in": 0.0, "soft": false},
	"flash": {"tex": "fx_glow", "add": true, "amount": 1, "life": 0.18, "explode": 1.0, "speed": [0.0, 0.0], "spread": 0.0,
		"gravity": 0.0, "size": [2.2, 3.4], "ramp": [Color(1, 0.95, 0.8, 0.9), Color(1, 0.7, 0.35, 0.0)], "fade_in": 0.0, "soft": false},
	# ---- chunks (3D)
	"blast_debris": {"mesh": "chunk", "amount": 8, "life": 1.0, "speed": [3.5, 6.5], "spread": 45.0, "gravity": -14.0,
		"size": [0.26, 0.2], "ramp": [Color(0.55, 0.5, 0.44, 1), Color(0.5, 0.46, 0.4, 1)], "spin": 540.0, "fade_in": 0.0, "soft": false},
	"dirt": {"mesh": "chunk", "amount": 7, "life": 0.8, "speed": [2.0, 4.0], "spread": 40.0, "gravity": -12.0,
		"size": [0.16, 0.12], "ramp": [Color(0.42, 0.33, 0.24, 1), Color(0.38, 0.3, 0.22, 1)], "spin": 540.0, "fade_in": 0.0, "soft": false},
	"bones": {"mesh": "chunk", "amount": 7, "life": 0.8, "speed": [1.8, 3.4], "spread": 60.0, "gravity": -11.0,
		"size": [0.15, 0.1], "ramp": [Color(0.92, 0.9, 0.82, 1), Color(0.88, 0.86, 0.78, 1)], "spin": 540.0, "fade_in": 0.0, "soft": false},
	# ---- sparks, glows and magic
	"death_sparks": {"tex": "fx_spark", "add": true, "amount": 5, "life": 0.4, "speed": [2.0, 4.0], "spread": 180.0,
		"gravity": -4.0, "size": [0.45, 0.08], "ramp": [Color(1, 1, 1, 1), Color(1, 1, 1, 0.0)], "fade_in": 0.0, "soft": false},
	"sparks": {"tex": "fx_spark", "add": true, "amount": 6, "life": 0.35, "speed": [2.0, 4.5], "spread": 180.0,
		"gravity": -2.0, "size": [0.35, 0.06], "ramp": [Color(1, 1, 1, 1), Color(1, 1, 1, 0.0)], "fade_in": 0.0, "soft": false},
	"holy_sparks": {"tex": "fx_spark", "add": true, "amount": 14, "life": 0.9, "speed": [1.5, 4.0], "spread": 180.0,
		"gravity": 1.2, "damp": 1.5, "size": [0.4, 0.06], "ramp": [Color(1, 1, 1, 1), Color(1, 0.88, 0.45, 0.8), Color(1, 0.8, 0.3, 0.0)],
		"fade_in": 0.0, "soft": false},
	"rise_sparks": {"tex": "fx_spark", "add": true, "amount": 16, "life": 1.1, "speed": [0.6, 1.6], "spread": 25.0,
		"gravity": 2.2, "size": [0.32, 0.06], "ramp": [Color(1, 1, 1, 1), Color(1, 1, 1, 0.0)], "ring": 1.0, "soft": false},
	"magic": {"tex": "fx_magic", "add": true, "amount": 2, "life": 0.5, "speed": [0.0, 0.3], "spread": 180.0,
		"gravity": 0.0, "size": [0.5, 1.6], "ramp": [Color(1, 1, 1, 0.9), Color(1, 1, 1, 0.0)], "spin": 300.0, "soft": false},
	"glow": {"tex": "fx_glow", "add": true, "amount": 1, "life": 0.35, "speed": [0.0, 0.0], "spread": 0.0,
		"gravity": 0.0, "size": [1.0, 1.8], "ramp": [Color(1, 1, 1, 0.8), Color(1, 1, 1, 0.0)], "fade_in": 0.0, "soft": false},
	"smite_ray": {"tex": "fx_ray", "add": true, "amount": 1, "life": 0.6, "speed": [0.0, 0.0], "spread": 0.0,
		"gravity": 0.0, "size": [1.8, 0.9], "tall": 5.0, "ramp": [Color(1, 1, 1, 1), Color(1, 0.9, 0.55, 0.9), Color(1, 0.85, 0.4, 0.0)],
		"look": "y", "fade_in": 0.05, "reach": 10.0},
	"rune": {"tex": "fx_rune", "add": true, "amount": 1, "life": 0.9, "speed": [0.0, 0.0], "spread": 0.0, "gravity": 0.0,
		"size": [1.2, 2.8], "ramp": [Color(1, 1, 1, 0.9), Color(1, 1, 1, 0.0)], "look": "flat", "spin": 70.0},
	"wisps": {"tex": "fx_wisp", "add": true, "amount": 4, "life": 1.3, "speed": [1.0, 2.0], "spread": 25.0,
		"gravity": 1.5, "size": [0.6, 1.0], "ramp": [Color(1, 1, 1, 0.9), Color(1, 1, 1, 0.0)], "radius": 0.4, "fade_in": 0.25},
	# ---- water and poison
	"splash": {"tex": "fx_splash", "add": true, "amount": 3, "life": 0.55, "speed": [0.5, 1.0], "spread": 60.0,
		"gravity": 0.0, "size": [0.9, 2.0], "ramp": [Color(0.9, 0.97, 1, 0.9), Color(0.6, 0.85, 1, 0.0)], "spin": 60.0, "fade_in": 0.05},
	"bubbles": {"tex": "fx_bubble", "amount": 8, "life": 1.0, "speed": [0.8, 2.0], "spread": 70.0, "gravity": 1.2,
		"damp": 1.0, "size": [0.22, 0.4], "ramp": [Color(1, 1, 1, 0.9), Color(1, 1, 1, 0.0)], "radius": 0.5, "soft": false},
}

static var _ok := -1
static var _proc := {}
static var _draw := {}


static func available() -> bool:
	if _ok == -1:
		_ok = 1 if (DisplayServer.get_name() != "headless" and ResourceLoader.exists(TEX + "fb_smoke.png")) else 0
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
	e.explosiveness = float(p.get("explode", 0.85))
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
	m.lifetime_randomness = 0.3
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
	# size over life: the quad (or chunk) is 1 unit, scaled from size[0] to size[1], each particle +-20%
	var s0 := float(p["size"][0])
	var s1 := float(p["size"][1])
	var top := maxf(s0, s1)
	m.scale_min = top * 0.8
	m.scale_max = top * 1.2
	var curve := Curve.new()
	curve.add_point(Vector2(0, s0 / top))
	curve.add_point(Vector2(1, s1 / top))
	var ct := CurveTexture.new()
	ct.curve = curve
	m.scale_curve = ct
	# colors over life, with a short fade-in so nothing pops, and a fade-out to nothing at the end
	var ramp: Array = p["ramp"]
	var fade_in := float(p.get("fade_in", 0.1))
	var offs := PackedFloat32Array()
	var cols := PackedColorArray()
	if fade_in > 0.0:
		var c0: Color = ramp[0]
		offs.append(0.0)
		cols.append(Color(c0.r * tint.r, c0.g * tint.g, c0.b * tint.b, 0.0))
	for i in ramp.size():
		var c: Color = ramp[i]
		offs.append(lerpf(fade_in, 0.8 if not p.has("mesh") else 1.0, float(i) / maxf(1.0, ramp.size() - 1)))
		cols.append(Color(c.r * tint.r, c.g * tint.g, c.b * tint.b, c.a * tint.a))
	if not p.has("mesh"):
		var cl: Color = cols[cols.size() - 1]
		offs.append(1.0)
		cols.append(Color(cl.r, cl.g, cl.b, 0.0))
	var g := Gradient.new()
	g.offsets = offs
	g.colors = cols
	var gt := GradientTexture1D.new()
	gt.gradient = g
	m.color_ramp = gt
	var spin := float(p.get("spin", 0.0))
	if spin > 0.0:
		m.angle_min = -180.0
		m.angle_max = 180.0
		m.angular_velocity_min = -spin
		m.angular_velocity_max = spin
	if String(p.get("tex", "")).begins_with("fb_"):
		# the flipbook plays once over each particle's life, starting a few frames in at random
		m.anim_speed_min = 1.0
		m.anim_speed_max = 1.0
		m.anim_offset_min = 0.0
		m.anim_offset_max = 0.08
	if String(p.get("look", "cam")) == "flat":
		m.particle_flag_rotate_y = true
	_proc[key] = m
	return m


static func _draw_mesh(preset: String) -> Mesh:
	if _draw.has(preset):
		return _draw[preset]
	var p: Dictionary = PRESETS[preset]
	if p.get("mesh", "") == "chunk":
		# a little faceted rock, lit like the rest of the world, colored by the particle's color
		var sm := SphereMesh.new()
		sm.radius = 0.5
		sm.height = 0.75
		sm.radial_segments = 5
		sm.rings = 3
		var rm := StandardMaterial3D.new()
		rm.vertex_color_use_as_albedo = true
		rm.roughness = 1.0
		sm.material = rm
		_draw[preset] = sm
		return sm
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
	mat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD if p.get("add", false) else BaseMaterial3D.BLEND_MODE_MIX
	mat.vertex_color_use_as_albedo = true
	mat.albedo_texture = load(TEX + String(p["tex"]) + ".png")
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.disable_receive_shadows = true
	if p.get("soft", true):
		# soft particles: fade out where they meet the ground or a model instead of cutting a hard line
		mat.proximity_fade_enabled = true
		mat.proximity_fade_distance = 0.6
	if String(p["tex"]).begins_with("fb_"):
		mat.particles_anim_h_frames = 8
		mat.particles_anim_v_frames = 8
		mat.particles_anim_loop = false
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
	play(parent, "death_smoke", pos, col.lerp(Color(0.9, 0.9, 0.88), 0.6), s)
	play(parent, "death_sparks", pos, col.lightened(0.3), s)


## A boulder, shell or bomb landing: a flash, a fireball rolling into smoke, flying stones and a ring of dust, sized
## by the splash radius (world units). Fiery ones throw embers too.
static func blast(parent: Node, pos: Vector3, splash: float, fiery := false) -> void:
	var s := clampf(splash / 2.4, 0.6, 2.2)
	play(parent, "flash", pos + Vector3(0, 0.5, 0), Color.WHITE, s)
	if fiery:
		play(parent, "blast_fire", pos + Vector3(0, 0.5, 0), Color.WHITE, s)
		play(parent, "embers", pos + Vector3(0, 0.4, 0), Color.WHITE, s)
	play(parent, "blast_debris", pos + Vector3(0, 0.2, 0), Color.WHITE, s)
	play(parent, "blast_smoke", pos + Vector3(0, 0.3, 0), Color.WHITE, s)
	play(parent, "dust_ring", pos + Vector3(0, 0.1, 0), Color.WHITE, s * 1.2)


static func poison(parent: Node, pos: Vector3, col: Color, splash: float) -> void:
	var s := clampf(splash / 2.4, 0.6, 1.8)
	play(parent, "poison_cloud", pos + Vector3(0, 0.4, 0), col.lerp(Color.WHITE, 0.25), s)
	play(parent, "bubbles", pos + Vector3(0, 0.2, 0), col.lightened(0.3), s)


## A slam, stomp or maul on the ground.
static func stomp(parent: Node, pos: Vector3, radius: float) -> void:
	var s := clampf(radius / 2.2, 0.5, 2.5)
	play(parent, "dust_ring", pos + Vector3(0, 0.1, 0), Color.WHITE, s * 1.3)
	play(parent, "ring_dust", pos + Vector3(0, 0.2, 0), Color.WHITE, s)
	play(parent, "dirt", pos + Vector3(0, 0.15, 0), Color.WHITE, s)


## The Fat Dragon's fire, from its mouth along dir for about length world units.
static func breath(parent: Node, mouth: Vector3, dir: Vector3, length: float) -> void:
	var s := clampf(length / 14.0, 0.5, 2.0)
	play(parent, "breath", mouth, Color.WHITE, s, dir)
	play(parent, "breath_smoke", mouth + Vector3(0, 0.5, 0), Color.WHITE, s, dir)
	play(parent, "glow", mouth, Color(1, 0.6, 0.2), 1.3)


static func smite(parent: Node, ground: Vector3, col: Color) -> void:
	play(parent, "smite_ray", ground, Color.WHITE, 1.0)
	play(parent, "flash", ground + Vector3(0, 0.8, 0), Color(1, 0.95, 0.75), 1.0)
	play(parent, "holy_sparks", ground + Vector3(0, 0.6, 0), Color.WHITE, 1.0)
	play(parent, "rune", ground + Vector3(0, 0.12, 0), col, 1.0)


static func splash(parent: Node, pos: Vector3, col: Color) -> void:
	play(parent, "splash", pos, col.lerp(Color.WHITE, 0.5), 1.0)
	play(parent, "bubbles", pos, col.lerp(Color.WHITE, 0.6), 0.8)


static func raise(parent: Node, ground: Vector3) -> void:
	var green := Color(0.55, 1.0, 0.45)
	play(parent, "rune", ground + Vector3(0, 0.12, 0), green, 0.8)
	play(parent, "wisps", ground + Vector3(0, 0.3, 0), green, 1.0)
	play(parent, "dirt", ground + Vector3(0, 0.15, 0), Color.WHITE, 0.8)


static func crumble(parent: Node, pos: Vector3) -> void:
	play(parent, "bones", pos + Vector3(0, 0.5, 0), Color.WHITE, 1.0)
	play(parent, "death_smoke", pos + Vector3(0, 0.3, 0), Color(0.78, 0.85, 0.7), 0.8)


static func magic_hit(parent: Node, pos: Vector3, col: Color, big := false) -> void:
	play(parent, "magic", pos, col.lerp(Color.WHITE, 0.3), 1.4 if big else 1.0)
	play(parent, "glow", pos, col, 1.2 if big else 0.8)
	play(parent, "sparks", pos, col.lerp(Color.WHITE, 0.4), 1.0)


static func build(parent: Node, center: Vector3, cells: int) -> void:
	var s := sqrt(float(cells))
	play(parent, "ring_dust", center + Vector3(0, 0.2, 0), Color.WHITE, s)
	play(parent, "dust_ring", center + Vector3(0, 0.1, 0), Color.WHITE, s * 1.2)


static func upgrade(parent: Node, center: Vector3, col: Color, cells: int) -> void:
	var s := sqrt(float(cells))
	play(parent, "rise_sparks", center + Vector3(0, 0.2, 0), col.lerp(Color(1, 0.9, 0.5), 0.5), s)
	play(parent, "rune", center + Vector3(0, 0.12, 0), Color(1, 0.85, 0.4), s * 1.1)
