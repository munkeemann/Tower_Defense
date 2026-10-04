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
	"Medium": ["MovementBasic", "General", "CombatMelee", "CombatRanged", "Special"],
	"Large": ["MovementBasic", "General", "CombatMelee", "Special"],
}
## Clips that loop (everything else plays once).
const LOOPING := ["Walking", "Running", "Idle", "Aiming", "Blocking", "Spellcasting", "Shooting", "Skeletons_Walking",
	"Skeletons_Idle", "Melee_2H_Idle", "Melee_Unarmed_Idle"]

static var _libs := {}
static var _heights := {}
static var _scenes := {}


static func available() -> bool:
	return ResourceLoader.exists(ANIMS + "Rig_Medium_MovementBasic.glb")


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
