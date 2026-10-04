class_name UiSkin
extends RefCounted
## The HUD's look, built from Kenney's UI Pack: RPG Expansion (CC0, assets/ui/kenney_rpg): wooden frames with nails,
## parchment insets and stone buttons, as nine-slice StyleBoxTextures. The light grey and light beige pieces are tinted
## (StyleBoxTexture.modulate_color), so a button keeps its meaning (slate when idle, warm wood when hovered, gold when
## live, a faction's own color on its cards) while keeping the pack's shapes and shading. Hud falls back to its flat
## styles when the files are missing or the game runs with --no-kenney.

const RPG := "res://assets/ui/kenney_rpg/"

static var enabled := true
static var _tex := {}
static var _boxes := {}

## Idle stone, hovered wood, "live" gold (selected, placing, affordable highlights) and dimmed.
const SLATE := Color(0.44, 0.45, 0.52)
const WOOD := Color(1.0, 1.0, 1.0)
const LIVE := Color(0.6, 0.5, 0.2)
const DIM := Color(0.34, 0.34, 0.38, 0.9)
## The wood a shade darker than the pack's, so gold, red and blue text stand out on it.
const PANEL := Color(0.8, 0.77, 0.75)
## Dark text for parchment (tooltips).
const INK := Color(0.24, 0.16, 0.09)


static func available() -> bool:
	return enabled and ResourceLoader.exists(RPG + "panel_brown.png")


static func tex(file: String) -> Texture2D:
	if not _tex.has(file):
		_tex[file] = load(RPG + file + ".png") if ResourceLoader.exists(RPG + file + ".png") else null
	return _tex[file]


## A nine-slice box. m: texture margins [left, top, right, bottom] in texture pixels (corners and edges that don't
## stretch); pad: content margins [left, top, right, bottom].
static func box(file: String, m: Array, pad: Array, tint := Color.WHITE, expand_top := 0.0) -> StyleBoxTexture:
	var key := "%s|%s|%s|%s|%.1f" % [file, m, pad, tint.to_html(), expand_top]
	if not _boxes.has(key):
		var s := StyleBoxTexture.new()
		s.texture = tex(file)
		s.texture_margin_left = m[0]
		s.texture_margin_top = m[1]
		s.texture_margin_right = m[2]
		s.texture_margin_bottom = m[3]
		s.content_margin_left = pad[0]
		s.content_margin_top = pad[1]
		s.content_margin_right = pad[2]
		s.content_margin_bottom = pad[3]
		s.modulate_color = tint
		s.expand_margin_top = expand_top
		_boxes[key] = s
	return _boxes[key]


## The wooden frame (top bar, build bar, side panels, menus).
static func panel(pad := 14.0) -> StyleBoxTexture:
	return box("panel_brown", [12, 12, 12, 12], [pad, pad * 0.8, pad, pad * 0.8], PANEL)


## A darker sunken wooden board, for panels that sit on other panels or over busy views.
static func inset(pad := 12.0) -> StyleBoxTexture:
	return box("panelInset_brown", [10, 10, 10, 10], [pad, pad * 0.8, pad, pad * 0.8], PANEL.darkened(0.2))


## Parchment (tooltips): pair with INK text.
static func parchment(pad := 10.0) -> StyleBoxTexture:
	return box("panelInset_beige", [10, 10, 10, 10], [pad, pad * 0.7, pad, pad * 0.7])


## A wooden-framed card washed in a color (faction, hero, reward and talent cards). strength: how much of the color
## shows (the rest is dark wood), so idle cards stay dim and hovered ones light up.
static func card(col: Color, strength := 0.45, pad := 12.0) -> StyleBoxTexture:
	var tint := Color(0.3, 0.24, 0.18).lerp(col, strength)
	var lum := tint.get_luminance()
	if lum > 0.42:   # pale colors (white, gold) would wash out the light text on top
		tint = Color(tint.r * 0.42 / lum, tint.g * 0.42 / lum, tint.b * 0.42 / lum, tint.a)
	return box("panel_beigeLight", [12, 12, 12, 12], [pad, pad, pad, pad], tint)


## Long stone buttons. state: normal / hover / pressed / disabled / live.
static func button(state: String) -> StyleBoxTexture:
	match state:
		"hover":
			return box("buttonLong_brown", [10, 8, 10, 12], [11, 6, 11, 10], WOOD)
		"pressed":
			return box("buttonLong_brown_pressed", [10, 8, 10, 8], [11, 9, 11, 7], Color(0.85, 0.82, 0.8), -4.0)
		"disabled":
			return box("buttonLong_grey", [10, 8, 10, 12], [11, 6, 11, 10], DIM)
		"live":
			return box("buttonLong_grey", [10, 8, 10, 12], [11, 6, 11, 10], LIVE)
	return box("buttonLong_grey", [10, 8, 10, 12], [11, 6, 11, 10], SLATE)


## Square stone cards (build bar). Same states as button().
static func square(state: String) -> StyleBoxTexture:
	match state:
		"hover":
			return box("buttonSquare_brown", [10, 8, 10, 12], [8, 6, 8, 10], WOOD)
		"pressed":
			return box("buttonSquare_brown_pressed", [10, 8, 10, 8], [8, 9, 8, 7], Color(0.85, 0.82, 0.8), -4.0)
		"disabled":
			return box("buttonSquare_grey", [10, 8, 10, 12], [8, 6, 8, 10], DIM)
		"live":
			return box("buttonSquare_grey", [10, 8, 10, 12], [8, 6, 8, 10], LIVE)
	return box("buttonSquare_grey", [10, 8, 10, 12], [8, 6, 8, 10], SLATE)


## The pack's gauntlet pointer as the mouse cursor (hotspot at the fingertip).
static func apply_cursor() -> void:
	var t := tex("cursorGauntlet_grey")
	if t:
		Input.set_custom_mouse_cursor(t, Input.CURSOR_ARROW, Vector2(3, 2))
