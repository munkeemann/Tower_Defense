class_name KayKit
extends RefCounted
## KayKit assets (Kay Lousberg, CC0): characters on the shared Rig_Medium / Rig_Large skeletons, the animation
## libraries that drive them, and the Medieval Hexagon pack (tiles, buildings, units, decoration).
## Files live in assets/kaykit: chars/, anims/, hex/, gear/ (see assets/CREDITS.md).

const ROOT := "res://assets/kaykit/"
const CHARS := ROOT + "chars/"
const ANIMS := ROOT + "anims/"
const HEX := ROOT + "hex/"
const GEAR := ROOT + "gear/"

## Animation files merged into one library per rig (the T-Pose clips are skipped).
const LIB_FILES := {
	"Medium": ["MovementBasic", "General", "CombatMelee", "CombatRanged", "Special", "Simulation", "Tools"],
	"Large": ["MovementBasic", "General", "CombatMelee", "Special"],
}
## Clips that loop (everything else plays once).
const LOOPING := ["Walking", "Running", "Idle", "Aiming", "Blocking", "Spellcasting", "Shooting", "Skeletons_Walking",
	"Skeletons_Idle", "Melee_2H_Idle", "Melee_Unarmed_Idle"]

## KayKit team color for each of your colors (buildings and the castle come in blue, green, red and yellow).
const TEAM := {"crown": "yellow", "verdant": "green", "forge": "red", "tide": "blue", "grave": "blue"}

static var enabled := true   # false: everything uses its pre-KayKit models (the --no-kaykit test flag)
static var _libs := {}
static var _heights := {}
static var _scenes := {}


static func available() -> bool:
	return enabled and ResourceLoader.exists(ANIMS + "Rig_Medium_MovementBasic.glb")


static func scene(path: String) -> PackedScene:
	if not _scenes.has(path):
		_scenes[path] = load(path) if ResourceLoader.exists(path) else null
	return _scenes[path]


## One AnimationLibrary per rig with every clip from LIB_FILES, shared by all characters on that rig.
static func library(rig: String) -> AnimationLibrary:
	if _libs.has(rig):
		return _libs[rig]
	var lib := AnimationLibrary.new()
	for part in LIB_FILES[rig]:
		var ps := scene(ANIMS + "Rig_%s_%s.glb" % [rig, part])
		if ps == null:
			continue
		var n := ps.instantiate()
		var ap := n.find_child("AnimationPlayer", true, false) as AnimationPlayer
		if ap:
			for an in ap.get_animation_list():
				if an == "T-Pose" or lib.has_animation(an):
					continue
				var a := ap.get_animation(an)
				var loop := false
				for k in LOOPING:
					if String(an).contains(k):
						loop = true
				a.loop_mode = Animation.LOOP_LINEAR if loop else Animation.LOOP_NONE
				lib.add_animation(an, a)
		n.free()
	_libs[rig] = lib
	return lib


## Height of a character file in its own units (measured once).
static func _height(file: String) -> float:
	if not _heights.has(file):
		var n := scene(CHARS + file).instantiate() as Node3D
		_heights[file] = maxf(Models._local_aabb(n).size.y, 0.1)
		n.free()
	return _heights[file]


## A character `height` world units tall, facing -Z, with an AnimationPlayer holding its rig's library (the rig,
## Medium or Large, is read from the file). Returns {"root", "body", "anim", "rig", "model"}; play clips by name
## (e.g. "Walking_A", "Death_A", "Ranged_Bow_Release"), or use clip() to fall back when a rig lacks one.
static func character(file: String, _rig_hint: String, height: float) -> Dictionary:
	var root := Node3D.new()
	var body := Node3D.new()
	root.add_child(body)
	var ps := scene(CHARS + file)
	if ps == null:
		return {}
	var model := ps.instantiate() as Node3D
	var rig := "Large" if model.has_node("Rig_Large") else "Medium"
	model.scale = Vector3.ONE * height / _height(file)
	model.rotation_degrees.y = 180.0
	body.add_child(model)
	var ap := AnimationPlayer.new()
	model.add_child(ap)
	ap.root_node = NodePath("..")
	ap.add_animation_library("", library(rig))
	return {"root": root, "body": body, "anim": ap, "rig": rig, "model": model}


## The first of `wanted` this player has, else the closest stand-in (Rig_Large has fewer clips).
static func clip(ap: AnimationPlayer, wanted: Array) -> String:
	for w in wanted:
		if ap.has_animation(w):
			return w
	for w in wanted:
		var base := String(w).split("_")[0]   # Walking_C -> Walking, Death_B -> Death ...
		for an in ap.get_animation_list():
			if String(an).begins_with(base):
				return an
	return ""


## A hex-pack model instance (tiles, buildings, units, decoration), or null.
static func hex(name: String) -> Node3D:
	var ps := scene(HEX + name + ".gltf")
	return ps.instantiate() as Node3D if ps else null


static var _meshes := {}


## The single mesh of a hex-pack model and its transform inside the file (for MultiMesh use).
static func hex_mesh(name: String) -> Array:
	if _meshes.has(name):
		return _meshes[name]
	var out: Array = [null, Transform3D()]
	var n := hex(name)
	if n:
		for c in n.find_children("*", "MeshInstance3D", true, false):
			var xf := Transform3D()
			var p: Node = c
			while p != null and p != n:
				if p is Node3D:
					xf = (p as Node3D).transform * xf
				p = p.get_parent()
			out = [(c as MeshInstance3D).mesh, xf]
			break
		n.free()
	_meshes[name] = out
	return out


static var _skins := {}


## Gives a character another of its pack's textures (e.g. "orc_texture_B.png" in assets/kaykit/chars).
static func reskin(ch: Dictionary, texture_file: String) -> void:
	var model: Node = ch.get("model")
	if model == null or not ResourceLoader.exists(CHARS + texture_file):
		return
	var tex: Texture2D = load(CHARS + texture_file)
	for node in model.find_children("*", "MeshInstance3D", true, false):
		var mi := node as MeshInstance3D
		for s in mi.mesh.get_surface_count():
			var base := mi.mesh.surface_get_material(s) as BaseMaterial3D
			if base == null:
				continue
			var key := "%d|%s" % [base.get_instance_id(), texture_file]
			if not _skins.has(key):
				var m := base.duplicate() as BaseMaterial3D
				m.albedo_texture = tex
				_skins[key] = m
			mi.set_surface_override_material(s, _skins[key])


## Puts a gear model (assets/kaykit/gear, e.g. "bow_withString", "staff", "Orc_Axe") in a character's hand ("r" or "l").
static func hold(ch: Dictionary, gear: String, hand := "r") -> Node3D:
	var model: Node = ch.get("model")
	if model == null:
		return null
	var skel := model.find_child("Skeleton3D", true, false) as Skeleton3D
	var ps := scene(GEAR + gear + ".gltf")
	if ps == null:
		ps = scene(GEAR + gear + ".glb")
	if skel == null or ps == null:
		return null
	var at := BoneAttachment3D.new()
	at.bone_name = "handslot." + hand
	skel.add_child(at)
	var g := ps.instantiate() as Node3D
	at.add_child(g)
	return g


## Any KayKit model by its path under assets/kaykit without the extension ("hex/well", "forest/Tree_1_A_Color1").
static func model(path: String) -> Node3D:
	var ps := scene(ROOT + path + ".gltf")
	return ps.instantiate() as Node3D if ps else null


## Height of `node`'s highest surface straight above point (x, z) of its parent's space, or 0 if it doesn't cover it.
## Lets pieces and crews stand on top of buildings (tower floors, rooftops) without hand-measured heights.
static func top_at(node: Node3D, x: float, z: float) -> float:
	var best := 0.0
	for c in node.find_children("*", "MeshInstance3D", true, false):
		var mi := c as MeshInstance3D
		if mi.mesh == null:
			continue
		var xf := Transform3D()
		var p: Node = mi
		while p != null and p != node.get_parent():
			if p is Node3D:
				xf = (p as Node3D).transform * xf
			p = p.get_parent()
		var box := xf * mi.mesh.get_aabb()
		if x < box.position.x or x > box.end.x or z < box.position.z or z > box.end.z or box.end.y <= best:
			continue
		var f := mi.mesh.get_faces()
		for i in range(0, f.size() - 2, 3):
			var a := xf * f[i]
			var b := xf * f[i + 1]
			var d := xf * f[i + 2]
			var den := (b.z - d.z) * (a.x - d.x) + (d.x - b.x) * (a.z - d.z)
			if absf(den) < 1e-9:
				continue
			var w0 := ((b.z - d.z) * (x - d.x) + (d.x - b.x) * (z - d.z)) / den
			var w1 := ((d.z - a.z) * (x - d.x) + (a.x - d.x) * (z - d.z)) / den
			var w2 := 1.0 - w0 - w1
			if w0 >= 0.0 and w1 >= 0.0 and w2 >= 0.0:
				best = maxf(best, w0 * a.y + w1 * b.y + w2 * d.y)
	return best
