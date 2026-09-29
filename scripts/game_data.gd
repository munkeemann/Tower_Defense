class_name GameData
extends RefCounted
## All game content lives here as plain data. Adding a faction, tower, enemy,
## boon or road segment should mostly mean adding an entry below.

const TILE := 2.0
const GRID := 45
const MAX_WAVES := 30
const START_GOLD := 220
const START_HP := 20
## A new portal (path branch) opens before each of these waves.
const BRANCH_WAVES := [1, 12, 22]
const BRANCH_NAMES := ["North", "South", "East", "West"]

# Tower level scaling (index = level - 1).
const LEVEL_DMG := [1.0, 1.55, 2.3]
const LEVEL_RANGE := [1.0, 1.1, 1.2]
const LEVEL_RATE := [1.0, 1.1, 1.25]
const LEVEL_BUFF := [1.0, 1.4, 1.8]
const UPGRADE_COST := [0.8, 1.25]  # fraction of base cost for lvl 2, lvl 3
const SELL_REFUND := 0.7
const LEY_BONUS := 0.25
## Each level of high ground adds this much tower range (Tower Dominion-style elevation).
const ELEVATION_RANGE := 0.15
## Raise Ground: cost = RAISE_BASE + RAISE_STEP * current level.
const RAISE_BASE := 40
const RAISE_STEP := 30

const TARGET_MODES := ["First", "Last", "Strongest", "Closest"]

## Every run rolls a biome, which shapes the procedurally generated map.
## hills: shifts terrain height (+ = more high ground). tree/rock: noise thresholds (lower = more).
const BIOMES := {
	"greenvale": {"name": "Greenvale", "desc": "Rolling meadows, scattered woods and a few ponds.",
		"hills": 0.0, "hill_freq": 0.05, "tree": 0.28, "rock": 0.45, "lakes": 2, "ley": 16,
		"trees": ["prop_oak", "prop_oak", "prop_pine", "prop_birch"], "tint": Color(1.0, 1.0, 1.0)},
	"highlands": {"name": "Highlands", "desc": "Windswept ridges and plateaus. High ground everywhere.",
		"hills": 0.1, "hill_freq": 0.065, "tree": 0.4, "rock": 0.28, "lakes": 0, "ley": 14,
		"trees": ["prop_pine", "prop_pine", "prop_oak"], "tint": Color(0.97, 0.97, 0.86)},
	"lakelands": {"name": "Lakelands", "desc": "Low marshy country dotted with lakes.",
		"hills": -0.1, "hill_freq": 0.045, "tree": 0.32, "rock": 0.5, "lakes": 7, "ley": 16,
		"trees": ["prop_birch", "prop_birch", "prop_oak"], "tint": Color(0.95, 1.04, 0.95)},
	"deepwood": {"name": "Deepwood", "desc": "An ancient forest, thick with trees and ley crystals.",
		"hills": 0.0, "hill_freq": 0.05, "tree": 0.12, "rock": 0.5, "lakes": 1, "ley": 24,
		"trees": ["prop_pine", "prop_oak", "prop_pine", "prop_birch"], "tint": Color(0.86, 0.98, 0.86)},
}

const DIFFICULTIES := [
	{"name": "Normal", "hp": 1.0, "count": 1.0, "desc": "The intended experience."},
	{"name": "Hard", "hp": 1.7, "count": 1.25, "desc": "Tougher, larger waves."},
	{"name": "Brutal", "hp": 2.3, "count": 1.4, "desc": "For Tower Dominion veterans."},
]

## The color pie. Every run is one color (set by your commander). You draft that color's own towers plus
## the shared towers every color can use. "passive" is folded into the run's modifiers like a hero's fx.
const SHARED_TOWERS := ["archer", "ballista", "trebuchet", "bombard"]
const FACTIONS := {
	"crown": {
		"name": "The Aurelian Crown", "pie": "White", "race": "Humans",
		"color": Color(0.95, 0.92, 0.78),
		"desc": "Disciplined humans. Arcane spires, holy chapels, war banners and gryphon riders.",
		"strengths": "Support auras, reliable all-round defense",
		"weakness": "No standout damage tricks",
		"passive_name": "Order", "passive_desc": "Support auras are 30% stronger. +5 castle health.",
		"passive": {"aura_mult": 1.3, "hp": 5},
		"towers": ["arcane", "chapel", "banner", "gryphon"],
		"start": ["archer", "ballista", "arcane"],
		"start_copies": {"archer": 3, "ballista": 1, "arcane": 1},
		"ability": {"name": "Rally Cry", "desc": "All towers attack 60% faster for 8 seconds.",
			"cooldown": 45.0, "kind": "haste", "power": 0.6, "duration": 8.0},
	},
	"verdant": {
		"name": "The Verdant Circle", "pie": "Green", "race": "Elves",
		"color": Color(0.45, 0.85, 0.4),
		"desc": "Elven druids of the deep wood. Poison, thorns and living trees that root, slow and wear down the horde.",
		"strengths": "Slows, poison, crowd control",
		"weakness": "Low burst damage against armor",
		"passive_name": "Wildgrowth", "passive_desc": "Slows and poison are 20% stronger.",
		"passive": {"slow_mult": 1.2, "poison_mult": 1.2},
		"towers": ["thorn", "spore", "briar", "treant", "storm", "hive", "moonwell", "rootbinder"],
		"start": ["thorn", "spore", "briar"],
		"start_copies": {"thorn": 3, "spore": 1, "briar": 2},
		"ability": {"name": "Entangling Roots", "desc": "Roots every ground enemy for 3 seconds and deals 40 damage.",
			"cooldown": 50.0, "kind": "root", "duration": 3.0, "damage": 40.0},
	},
	"forge": {
		"name": "The Deep Forge", "pie": "Red", "race": "Dwarves",
		"color": Color(0.92, 0.36, 0.25),
		"desc": "Dwarven engineers. Flamethrowers, steam hammers, colossal mortars and flak batteries.",
		"strengths": "Huge damage, splash, crushes armor",
		"weakness": "Slow to fire, weak against flyers and camouflage",
		"passive_name": "Forgecraft", "passive_desc": "+15% physical damage. Upgrades cost 15% less.",
		"passive": {"phys": 0.15, "upgrade_discount": 0.15},
		"towers": ["dwarf_flame", "dwarf_hammer", "dwarf_mortar", "dwarf_gyro"],
		"start": ["archer", "dwarf_flame", "dwarf_hammer"],
		"start_copies": {"archer": 3, "dwarf_flame": 2, "dwarf_hammer": 1},
		"ability": {"name": "Forgefire Barrage", "desc": "Deals 60 damage (+15 per wave) to every ground enemy.",
			"cooldown": 45.0, "kind": "blast", "damage": 60.0, "duration": 0.0},
	},
	"tide": {
		"name": "The Tidal Court", "pie": "Blue", "race": "Merfolk",
		"color": Color(0.35, 0.65, 0.98),
		"desc": "Merfolk of the deep. Tides, harpoons, whirlpools and siren song that control the battlefield.",
		"strengths": "Slows, pushback, stuns; loves water",
		"weakness": "Low raw damage, struggles against bosses",
		"passive_name": "Tidebound", "passive_desc": "Towers next to water deal +30% damage, and your tiles bring more ponds.",
		"passive": {"water_dmg": 0.3, "ponds": 0.25},
		"towers": ["mer_tide", "mer_harpoon", "mer_whirl", "mer_siren"],
		"start": ["archer", "mer_tide", "mer_harpoon"],
		"start_copies": {"archer": 2, "mer_tide": 2, "mer_harpoon": 1},
		"ability": {"name": "Tidal Surge", "desc": "Washes every enemy 3 tiles back along the road and slows them 40% for 3 seconds.",
			"cooldown": 50.0, "kind": "surge", "push": 3.0, "duration": 3.0},
	},
	"grave": {
		"name": "The Bone Legion", "pie": "Black", "race": "Skeletons",
		"color": Color(0.62, 0.45, 0.85),
		"desc": "The restless dead. Cheap bone archers, plague, soul-draining obelisks and cursed tombs.",
		"strengths": "Attrition, poison, shreds bosses and big health pools",
		"weakness": "Short range, slow to kill fast swarms",
		"passive_name": "Plague Tide", "passive_desc": "Poisoned enemies burst when they die, hitting nearby enemies for 15% of their max health.",
		"passive": {"death_burst": 0.15, "poison_mult": 1.15},
		"towers": ["bone_crypt", "plague_cauldron", "soul_obelisk", "hex_tomb"],
		"start": ["bone_crypt", "plague_cauldron", "archer"],
		"start_copies": {"bone_crypt": 4, "plague_cauldron": 1, "archer": 2},
		"ability": {"name": "Reaping", "desc": "Every enemy loses 15% of its max health (bosses 5%).",
			"cooldown": 50.0, "kind": "reap", "pct": 0.15, "duration": 0.0},
	},
}


## Every tower a run of this color can draft: its own towers plus the shared ones.
static func run_towers(fid: String) -> Array:
	var out: Array = SHARED_TOWERS.duplicate()
	out.append_array(FACTIONS[fid]["towers"])
	return out

## attack kinds: arrow (homing), bolt (straight, pierces), lob (arc, ground only),
## orb (slow homing), chain (instant lightning), slam (instant splash at target),
## aura_dmg (pulses around tower), aura_buff (boosts nearby towers)
const TOWERS := {
	# ---------------- Aurelian Crown ----------------
	"archer": {"name": "Archer Tower", "cost": 60, "attack": "arrow", "dmg": 10.0, "rate": 1.6, "range": 3.6,
		"dtype": "phys", "air": true, "ground": true, "color": Color(0.35, 0.55, 0.9),
		"desc": "Cheap, reliable, hits air and ground."},
	"ballista": {"name": "Ballista", "cost": 110, "attack": "bolt", "dmg": 48.0, "rate": 0.55, "range": 6.2,
		"dtype": "phys", "air": true, "ground": true, "pierce": true, "color": Color(0.6, 0.42, 0.25),
		"desc": "Heavy bolts that pierce through every enemy in a line."},
	"arcane": {"name": "Arcane Spire", "cost": 125, "attack": "orb", "dmg": 26.0, "rate": 0.9, "range": 4.2,
		"dtype": "magic", "air": true, "ground": true, "splash": 0.6, "shred": true, "color": Color(0.65, 0.4, 1.0),
		"desc": "Magic orbs that ignore armor and burst on impact."},
	"trebuchet": {"name": "Trebuchet", "cost": 150, "attack": "lob", "dmg": 66.0, "rate": 0.33, "range": 8.5,
		"dtype": "phys", "air": false, "ground": true, "splash": 1.4, "color": Color(0.55, 0.45, 0.35),
		"desc": "Enormous range. Boulders crush whole groups. Can't hit flyers."},
	"chapel": {"name": "Chapel of Dawn", "cost": 115, "attack": "aura_dmg", "dmg": 12.0, "rate": 1.0, "range": 2.4,
		"dtype": "magic", "air": true, "ground": true, "slow": [0.3, 1.2], "detect": true, "color": Color(1.0, 0.92, 0.6),
		"desc": "Radiant pulses burn and slow everything nearby."},
	"banner": {"name": "War Banner", "cost": 120, "attack": "aura_buff", "dmg": 0.0, "rate": 0.0, "range": 2.6,
		"buff": {"dmg": 0.25}, "color": Color(0.85, 0.2, 0.2),
		"desc": "Nearby towers deal +25% damage (scales with level)."},
	"gryphon": {"name": "Gryphon Roost", "cost": 150, "attack": "arrow", "dmg": 24.0, "rate": 1.3, "range": 5.5,
		"dtype": "phys", "air": true, "ground": false, "air_bonus": 1.5, "detect": true, "color": Color(0.9, 0.75, 0.45),
		"desc": "Anti-air specialist. Massive damage to flying enemies only."},
	"bombard": {"name": "Royal Bombard", "cost": 200, "attack": "lob", "dmg": 58.0, "rate": 0.4, "range": 4.4,
		"dtype": "phys", "air": false, "ground": true, "splash": 1.1, "stun": [0.25, 0.7], "color": Color(0.3, 0.3, 0.35),
		"desc": "Short-range cannon. Big splash, may stun."},
	# ---------------- Verdant Circle ----------------
	"thorn": {"name": "Thornspitter", "cost": 55, "attack": "arrow", "dmg": 6.0, "rate": 2.6, "range": 3.4,
		"dtype": "phys", "air": true, "ground": true, "color": Color(0.4, 0.75, 0.3),
		"desc": "Rapid-fire thorns. Hits air and ground."},
	"spore": {"name": "Spore Mound", "cost": 100, "attack": "lob", "dmg": 14.0, "rate": 0.6, "range": 4.2,
		"dtype": "magic", "air": false, "ground": true, "splash": 1.3, "dot": [12.0, 4.0], "color": Color(0.6, 0.35, 0.7),
		"desc": "Lobs spore pods that poison groups over time."},
	"briar": {"name": "Briar Thicket", "cost": 80, "attack": "aura_dmg", "dmg": 7.0, "rate": 1.2, "range": 2.0,
		"dtype": "phys", "air": false, "ground": true, "slow": [0.45, 1.0], "color": Color(0.35, 0.5, 0.2),
		"desc": "Thorny vines heavily slow and scratch passing ground enemies."},
	"treant": {"name": "Elder Treant", "cost": 150, "attack": "slam", "dmg": 72.0, "rate": 0.55, "range": 2.6,
		"dtype": "phys", "air": false, "ground": true, "splash": 1.0, "stun": [0.2, 0.8], "color": Color(0.45, 0.3, 0.18),
		"desc": "Slams the ground at short range. Crushing splash, may stun."},
	"storm": {"name": "Stormcaller Oak", "cost": 165, "attack": "chain", "dmg": 34.0, "rate": 0.7, "range": 4.6,
		"dtype": "magic", "air": true, "ground": true, "chain": 4, "shred": true, "color": Color(0.4, 0.6, 1.0),
		"desc": "Lightning that arcs between up to 5 enemies."},
	"hive": {"name": "Wasp Hive", "cost": 120, "attack": "arrow", "dmg": 5.0, "rate": 5.0, "range": 4.0,
		"dtype": "phys", "air": true, "ground": true, "air_bonus": 2.0, "detect": true, "color": Color(0.95, 0.8, 0.2),
		"desc": "A swarm of stingers. Double damage to flyers; the swarm sniffs out camouflaged enemies."},
	"moonwell": {"name": "Moonwell", "cost": 110, "attack": "aura_buff", "dmg": 0.0, "rate": 0.0, "range": 2.6,
		"buff": {"rate": 0.25}, "detect": true, "color": Color(0.5, 0.9, 1.0),
		"desc": "Nearby towers attack 25% faster (scales with level)."},
	"rootbinder": {"name": "Rootbinder Shrine", "cost": 170, "attack": "orb", "dmg": 26.0, "rate": 0.5, "range": 5.2,
		"dtype": "magic", "air": false, "ground": true, "stun": [1.0, 1.1], "color": Color(0.3, 0.9, 0.5),
		"desc": "Every hit roots a ground enemy in place."},
	# ---------------- Red: the Deep Forge (dwarves) ----------------
	"dwarf_flame": {"name": "Flame Belcher", "cost": 85, "attack": "aura_dmg", "dmg": 10.0, "rate": 2.2, "range": 2.8,
		"dtype": "magic", "air": true, "ground": true, "dot": [8.0, 2.0], "color": Color(1.0, 0.45, 0.15),
		"desc": "Breathes fire in a cone in front of it, burning everything it touches."},
	"dwarf_hammer": {"name": "Runic Hammer", "cost": 150, "attack": "slam", "dmg": 95.0, "rate": 0.5, "range": 2.6,
		"dtype": "phys", "air": false, "ground": true, "splash": 1.2, "stun": [0.35, 1.0], "shred": true, "color": Color(0.8, 0.45, 0.3),
		"desc": "A rune-powered steam hammer. Crushes groups, stuns, and shatters shields."},
	"dwarf_mortar": {"name": "Siege Mortar", "cost": 190, "attack": "lob", "dmg": 120.0, "rate": 0.25, "range": 9.5,
		"dtype": "phys", "air": false, "ground": true, "splash": 1.9, "color": Color(0.45, 0.4, 0.36),
		"desc": "Colossal range and blast radius. Can't hit flyers."},
	"dwarf_gyro": {"name": "Flak Battery", "cost": 135, "attack": "arrow", "dmg": 16.0, "rate": 2.4, "range": 5.8,
		"dtype": "phys", "air": true, "ground": false, "air_bonus": 1.5, "color": Color(0.85, 0.62, 0.3),
		"desc": "Twin rotary flak guns that shred flyers. Can't hit the ground."},
	# ---------------- Blue: the Tidal Court (merfolk) ----------------
	"mer_tide": {"name": "Tide Spire", "cost": 90, "attack": "aura_dmg", "dmg": 8.0, "rate": 0.8, "range": 2.8,
		"dtype": "magic", "air": true, "ground": true, "slow": [0.4, 1.5], "detect": true, "color": Color(0.35, 0.78, 0.95),
		"desc": "Pulses of tidewater slow everything nearby. Senses camouflaged enemies."},
	"mer_harpoon": {"name": "Coral Harpooner", "cost": 120, "attack": "bolt", "dmg": 36.0, "rate": 0.7, "range": 6.0,
		"dtype": "phys", "air": true, "ground": true, "pierce": true, "slow": [0.3, 1.2], "color": Color(0.95, 0.55, 0.55),
		"desc": "Barbed harpoons pierce a whole line and slow every enemy they hit."},
	"mer_whirl": {"name": "Whirlpool Shrine", "cost": 160, "attack": "aura_dmg", "dmg": 14.0, "rate": 0.5, "range": 2.5,
		"dtype": "magic", "air": false, "ground": true, "push": [0.3, 1.6], "color": Color(0.3, 0.55, 0.95),
		"desc": "A swirling vortex that drags ground enemies back along the road."},
	"mer_siren": {"name": "Siren Rock", "cost": 150, "attack": "chain", "dmg": 24.0, "rate": 0.6, "range": 5.0,
		"dtype": "magic", "air": true, "ground": true, "chain": 3, "stun": [0.25, 0.9], "color": Color(0.6, 0.85, 1.0),
		"desc": "A siren's song arcs between enemies and can leave them spellbound."},
	# ---------------- Black: the Bone Legion (skeletons) ----------------
	"bone_crypt": {"name": "Bone Crypt", "cost": 50, "attack": "arrow", "dmg": 8.5, "rate": 1.9, "range": 3.5,
		"dtype": "phys", "air": true, "ground": true, "color": Color(0.88, 0.86, 0.76),
		"desc": "Cheap skeleton archers. Hits air and ground."},
	"plague_cauldron": {"name": "Plague Cauldron", "cost": 105, "attack": "lob", "dmg": 10.0, "rate": 0.55, "range": 4.2,
		"dtype": "magic", "air": false, "ground": true, "splash": 1.4, "dot": [16.0, 4.0], "color": Color(0.5, 0.85, 0.3),
		"desc": "Hurls bubbling plague that poisons whole groups."},
	"soul_obelisk": {"name": "Soul Obelisk", "cost": 165, "attack": "orb", "dmg": 20.0, "rate": 0.45, "range": 5.0,
		"dtype": "magic", "air": true, "ground": true, "pct": 0.09, "color": Color(0.65, 0.35, 0.95),
		"desc": "Rips out 9% of a target's current health with every hit. Bosses resist."},
	"hex_tomb": {"name": "Hex Tomb", "cost": 140, "attack": "aura_curse", "dmg": 0.0, "rate": 0.0, "range": 2.8,
		"curse": 0.25, "air": true, "ground": true, "color": Color(0.55, 0.3, 0.7),
		"desc": "Curses nearby enemies: they take +25% damage from everything (scales with level)."},
}

## speed is in tiles per second.
const ENEMIES := {
	"goblin": {"name": "Goblin", "hp": 38.0, "speed": 1.15, "armor": 0.0, "resist": 0.0, "gold": 4, "leak": 1,
		"cost": 1, "min_wave": 1, "color": Color(0.45, 0.7, 0.25), "size": 0.6, "h": 1.4},
	"wolf": {"name": "War Hound", "hp": 26.0, "speed": 2.0, "armor": 0.0, "resist": 0.0, "gold": 3, "leak": 1,
		"cost": 1, "min_wave": 2, "color": Color(0.85, 0.6, 0.3), "size": 0.6, "h": 1.2},
	"wasp": {"name": "Giant Wasp", "hp": 30.0, "speed": 1.9, "armor": 0.0, "resist": 0.0, "gold": 4, "leak": 1,
		"cost": 2, "min_wave": 9, "flying": true, "color": Color(0.95, 0.8, 0.2), "size": 0.6, "h": 1.0},
	"frostimp": {"name": "Frost Imp", "hp": 80.0, "speed": 1.3, "armor": 0.0, "resist": 0.5, "gold": 7, "leak": 1,
		"cost": 3, "min_wave": 13, "color": Color(0.3, 0.6, 0.9), "size": 0.7, "h": 1.6},
	"gargoyle": {"name": "Gargoyle", "hp": 125.0, "speed": 0.8, "armor": 0.5, "resist": 0.1, "gold": 10, "leak": 2,
		"cost": 4, "min_wave": 16, "flying": true, "color": Color(0.6, 0.7, 0.35), "size": 0.9, "h": 1.4},
	"spikeback": {"name": "Spikeback", "hp": 230.0, "speed": 0.7, "armor": 0.45, "resist": 0.2, "gold": 12, "leak": 3,
		"cost": 5, "min_wave": 18, "color": Color(0.3, 0.45, 0.3), "size": 1.0, "h": 1.9},
	"orc": {"name": "Orc Brute", "hp": 115.0, "speed": 0.85, "armor": 0.35, "resist": 0.0, "gold": 8, "leak": 2,
		"cost": 3, "min_wave": 4, "color": Color(0.3, 0.45, 0.2), "size": 0.9, "h": 1.9},
	"harpy": {"name": "Harpy", "hp": 42.0, "speed": 1.45, "armor": 0.0, "resist": 0.1, "gold": 6, "leak": 1,
		"cost": 2, "min_wave": 5, "flying": true, "color": Color(0.6, 0.35, 0.6), "size": 0.7, "h": 1.3},
	"slime": {"name": "Gel Slime", "hp": 70.0, "speed": 0.95, "armor": 0.0, "resist": 0.2, "gold": 3, "leak": 1,
		"cost": 3, "min_wave": 6, "split": {"into": "slimelet", "count": 3}, "color": Color(0.3, 0.9, 0.5), "size": 0.8, "h": 1.2},
	"slimelet": {"name": "Slimelet", "hp": 22.0, "speed": 1.25, "armor": 0.0, "resist": 0.2, "gold": 1, "leak": 1,
		"cost": 1, "min_wave": 999, "color": Color(0.4, 0.95, 0.6), "size": 0.45, "h": 0.7},
	"shaman": {"name": "Goblin Shaman", "hp": 60.0, "speed": 0.95, "armor": 0.0, "resist": 0.3, "gold": 7, "leak": 1,
		"cost": 3, "min_wave": 8, "heal": {"radius": 3.0, "hps": 8.0}, "color": Color(0.7, 0.5, 0.3), "size": 0.65, "h": 1.4},
	"hexguard": {"name": "Hexguard", "hp": 130.0, "speed": 0.9, "armor": 0.1, "resist": 0.6, "gold": 9, "leak": 2,
		"cost": 4, "min_wave": 11, "color": Color(0.35, 0.2, 0.5), "size": 0.85, "h": 1.8},
	"ironclad": {"name": "Ironclad", "hp": 170.0, "speed": 0.75, "armor": 0.6, "resist": 0.0, "gold": 10, "leak": 2,
		"cost": 4, "min_wave": 14, "color": Color(0.55, 0.55, 0.6), "size": 0.95, "h": 2.0},
	"skeleton": {"name": "Skeleton", "hp": 45.0, "speed": 1.1, "armor": 0.15, "resist": 0.0, "gold": 2, "leak": 1,
		"cost": 1, "min_wave": 999, "color": Color(0.9, 0.88, 0.8), "size": 0.6, "h": 1.5},
	# ---------------- Bosses ----------------
	"troll": {"name": "Frost Troll", "hp": 2600.0, "speed": 0.6, "armor": 0.3, "resist": 0.0, "gold": 120, "leak": 10,
		"cost": 0, "min_wave": 999, "boss": true, "regen": 20.0, "color": Color(0.7, 0.85, 0.9), "size": 1.8, "h": 3.6},
	"dragon": {"name": "Ember Dragon", "hp": 6500.0, "speed": 0.65, "armor": 0.2, "resist": 0.25, "gold": 250, "leak": 15,
		"cost": 0, "min_wave": 999, "boss": true, "flying": true, "color": Color(0.85, 0.4, 0.15), "size": 2.0, "h": 3.2},
	"lich": {"name": "The Lich King", "hp": 16000.0, "speed": 0.5, "armor": 0.2, "resist": 0.45, "gold": 500, "leak": 20,
		"cost": 0, "min_wave": 999, "boss": true, "summon": {"type": "skeleton", "every": 2.5, "count": 2},
		"color": Color(0.2, 0.2, 0.3), "size": 1.9, "h": 3.8},
}

const BOSS_WAVES := {10: "troll", 20: "dragon", 30: "lich"}

## Road segments. Moves: F = forward, L = turn left then step, R = turn right then step.
## Shorter roads pay gold because they give your towers less time to shoot.
const SEGMENTS := [
	{"name": "Straight Road", "moves": "FFFF", "gold": 0},
	{"name": "Long Road", "moves": "FFFFFF", "gold": 0},
	{"name": "Short Cut", "moves": "FF", "gold": 45},
	{"name": "Left Bend", "moves": "FLFF", "gold": 0},
	{"name": "Right Bend", "moves": "FRFF", "gold": 0},
	{"name": "Sharp Left", "moves": "LFF", "gold": 15},
	{"name": "Sharp Right", "moves": "RFF", "gold": 15},
	{"name": "Winding Road", "moves": "FLFRFF", "gold": 0},
	{"name": "Serpent Road", "moves": "FRFLFF", "gold": 0},
	{"name": "Switchback", "moves": "LFLFF", "gold": 0},
	{"name": "Switchback", "moves": "RFRFF", "gold": 0},
	{"name": "Grand Loop", "moves": "FLFFLFFRF", "gold": 0},
	{"name": "Grand Loop", "moves": "FRFFRFFLF", "gold": 0},
	{"name": "Gold Trail", "moves": "FFF", "gold": 30},
]

const RARITY_NAMES := ["Common", "Rare", "Epic"]
const RARITY_COLORS := [Color(0.8, 0.8, 0.8), Color(0.35, 0.65, 1.0), Color(0.8, 0.45, 1.0)]

## Boons offered after each wave. Effects are applied in Game.apply_boon().
const BOONS := [
	{"id": "war_chest", "name": "War Chest", "rarity": 0, "weight": 10},
	{"id": "whetstone", "name": "Whetstones", "rarity": 0, "weight": 8, "desc": "+12% physical damage for all towers."},
	{"id": "attune", "name": "Arcane Attunement", "rarity": 0, "weight": 8, "desc": "+12% magic damage for all towers."},
	{"id": "range", "name": "Watchtowers", "rarity": 1, "weight": 5, "desc": "+8% range for all towers."},
	{"id": "rate", "name": "Drill Sergeants", "rarity": 1, "weight": 5, "desc": "+10% attack speed for all towers."},
	{"id": "discount", "name": "Guild Discount", "rarity": 1, "weight": 5, "desc": "Towers and upgrades cost 10% less."},
	{"id": "bounty", "name": "Bounty Hunters", "rarity": 0, "weight": 6, "desc": "+1 gold for every enemy killed."},
	{"id": "masons", "name": "Stonemasons", "rarity": 0, "weight": 6, "desc": "+5 max castle health and fully repair the castle."},
	{"id": "treasury", "name": "Royal Treasury", "rarity": 1, "weight": 5, "desc": "+20 gold at the end of every wave."},
	{"id": "ley", "name": "Ley Surge", "rarity": 1, "weight": 4, "desc": "Towers on ley crystals get a further +25% damage."},
	{"id": "crit", "name": "Keen Edges", "rarity": 2, "weight": 3, "desc": "Every attack has a 12% chance to deal triple damage."},
	{"id": "execute", "name": "Executioner", "rarity": 2, "weight": 3, "desc": "Enemies below 12% health die instantly when hit."},
	{"id": "ability", "name": "Commander's Focus", "rarity": 1, "weight": 4, "desc": "Your faction ability recharges 25% faster."},
]


# ====================================================================== Tower Dominion-style systems

## ---- Terrain tiles -------------------------------------------------------------------------
## The map grows from 5x5-cell terrain tiles attached to open road ends. Templates are drawn
## entering from the SOUTH port (2,4); ports sit mid-edge: N (2,0), W (0,2), E (4,2).
## A family is one card; its variants are what "rotate" cycles through.
const CHUNK := 5
const EXPAND_EVERY := 1
const DOCTRINE_EVERY := 2
const TILE_FAMILIES := {
	"straight": {"name": "Straight Road", "weight": 9, "desc": "A plain stretch of road.",
		"variants": [[[[2, 4], [2, 3], [2, 2], [2, 1], [2, 0]]]]},
	"winding": {"name": "Winding Road", "weight": 9, "desc": "Snakes back and forth: a longer road for your towers.",
		"variants": [[[[2, 4], [2, 3], [1, 3], [1, 2], [1, 1], [2, 1], [2, 0]]],
			[[[2, 4], [2, 3], [3, 3], [3, 2], [3, 1], [2, 1], [2, 0]]]]},
	"bend": {"name": "Bend", "weight": 9, "desc": "Turns the road left or right.",
		"variants": [[[[2, 4], [2, 3], [2, 2], [1, 2], [0, 2]]], [[[2, 4], [2, 3], [2, 2], [3, 2], [4, 2]]]]},
	"long_bend": {"name": "Long Bend", "weight": 6, "desc": "A long hooked turn: lots of road in one tile.",
		"variants": [[[[2, 4], [2, 3], [3, 3], [3, 2], [3, 1], [2, 1], [1, 1], [1, 2], [0, 2]]],
			[[[2, 4], [2, 3], [1, 3], [1, 2], [1, 1], [2, 1], [3, 1], [3, 2], [4, 2]]]]},
	"fork": {"name": "Fork", "weight": 4, "desc": "Splits the road: one more entry point, and +1 Rune per wave while it stays open.",
		"variants": [[[[2, 4], [2, 3], [2, 2], [1, 2], [0, 2]], [[2, 2], [3, 2], [4, 2]]],
			[[[2, 4], [2, 3], [2, 2], [2, 1], [2, 0]], [[2, 2], [3, 2], [4, 2]]],
			[[[2, 4], [2, 3], [2, 2], [2, 1], [2, 0]], [[2, 2], [1, 2], [0, 2]]]]},
}

## ---- Neutral buildings (appear on tiles; boost adjacent towers) -------------------------------
const NEUTRALS := {
	"ammo": {"name": "Ammo Depot", "model": "bld_ammo_depot", "desc": "Towers next to it attack 25% faster."},
	"relay": {"name": "Relay Station", "model": "bld_relay", "desc": "Towers next to it get +20% range."},
	"scout": {"name": "Scout Hideout", "model": "bld_scout", "desc": "Reveals camouflaged enemies within 4 tiles."},
	"supply": {"name": "Supply Point", "model": "bld_supply", "desc": "+15 gold after every wave."},
}

## ---- Discoveries hidden in the fog (claimed when a tile covers them or a tower's range reaches them)
const DISCOVERIES := {
	"chest": {"name": "Treasure Chest", "model": "poi_chest", "desc": "Gold and a Rune."},
	"shrine": {"name": "Ancient Shrine", "model": "poi_shrine", "desc": "Grants a free doctrine."},
	"mine": {"name": "Abandoned Mine", "model": "poi_mine", "desc": "+20 gold after every wave."},
	"ruins": {"name": "Forgotten Ruins", "model": "prop_ruin", "desc": "Two free blueprint copies."},
	"cache": {"name": "Rune Cache", "model": "poi_cache", "desc": "+3 Runes."},
}

## ---- Per-run threats (enemy modifiers rolled once per run) -----------------------------------
## trait: shield (extra shield health; magic and shield-breakers strip it), camo (only detecting
## towers / scout hideouts reveal it), swift (+40% speed)
const THREATS := {
	"skyhunters": {"name": "Harpy Flights", "enemy": "harpy", "desc": "Flyers. Only towers that hit air can stop them."},
	"wasps": {"name": "Wasp Swarms", "enemy": "wasp", "desc": "Fast flying swarms."},
	"gargoyles": {"name": "Gargoyles", "enemy": "gargoyle", "desc": "Armored flyers."},
	"shieldguard": {"name": "Shielded Hexguards", "enemy": "hexguard", "trait": "shield", "desc": "Shields absorb damage. Magic and shield-breakers strip them fast."},
	"stalkers": {"name": "Shadow Stalkers", "enemy": "wolf", "trait": "camo", "desc": "Camouflaged hounds. Towers need detection to target them."},
	"slimes": {"name": "Gel Slimes", "enemy": "slime", "desc": "Split into smaller slimes when killed."},
	"shamans": {"name": "Goblin Shamans", "enemy": "shaman", "desc": "Heal nearby enemies."},
	"ironclads": {"name": "Ironclads", "enemy": "ironclad", "desc": "Heavily armored. Magic damage works best."},
	"frost": {"name": "Frost Imps", "enemy": "frostimp", "trait": "swift", "desc": "Swift and resistant to magic."},
	"spikebacks": {"name": "Spikebacks", "enemy": "spikeback", "trait": "shield", "desc": "Huge shielded brutes."},
	"phantoms": {"name": "Phantom Legion", "enemy": "skeleton", "trait": "camo", "desc": "Camouflaged skeletons."},
}
const THREAT_WAVES := [4, 9, 15, 21]     # a new threat joins the invasion on each of these waves
const THREAT_REVEAL := 3                 # threats are revealed this many waves before they arrive
const BASE_ENEMIES := {"goblin": 1, "wolf": 2, "orc": 5}

## ---- Heroes (commanders) ---------------------------------------------------------------------
## fx: phys / magic / rate / range (added to mods), hp, start_copies {tid: n}, bonus_copies {tid: n},
## tower_dmg {tids, mult}, recon, detect_all, slow_mult, poison_mult, kill_gold, ability_cd
const HEROES := {
	"aldric": {"faction": "crown", "name": "Lord Marshal Aldric", "cost": 0, "portrait": "hero_aldric",
		"powers": ["All towers deal +10% damage.", "+5 castle health."],
		"fx": {"phys": 0.1, "magic": 0.1, "hp": 5}},
	"seraphine": {"faction": "crown", "name": "Archmage Seraphine", "cost": 0, "portrait": "hero_seraphine",
		"powers": ["+20% magic damage.", "Arcane Spire blueprints give +1 copy."],
		"fx": {"magic": 0.2, "bonus_copies": {"arcane": 1}}},
	"brann": {"faction": "crown", "name": "Siegemaster Brann", "cost": 40, "portrait": "hero_brann",
		"powers": ["Ballista, Trebuchet and Bombard deal +30% damage.", "Start with a Trebuchet blueprint."],
		"fx": {"tower_dmg": {"tids": ["ballista", "trebuchet", "bombard"], "mult": 0.3}, "start_copies": {"trebuchet": 1}}},
	"elsa": {"faction": "crown", "name": "Scout-Captain Elsa", "cost": 60, "portrait": "hero_elsa",
		"powers": ["Every tower can detect camouflaged enemies.", "+1 Rune after every wave."],
		"fx": {"detect_all": true, "recon": 1}},
	"thornwood": {"faction": "verdant", "name": "Elder Thornwood", "cost": 0, "portrait": "hero_thornwood",
		"powers": ["Slows are 30% stronger.", "Briar Thicket blueprints give +1 copy."],
		"fx": {"slow_mult": 1.3, "bonus_copies": {"briar": 1}}},
	"lira": {"faction": "verdant", "name": "Moon-priestess Lira", "cost": 0, "portrait": "hero_lira",
		"powers": ["All towers attack 15% faster.", "Moonwell blueprints give +1 copy."],
		"fx": {"rate": 0.15, "bonus_copies": {"moonwell": 1}}},
	"oma": {"faction": "verdant", "name": "Grovekeeper Oma", "cost": 40, "portrait": "hero_oma",
		"powers": ["Poison deals +60% damage.", "Start with an extra Spore Mound."],
		"fx": {"poison_mult": 1.6, "start_copies": {"spore": 1}}},
	"hunt": {"faction": "verdant", "name": "The Wild Hunt", "cost": 60, "portrait": "hero_hunt",
		"powers": ["+25% gold from kills.", "Your faction ability recharges 30% faster."],
		"fx": {"kill_gold": 0.25, "ability_cd": 0.7}},
	"durgan": {"faction": "forge", "name": "Thane Durgan Ironbeard", "cost": 0, "portrait": "hero_durgan",
		"powers": ["Runic Hammer and Siege Mortar deal +25% damage.", "Start with a Siege Mortar blueprint."],
		"fx": {"tower_dmg": {"tids": ["dwarf_hammer", "dwarf_mortar"], "mult": 0.25}, "start_copies": {"dwarf_mortar": 1}}},
	"nerissa": {"faction": "tide", "name": "Tidequeen Nerissa", "cost": 0, "portrait": "hero_nerissa",
		"powers": ["Slows are 25% stronger.", "+1 Rune after every wave."],
		"fx": {"slow_mult": 1.25, "recon": 1}},
	"mortis": {"faction": "grave", "name": "Mortis, the Bone Lord", "cost": 0, "portrait": "hero_mortis",
		"powers": ["Poison deals +40% damage.", "+20% gold from kills."],
		"fx": {"poison_mult": 1.4, "kill_gold": 0.2}},
}

## ---- Tower specializations (chosen when a tower reaches level III) --------------------------
## fx: dmg / range / rate (multiplier add), multishot (extra targets), splash (tiles), slow, stun,
## dot [dps, dur], dot_mult, chain (extra jumps), detect, shred, buff_dmg / buff_rate (aura add)
const SPECS := {
	"archer": [{"name": "Longbow", "desc": "+50% range, +30% damage.", "fx": {"range": 0.5, "dmg": 0.3}},
		{"name": "Volley", "desc": "Each attack also fires at 2 more enemies.", "fx": {"multishot": 2}}],
	"ballista": [{"name": "Siege Bolts", "desc": "+60% damage.", "fx": {"dmg": 0.6}},
		{"name": "Repeater", "desc": "+80% attack speed.", "fx": {"rate": 0.8}}],
	"arcane": [{"name": "Arcane Nova", "desc": "Orbs explode in a much larger blast.", "fx": {"splash": 1.0}},
		{"name": "Spellbreaker", "desc": "+30% damage; strips shields even faster.", "fx": {"dmg": 0.3, "shred": true}}],
	"trebuchet": [{"name": "Firepots", "desc": "Impacts burn: 25 damage/s for 3s.", "fx": {"dot": [25.0, 3.0]}},
		{"name": "Heavy Stones", "desc": "Bigger impacts that can stun.", "fx": {"splash": 0.4, "stun": [0.3, 1.0]}}],
	"chapel": [{"name": "Sanctified Ground", "desc": "Pulses slow by 55%.", "fx": {"slow": [0.55, 1.5]}},
		{"name": "Revelation", "desc": "+40% damage.", "fx": {"dmg": 0.4}}],
	"banner": [{"name": "Rallying Standard", "desc": "Aura grants an extra +15% damage.", "fx": {"buff_dmg": 0.15}},
		{"name": "Drill Master", "desc": "Aura also grants +20% attack speed.", "fx": {"buff_rate": 0.2}}],
	"gryphon": [{"name": "Talon Strike", "desc": "+60% damage.", "fx": {"dmg": 0.6}},
		{"name": "Sky Hunter", "desc": "Attacks one extra enemy.", "fx": {"multishot": 1}}],
	"bombard": [{"name": "Grapeshot", "desc": "Much larger blast radius.", "fx": {"splash": 0.8}},
		{"name": "Concussive", "desc": "50% chance to stun for 1s.", "fx": {"stun": [0.5, 1.0]}}],
	"thorn": [{"name": "Venom Thorns", "desc": "Thorns poison: 10 damage/s for 3s.", "fx": {"dot": [10.0, 3.0]}},
		{"name": "Thorn Barrage", "desc": "Each attack also fires at 2 more enemies.", "fx": {"multishot": 2}}],
	"spore": [{"name": "Plague", "desc": "Poison deals 80% more damage.", "fx": {"dot_mult": 1.8}},
		{"name": "Choking Spores", "desc": "Spores also slow by 35%.", "fx": {"slow": [0.35, 2.0]}}],
	"briar": [{"name": "Strangleroot", "desc": "Vines can root enemies in place.", "fx": {"stun": [0.18, 0.8]}},
		{"name": "Razorvine", "desc": "+80% damage.", "fx": {"dmg": 0.8}}],
	"treant": [{"name": "Earthshaker", "desc": "Slams hit a much larger area.", "fx": {"splash": 0.8}},
		{"name": "Ancient Might", "desc": "+60% damage.", "fx": {"dmg": 0.6}}],
	"storm": [{"name": "Forked Lightning", "desc": "Lightning jumps to 3 more enemies.", "fx": {"chain": 3}},
		{"name": "Thunderhead", "desc": "+50% damage and a chance to stun.", "fx": {"dmg": 0.5, "stun": [0.15, 0.6]}}],
	"hive": [{"name": "Hornet Queen", "desc": "+50% damage.", "fx": {"dmg": 0.5}},
		{"name": "Swarm", "desc": "Each attack also fires at 2 more enemies.", "fx": {"multishot": 2}}],
	"moonwell": [{"name": "Lunar Font", "desc": "Aura grants an extra +15% attack speed.", "fx": {"buff_rate": 0.15}},
		{"name": "Moonlight", "desc": "Aura also grants +10% damage.", "fx": {"buff_dmg": 0.1}}],
	"rootbinder": [{"name": "Deep Roots", "desc": "Roots last almost twice as long.", "fx": {"stun": [1.0, 2.0]}},
		{"name": "Thornbind", "desc": "+80% damage and strips shields.", "fx": {"dmg": 0.8, "shred": true}}],
	"dwarf_flame": [{"name": "Dragonfire", "desc": "Burns 80% hotter.", "fx": {"dot_mult": 1.8}},
		{"name": "Wide Nozzle", "desc": "The fire cone reaches 40% further.", "fx": {"range": 0.4}}],
	"dwarf_hammer": [{"name": "Earthquake", "desc": "Slams hit a much larger area.", "fx": {"splash": 0.8}},
		{"name": "Runeforged", "desc": "+60% damage.", "fx": {"dmg": 0.6}}],
	"dwarf_mortar": [{"name": "Cluster Bombs", "desc": "Much bigger blasts.", "fx": {"splash": 0.8}},
		{"name": "Rapid Loader", "desc": "+60% attack speed.", "fx": {"rate": 0.6}}],
	"dwarf_gyro": [{"name": "Heavy Flak", "desc": "+60% damage.", "fx": {"dmg": 0.6}},
		{"name": "Spotters", "desc": "Detects camouflaged enemies and +30% range.", "fx": {"detect": true, "range": 0.3}}],
	"mer_tide": [{"name": "Undertow", "desc": "Slows by 60%.", "fx": {"slow": [0.6, 1.8]}},
		{"name": "Riptide", "desc": "+80% damage.", "fx": {"dmg": 0.8}}],
	"mer_harpoon": [{"name": "Barbed Volley", "desc": "Also fires at 2 more enemies.", "fx": {"multishot": 2}},
		{"name": "Leviathan Harpoon", "desc": "+70% damage.", "fx": {"dmg": 0.7}}],
	"mer_whirl": [{"name": "Maelstrom", "desc": "Drags enemies back much more often.", "fx": {"push": [0.55, 1.8]}},
		{"name": "Crushing Depths", "desc": "+100% damage.", "fx": {"dmg": 1.0}}],
	"mer_siren": [{"name": "Chorus", "desc": "The song jumps to 3 more enemies.", "fx": {"chain": 3}},
		{"name": "Lullaby", "desc": "Stuns more often, for longer.", "fx": {"stun": [0.45, 1.3]}}],
	"bone_crypt": [{"name": "Bone Volley", "desc": "Also fires at 2 more enemies.", "fx": {"multishot": 2}},
		{"name": "Grave Arrows", "desc": "Arrows poison: 10 damage/s for 3s.", "fx": {"dot": [10.0, 3.0]}}],
	"plague_cauldron": [{"name": "Black Death", "desc": "Poison deals 80% more.", "fx": {"dot_mult": 1.8}},
		{"name": "Miasma", "desc": "Much bigger splash.", "fx": {"splash": 0.8}}],
	"soul_obelisk": [{"name": "Soul Harvest", "desc": "Rips out 14% of current health.", "fx": {"pct": 0.14}},
		{"name": "Twin Souls", "desc": "Hits one extra enemy.", "fx": {"multishot": 1}}],
	"hex_tomb": [{"name": "Doom", "desc": "The curse is 15% stronger.", "fx": {"curse": 0.15}},
		{"name": "Withering", "desc": "Cursed enemies are also slowed 25%.", "fx": {"slow": [0.25, 1.0]}}],
}

## ---- Meta progression (Renown, spent in the War Council between runs) -----------------------
const META_UPGRADES := {
	"gold": {"name": "Veteran Engineers", "desc": "+40 starting gold per level.", "costs": [20, 40, 60]},
	"recon": {"name": "Rune Hoard", "desc": "+1 starting Rune per level.", "costs": [15, 30, 45]},
	"armory": {"name": "Royal Armory", "desc": "+1 copy of your first starting tower per level.", "costs": [30, 60]},
	"keep": {"name": "Fortified Keep", "desc": "+3 castle health per level.", "costs": [20, 40, 60]},
}
const START_RECON := 2
const REROLL_COST := 1


## How many copies a blueprint pick grants (cheap towers come in bundles).
static func copies_for(tid: String) -> int:
	var cost: int = TOWERS[tid]["cost"]
	if cost <= 80:
		return 3
	if cost <= 130:
		return 2
	return 1

# ====================================================================== hex map

## How many entrances a rolled terrain tile has (weights; strongly skewed toward 2).
const ENTRANCE_ODDS := {2: 50, 3: 27, 4: 13, 5: 7, 6: 3}

## ---- Tower footprints ------------------------------------------------------------------------
## Cells are axial offsets drawn facing north: (0,-1) is the cell in front, (0,1) behind, (1,-1) / (-1,0)
## the front-right / front-left cells, (1,0) / (-1,1) the back-right / back-left cells.
## muzzles: the cells a tower fires from; each fires its own shot.
const SHAPES := {
	"single": {"name": "1 hex", "cells": [[0, 0]], "muzzles": [[0, 0]]},
	"pair": {"name": "2 hexes", "cells": [[0, 0], [0, 1]], "muzzles": [[0, 0]]},
	"line3": {"name": "3 in a line", "cells": [[0, 0], [0, 1], [0, 2]], "muzzles": [[0, 0]]},
	"arrow3": {"name": "3, arrowhead", "cells": [[0, 0], [1, 0], [-1, 1]], "muzzles": [[0, 0]]},
	"wing3": {"name": "3, two front guns", "cells": [[0, 0], [1, -1], [-1, 0]], "muzzles": [[1, -1], [-1, 0]]},
	"fan4": {"name": "4, fan", "cells": [[0, 0], [-1, 0], [0, -1], [1, -1]], "muzzles": [[0, -1]]},
	"line4": {"name": "4 in a line", "cells": [[0, 0], [0, 1], [0, 2], [0, 3]], "muzzles": [[0, 0]]},
	"arrow5": {"name": "5, arrow", "cells": [[0, 0], [1, 0], [-1, 1], [0, 1], [0, 2]], "muzzles": [[0, 0]]},
	"star5": {"name": "5, cross", "cells": [[0, 0], [1, -1], [-1, 0], [1, 0], [-1, 1]], "muzzles": [[0, 0]]},
	"battery6": {"name": "6, two front guns", "cells": [[0, 0], [1, -1], [-1, 0], [1, 0], [-1, 1], [0, 1]], "muzzles": [[1, -1], [-1, 0]]},
	"flower7": {"name": "7, flower", "cells": [[0, 0], [1, 0], [0, 1], [-1, 1], [-1, 0], [0, -1], [1, -1]], "muzzles": [[0, 0]]},
}
## tower -> [shape, firing arc in degrees (360 = all round)]
const FOOTPRINTS := {
	"archer": ["single", 360], "ballista": ["line3", 60], "arcane": ["pair", 360], "trebuchet": ["arrow5", 120],
	"chapel": ["fan4", 360], "banner": ["single", 360], "gryphon": ["wing3", 180], "bombard": ["battery6", 120],
	"thorn": ["single", 360], "spore": ["pair", 360], "briar": ["line4", 360], "treant": ["star5", 360],
	"storm": ["arrow3", 360], "hive": ["pair", 360], "moonwell": ["single", 360], "rootbinder": ["flower7", 360],
	"dwarf_flame": ["pair", 90], "dwarf_hammer": ["arrow3", 360], "dwarf_mortar": ["fan4", 360], "dwarf_gyro": ["wing3", 180],
	"mer_tide": ["single", 360], "mer_harpoon": ["line3", 60], "mer_whirl": ["arrow3", 360], "mer_siren": ["pair", 360],
	"bone_crypt": ["single", 360], "plague_cauldron": ["pair", 360], "soul_obelisk": ["pair", 360], "hex_tomb": ["fan4", 360],
}


static func footprint_of(tid: String) -> Array:
	return FOOTPRINTS.get(tid, ["single", 360])


static func shape_of(tid: String) -> Dictionary:
	return SHAPES[footprint_of(tid)[0]]


static func arc_of(tid: String) -> float:
	return float(footprint_of(tid)[1])


## World-agnostic footprint: the cells a tower covers when its front cell is `anchor` and it faces side f.
static func footprint(tid: String, anchor: Vector2i, facing: int) -> Array:
	var out: Array = []
	for c in shape_of(tid)["cells"]:
		out.append(anchor + Hex.rot(Vector2i(c[0], c[1]), facing - 4))
	return out


static func muzzle_cells(tid: String, anchor: Vector2i, facing: int) -> Array:
	var out: Array = []
	for c in shape_of(tid)["muzzles"]:
		out.append(anchor + Hex.rot(Vector2i(c[0], c[1]), facing - 4))
	return out


# ====================================================================== colors: specializations, heroes


# ====================================================================== castle talents (in-run)
## Four paths, bought with gold during a run. Treasury / Artificers / Bulwark are sequential (each node needs
## the one before it) and get much stronger deeper in; Slayers are separate picks you take (up to two ranks)
## to answer the threats in front of you.
const TALENT_COSTS := [60, 110, 170, 250]
const TALENTS := {
	"treasury": {"name": "Treasury", "color": Color(1.0, 0.82, 0.35), "desc": "Resource generation", "nodes": [
		{"id": "tax", "name": "Tax Collectors", "desc": "+20 gold after every wave."},
		{"id": "interest", "name": "Moneylenders", "desc": "Earn 6% interest on unspent gold after every wave (up to 45)."},
		{"id": "scouts", "name": "Runecarvers", "desc": "+1 Rune after every wave, and a free Builder every 3 waves."},
		{"id": "mint", "name": "Royal Mint", "desc": "+30% gold from kills and +40 gold after every wave."},
		{"id": "caravan", "name": "Trade Caravans", "desc": "Buy a Builder and 2 Runes right now. Repeatable.", "repeat": true}]},
	"artificers": {"name": "Artificers", "color": Color(0.55, 0.8, 1.0), "desc": "Stronger, cheaper towers", "nodes": [
		{"id": "guild", "name": "Guild Discount", "desc": "Towers and upgrades cost 10% less."},
		{"id": "drill", "name": "Drillmasters", "desc": "All towers attack 12% faster."},
		{"id": "optics", "name": "Optics", "desc": "All towers get +12% range."},
		{"id": "masters", "name": "Master Crafters", "desc": "Blueprints give +1 copy and all towers deal +15% damage."},
		{"id": "refine", "name": "Refinement", "desc": "All towers deal +6% damage. Repeatable.", "repeat": true}]},
	"slayers": {"name": "Slayers", "color": Color(1.0, 0.45, 0.35), "desc": "Extra damage against what's coming", "pick": true, "nodes": [
		{"id": "sky", "name": "Sky Hunters", "desc": "+30% damage to flying enemies (per rank).", "cost": 80},
		{"id": "pierce", "name": "Armor Piercers", "desc": "+30% damage to armored enemies (per rank).", "cost": 80},
		{"id": "breaker", "name": "Shield Breakers", "desc": "Shields break 60% faster (per rank).", "cost": 80},
		{"id": "seers", "name": "Seers", "desc": "The castle sees camouflage 4 tiles further, +20% damage to camouflaged enemies (per rank).", "cost": 80},
		{"id": "giant", "name": "Giant Slayers", "desc": "+30% damage to bosses (per rank).", "cost": 100}]},
	"bulwark": {"name": "Bulwark", "color": Color(0.75, 0.75, 0.8), "desc": "Castle defenses", "nodes": [
		{"id": "walls", "name": "Stone Walls", "desc": "+8 castle health."},
		{"id": "turret", "name": "Keep Ballista", "desc": "The castle shoots enemies within 4 tiles."},
		{"id": "moat", "name": "Moat", "desc": "Enemies within 5 tiles of the castle are slowed by 35%."},
		{"id": "citadel", "name": "Citadel", "desc": "The keep ballista fires twice as fast, and the castle repairs 3 health after every wave."},
		{"id": "ramparts", "name": "Ramparts", "desc": "+4 castle health and the keep ballista deals +25% damage. Repeatable.", "repeat": true}]},
}
const TALENT_MAX_RANK := 2
const TALENT_REPEAT_COST := [200, 120]   # repeatable capstones: base, + this per rank owned


# ====================================================================== rewards after each wave
## Each option is a pair of items. Weights for rolling an item kind.
const REWARD_KINDS := {"blueprint": 40, "doctrine": 14, "builder": 12, "digger": 7, "gold": 12, "recon": 8, "masterwork": 6}
const START_BUILDERS := 2
const START_DIGGERS := 1
