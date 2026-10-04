class_name Hud
extends CanvasLayer
## All 2D UI, built in code. Talks to the Game through direct method calls.

var game: Game
var root: Control

var top_wave: Label
var top_hp: Label
var top_gold: Label
var top_phase: Label
var top_recon: Label
var top_fronts: Label
var speed_btn: Button
var pause_btn: Button
var mute_btn: Button
var intel_panel: PanelContainer
var dmg_panel: PanelContainer         # the damage chart (top right)
var dmg_rows: Array = []              # [row, name label, bar fill, value label] per shown tower
var dmg_toggle: Button
var dmg_mode := 0                     # 0 shown, 1 see-through, 2 hidden (K or its button cycles)
var _dmg_t := 0.0
const DMG_ROWS := 10
const DMG_BAR_W := 96.0
var intel_box: VBoxContainer
var hint_panel: PanelContainer
var hint_lbl: Label

var build_bar: PanelContainer
var build_box: HBoxContainer
var tower_buttons := {}   # id -> Button
var raise_btn: Button
var dig_btn: Button
var castle_btn: Button
var tile_panel: PanelContainer
var tile_title_lbl: Label
var tile_reroll: Button
var castle_root: PanelContainer
var castle_detail: Label
var _castle_btns: Array = []   # [Button, path, index]
var choice_detail: PanelContainer
var choice_detail_box: HBoxContainer

var start_panel: PanelContainer
var start_btn: Button
var preview_lbl: Label

var ability_btn: Button
var help_panel: PanelContainer

var info_panel: PanelContainer
var info_title: Label
var info_body: Label
var info_upgrade: Button
var info_specs: Array = []
var info_target: Button
var info_sell: Button

var choice_root: Control
var choice_title: Label
var choice_sub: Label
var choice_row: HBoxContainer
var choice_skip: Button
var choice_extra: Button

var toast_lbl: Label
var pause_lbl: Label
var menu_root: Control
var end_root: Control

const GOLD_C := Color(1.0, 0.84, 0.35)
const HP_C := Color(1.0, 0.45, 0.4)
const TEXT_C := Color(0.93, 0.9, 0.85)
const DIM_C := Color(0.65, 0.62, 0.6)
const RECON_C := Color(0.55, 0.85, 1.0)

var kenney := false   # Kenney RPG skin (UiSkin) instead of the flat dark styles


func setup(g: Game) -> void:
	game = g
	layer = 10
	if "--no-kenney" in OS.get_cmdline_user_args():
		UiSkin.enabled = false
	kenney = UiSkin.available()
	if kenney and DisplayServer.get_name() != "headless":
		UiSkin.apply_cursor()
	process_mode = Node.PROCESS_MODE_ALWAYS
	root = Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.theme = _make_theme()
	add_child(root)
	_build_top()
	_build_bottom()
	_build_info()
	_build_choices()
	_build_misc()
	_build_intel()
	_build_damage()
	_build_hint()
	set_game_ui_visible(false)


# ------------------------------------------------------------------ theme & helpers

func _sb(bg: Color, border := Color(0, 0, 0, 0), bw := 0, radius := 8, pad := 10, skew := 0.0) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = bg
	s.border_color = border
	s.set_border_width_all(bw)
	s.set_corner_radius_all(radius)
	if skew != 0.0:
		s.skew = Vector2(skew, 0.0)
		s.expand_margin_left = 4.0
		s.expand_margin_right = 4.0
	s.content_margin_left = pad
	s.content_margin_right = pad
	s.content_margin_top = pad * 0.6
	s.content_margin_bottom = pad * 0.6
	return s


## A colored card (faction, hero, reward, talent): Kenney's wood-framed card washed in col (strength: how lit it is),
## or the flat dark card with a col border.
func _card_box(col: Color, strength: float, bg: Color, border: Color, bw: int, radius: int) -> StyleBox:
	if kenney:
		return UiSkin.card(col, strength)
	return _sb(bg, border, bw, radius)


## A panel: Kenney's wooden frame (or its sunken board), or the flat dark panel.
func _panel_box(pad: float, bg: Color, border: Color, bw: int, radius: int, flat_pad: int, sunken := false) -> StyleBox:
	if kenney:
		return UiSkin.inset(pad) if sunken else UiSkin.panel(pad)
	return _sb(bg, border, bw, radius, flat_pad)


## Fonts: Windows' own Bahnschrift (a condensed DIN-style face, loaded from the system rather than bundled),
## semibold for text and a bold slanted cut for titles and numbers. Falls back to Godot's font elsewhere.
var body_font: Font
var title_font: Font


func _make_fonts() -> void:
	var sf := SystemFont.new()
	sf.font_names = PackedStringArray(["Bahnschrift"])
	var b := FontVariation.new()
	b.base_font = sf
	b.variation_opentype = {"wght": 560, "wdth": 88}
	body_font = b
	var t := FontVariation.new()
	t.base_font = sf
	t.variation_opentype = {"wght": 700, "wdth": 75}
	t.variation_transform = Transform2D(Vector2(1, 0), Vector2(0.2, 1), Vector2.ZERO)   # italic slant
	t.spacing_glyph = 1
	title_font = t


## A label in the bold slanted title face.
func _title(text: String, size := 22, color := TEXT_C) -> Label:
	var l := _label(text, size, color)
	l.add_theme_font_override("font", title_font)
	return l


func _make_theme() -> Theme:
	_make_fonts()
	var t := Theme.new()
	t.default_font = body_font
	t.default_font_size = 16
	if kenney:
		# Kenney RPG: wooden frames, slate stone buttons that warm to wood when hovered, parchment tooltips
		t.set_stylebox("panel", "PanelContainer", UiSkin.panel())
		for st in ["normal", "hover", "pressed", "disabled"]:
			t.set_stylebox(st, "Button", UiSkin.button(st))
		t.set_stylebox("hover_pressed", "Button", UiSkin.button("pressed"))
		t.set_color("font_pressed_color", "Button", Color(1, 0.95, 0.8))
		t.set_color("font_hover_pressed_color", "Button", Color(1, 0.95, 0.8))
	else:
		# Tower Dominion-style chrome: near-black panels, slanted buttons, yellow for anything live
		t.set_stylebox("panel", "PanelContainer", _sb(Color(0.03, 0.03, 0.04, 0.86), Color(0, 0, 0, 0), 0, 4))
		t.set_stylebox("normal", "Button", _sb(Color(0.06, 0.06, 0.07, 0.94), Color(1, 1, 1, 0.14), 1, 3, 10, -0.18))
		t.set_stylebox("hover", "Button", _sb(Color(0.12, 0.11, 0.09, 0.97), GOLD_C, 2, 3, 10, -0.18))
		t.set_stylebox("pressed", "Button", _sb(Color(0.3, 0.24, 0.08, 0.97), GOLD_C, 2, 3, 10, -0.18))
		t.set_stylebox("disabled", "Button", _sb(Color(0.05, 0.05, 0.06, 0.8), Color(1, 1, 1, 0.06), 1, 3, 10, -0.18))
	t.set_stylebox("focus", "Button", StyleBoxEmpty.new())
	t.set_color("font_color", "Button", TEXT_C)
	t.set_color("font_hover_color", "Button", Color(1, 1, 1))
	t.set_color("font_disabled_color", "Button", Color(0.5, 0.48, 0.46))
	t.set_color("font_color", "Label", TEXT_C)
	t.set_color("font_outline_color", "Label", Color(0.02, 0.01, 0.03, 0.85))
	t.set_constant("outline_size", "Label", 3 if kenney else 0)   # keeps light text crisp on the wood
	if kenney:
		t.set_color("font_outline_color", "Button", Color(0.08, 0.05, 0.03, 0.7))
		t.set_constant("outline_size", "Button", 3)
		t.set_stylebox("panel", "TooltipPanel", UiSkin.parchment())
		t.set_color("font_color", "TooltipLabel", UiSkin.INK)
	else:
		t.set_stylebox("panel", "TooltipPanel", _sb(Color(0.02, 0.02, 0.03, 0.96), Color(1, 1, 1, 0.12), 1, 3))
		t.set_color("font_color", "TooltipLabel", TEXT_C)
	return t


func _label(text: String, size := 16, color := TEXT_C) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


func _wrap_label(text: String, width: float, size := 15, color := TEXT_C) -> Label:
	var l := _label(text, size, color)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size = Vector2(width, 0)
	return l


func _button(text: String, cb: Callable, size := 16) -> Button:
	var b := Button.new()
	b.text = text
	b.add_theme_font_size_override("font_size", size)
	b.pressed.connect(cb)
	b.pressed.connect(func(): game.sfx("click"))
	b.focus_mode = Control.FOCUS_NONE
	return b


func _ignore_all(c: Control) -> void:
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	for ch in c.get_children():
		if ch is Control:
			_ignore_all(ch)


# ------------------------------------------------------------------ top bar

func _build_top() -> void:
	var p := PanelContainer.new()
	p.set_anchors_preset(Control.PRESET_TOP_WIDE)
	p.offset_left = 10
	p.offset_right = -10
	p.offset_top = 8
	root.add_child(p)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 18 if kenney else 28)
	p.add_child(h)
	top_wave = _title("Wave 0/30", 23)
	top_hp = _title("Castle 20/20", 23, HP_C)
	top_gold = _title("Gold 0", 23, GOLD_C)
	top_recon = _title("Runes 0", 23, RECON_C)
	top_recon.mouse_filter = Control.MOUSE_FILTER_PASS
	top_recon.tooltip_text = "Runes: cast them to reroll the tile or the rewards you're offered.\n+1 after every wave, +1 more for each extra battlefront (up to +3)."
	top_fronts = _title("Fronts 1", 23, Color(0.85, 0.55, 1.0))
	top_fronts.mouse_filter = Control.MOUSE_FILTER_PASS
	top_fronts.tooltip_text = "Battlefronts: every open road end is an enemy entry point.\nMerge roads to close them; forks open more."
	top_phase = _label("", 18, DIM_C)
	top_phase.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top_phase.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	top_phase.clip_text = true   # long phase lines trim instead of pushing the buttons off screen
	top_phase.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	for l in [top_wave, top_hp, top_gold, top_recon, top_fronts, top_phase]:
		h.add_child(l)
	speed_btn = _button("Speed 1x [V]", func(): game.cycle_speed())
	pause_btn = _button("Pause [P]", func(): game.toggle_pause())
	mute_btn = _button("Sound [M]", func(): game.toggle_mute())
	var help_btn := _button("Help [H]", func(): help_panel.visible = not help_panel.visible)
	var menu_btn := _button("Menu", func(): game.open_menu())
	for b in [speed_btn, pause_btn, mute_btn, help_btn, menu_btn]:
		h.add_child(b)


# ------------------------------------------------------------------ bottom (build bar, start, ability)

func _build_bottom() -> void:
	build_bar = PanelContainer.new()
	build_bar.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	build_bar.grow_horizontal = Control.GROW_DIRECTION_BOTH
	build_bar.grow_vertical = Control.GROW_DIRECTION_BEGIN
	build_bar.offset_bottom = -8
	root.add_child(build_bar)
	build_box = HBoxContainer.new()
	build_box.add_theme_constant_override("separation", 6)
	build_bar.add_child(build_box)

	start_panel = PanelContainer.new()
	start_panel.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	start_panel.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	start_panel.grow_vertical = Control.GROW_DIRECTION_BEGIN
	start_panel.offset_right = -10
	start_panel.offset_bottom = -118
	root.add_child(start_panel)
	var v := VBoxContainer.new()
	start_panel.add_child(v)
	v.add_child(_label("Next wave", 14, DIM_C))
	preview_lbl = _wrap_label("", 260, 14)
	v.add_child(preview_lbl)
	start_btn = _button("Start Wave  [Space]", func(): game.start_wave(), 20)
	start_btn.custom_minimum_size = Vector2(260, 48)
	v.add_child(start_btn)

	# the commander's signature passive: its name and what it's doing now (click for the details)
	ability_btn = _button("", func(): toast(String(game.sig.get("desc", "")), GOLD_C), 15)
	ability_btn.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	ability_btn.grow_vertical = Control.GROW_DIRECTION_BEGIN
	ability_btn.offset_left = 10
	ability_btn.offset_bottom = -10
	ability_btn.custom_minimum_size = Vector2(196, 58)
	root.add_child(ability_btn)

	help_panel = PanelContainer.new()
	help_panel.set_anchors_preset(Control.PRESET_BOTTOM_LEFT)
	help_panel.grow_vertical = Control.GROW_DIRECTION_BEGIN
	help_panel.offset_left = 10
	help_panel.offset_bottom = -132
	root.add_child(help_panel)
	help_panel.add_child(_label(
		"WASD / right-drag: camera   Wheel: zoom   Q/E: rotate\n" +
		"Before each wave: place a hex tile on a glowing spot\n" +
		"  (R / Shift+R turn it; touching sides must match)\n" +
		"Every open road end is an enemy entry point:\n" +
		"  merge roads to close them, forks open more\n" +
		"1-9: build on your tiles (uses a blueprint copy)\n" +
		"  R / Shift+R turn the tower: big ones fill several hexes\n" +
		"Click tower: select   U: upgrade   X: sell   T: target\n" +
		"Level III: choose a specialization\n" +
		"F: ability   B: Builder (raise)   N: Digger (lower)\n" +
		"C: castle talents (spend gold on long-term upgrades)\n" +
		"Space: start wave   V: speed   P: pause   M: sound\n" +
		"Esc / right-click: cancel   F11: fullscreen   H: hide this", 13, DIM_C))
	help_panel.visible = false   # out of the way until H


func build_tower_bar() -> void:
	for c in build_box.get_children():
		c.queue_free()
	tower_buttons.clear()
	var i := 0
	for tid in game.bar_towers():
		i += 1
		var d: Dictionary = GameData.TOWERS[tid]
		var b := Button.new()
		b.focus_mode = Control.FOCUS_NONE
		b.custom_minimum_size = Vector2(124, 96)
		b.clip_text = true
		b.vertical_icon_alignment = VERTICAL_ALIGNMENT_TOP
		b.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
		b.add_theme_constant_override("icon_max_width", 46)
		b.add_theme_font_size_override("font_size", 13)
		b.pressed.connect(game.begin_placing.bind(tid))
		_card_style(b)
		b.add_child(_stripe(d["color"]))
		b.set_meta("hotkey", i)
		build_box.add_child(b)
		tower_buttons[tid] = b
	raise_btn = _item_button("builder", game.begin_raise, Color(0.62, 0.47, 0.33),
		("Builders (B)\nPut up scaffolding to raise a hex, or a whole tower, by one level (max %d).\n" +
		"Each level of high ground gives a tower +%d%% range.\nHold Shift to keep building.\nEarn more from wave rewards.") % [
		Board.MAX_LEVEL, int(GameData.ELEVATION_RANGE * 100)])
	dig_btn = _item_button("digger", game.begin_dig, Color(0.5, 0.4, 0.3),
		"Diggers (N)\nLower a raised hex, or a whole tower, by one level.\nUseful for flattening ground so big towers fit.")
	castle_btn = _item_button("castle", toggle_castle, GOLD_C,
		"Castle (C)\nSpend gold on talent paths: more income, stronger or cheaper towers,\nextra damage against the threats coming, or castle defenses.")
	refresh_tower_bar()


var _card_sb: StyleBox


func _card_normal() -> StyleBox:
	if _card_sb == null:
		_card_sb = UiSkin.square("normal") if kenney else _sb(Color(0.05, 0.05, 0.06, 0.94), Color(1, 1, 1, 0.12), 1, 4)
	return _card_sb


## The card style of whatever you're placing right now.
func _card_live() -> StyleBox:
	return UiSkin.square("live") if kenney else _sb(Color(0.3, 0.25, 0.15), GOLD_C, 2, 6)


## Build-bar cards: square stone (dark and square in the flat look), lit when hovered.
func _card_style(b: Button) -> void:
	b.add_theme_stylebox_override("normal", _card_normal())
	if kenney:
		for st in ["hover", "pressed", "disabled"]:
			b.add_theme_stylebox_override(st, UiSkin.square(st))
		return
	b.add_theme_stylebox_override("hover", _sb(Color(0.11, 0.1, 0.08, 0.97), GOLD_C, 2, 4))
	b.add_theme_stylebox_override("pressed", _sb(Color(0.3, 0.24, 0.08, 0.97), GOLD_C, 2, 4))
	b.add_theme_stylebox_override("disabled", _sb(Color(0.04, 0.04, 0.05, 0.8), Color(1, 1, 1, 0.05), 1, 4))


func _stripe(col: Color) -> ColorRect:
	var stripe := ColorRect.new()
	stripe.color = col
	stripe.set_anchors_preset(Control.PRESET_LEFT_WIDE)
	stripe.offset_right = 5
	stripe.offset_top = 4
	stripe.offset_bottom = -4
	stripe.offset_left = 3
	stripe.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return stripe


func _item_button(kind: String, cb: Callable, col: Color, tip: String) -> Button:
	var b := Button.new()
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size = Vector2(96, 96)
	b.add_theme_font_size_override("font_size", 13)
	b.pressed.connect(cb)
	b.tooltip_text = tip
	_card_style(b)
	b.add_child(_stripe(col))
	var ic := ItemIcon.new()
	ic.kind = kind
	ic.set_anchors_preset(Control.PRESET_CENTER_TOP)
	ic.offset_left = -22
	ic.offset_right = 22
	ic.offset_top = 6
	ic.offset_bottom = 50
	ic.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(ic)
	build_box.add_child(b)
	return b


func refresh_tower_bar() -> void:
	for it in [[raise_btn, "Builders [B]", game.builders, Game.RAISE], [dig_btn, "Diggers [N]", game.diggers, Game.DIG]]:
		var ib: Button = it[0]
		if ib == null or not is_instance_valid(ib):
			continue
		ib.text = "\n\n%s\nx%d" % [it[1], it[2]]
		ib.disabled = int(it[2]) <= 0
		ib.modulate = Color(1, 1, 1) if int(it[2]) > 0 else Color(0.6, 0.6, 0.6)
		if game.placing == it[3]:
			ib.add_theme_stylebox_override("normal", _card_live())
		else:
			ib.add_theme_stylebox_override("normal", _card_normal())
	if castle_btn and is_instance_valid(castle_btn):
		castle_btn.text = "\n\nCastle [C]\n%d talents" % game.talents.size() if game.talents.size() > 0 else "\n\nCastle [C]\ntalents"
	_fill_pending_thumbs()
	for tid in tower_buttons:
		var b: Button = tower_buttons[tid]
		if b.icon == null:
			b.icon = game.thumbs.get_thumb(tid)
		var d: Dictionary = GameData.TOWERS[tid]
		var copies := int(game.owned.get(tid, 0))
		var owned: bool = copies > 0
		var cost := game.tower_cost(tid)
		var hk: int = b.get_meta("hotkey")
		if owned:
			b.text = "%d  %s\n%d gold   x%d" % [hk, d["name"], cost, copies]
			b.disabled = game.gold < cost
			b.tooltip_text = tower_tooltip(tid) + "\n\n%d blueprint cop%s left to build." % [copies, "y" if copies == 1 else "ies"]
		else:
			b.text = "%d  %s\n%s" % [hk, d["name"], "No copies" if game.owned.has(tid) else "No blueprint"]
			b.disabled = true
			b.tooltip_text = tower_tooltip(tid) + "\n\nDraft this blueprint after a wave to build more."
		b.modulate = Color(1, 1, 1) if owned else Color(0.55, 0.55, 0.55)
		if game.placing == tid:
			b.add_theme_stylebox_override("normal", _card_live())
		else:
			b.add_theme_stylebox_override("normal", _card_normal())


func tower_tooltip(tid: String) -> String:
	var d: Dictionary = GameData.TOWERS[tid]
	var s: String = "%s  (%d gold)\n%s\n" % [d["name"], d["cost"], d["desc"]]
	var sh: Dictionary = GameData.shape_of(tid)
	var arc := GameData.arc_of(tid)
	s += "Footprint: %s" % sh["name"]
	if sh["muzzles"].size() > 1:
		s += ", fires from %d hexes" % sh["muzzles"].size()
	s += ("   Fires all around\n" if arc >= 359.0 else "   Fires in a %d degree arc (R turns it)\n" % int(arc))
	if d["attack"] == "aura_buff":
		s += "Range %.1f tiles" % float(d["range"])
		return s
	s += "Damage %d %s   Attacks/sec %.2f   Range %.1f tiles\n" % [d["dmg"], "magic" if d.get("dtype", "") == "magic" else "physical", d["rate"], d["range"]]
	var hits: PackedStringArray = []
	if d.get("ground", false): hits.append("ground")
	if d.get("air", false): hits.append("air")
	s += "Hits: " + ", ".join(hits)
	if d.has("splash"): s += "   Splash %.1f" % float(d["splash"])
	if d.has("slow"): s += "   Slow %d%%" % int(d["slow"][0] * 100)
	if d.has("dot"): s += "   Poison %d/s" % int(d["dot"][0])
	if d.has("stun"): s += "   Stun %d%%" % int(d["stun"][0] * 100)
	if d.has("chain"): s += "   Chains %d" % int(d["chain"])
	if d.get("detect", false): s += "\nDetects camouflaged enemies"
	if d.get("shred", false): s += "\nBreaks shields fast"
	if GameData.SPECS.has(tid):
		var sp: Array = GameData.SPECS[tid]
		s += "\nLevel III: %s or %s" % [sp[0]["name"], sp[1]["name"]]
	return s


func set_start(visible_: bool, text := "", preview := "") -> void:
	start_panel.visible = visible_
	start_btn.text = text
	preview_lbl.text = preview


## The commander's signature passive, bottom left.
func update_signature(sig: Dictionary, status: String) -> void:
	ability_btn.visible = not sig.is_empty() and build_bar.visible
	if sig.is_empty():
		return
	ability_btn.text = "%s\n%s" % [sig["name"], status]
	ability_btn.tooltip_text = String(sig["desc"])


# ------------------------------------------------------------------ top values

func refresh_top() -> void:
	if castle_open():
		_style_castle()
	top_wave.text = "Wave %d / %d" % [game.wave, GameData.MAX_WAVES]
	if game.difficulty > 0:
		top_wave.text += "  (%s)" % GameData.DIFFICULTIES[game.difficulty]["name"]
	top_hp.text = "Castle %d / %d" % [game.hp, game.max_hp]
	top_gold.text = "Gold %d" % game.gold
	top_recon.text = "Runes %d" % game.recon
	top_fronts.text = "Fronts %d" % game.board.battlefronts()
	top_phase.text = game.phase_text()
	speed_btn.text = "Speed %dx [V]" % int(game.speed)
	mute_btn.text = "Sound: %s [M]" % ("Off" if game.audio.muted else "On")


# ------------------------------------------------------------------ tower info panel

func _build_info() -> void:
	info_panel = PanelContainer.new()
	info_panel.set_anchors_preset(Control.PRESET_CENTER_RIGHT)
	info_panel.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	info_panel.grow_vertical = Control.GROW_DIRECTION_BOTH
	info_panel.offset_right = -10
	root.add_child(info_panel)
	var v := VBoxContainer.new()
	v.custom_minimum_size = Vector2(270, 0)
	v.add_theme_constant_override("separation", 6)
	info_panel.add_child(v)
	info_title = _label("", 20, GOLD_C)
	v.add_child(info_title)
	info_body = _wrap_label("", 270, 14)
	v.add_child(info_body)
	info_upgrade = _button("Upgrade", func(): game.upgrade_selected())
	v.add_child(info_upgrade)
	for i in 2:
		var sb := _button("", func(): game.upgrade_selected(i), 14)
		sb.custom_minimum_size = Vector2(270, 58)
		sb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		v.add_child(sb)
		info_specs.append(sb)
	info_target = _button("Target: First  [T]", func(): game.cycle_target())
	info_sell = _button("Sell", func(): game.sell_selected())
	for b in [info_target, info_sell]:
		v.add_child(b)
	info_panel.visible = false


func show_tower_info(t: Tower) -> void:
	if t == null:
		info_panel.visible = false
		return
	info_panel.visible = true
	var d := t.data
	info_title.text = "%s  %s" % [d["name"], "I".repeat(t.level)]
	if t.spec >= 0:
		info_title.text += "  -  " + String(GameData.SPECS[t.id][t.spec]["name"])
	info_title.add_theme_color_override("font_color", d["color"])
	var s := String(d["desc"]) + "\n\n"
	if t.is_support():
		var b := t.buff()
		if b.has("dmg"):
			s += "Aura: +%d%% damage to nearby towers\n" % int(b["dmg"] * 100)
		if b.has("rate"):
			s += "Aura: +%d%% attack speed to nearby towers\n" % int(b["rate"] * 100)
		s += "Range: %.1f tiles\n" % (t.range_world() / GameData.TILE)
	else:
		s += "Damage: %d %s\n" % [int(t.damage()), "magic" if d.get("dtype", "") == "magic" else "physical"]
		s += "Attacks/sec: %.2f\n" % t.fire_rate()
		var shape := "" if t.arc >= 359.0 else ", %d degree arc" % int(t.arc)
		if t.line_w > 0.0:
			shape = ", in a straight line ahead"
		s += "Range: %.1f tiles%s\n" % [t.range_world() / GameData.TILE, shape]
		if t.buff_dmg > 0.0 or t.buff_rate > 0.0:
			s += "Aura bonus: +%d%% dmg, +%d%% speed\n" % [int(t.buff_dmg * 100), int(t.buff_rate * 100)]
		if t.on_ley:
			s += "Ley crystal: +%d%% damage\n" % int((GameData.LEY_BONUS + game.mods["ley"]) * 100)
		if t.elevation > 0:
			s += "High ground (level %d): +%d%% range\n" % [t.elevation, int(GameData.ELEVATION_RANGE * t.elevation * 100)]
		if t.nb_range > 0.0:
			s += "Relay Station: +%d%% range\n" % int(t.nb_range * 100)
		if t.detects():
			s += "Detects camouflaged enemies\n"
		if t.spec >= 0:
			s += "%s: %s\n" % [GameData.SPECS[t.id][t.spec]["name"], GameData.SPECS[t.id][t.spec]["desc"]]
		s += "\nKills: %d    Damage dealt: %d" % [t.kills, int(t.damage_done)]
	info_body.text = s
	var uc := t.upgrade_cost()
	var choosing := game.needs_spec(t)
	info_upgrade.visible = not choosing
	for i in info_specs.size():
		var sb: Button = info_specs[i]
		sb.visible = choosing
		if choosing:
			var sp: Dictionary = GameData.SPECS[t.id][i]
			sb.text = "%s  (%d gold)\n%s" % [sp["name"], uc, sp["desc"]]
			sb.disabled = game.gold < uc
	if uc < 0:
		info_upgrade.text = "Max level"
		info_upgrade.disabled = true
	elif not choosing:
		info_upgrade.text = "Upgrade to %s  (%d gold)  [U]" % ["I".repeat(t.level + 1), uc]
		info_upgrade.disabled = game.gold < uc
	info_target.visible = not t.is_support() and t.attack() != "aura_dmg"
	info_target.text = "Target: %s  [T]" % GameData.TARGET_MODES[t.target_mode]
	info_sell.text = "Sell  (+%d gold)  [X]" % t.sell_value()


# ------------------------------------------------------------------ choice cards

func _build_choices() -> void:
	choice_root = Control.new()
	choice_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	choice_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(choice_root)
	var v := VBoxContainer.new()
	v.set_anchors_preset(Control.PRESET_CENTER_TOP)
	v.grow_horizontal = Control.GROW_DIRECTION_BOTH
	v.offset_top = 70
	v.alignment = BoxContainer.ALIGNMENT_BEGIN
	v.add_theme_constant_override("separation", 8)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	choice_root.add_child(v)
	choice_title = _title("", 40, GOLD_C)
	choice_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	choice_title.add_theme_constant_override("outline_size", 10)
	choice_sub = _label("", 18, TEXT_C)
	choice_sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	choice_sub.add_theme_constant_override("outline_size", 7)
	v.add_child(choice_title)
	v.add_child(choice_sub)
	choice_row = HBoxContainer.new()
	choice_row.alignment = BoxContainer.ALIGNMENT_CENTER
	choice_row.add_theme_constant_override("separation", 16)
	choice_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(choice_row)
	choice_detail = PanelContainer.new()
	choice_detail.add_theme_stylebox_override("panel", _panel_box(16, Color(0.06, 0.05, 0.08, 0.93), Color(1, 1, 1, 0.15), 1, 10, 14, true))
	choice_detail.custom_minimum_size = Vector2(760, 112)
	choice_detail.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	choice_detail.mouse_filter = Control.MOUSE_FILTER_IGNORE
	choice_detail_box = HBoxContainer.new()
	choice_detail_box.add_theme_constant_override("separation", 26)
	choice_detail.add_child(choice_detail_box)
	v.add_child(choice_detail)
	var brow := HBoxContainer.new()
	brow.alignment = BoxContainer.ALIGNMENT_CENTER
	brow.add_theme_constant_override("separation", 14)
	v.add_child(brow)
	choice_extra = _button("", func(): pass)
	choice_extra.add_theme_color_override("font_color", RECON_C)
	brow.add_child(choice_extra)
	choice_skip = _button("", func(): pass)
	brow.add_child(choice_skip)
	choice_root.visible = false


## options: [{"kind","title","desc","color","footer"}]
func show_choices(title: String, sub: String, options: Array, on_pick: Callable, on_hover: Callable, skip_text := "", on_skip := Callable(),
		extra_text := "", on_extra := Callable()) -> void:
	for c in choice_row.get_children():
		c.queue_free()
	choice_detail.visible = false
	choice_title.text = title
	choice_sub.text = sub
	for i in options.size():
		var o: Dictionary = options[i]
		var col: Color = o.get("color", TEXT_C)
		var b := Button.new()
		b.focus_mode = Control.FOCUS_NONE
		b.custom_minimum_size = Vector2(250, 372)
		b.add_theme_stylebox_override("normal", _card_box(col, 0.3, Color(0.08, 0.07, 0.1, 0.94), col.darkened(0.2), 2, 10))
		b.add_theme_stylebox_override("hover", _card_box(col, 0.55, Color(0.16, 0.13, 0.2, 0.97), col, 3, 10))
		b.add_theme_stylebox_override("pressed", _card_box(col, 0.42, Color(0.22, 0.18, 0.12, 0.97), col, 3, 10))
		var vb := VBoxContainer.new()
		vb.set_anchors_preset(Control.PRESET_FULL_RECT)
		vb.offset_left = 14
		vb.offset_right = -14
		vb.offset_top = 10
		vb.offset_bottom = -10
		vb.add_theme_constant_override("separation", 6)
		vb.add_child(_label(o.get("kind", ""), 13, col.lightened(0.35)))
		var pv := _card_preview(o)
		if pv:
			vb.add_child(pv)
		vb.add_child(_wrap_label(o.get("title", ""), 222, 21, TEXT_C))
		vb.add_child(_wrap_label(o.get("desc", ""), 222, 14, DIM_C.lightened(0.2)))
		var spacer := Control.new()
		spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
		vb.add_child(spacer)
		vb.add_child(_label(o.get("footer", ""), 13, GOLD_C))
		b.add_child(vb)
		_ignore_all(vb)
		b.pressed.connect(on_pick.bind(i))
		b.mouse_entered.connect(on_hover.bind(i))
		b.mouse_exited.connect(on_hover.bind(-1))
		choice_row.add_child(b)
	_reconnect(choice_skip, on_skip)
	choice_skip.visible = skip_text != ""
	choice_skip.text = skip_text
	_reconnect(choice_extra, on_extra)
	choice_extra.visible = extra_text != ""
	choice_extra.text = extra_text
	choice_extra.disabled = game.recon < GameData.REROLL_COST
	choice_root.visible = true


const KIND_COLORS := {"blueprint": Color(0.95, 0.8, 0.45), "doctrine": Color(0.75, 0.55, 1.0), "masterwork": Color(1.0, 0.7, 0.3),
	"builder": Color(0.75, 0.6, 0.4), "digger": Color(0.7, 0.5, 0.35), "gold": Color(1.0, 0.84, 0.35), "recon": Color(0.55, 0.85, 1.0)}


## Wave rewards: three options, each a pair of items shown as icons only. Hovering shows what they are.
func show_pair_choices(title: String, options: Array, on_pick: Callable, skip_text: String, on_skip: Callable,
		extra_text: String, on_extra: Callable) -> void:
	for c in choice_row.get_children():
		c.queue_free()
	choice_title.text = title
	choice_sub.text = "Pick one pair   (hover for details)"
	for i in options.size():
		var items: Array = options[i]["items"]
		var col: Color = _item_color(items[0])
		var b := Button.new()
		b.focus_mode = Control.FOCUS_NONE
		b.custom_minimum_size = Vector2(300, 196)
		b.add_theme_stylebox_override("normal", _card_box(col, 0.25, Color(0.08, 0.07, 0.1, 0.94), col.darkened(0.35), 2, 12))
		b.add_theme_stylebox_override("hover", _card_box(col, 0.55, Color(0.16, 0.13, 0.2, 0.97), col, 3, 12))
		b.add_theme_stylebox_override("pressed", _card_box(col, 0.42, Color(0.22, 0.18, 0.12, 0.97), col, 3, 12))
		var h := HBoxContainer.new()
		h.set_anchors_preset(Control.PRESET_FULL_RECT)
		h.alignment = BoxContainer.ALIGNMENT_CENTER
		h.add_theme_constant_override("separation", 6)
		b.add_child(h)
		for k in items.size():
			if k > 0:
				var plus := _label("+", 30, DIM_C)
				plus.size_flags_vertical = Control.SIZE_SHRINK_CENTER
				h.add_child(plus)
			h.add_child(_item_slot(items[k]))
		_ignore_all(h)
		b.pressed.connect(on_pick.bind(i))
		b.mouse_entered.connect(_show_pair_detail.bind(items))
		b.mouse_exited.connect(func(): choice_detail.modulate.a = 0.0)
		choice_row.add_child(b)
	choice_detail.visible = true
	choice_detail.modulate.a = 0.0
	_reconnect(choice_skip, on_skip)
	choice_skip.visible = skip_text != ""
	choice_skip.text = skip_text
	_reconnect(choice_extra, on_extra)
	choice_extra.visible = extra_text != ""
	choice_extra.text = extra_text
	choice_extra.disabled = game.recon < GameData.REROLL_COST
	choice_root.visible = true


func _item_color(it: Dictionary) -> Color:
	if it["kind"] == "blueprint":
		return GameData.TOWERS[it["tower"]]["color"]
	return KIND_COLORS.get(it["kind"], TEXT_C)


## One item on a reward card: its picture, and a small count underneath.
func _item_slot(it: Dictionary) -> Control:
	var v := VBoxContainer.new()
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_theme_constant_override("separation", 2)
	var pic: Control
	var kind: String = it["kind"]
	if kind == "blueprint" or (kind in ["doctrine", "masterwork"] and ResourceLoader.exists(String(it.get("icon", "")))):
		var tr := TextureRect.new()
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		if kind == "blueprint":
			var tex := game.thumbs.get_thumb(it["tower"])
			if tex:
				tr.texture = tex
			else:
				_pending_thumbs.append([tr, it["tower"]])
		else:
			tr.texture = load(it["icon"])
		pic = tr
	else:
		var ic := ItemIcon.new()
		ic.kind = kind
		pic = ic
	pic.custom_minimum_size = Vector2(118, 118)
	v.add_child(pic)
	var badge := _label(String(it.get("badge", "")), 17, _item_color(it).lightened(0.2))
	badge.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	badge.add_theme_constant_override("outline_size", 6)
	v.add_child(badge)
	return v


func _show_pair_detail(items: Array) -> void:
	for c in choice_detail_box.get_children():
		c.queue_free()
	for it in items:
		var vb := VBoxContainer.new()
		vb.custom_minimum_size = Vector2(360, 0)
		vb.add_child(_wrap_label(String(it["name"]), 360, 18, _item_color(it)))
		vb.add_child(_wrap_label(String(it["desc"]), 360, 14, TEXT_C))
		choice_detail_box.add_child(vb)
	choice_detail.modulate.a = 1.0


## Points a button at a new callback (keeping its click sound).
func _reconnect(b: Button, cb: Callable) -> void:
	for cn in b.pressed.get_connections():
		b.pressed.disconnect(cn["callable"])
	b.pressed.connect(func(): game.sfx("click"))
	if cb.is_valid():
		b.pressed.connect(cb)


var _pending_thumbs: Array = []   # [TextureRect, tower id] waiting for a portrait render


func _fill_pending_thumbs() -> void:
	for pt in _pending_thumbs.duplicate():
		if not is_instance_valid(pt[0]):
			_pending_thumbs.erase(pt)
			continue
		var tr: TextureRect = pt[0]
		var tex := game.thumbs.get_thumb(pt[1])
		if tex:
			tr.texture = tex
			_pending_thumbs.erase(pt)


## Picture for a choice card: a tower portrait, a boon icon, or a diagram of a road piece.
func _card_preview(o: Dictionary) -> Control:
	if o.has("tile"):
		var td := TileDiagram.new()
		td.card = o["tile"]
		td.custom_minimum_size = Vector2(222, 132)
		return td
	if o.has("moves"):
		var rd := RoadDiagram.new()
		rd.moves = o["moves"]
		rd.color = o.get("color", GOLD_C)
		rd.custom_minimum_size = Vector2(222, 112)
		return rd
	var tr := TextureRect.new()
	tr.custom_minimum_size = Vector2(222, 120)
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	if o.has("tower"):
		var tex := game.thumbs.get_thumb(o["tower"])
		if tex:
			tr.texture = tex
		else:
			_pending_thumbs.append([tr, o["tower"]])
		return tr
	if o.has("icon") and ResourceLoader.exists(o["icon"]):
		tr.texture = load(o["icon"])
		return tr
	return null


## Drawn icons for items that have no picture: Builders, Diggers, gold, Runes and the castle.
class ItemIcon extends Control:
	var kind := ""

	func _draw() -> void:
		var u := minf(size.x, size.y)
		var o := (size - Vector2(u, u)) * 0.5
		var P := func(x: float, y: float) -> Vector2: return o + Vector2(x, y) * u
		match kind:
			"builder":
				var wood := Color(0.72, 0.52, 0.3)
				var dark := Color(0.45, 0.3, 0.17)
				draw_rect(Rect2(P.call(0.12, 0.82), Vector2(0.76, 0.1) * u), Color(0.42, 0.55, 0.3))
				draw_rect(Rect2(P.call(0.2, 0.52), Vector2(0.6, 0.3) * u), Color(0.5, 0.62, 0.36))
				for x in [0.18, 0.5, 0.78]:
					draw_rect(Rect2(P.call(x, 0.22), Vector2(0.05, 0.62) * u), wood)
				for y in [0.26, 0.5]:
					draw_rect(Rect2(P.call(0.16, y), Vector2(0.68, 0.045) * u), wood)
				draw_line(P.call(0.2, 0.5), P.call(0.52, 0.27), dark, u * 0.035)
				draw_line(P.call(0.52, 0.5), P.call(0.8, 0.27), dark, u * 0.035)
				draw_colored_polygon(PackedVector2Array([P.call(0.5, 0.0), P.call(0.64, 0.15), P.call(0.36, 0.15)]), Color(0.5, 1.0, 0.55))
			"digger":
				draw_colored_polygon(PackedVector2Array([P.call(0.05, 0.92), P.call(0.25, 0.7), P.call(0.55, 0.64), P.call(0.8, 0.74), P.call(0.95, 0.92)]), Color(0.5, 0.36, 0.22))
				draw_line(P.call(0.28, 0.1), P.call(0.56, 0.58), Color(0.7, 0.5, 0.3), u * 0.07)
				draw_line(P.call(0.2, 0.12), P.call(0.36, 0.06), Color(0.7, 0.5, 0.3), u * 0.07)
				draw_colored_polygon(PackedVector2Array([P.call(0.46, 0.56), P.call(0.64, 0.46), P.call(0.8, 0.72), P.call(0.66, 0.84)]), Color(0.72, 0.74, 0.78))
				draw_colored_polygon(PackedVector2Array([P.call(0.82, 0.05), P.call(0.96, 0.05), P.call(0.89, 0.2)]), Color(1.0, 0.7, 0.35))
			"gold":
				for k in 4:
					var c: Vector2 = P.call(0.36, 0.78 - k * 0.1)
					draw_set_transform(c, 0.0, Vector2(1.0, 0.45))
					draw_circle(Vector2.ZERO, u * 0.24, Color(0.78, 0.58, 0.15))
					draw_circle(Vector2.ZERO, u * 0.21, Color(1.0, 0.82, 0.3))
				draw_set_transform(Vector2.ZERO)
				draw_circle(P.call(0.66, 0.5), u * 0.26, Color(0.78, 0.58, 0.15))
				draw_circle(P.call(0.66, 0.5), u * 0.22, Color(1.0, 0.84, 0.35))
				draw_circle(P.call(0.66, 0.5), u * 0.13, Color(0.9, 0.7, 0.22))
			"recon":
				var stone := PackedVector2Array([P.call(0.3, 0.06), P.call(0.72, 0.1), P.call(0.86, 0.4), P.call(0.8, 0.84),
					P.call(0.46, 0.96), P.call(0.16, 0.82), P.call(0.12, 0.38)])
				draw_colored_polygon(stone, Color(0.3, 0.33, 0.42))
				var inner := PackedVector2Array()
				for q in stone:
					inner.append(P.call(0.5, 0.52) + (q - P.call(0.5, 0.52)) * 0.86)
				draw_colored_polygon(inner, Color(0.4, 0.44, 0.55))
				var glow := Color(0.45, 0.9, 1.0)
				draw_circle(P.call(0.5, 0.5), u * 0.3, Color(glow, 0.12))
				for seg in [[0.5, 0.2, 0.5, 0.8], [0.5, 0.36, 0.7, 0.24], [0.5, 0.36, 0.3, 0.24], [0.5, 0.62, 0.68, 0.76], [0.5, 0.62, 0.32, 0.76]]:
					draw_line(P.call(seg[0], seg[1]), P.call(seg[2], seg[3]), glow, u * 0.055)
			"castle":
				var stone := Color(0.75, 0.72, 0.66)
				draw_rect(Rect2(P.call(0.15, 0.4), Vector2(0.7, 0.52) * u), stone)
				draw_rect(Rect2(P.call(0.35, 0.18), Vector2(0.3, 0.3) * u), stone.lightened(0.1))
				for x in [0.15, 0.31, 0.53, 0.69]:
					draw_rect(Rect2(P.call(x, 0.32), Vector2(0.16 if x < 0.3 or x > 0.6 else 0.12, 0.1) * u), stone)
				for x in [0.35, 0.47, 0.59]:
					draw_rect(Rect2(P.call(x, 0.1), Vector2(0.06, 0.1) * u), stone.lightened(0.1))
				draw_rect(Rect2(P.call(0.42, 0.66), Vector2(0.16, 0.26) * u), Color(0.25, 0.18, 0.12))
				draw_line(P.call(0.5, 0.1), P.call(0.5, -0.04), Color(0.5, 0.4, 0.3), u * 0.025)
				draw_colored_polygon(PackedVector2Array([P.call(0.5, -0.04), P.call(0.68, 0.0), P.call(0.5, 0.04)]), Color(1.0, 0.8, 0.3))


## Draws a road piece from its move string (F/L/R) as a little tile path, starting from the current road end.
class RoadDiagram extends Control:
	var moves := ""
	var color := Color(1, 0.85, 0.4)

	func _draw() -> void:
		var cells: Array = [Vector2i(0, 0)]
		var cur := Vector2i(0, 0)
		var dir := Vector2i(0, -1)
		for ch in moves:
			if ch == "L":
				dir = Vector2i(dir.y, -dir.x)
			elif ch == "R":
				dir = Vector2i(-dir.y, dir.x)
			cur += dir
			cells.append(cur)
		var lo := Vector2i(0, 0)
		var hi := Vector2i(0, 0)
		for c in cells:
			lo = Vector2i(mini(lo.x, c.x), mini(lo.y, c.y))
			hi = Vector2i(maxi(hi.x, c.x), maxi(hi.y, c.y))
		var span := Vector2(hi - lo + Vector2i.ONE)
		var cell := minf(size.x / span.x, size.y / span.y)
		cell = minf(cell, 30.0)
		var origin := (size - span * cell) * 0.5
		for i in cells.size():
			var c: Vector2i = cells[i]
			var r := Rect2(origin + Vector2(c - lo) * cell + Vector2(2, 2), Vector2(cell - 4, cell - 4))
			if i == 0:
				draw_rect(r, Color(0.45, 0.42, 0.4, 0.8))   # the existing road end
			else:
				draw_rect(r, color.darkened(0.15 * float(i % 2)))
		var last: Vector2i = cells[cells.size() - 1]
		var ctr := origin + (Vector2(last - lo) + Vector2(0.5, 0.5)) * cell
		draw_circle(ctr, cell * 0.22, Color(0.75, 0.3, 1.0))   # where the portal moves to


## A terrain tile card: 5x5 grid, road (entering from the bottom), features and new road ends.
## A terrain tile card, drawn from its wedges so the half hexes on the edges show as halves.
class TileDiagram extends Control:
	var card: Dictionary

	func _draw() -> void:
		Hex.setup()
		var px := minf(size.x / (2.0 * Hex.K + 0.6), (size.y - 4.0) / (Hex.K * Hex.SQ3 + 0.4))
		var k := px / Hex.R
		var mid := size * 0.5
		var roads := {}
		for pth in card["paths"]:
			for c in pth:
				roads[c] = true
		var feat := {}
		for f in card["features"]:
			feat[f["cell"]] = f
		var font := get_theme_default_font()
		for entry in Hex.TEMPLATE:
			var off: Vector2i = entry[0]
			var mask: int = entry[1]
			var w := Hex.to_world(off)
			var ctr := mid + Vector2(w.x, w.z) * k
			var col := Color(0.3, 0.46, 0.25)
			var ft: String = String(feat[off]["type"]) if feat.has(off) else ""
			if ft == "pond":
				col = Color(0.62, 0.45, 0.28) if roads.has(off) else Color(0.33, 0.6, 0.88)
			elif roads.has(off):
				col = Color(0.8, 0.64, 0.4)
			elif ft == "plateau":
				col = Color(0.5, 0.64, 0.36)
			for i in 6:
				if mask & (1 << i) == 0:
					continue
				var ca: Vector3 = Hex.CORNER[i]
				var cb: Vector3 = Hex.CORNER[(i + 1) % 6]
				var pts := PackedVector2Array([ctr, ctr + Vector2(ca.x, ca.z) * k * 0.94, ctr + Vector2(cb.x, cb.z) * k * 0.94])
				draw_colored_polygon(pts, col)
			if feat.has(off) and not roads.has(off):
				var f: Dictionary = feat[off]
				match String(f["type"]):
					"tree": draw_circle(ctr, px * 0.45, Color(0.13, 0.36, 0.14))
					"rock": draw_circle(ctr, px * 0.38, Color(0.58, 0.58, 0.6))
					"ley": draw_circle(ctr, px * 0.38, Color(0.4, 0.9, 1.0))
					"neutral":
						draw_circle(ctr, px * 0.62, Color(1.0, 0.62, 0.2))
						var letter := String(GameData.NEUTRALS[f["kind"]]["name"]).substr(0, 1)
						draw_string(font, ctr + Vector2(-px * 0.32, px * 0.36), letter, HORIZONTAL_ALIGNMENT_LEFT, -1, int(px * 1.0), Color(0.15, 0.08, 0.02))
		for s_ in card["entrances"]:
			var e := Hex.to_world(Hex.E[s_] * Hex.HALF)
			draw_circle(mid + Vector2(e.x, e.z) * k, px * 0.42, Color(0.8, 0.35, 1.0))
		var rise: int = card.get("rise", 0)
		if rise != 0:
			draw_string(font, Vector2(2, 14), "Raised" if rise > 0 else "Lowland", HORIZONTAL_ALIGNMENT_LEFT, -1, 13,
				Color(1, 0.88, 0.55) if rise > 0 else Color(0.65, 0.82, 1.0))


func hide_choices() -> void:
	choice_root.visible = false


## Hides the run's pop-up panels (reward pick, tile, castle talents) while the run is parked; returns what was open.
func park_panels() -> Dictionary:
	var open := {}
	for n in [choice_root, tile_panel, castle_root, choice_detail]:
		if n:
			open[n] = n.visible
			n.visible = false
	return open


func unpark_panels(open: Dictionary) -> void:
	for n in open:
		if is_instance_valid(n):
			n.visible = open[n]


# ------------------------------------------------------------------ damage chart (top right)

func _build_damage() -> void:
	dmg_panel = PanelContainer.new()
	dmg_panel.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	dmg_panel.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	dmg_panel.offset_right = -10
	dmg_panel.offset_top = 62
	root.add_child(dmg_panel)
	var v := VBoxContainer.new()
	v.custom_minimum_size = Vector2(250, 0)
	v.add_theme_constant_override("separation", 3)
	dmg_panel.add_child(v)
	var head := HBoxContainer.new()
	v.add_child(head)
	var t := _label("DAMAGE", 14, Color(1, 0.6, 0.4))
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(t)
	dmg_toggle = _button("Fade [K]", func(): cycle_damage(), 12)
	head.add_child(dmg_toggle)
	for i in DMG_ROWS:
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 6)
		var nm := _label("", 13, TEXT_C)
		nm.custom_minimum_size = Vector2(96, 0)
		nm.clip_text = true
		nm.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		row.add_child(nm)
		var back := ColorRect.new()
		back.color = Color(0, 0, 0, 0.35)
		back.custom_minimum_size = Vector2(DMG_BAR_W, 12)
		back.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(back)
		var fill := ColorRect.new()
		fill.size = Vector2(0, 12)
		back.add_child(fill)
		var val := _label("", 13, DIM_C)
		val.custom_minimum_size = Vector2(44, 0)
		val.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		row.add_child(val)
		row.visible = false
		v.add_child(row)
		dmg_rows.append([row, nm, fill, val])
	var empty := _label("No damage yet", 13, DIM_C)
	empty.name = "Empty"
	v.add_child(empty)
	dmg_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE


## Shown -> see-through -> hidden -> shown.
func cycle_damage() -> void:
	dmg_mode = (dmg_mode + 1) % 3
	_dmg_t = 0.0
	refresh_damage(0.0)


## Every tower you own, the most damage first: its name and level, a bar in its colour and the total it has dealt.
func refresh_damage(dt: float) -> void:
	_dmg_t -= dt
	if _dmg_t > 0.0 or dmg_panel == null:
		return
	_dmg_t = 0.5
	dmg_panel.modulate.a = 0.45 if dmg_mode == 1 else 1.0
	dmg_toggle.text = ["Fade [K]", "Hide [K]", "Show [K]"][dmg_mode]
	var list: Array = game.towers.filter(func(t): return is_instance_valid(t))
	list.sort_custom(func(a, b): return a.damage_done > b.damage_done)
	var top := 0.0
	if not list.is_empty():
		top = maxf(1.0, list[0].damage_done)
	var shown := 0
	for i in DMG_ROWS:
		var r: Array = dmg_rows[i]
		var on: bool = dmg_mode != 2 and i < list.size()
		(r[0] as Control).visible = on
		if not on:
			continue
		var t: Tower = list[i]
		var td: Dictionary = GameData.TOWERS[t.id]
		(r[1] as Label).text = "%s %s" % [td["name"], ["", "I", "II", "III", "IV", "V"][clampi(t.level, 0, 5)]]
		var fill := r[2] as ColorRect
		fill.color = td["color"]
		fill.size = Vector2(DMG_BAR_W * t.damage_done / top, 12)
		(r[3] as Label).text = _compact(t.damage_done)
		shown += 1
	var empty := dmg_panel.find_child("Empty", true, false) as Control
	if empty:
		empty.visible = dmg_mode != 2 and shown == 0


func _compact(v: float) -> String:
	if v >= 1000000.0:
		return "%.1fM" % (v / 1000000.0)
	if v >= 10000.0:
		return "%dk" % int(v / 1000.0)
	if v >= 1000.0:
		return "%.1fk" % (v / 1000.0)
	return str(int(v))


# ------------------------------------------------------------------ threat intel + placement hint

func _build_intel() -> void:
	intel_panel = PanelContainer.new()
	intel_panel.set_anchors_preset(Control.PRESET_TOP_LEFT)
	intel_panel.offset_left = 10
	intel_panel.offset_top = 62
	root.add_child(intel_panel)
	intel_box = VBoxContainer.new()
	intel_box.custom_minimum_size = Vector2(250, 0)
	intel_box.add_theme_constant_override("separation", 3)
	intel_panel.add_child(intel_box)


## Lists this run's threats (revealed a few waves ahead) and bosses.
func refresh_intel() -> void:
	for c in intel_box.get_children():
		c.queue_free()
	intel_box.add_child(_label("THREAT INTEL", 14, Color(1, 0.6, 0.4)))
	var next := game.wave + 1
	for t in game.threats:
		var th: Dictionary = GameData.THREATS[t["id"]]
		var w: int = t["wave"]
		var l: Label
		if w <= game.wave or (w == next and game.state == Game.S.WAVE):
			l = _label("Active: %s" % th["name"], 14, TEXT_C)
		elif game.threat_known(t):
			l = _label("Wave %d: %s" % [w, th["name"]], 14, Color(1, 0.75, 0.5))
		else:
			l = _label("Wave %d: ???" % w, 14, DIM_C)
		if game.threat_known(t):
			l.tooltip_text = "%s\n%s" % [th["name"], th["desc"]]
			l.mouse_filter = Control.MOUSE_FILTER_PASS
		intel_box.add_child(l)
	var bw: Array = game.boss_plan.keys()
	bw.sort()
	for w in bw:
		if w < next:
			continue
		var bd: Dictionary = GameData.ENEMIES[game.boss_plan[w]]
		intel_box.add_child(_label("Wave %d boss: %s%s" % [w, bd["name"], " (air)" if bd.get("flying", false) else ""], 14, HP_C))


func _build_hint() -> void:
	hint_panel = PanelContainer.new()
	hint_panel.set_anchors_preset(Control.PRESET_CENTER_TOP)
	hint_panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	hint_panel.offset_top = 64
	root.add_child(hint_panel)
	hint_lbl = _label("", 17, TEXT_C)
	hint_panel.add_child(hint_lbl)
	hint_panel.visible = false

	# the one tile on offer: the map shows it as a hologram on the spot you point at; here, just how to turn it and the reroll
	tile_panel = PanelContainer.new()
	tile_panel.set_anchors_preset(Control.PRESET_CENTER_TOP)
	tile_panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	tile_panel.offset_top = 60
	tile_panel.add_theme_stylebox_override("panel", _panel_box(10, Color(0.06, 0.05, 0.08, 0.85), Color(1, 0.85, 0.4, 0.4), 2, 10, 6))
	root.add_child(tile_panel)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 14)
	tile_panel.add_child(h)
	tile_title_lbl = _label("", 17, GOLD_C)
	h.add_child(tile_title_lbl)
	h.add_child(_label("Click a glowing spot   R / Shift+R: turn", 14, DIM_C))
	tile_reroll = _button("", func(): game.reroll(), 15)
	tile_reroll.add_theme_color_override("font_color", RECON_C)
	h.add_child(tile_reroll)
	tile_panel.visible = false


## The tile bar: the tile's name and the reroll (the hologram on the map shows the tile itself).
func show_tile_panel(title: String, reroll_text: String) -> void:
	tile_title_lbl.text = title
	tile_reroll.text = reroll_text
	tile_reroll.disabled = game.recon < GameData.REROLL_COST
	tile_panel.visible = true


func show_place_hint(text: String) -> void:
	hint_lbl.text = text
	hint_panel.visible = true


func hide_place_hint() -> void:
	hint_panel.visible = false
	tile_panel.visible = false


# ------------------------------------------------------------------ castle talents

func castle_open() -> bool:
	return castle_root != null and castle_root.visible


func toggle_castle() -> void:
	if game.state in [Game.S.MENU, Game.S.OVER]:
		return
	if castle_open():
		castle_root.visible = false
		return
	game.sfx("click")
	_build_castle()


func _build_castle() -> void:
	if castle_root:
		castle_root.queue_free()
	_castle_btns.clear()
	castle_root = PanelContainer.new()
	castle_root.set_anchors_preset(Control.PRESET_CENTER)
	castle_root.grow_horizontal = Control.GROW_DIRECTION_BOTH
	castle_root.grow_vertical = Control.GROW_DIRECTION_BOTH
	castle_root.add_theme_stylebox_override("panel", _panel_box(20, Color(0.05, 0.04, 0.07, 0.95), GOLD_C.darkened(0.3), 2, 14, 18))
	root.add_child(castle_root)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 10)
	castle_root.add_child(v)
	var head := HBoxContainer.new()
	var t := _title("Castle Talents", 34, GOLD_C)
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(t)
	head.add_child(_button("Close  [C]", func(): castle_root.visible = false, 15))
	v.add_child(head)
	v.add_child(_label("Spend gold now for a stronger realm later. Each path unlocks in order; Slayers can be taken in any order, twice.", 14, DIM_C))
	var cols := HBoxContainer.new()
	cols.add_theme_constant_override("separation", 14)
	v.add_child(cols)
	for path in game.talent_tree():
		var tp: Dictionary = game.talent_tree()[path]
		var col: Color = tp["color"]
		var cv := VBoxContainer.new()
		cv.add_theme_constant_override("separation", 8)
		cv.custom_minimum_size = Vector2(196, 0)
		cols.add_child(cv)
		cv.add_child(_label(tp["name"], 21, col))
		cv.add_child(_label(tp["desc"], 13, DIM_C))
		for i in tp["nodes"].size():
			var node: Dictionary = tp["nodes"][i]
			var b := Button.new()
			b.focus_mode = Control.FOCUS_NONE
			b.custom_minimum_size = Vector2(196, 64)
			b.add_theme_font_size_override("font_size", 14)
			b.pressed.connect(func():
				game.buy_talent(path, i)
				_style_castle())
			b.mouse_entered.connect(func(): castle_detail.text = "%s: %s" % [node["name"], node["desc"]])
			b.mouse_exited.connect(func(): castle_detail.text = "")
			cv.add_child(b)
			_castle_btns.append([b, path, i])
	castle_detail = _wrap_label("", 830, 16, TEXT_C)
	castle_detail.custom_minimum_size = Vector2(830, 48)
	v.add_child(castle_detail)
	_style_castle()


func _style_castle() -> void:
	for cb in _castle_btns:
		var b: Button = cb[0]
		var path: String = cb[1]
		var i: int = cb[2]
		var tp: Dictionary = game.talent_tree()[path]
		var node: Dictionary = tp["nodes"][i]
		var col: Color = tp["color"]
		var st := game.talent_state(path, i)
		var cost := game.talent_cost(path, i)
		var rank := game.talent_rank(node["id"])
		var pick: bool = tp.get("pick", false)
		match st:
			"owned":
				b.text = "%s\nOwned" % node["name"]
				b.add_theme_stylebox_override("normal", _card_box(col, 0.7, col.darkened(0.55), col, 2, 8))
				b.add_theme_stylebox_override("disabled", _card_box(col, 0.7, col.darkened(0.55), col, 2, 8))
				b.disabled = true
			"maxed":
				b.text = "%s\nRank %d/%d" % [node["name"], rank, GameData.TALENT_MAX_RANK]
				b.add_theme_stylebox_override("disabled", _card_box(col, 0.7, col.darkened(0.55), col, 2, 8))
				b.disabled = true
			"locked":
				b.text = "%s\n%d gold" % [node["name"], cost]
				b.add_theme_stylebox_override("disabled", _card_box(Color(0.3, 0.3, 0.32), 0.3, Color(0.1, 0.1, 0.12, 0.9), Color(0.3, 0.3, 0.3), 1, 8))
				b.disabled = true
			_:
				if pick:
					b.text = "%s  %d/%d\n%d gold" % [node["name"], rank, GameData.TALENT_MAX_RANK, cost]
				elif node.get("repeat", false):
					b.text = "%s%s\n%d gold" % [node["name"], "  x%d" % rank if rank > 0 else "", cost]
				else:
					b.text = "%s\n%d gold" % [node["name"], cost]
				b.add_theme_stylebox_override("normal", _card_box(col, 0.35, Color(0.1, 0.09, 0.12, 0.95), col.darkened(0.2), 2, 8))
				b.add_theme_stylebox_override("hover", _card_box(col, 0.55, Color(0.16, 0.13, 0.2, 0.97), col, 2, 8))
				b.add_theme_stylebox_override("disabled", _card_box(col, 0.12, Color(0.1, 0.09, 0.12, 0.95), col.darkened(0.6), 1, 8))
				b.disabled = game.gold < cost


# ------------------------------------------------------------------ toast, pause, menu, end

func _build_misc() -> void:
	toast_lbl = _title("", 30, GOLD_C)
	toast_lbl.set_anchors_preset(Control.PRESET_CENTER)
	toast_lbl.grow_horizontal = Control.GROW_DIRECTION_BOTH
	toast_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	toast_lbl.offset_top = 150
	toast_lbl.offset_bottom = 200
	toast_lbl.add_theme_constant_override("outline_size", 10)
	toast_lbl.modulate.a = 0.0
	root.add_child(toast_lbl)

	pause_lbl = _label("PAUSED", 64, TEXT_C)
	pause_lbl.set_anchors_preset(Control.PRESET_CENTER)
	pause_lbl.grow_horizontal = Control.GROW_DIRECTION_BOTH
	pause_lbl.grow_vertical = Control.GROW_DIRECTION_BOTH
	pause_lbl.add_theme_constant_override("outline_size", 10)
	pause_lbl.visible = false
	root.add_child(pause_lbl)


var _toasts: Array = []
var _toast_tw: Tween


## Big center message. Several in a row queue up instead of overwriting each other.
func toast(text: String, color := GOLD_C) -> void:
	if _toast_tw and _toast_tw.is_running():
		if _toasts.size() < 4:
			_toasts.append([text, color])
		return
	toast_lbl.text = text
	toast_lbl.add_theme_color_override("font_color", color)
	_toast_tw = toast_lbl.create_tween()
	toast_lbl.modulate.a = 1.0
	_toast_tw.tween_interval(1.5 if _toasts.is_empty() else 1.1)
	_toast_tw.tween_property(toast_lbl, "modulate:a", 0.0, 0.4)
	_toast_tw.finished.connect(_next_toast)


func _next_toast() -> void:
	if _toasts.size() > 0:
		var t: Array = _toasts.pop_front()
		toast(t[0], t[1])


func set_paused(p: bool) -> void:
	pause_lbl.visible = p
	pause_btn.text = "Resume [P]" if p else "Pause [P]"


func set_game_ui_visible(v: bool) -> void:
	for n in [top_wave.get_parent().get_parent(), build_bar, start_panel, ability_btn, intel_panel, dmg_panel]:
		n.visible = v
	if not v:
		help_panel.visible = false
		info_panel.visible = false
		choice_root.visible = false
		pause_lbl.visible = false
		hint_panel.visible = false
		tile_panel.visible = false
		if castle_root:
			castle_root.visible = false


func show_menu(stats: Dictionary) -> void:
	hide_end()
	if menu_root:
		menu_root.queue_free()
	set_game_ui_visible(false)
	menu_root = Control.new()
	menu_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(menu_root)
	var shade := ColorRect.new()
	shade.color = Color(0.03, 0.02, 0.05, 0.55)
	shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	menu_root.add_child(shade)
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	menu_root.add_child(center)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 14)
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	center.add_child(v)
	var title := _title("TOWER REALMS", 92, GOLD_C)
	title.add_theme_constant_override("outline_size", 14)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(title)
	var sub := _label("Build the road.  Hold the realm.", 22, TEXT_C)
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sub.add_theme_constant_override("outline_size", 8)
	v.add_child(sub)
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(0, 18)
	v.add_child(gap)
	if game.can_resume():
		var f: Dictionary = GameData.FACTIONS[game.faction]
		var res := _button("Resume run:  %s, wave %d" % [f["name"], maxi(1, game.wave)], func(): game.resume_run(), 22)
		res.custom_minimum_size = Vector2(460, 54)
		res.add_theme_color_override("font_color", GOLD_C)
		res.tooltip_text = "Pick up exactly where you left off. Starting a new run abandons this one."
		var rc := CenterContainer.new()
		rc.add_child(res)
		v.add_child(rc)
	var pick := _label("Choose your color" if not game.can_resume() else "...or start a new run (abandons the current one)", 20, TEXT_C)
	pick.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	pick.add_theme_constant_override("outline_size", 8)
	v.add_child(pick)
	var drow := HBoxContainer.new()
	drow.alignment = BoxContainer.ALIGNMENT_CENTER
	drow.add_theme_constant_override("separation", 8)
	v.add_child(drow)
	var group := ButtonGroup.new()
	for i in GameData.DIFFICULTIES.size():
		var dd: Dictionary = GameData.DIFFICULTIES[i]
		var db := _button(dd["name"], game.set_difficulty.bind(i), 16)
		db.toggle_mode = true
		db.button_group = group
		db.button_pressed = i == game.difficulty
		db.tooltip_text = dd["desc"]
		db.custom_minimum_size = Vector2(110, 36)
		drow.add_child(db)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 12)
	v.add_child(row)
	for fid in GameData.FACTIONS:
		row.add_child(_faction_card(fid, stats))
	var foot := HBoxContainer.new()
	foot.alignment = BoxContainer.ALIGNMENT_CENTER
	foot.add_theme_constant_override("separation", 16)
	v.add_child(foot)
	var council := _button("War Council  (%d Renown)" % game.renown(), func(): show_council(), 18)
	council.add_theme_color_override("font_color", GOLD_C)
	foot.add_child(council)
	foot.add_child(_button("Sound: %s" % ("Off" if game.audio.muted else "On"), func():
		game.toggle_mute()
		show_menu(game.stats), 16))
	foot.add_child(_button("Fullscreen: %s  [F11]" % ("On" if game.is_fullscreen() else "Off"), func(): game.toggle_fullscreen(), 16))
	foot.add_child(_button("Quit", func(): game.get_tree().quit()))


func _faction_card(fid: String, stats: Dictionary) -> Button:
	var f: Dictionary = GameData.FACTIONS[fid]
	var col: Color = f["color"]
	var b := Button.new()
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size = Vector2(300, 470)
	b.add_theme_stylebox_override("normal", _card_box(col, 0.28, Color(0.07, 0.06, 0.09, 0.94), col.darkened(0.3), 2, 12))
	b.add_theme_stylebox_override("hover", _card_box(col, 0.5, Color(0.13, 0.11, 0.16, 0.97), col, 3, 12))
	b.add_theme_stylebox_override("pressed", _card_box(col, 0.4, Color(0.2, 0.16, 0.1, 0.97), col, 3, 12))
	b.pressed.connect(show_hero_select.bind(fid))
	var vb := VBoxContainer.new()
	vb.set_anchors_preset(Control.PRESET_FULL_RECT)
	vb.offset_left = 14
	vb.offset_right = -14
	vb.offset_top = 12
	vb.offset_bottom = -12
	vb.add_theme_constant_override("separation", 6)
	b.add_child(vb)
	var pie := HBoxContainer.new()
	pie.add_theme_constant_override("separation", 8)
	var dot := ColorRect.new()
	dot.color = col
	dot.custom_minimum_size = Vector2(16, 16)
	dot.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	pie.add_child(dot)
	pie.add_child(_label("%s  -  %s" % [String(f["pie"]).to_upper(), f["race"]], 15, col.lightened(0.2)))
	vb.add_child(pie)
	var fname := _title(f["name"], 24, col)
	fname.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	fname.custom_minimum_size = Vector2(272, 0)
	vb.add_child(fname)
	vb.add_child(_wrap_label(f["desc"], 272, 13))
	vb.add_child(_wrap_label("Strong: " + String(f["strengths"]), 272, 13, Color(0.6, 0.95, 0.6)))
	vb.add_child(_wrap_label("Weak: " + String(f["weakness"]), 272, 13, Color(1.0, 0.6, 0.5)))
	vb.add_child(_wrap_label("%s: %s" % [f["passive_name"], f["passive_desc"]], 272, 13, RECON_C))
	var names: PackedStringArray = []
	for tid in f["towers"]:
		names.append(GameData.TOWERS[tid]["name"])
	vb.add_child(_wrap_label("Own towers: " + ", ".join(names), 272, 12, DIM_C.lightened(0.15)))
	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	vb.add_child(spacer)
	var best: int = stats.get(fid + "_best", 0)
	var wins: int = stats.get(fid + "_wins", 0)
	vb.add_child(_label("Best wave %d    Victories %d" % [best, wins], 13, DIM_C))
	vb.add_child(_label("Choose a commander", 15, col))
	_ignore_all(vb)
	return b


func hide_menu() -> void:
	if menu_root:
		menu_root.queue_free()
		menu_root = null


func show_end(victory: bool, lines: String) -> void:
	hide_end()
	end_root = CenterContainer.new()
	end_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(end_root)
	var p := PanelContainer.new()
	p.add_theme_stylebox_override("panel", _panel_box(30, Color(0.05, 0.04, 0.07, 0.95), GOLD_C if victory else HP_C, 2, 12, 28))
	end_root.add_child(p)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 14)
	p.add_child(v)
	var t := _label("VICTORY" if victory else "THE REALM HAS FALLEN", 48, GOLD_C if victory else HP_C)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(t)
	var body := _label(lines, 18)
	body.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(body)
	var h := HBoxContainer.new()
	h.alignment = BoxContainer.ALIGNMENT_CENTER
	h.add_theme_constant_override("separation", 14)
	v.add_child(h)
	h.add_child(_button("Play Again", func(): game.start_run(game.faction, game.hero), 18))
	h.add_child(_button("Main Menu", func(): game.to_menu(), 18))


func hide_end() -> void:
	if end_root:
		end_root.queue_free()
		end_root = null


# ------------------------------------------------------------------ hero select & war council

func _overlay_screen(title: String, sub: String) -> VBoxContainer:
	hide_menu()
	menu_root = Control.new()
	menu_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(menu_root)
	var shade := ColorRect.new()
	shade.color = Color(0.03, 0.02, 0.05, 0.62)
	shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	menu_root.add_child(shade)
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	menu_root.add_child(center)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 14)
	center.add_child(v)
	var t := _title(title, 52, GOLD_C)
	t.add_theme_constant_override("outline_size", 12)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(t)
	var s2 := _label(sub, 18, TEXT_C)
	s2.add_theme_constant_override("outline_size", 7)
	s2.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(s2)
	return v


## Heroes of one faction. Locked heroes can be unlocked with Renown right here.
func show_hero_select(fid: String) -> void:
	var f: Dictionary = GameData.FACTIONS[fid]
	var v := _overlay_screen("Choose your Commander", "%s  (%s)   -   Renown: %d" % [f["name"], f["pie"], game.renown()])
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 16)
	v.add_child(row)
	for hid in GameData.HEROES:
		var hd: Dictionary = GameData.HEROES[hid]
		if hd["faction"] != fid:
			continue
		var unlocked := game.hero_unlocked(hid)
		var col: Color = f["color"]
		var b := Button.new()
		b.focus_mode = Control.FOCUS_NONE
		b.custom_minimum_size = Vector2(250, 390)
		b.add_theme_stylebox_override("normal", _card_box(col if unlocked else Color(0.35, 0.35, 0.37), 0.28, Color(0.07, 0.06, 0.09, 0.95),
			col.darkened(0.3) if unlocked else Color(0.3, 0.3, 0.3), 2, 12))
		b.add_theme_stylebox_override("hover", _card_box(col, 0.5, Color(0.13, 0.11, 0.16, 0.97), col, 3, 12))
		b.add_theme_stylebox_override("pressed", _card_box(col, 0.4, Color(0.2, 0.16, 0.1, 0.97), col, 3, 12))
		var vb := VBoxContainer.new()
		vb.set_anchors_preset(Control.PRESET_FULL_RECT)
		vb.offset_left = 14
		vb.offset_right = -14
		vb.offset_top = 12
		vb.offset_bottom = -12
		vb.add_theme_constant_override("separation", 6)
		b.add_child(vb)
		var tr := TextureRect.new()
		tr.custom_minimum_size = Vector2(222, 170)
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		var path := "res://assets/custom/icons/%s.png" % hd["portrait"]
		if ResourceLoader.exists(path):
			tr.texture = load(path)
		if not unlocked:
			tr.modulate = Color(0.45, 0.45, 0.45)
		vb.add_child(tr)
		vb.add_child(_wrap_label(hd["name"], 222, 19, col if unlocked else DIM_C))
		for pw in hd["powers"]:
			vb.add_child(_wrap_label("- " + String(pw), 222, 14, TEXT_C if unlocked else DIM_C))
		if hd.has("sig"):
			vb.add_child(_wrap_label("%s: %s" % [hd["sig"]["name"], hd["sig"]["desc"]], 222, 13, GOLD_C if unlocked else DIM_C))
		var spacer := Control.new()
		spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
		vb.add_child(spacer)
		if unlocked:
			vb.add_child(_label("Click to begin", 15, col))
			b.pressed.connect(func():
				game.sfx("card")
				game.start_run(fid, hid))
		else:
			var cost: int = hd["cost"]
			var can := game.renown() >= cost
			vb.add_child(_label("Unlock: %d Renown" % cost, 15, GOLD_C if can else HP_C))
			b.pressed.connect(func():
				if game.unlock_hero(hid):
					show_hero_select(fid)
				else:
					toast("Not enough Renown - finish runs to earn it", HP_C))
		_ignore_all(vb)
		row.add_child(b)
	var foot := HBoxContainer.new()
	foot.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_child(foot)
	foot.add_child(_button("Back", func(): show_menu(game.stats), 18))


## Permanent upgrades bought with Renown (earned at the end of every run).
func show_council() -> void:
	var v := _overlay_screen("War Council", "Renown: %d   -   earned at the end of every run (more for later waves, harder difficulties and victories)" % game.renown())
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 16)
	grid.add_theme_constant_override("v_separation", 12)
	v.add_child(grid)
	for k in GameData.META_UPGRADES:
		var m: Dictionary = GameData.META_UPGRADES[k]
		var lvl := game.meta_level(k)
		var costs: Array = m["costs"]
		var p := PanelContainer.new()
		p.custom_minimum_size = Vector2(420, 0)
		var vb := VBoxContainer.new()
		p.add_child(vb)
		vb.add_child(_label("%s   %s" % [m["name"], "*".repeat(lvl) + "-".repeat(costs.size() - lvl)], 20, GOLD_C))
		vb.add_child(_wrap_label(m["desc"], 390, 15))
		if lvl >= costs.size():
			vb.add_child(_label("Fully upgraded", 15, DIM_C))
		else:
			var cost: int = costs[lvl]
			var bb := _button("Upgrade  (%d Renown)" % cost, func():
				game.buy_meta(k)
				show_council(), 16)
			bb.disabled = game.renown() < cost
			vb.add_child(bb)
		grid.add_child(p)
	var foot := HBoxContainer.new()
	foot.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_child(foot)
	foot.add_child(_button("Back", func(): show_menu(game.stats), 18))
