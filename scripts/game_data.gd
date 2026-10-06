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
const LEVEL_RANGE := [1.0, 1.05, 1.1]   # (2026-10-04: was 1.1 / 1.2; ranges felt too long)
const LEVEL_RATE := [1.0, 1.1, 1.25]
const LEVEL_BUFF := [1.0, 1.4, 1.8]
const UPGRADE_COST := [0.8, 1.25]  # fraction of base cost for lvl 2, lvl 3
const SELL_REFUND := 0.7
const LEY_BONUS := 0.25
## Each level of high ground adds this much tower range (Tower Dominion-style elevation).
const ELEVATION_RANGE := 0.1   # range per level of high ground (was 0.15)
const RELAY_RANGE := 0.15      # a neighboring Relay Station (was 0.2)
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

## "gold": kill gold multiplier (tougher enemies pay more); every road past the first adds EXTRA_ROAD_GOLD at the start.
const DIFFICULTIES := [
	{"name": "Normal", "hp": 1.0, "count": 1.0, "exits": 1, "gold": 1.0, "desc": "The intended experience. One road leaves the castle."},
	{"name": "Hard", "hp": 1.7, "count": 1.25, "exits": 2, "gold": 1.1, "desc": "Tougher, larger waves. Two roads leave the castle (+150 gold): join them into one chokepoint. Kills pay 10% more."},
	{"name": "Brutal", "hp": 2.3, "count": 1.4, "exits": 3, "gold": 1.15, "desc": "For Tower Dominion veterans. Three roads leave the castle (+300 gold). Kills pay 15% more."},
]
## Hard and Brutal ease in: their health and size multipliers grow from 1.0 on wave 1 to full strength by this wave
## (playtests: with two or three roads to cover from the first wave, the full multipliers ended most runs by wave 5;
## reaching full strength on wave 10, with the first boss, left a wall at waves 8-12; by wave 18, Hard played like Normal).
const DIFF_RAMP := 14
const EXTRA_ROAD_GOLD := 150   # (playtests: Brutal's three roads left too few towers by the wave-10 boss at +100)

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
		"towers": ["arcane", "chapel", "banner", "gryphon", "seraph", "archangel", "knight_hall", "sunlance"],
		"start": ["archer", "ballista", "arcane"],
		"start_copies": {"archer": 3, "ballista": 1, "arcane": 1},
	},
	"verdant": {
		"name": "The Verdant Circle", "pie": "Green", "race": "Elves",
		"color": Color(0.45, 0.85, 0.4),
		"desc": "Elven druids of the deep wood. Poison, thorns and living trees that root, slow and wear down the horde.",
		"strengths": "Slows, poison, crowd control",
		"weakness": "Low burst damage against armor",
		"passive_name": "Wildgrowth", "passive_desc": "Slows and poison are 20% stronger.",
		"passive": {"slow_mult": 1.2, "poison_mult": 1.2},
		"towers": ["thorn", "spore", "briar", "treant", "storm", "hive", "moonwell", "rootbinder", "dire_bear", "mammoth", "heart_tree"],
		"start": ["thorn", "spore", "briar"],
		"start_copies": {"thorn": 3, "spore": 1, "briar": 2},
	},
	"forge": {
		"name": "The Deep Forge", "pie": "Red", "race": "Dwarves",
		"color": Color(0.92, 0.36, 0.25),
		"desc": "Dwarven engineers. Flamethrowers, steam hammers, colossal mortars and flak batteries.",
		"strengths": "Huge damage, splash, crushes armor",
		"weakness": "Slow to fire, weak against flyers and camouflage",
		"passive_name": "Forgecraft", "passive_desc": "+15% physical damage. Upgrades cost 15% less.",
		"passive": {"phys": 0.15, "upgrade_discount": 0.15},
		"towers": ["dwarf_flame", "dwarf_hammer", "dwarf_mortar", "dwarf_gyro", "magma_golem", "fat_dragon", "doom_cannon", "war_forge"],
		"start": ["archer", "dwarf_flame", "dwarf_hammer"],
		"start_copies": {"archer": 3, "dwarf_flame": 2, "dwarf_hammer": 1},
	},
	"tide": {
		"name": "The Tidal Court", "pie": "Blue", "race": "Merfolk",
		"color": Color(0.35, 0.65, 0.98),
		"desc": "Merfolk of the deep. Tides, harpoons, whirlpools and siren song that control the battlefield.",
		"strengths": "Slows, pushback, stuns; loves water",
		"weakness": "Low raw damage, struggles against bosses",
		"passive_name": "Tidebound", "passive_desc": "Towers next to water deal +30% damage, and your tiles bring more ponds.",
		"passive": {"water_dmg": 0.3, "ponds": 0.25},
		"towers": ["mer_tide", "mer_harpoon", "mer_whirl", "mer_siren", "snapjaw_crab", "kraken", "leviathan", "tidecaller"],
		"start": ["archer", "mer_tide", "mer_harpoon"],
		"start_copies": {"archer": 2, "mer_tide": 2, "mer_harpoon": 1},
	},
	"grave": {
		"name": "The Bone Legion", "pie": "Black", "race": "Skeletons",
		"color": Color(0.62, 0.45, 0.85),
		"desc": "The restless dead. Cheap bone archers, plague, soul-draining obelisks and cursed tombs.",
		"strengths": "Attrition, poison, shreds bosses and big health pools",
		"weakness": "Short range, slow to kill fast swarms",
		"passive_name": "Plague Tide", "passive_desc": "Poisoned enemies burst when they die, hitting nearby enemies for 15% of their max health.",
		"passive": {"death_burst": 0.15, "poison_mult": 1.15},
		"towers": ["bone_crypt", "plague_cauldron", "soul_obelisk", "hex_tomb", "mass_grave", "necromancer", "bone_colossus", "blood_altar"],
		"start": ["bone_crypt", "plague_cauldron", "archer"],
		"start_copies": {"bone_crypt": 4, "plague_cauldron": 1, "archer": 2},
	},
}


## Every tower a run of this color can draft: its own towers plus the shared ones.
static func run_towers(fid: String) -> Array:
	var out: Array = SHARED_TOWERS.duplicate()
	out.append_array(FACTIONS[fid]["towers"])
	return out

## attack kinds: arrow (homing), bolt (straight, pierces), lob (arc, ground only),
## orb (slow homing), chain (instant lightning), slam (instant splash at target),
## aura_dmg (pulses around tower), aura_buff (boosts nearby towers), swoop (one target, struck in person: see STRIKES)
const TOWERS := {
	# ---------------- Aurelian Crown ----------------
	"archer": {"name": "Archer Tower", "tier": 1, "copies": 3, "cost": 60, "attack": "arrow", "dmg": 10.0, "rate": 1.6, "range": 3.2,
		"dtype": "phys", "air": true, "ground": true, "color": Color(0.35, 0.55, 0.9),
		"desc": "Cheap, reliable, hits air and ground."},
	"ballista": {"name": "Ballista", "tier": 2, "copies": 2, "cost": 160, "attack": "bolt", "dmg": 82.0, "rate": 0.55, "range": 5.0,
		"dtype": "phys", "air": true, "ground": true, "pierce": true, "color": Color(0.6, 0.42, 0.25),
		"desc": "Heavy bolts that pierce through every enemy in a line."},
	"arcane": {"name": "Arcane Spire", "tier": 2, "copies": 2, "cost": 170, "attack": "orb", "dmg": 46.0, "rate": 0.9, "range": 3.6,
		"dtype": "magic", "air": true, "ground": true, "splash": 0.6, "shred": true, "color": Color(0.65, 0.4, 1.0),
		"desc": "Magic orbs that ignore armor and burst on impact."},
	"trebuchet": {"name": "Trebuchet", "tier": 3, "copies": 1, "cost": 270, "attack": "lob", "dmg": 150.0, "rate": 0.33, "range": 7.0, "min_range": 2.5,
		"dtype": "phys", "air": false, "ground": true, "splash": 1.4, "color": Color(0.55, 0.45, 0.35),
		"desc": "Enormous range. Boulders crush whole groups. Can't hit flyers."},
	"chapel": {"name": "Chapel of Dawn", "tier": 2, "copies": 2, "cost": 160, "attack": "aura_dmg", "dmg": 21.0, "rate": 1.0, "range": 2.4,
		"dtype": "magic", "air": true, "ground": true, "slow": [0.3, 1.2], "detect": true, "color": Color(1.0, 0.92, 0.6),
		"desc": "Radiant pulses burn and slow everything nearby."},
	"banner": {"name": "War Banner", "tier": 2, "copies": 2, "cost": 160, "attack": "aura_buff", "dmg": 0.0, "rate": 0.0, "range": 2.6,
		"buff": {"dmg": 0.35}, "color": Color(0.85, 0.2, 0.2),
		"desc": "Nearby towers deal +35% damage (scales with level)."},
	"gryphon": {"name": "Gryphon Roost", "tier": 3, "copies": 1, "cost": 260, "attack": "swoop", "dmg": 50.0, "rate": 1.3, "range": 4.8,
		"dtype": "phys", "air": true, "ground": true, "air_bonus": 2.5, "detect": true, "color": Color(0.9, 0.75, 0.45), "sfx": "claw",
		"desc": "Its gryphon takes wing and swoops on enemy after enemy, talons first. Anti-air specialist: 2.5x damage to flying enemies, and it still strikes the ground."},
	"bombard": {"name": "Royal Bombard", "tier": 3, "copies": 1, "cost": 320, "attack": "lob", "dmg": 140.0, "rate": 0.4, "range": 4.0,
		"dtype": "phys", "air": false, "ground": true, "splash": 1.1, "stun": [0.25, 0.7], "color": Color(0.3, 0.3, 0.35),
		"desc": "Short-range cannon. Big splash, may stun."},
	# ---------------- Verdant Circle ----------------
	"thorn": {"name": "Thornspitter", "tier": 1, "copies": 3, "cost": 55, "attack": "arrow", "dmg": 6.0, "rate": 2.6, "range": 3.0,
		"dtype": "phys", "air": true, "ground": true, "color": Color(0.4, 0.75, 0.3),
		"desc": "Rapid-fire thorns. Hits air and ground."},
	"spore": {"name": "Spore Mound", "tier": 2, "copies": 2, "cost": 140, "attack": "lob", "dmg": 22.0, "rate": 0.6, "range": 3.6,
		"dtype": "magic", "air": false, "ground": true, "splash": 1.3, "dot": [20.0, 4.0], "color": Color(0.6, 0.35, 0.7),
		"desc": "Lobs spore pods that poison groups over time."},
	"briar": {"name": "Briar Thicket", "tier": 1, "copies": 3, "cost": 80, "attack": "aura_dmg", "dmg": 7.0, "rate": 1.2, "range": 2.0,
		"dtype": "phys", "air": false, "ground": true, "slow": [0.45, 1.0], "color": Color(0.35, 0.5, 0.2),
		"desc": "Thorny vines heavily slow and scratch passing ground enemies."},
	"treant": {"name": "Elder Treant", "tier": 3, "copies": 1, "cost": 260, "attack": "slam", "dmg": 135.0, "rate": 0.55, "range": 2.9,
		"dtype": "phys", "air": false, "ground": true, "splash": 1.0, "stun": [0.2, 0.8], "color": Color(0.45, 0.3, 0.18),
		"desc": "Slams the ground at short range. Crushing splash, may stun."},
	"storm": {"name": "Stormcaller Oak", "tier": 3, "copies": 1, "cost": 280, "attack": "chain", "dmg": 75.0, "rate": 0.7, "range": 4.2,
		"dtype": "magic", "air": true, "ground": true, "chain": 4, "shred": true, "color": Color(0.4, 0.6, 1.0),
		"desc": "Lightning that arcs between up to 5 enemies."},
	"hive": {"name": "Wasp Hive", "tier": 2, "copies": 2, "cost": 165, "attack": "arrow", "dmg": 12.0, "rate": 5.0, "range": 3.4,
		"dtype": "phys", "air": true, "ground": true, "air_bonus": 2.0, "detect": true, "color": Color(0.95, 0.8, 0.2),
		"desc": "A swarm of stingers. Double damage to flyers; the swarm sniffs out camouflaged enemies."},
	"moonwell": {"name": "Moonwell", "tier": 2, "copies": 2, "cost": 150, "attack": "aura_buff", "dmg": 0.0, "rate": 0.0, "range": 2.6,
		"buff": {"rate": 0.35}, "detect": true, "color": Color(0.5, 0.9, 1.0),
		"desc": "Nearby towers attack 35% faster (scales with level)."},
	"rootbinder": {"name": "Rootbinder Shrine", "tier": 3, "copies": 1, "cost": 280, "attack": "orb", "dmg": 120.0, "rate": 0.6, "range": 4.5,
		"dtype": "magic", "air": false, "ground": true, "stun": [1.0, 1.1], "color": Color(0.3, 0.9, 0.5),
		"desc": "Every hit roots a ground enemy in place."},
	# ---------------- Red: the Deep Forge (dwarves) ----------------
	"dwarf_flame": {"name": "Flame Belcher", "tier": 1, "copies": 2, "cost": 85, "attack": "aura_dmg", "dmg": 10.0, "rate": 2.2, "range": 2.8,
		"dtype": "magic", "air": true, "ground": true, "dot": [8.0, 2.0], "color": Color(1.0, 0.45, 0.15), "sfx": "fire",
		"desc": "Breathes fire in a cone in front of it, burning everything it touches."},
	"dwarf_hammer": {"name": "Runic Hammer", "tier": 2, "copies": 1, "cost": 175, "attack": "slam", "dmg": 95.0, "rate": 0.5, "range": 2.6,
		"dtype": "phys", "air": false, "ground": true, "splash": 1.2, "stun": [0.35, 1.0], "shred": true, "color": Color(0.8, 0.45, 0.3),
		"desc": "A rune-powered steam hammer. Crushes groups, stuns, and shatters shields."},
	"dwarf_mortar": {"name": "Siege Mortar", "tier": 3, "copies": 1, "cost": 320, "attack": "lob", "dmg": 225.0, "rate": 0.25, "range": 7.5, "min_range": 3.0,
		"dtype": "phys", "air": false, "ground": true, "splash": 1.9, "color": Color(0.45, 0.4, 0.36),
		"desc": "Colossal range and blast radius. Can't hit flyers."},
	"dwarf_gyro": {"name": "Flak Battery", "tier": 2, "copies": 1, "cost": 180, "attack": "arrow", "dmg": 36.0, "rate": 2.4, "range": 4.6,
		"dtype": "phys", "air": true, "ground": false, "air_bonus": 1.5, "color": Color(0.85, 0.62, 0.3),
		"desc": "Twin rotary flak guns that shred flyers. Can't hit the ground."},
	# ---------------- Blue: the Tidal Court (merfolk) ----------------
	"mer_tide": {"name": "Tide Spire", "tier": 1, "copies": 2, "cost": 90, "attack": "aura_dmg", "dmg": 8.0, "rate": 0.8, "range": 2.8,
		"dtype": "magic", "air": true, "ground": true, "slow": [0.4, 1.5], "detect": true, "color": Color(0.35, 0.78, 0.95),
		"desc": "Pulses of tidewater slow everything nearby. Senses camouflaged enemies."},
	"mer_harpoon": {"name": "Coral Harpooner", "tier": 2, "copies": 2, "cost": 165, "attack": "bolt", "dmg": 60.0, "rate": 0.7, "range": 4.8,
		"dtype": "phys", "air": true, "ground": true, "pierce": true, "slow": [0.3, 1.2], "color": Color(0.95, 0.55, 0.55),
		"desc": "Barbed harpoons pierce a whole line and slow every enemy they hit."},
	"mer_whirl": {"name": "Whirlpool Shrine", "tier": 3, "copies": 1, "cost": 270, "attack": "aura_dmg", "dmg": 34.0, "rate": 0.5, "range": 2.8,
		"dtype": "magic", "air": false, "ground": true, "push": [0.3, 1.6], "color": Color(0.3, 0.55, 0.95),
		"desc": "A swirling vortex that drags ground enemies back along the road."},
	"mer_siren": {"name": "Siren Rock", "tier": 3, "copies": 1, "cost": 260, "attack": "chain", "dmg": 55.0, "rate": 0.6, "range": 4.4,
		"dtype": "magic", "air": true, "ground": true, "chain": 3, "stun": [0.25, 0.9], "color": Color(0.6, 0.85, 1.0),
		"desc": "A siren's song arcs between enemies and can leave them spellbound."},
	# ---------------- Black: the Bone Legion (skeletons) ----------------
	"bone_crypt": {"name": "Bone Crypt", "tier": 1, "copies": 3, "cost": 50, "attack": "arrow", "dmg": 8.5, "rate": 1.9, "range": 3.0,
		"dtype": "phys", "air": true, "ground": true, "color": Color(0.88, 0.86, 0.76),
		"desc": "Cheap skeleton archers. Hits air and ground."},
	"plague_cauldron": {"name": "Plague Cauldron", "tier": 2, "copies": 2, "cost": 145, "attack": "lob", "dmg": 16.0, "rate": 0.55, "range": 3.6,
		"dtype": "magic", "air": false, "ground": true, "splash": 1.4, "dot": [26.0, 4.0], "color": Color(0.5, 0.85, 0.3),
		"desc": "Hurls bubbling plague that poisons whole groups."},
	"soul_obelisk": {"name": "Soul Obelisk", "tier": 3, "copies": 1, "cost": 280, "attack": "orb", "dmg": 80.0, "rate": 0.55, "range": 4.4,
		"dtype": "magic", "air": true, "ground": true, "pct": 0.15, "color": Color(0.65, 0.35, 0.95),
		"desc": "Rips out 15% of a target's current health with every hit. Bosses resist."},
	"hex_tomb": {"name": "Hex Tomb", "tier": 2, "copies": 1, "cost": 185, "attack": "aura_curse", "dmg": 0.0, "rate": 0.0, "range": 2.8,
		"curse": 0.35, "air": true, "ground": true, "color": Color(0.55, 0.3, 0.7),
		"desc": "Curses nearby enemies: they take +35% damage from everything (scales with level)."},
	# ---------------- Creatures: one Tier II and one Tier III for every color ----------------
	# attack kinds added for them: smite (a pillar of light on the target, splash), breath (fixed straight line
	# ahead: "line" is its width in tiles, "static" towers never turn), grasp (seizes up to "grasp" enemies at once).
	# Other new keys: vuln [extra damage taken, seconds], boss_bonus (extra damage to bosses), target (default mode),
	# raise (Necromancer: enemies dying in reach rise as zombies, see Thrall).
	"seraph": {"name": "Seraph", "tier": 2, "copies": 2, "cost": 170, "attack": "arrow", "dmg": 34.0, "rate": 1.4, "range": 4.2,
		"dtype": "magic", "air": true, "ground": true, "air_bonus": 1.75, "detect": true, "color": Color(1.0, 0.93, 0.66), "sfx": "spear",
		"desc": "An armored angel that hurls spears of light. Hits air and ground, +75% against flyers, sees camouflage."},
	"archangel": {"name": "Archangel", "tier": 3, "copies": 1, "cost": 300, "attack": "smite", "dmg": 180.0, "rate": 0.4, "range": 4.6,
		"dtype": "magic", "air": true, "ground": true, "splash": 0.8, "stun": [1.0, 0.6], "boss_bonus": 0.5, "target": 2, "sfx": "smite",
		"color": Color(1.0, 0.85, 0.4),
		"desc": "Calls down judgment on the strongest enemy in reach: a pillar of light that stuns and splashes. +50% against bosses."},
	"dire_bear": {"name": "Dire Bear", "tier": 2, "copies": 2, "cost": 150, "attack": "slam", "dmg": 45.0, "rate": 0.8, "range": 2.2,
		"dtype": "phys", "air": false, "ground": true, "splash": 0.7, "dot": [10.0, 3.0], "color": Color(0.6, 0.42, 0.24), "sfx": "maul",
		"desc": "A rune-painted grizzly that mauls ground enemies next to it and leaves them bleeding."},
	"mammoth": {"name": "Ancient Mammoth", "tier": 3, "copies": 1, "cost": 320, "attack": "aura_dmg", "dmg": 90.0, "rate": 0.35, "range": 2.8,
		"dtype": "phys", "air": false, "ground": true, "stun": [1.0, 0.8], "color": Color(0.62, 0.5, 0.38), "sfx": "stomp",
		"desc": "Stomps the ground: heavy damage to every ground enemy around it, and they're all stunned."},
	"magma_golem": {"name": "Magma Golem", "tier": 2, "copies": 2, "cost": 165, "attack": "lob", "dmg": 40.0, "rate": 0.5, "range": 4.0,
		"dtype": "phys", "air": false, "ground": true, "splash": 1.2, "dot": [12.0, 3.0], "color": Color(1.0, 0.45, 0.1), "sfx": "magma",
		"desc": "Hurls molten boulders that splash and leave enemies burning."},
	"fat_dragon": {"name": "Fat Dragon", "tier": 3, "copies": 1, "cost": 340, "attack": "breath", "dmg": 90.0, "rate": 0.8, "range": 6.0,
		"line": 1.5, "static": true, "dtype": "magic", "air": true, "ground": true, "dot": [30.0, 3.0], "color": Color(1.0, 0.38, 0.1), "sfx": "breath",
		"desc": "Too heavy to move, so it just lies there and breathes fire in a straight line where it faces. Burns everything in the line, air and ground. Aim it with R."},
	"snapjaw_crab": {"name": "Snapjaw Crab", "tier": 2, "copies": 2, "cost": 160, "attack": "slam", "dmg": 25.0, "rate": 0.7, "range": 2.4,
		"dtype": "phys", "air": false, "ground": true, "splash": 0.5, "vuln": [0.25, 3.0], "color": Color(0.95, 0.5, 0.3), "sfx": "claw",
		"desc": "Two giant claws, each crushing ground enemies. Cracked shells take +25% damage from everything for 3 seconds."},
	"kraken": {"name": "Kraken", "tier": 3, "copies": 1, "cost": 330, "attack": "grasp", "dmg": 95.0, "rate": 0.45, "range": 3.2,
		"dtype": "phys", "air": true, "ground": true, "grasp": 3, "stun": [1.0, 1.2], "color": Color(0.62, 0.36, 0.78), "sfx": "grasp",
		"desc": "Tentacles seize and crush up to 3 enemies at once, holding walkers in place."},
	"mass_grave": {"name": "Mass Grave", "tier": 2, "copies": 2, "cost": 150, "attack": "aura_dmg", "dmg": 16.0, "rate": 1.0, "range": 1.8,
		"dtype": "phys", "air": false, "ground": true, "slow": [0.55, 1.0], "color": Color(0.5, 0.72, 0.36), "sfx": "graves",
		"desc": "A long trench of grasping dead hands: ground enemies passing it are clawed and slowed 55%."},
	"necromancer": {"name": "Necromancer", "tier": 3, "copies": 1, "cost": 300, "attack": "orb", "dmg": 40.0, "rate": 0.8, "range": 4.0,
		"dtype": "magic", "air": true, "ground": true, "raise": {"max": 5, "life": 8.0, "grab": 0.3}, "color": Color(0.55, 0.85, 0.35),
		"desc": "Dark bolts. Walkers that die in its reach rise as zombies (up to 5 at once) that shamble back down the road and grab the next enemy they meet: stunned and mauled for 30% of the zombie's old health."},
	# ---- Tier IV (legendary, from wave 16): each color's late game
	"knight_hall": {"name": "Hall of Knights", "tier": 4, "copies": 1, "cost": 440, "attack": "muster", "dmg": 240.0, "rate": 0.6, "range": 4.0,
		"dtype": "phys", "air": false, "ground": true, "muster": {"max": 5, "life": 14.0, "stun": 1.6, "hits": 3}, "color": Color(0.95, 0.88, 0.6), "sfx": "shield",
		"desc": "Musters knights who march out onto the road ahead of the foe and pin it: stunned and cut down. Up to 5 knights at once, each fighting three times."},
	"sunlance": {"name": "Sunlance Lighthouse", "tier": 4, "copies": 1, "cost": 420, "attack": "beam", "dmg": 160.0, "rate": 0.6, "range": 6.0,
		"beam_w": 1.1, "dtype": "magic", "air": true, "ground": true, "detect": true, "color": Color(1.0, 0.92, 0.55), "sfx": "smite",
		"desc": "A lance of sunlight that burns through everything in a straight line toward its target, flyers too. Sees camouflaged enemies."},
	"doom_cannon": {"name": "Doomsday Cannon", "tier": 4, "copies": 1, "cost": 480, "attack": "lob", "dmg": 520.0, "rate": 0.18, "range": 8.5, "min_range": 3.0,
		"dtype": "phys", "air": false, "ground": true, "splash": 2.4, "stun": [0.5, 1.0], "color": Color(0.9, 0.45, 0.25),
		"desc": "The Forge's masterpiece: a colossal cannon whose shells level whole crowds at the far end of the map, and can stun what's left."},
	"war_forge": {"name": "Forge of Ages", "tier": 4, "copies": 1, "cost": 420, "attack": "aura_buff", "dmg": 0.0, "rate": 0.0, "range": 2.8,
		"buff": {"dmg": 0.3}, "burn": [22.0, 3.0], "color": Color(1.0, 0.5, 0.2),
		"desc": "An ancient forge that tempers the towers around it: they deal +30% damage and set what they hit burning."},
	"leviathan": {"name": "Leviathan", "tier": 4, "copies": 1, "cost": 480, "attack": "bolt", "dmg": 260.0, "rate": 0.55, "range": 5.6,
		"dtype": "magic", "air": true, "ground": true, "pierce": true, "slow": [0.4, 1.5], "push": [0.35, 1.2], "color": Color(0.3, 0.75, 0.95), "sfx": "surge",
		"desc": "A sea serpent from the deep. Its water jet pierces a whole line, slows everything it hits and can wash walkers back down the road."},
	"tidecaller": {"name": "Tidecaller Spire", "tier": 4, "copies": 1, "cost": 430, "attack": "aura_dmg", "dmg": 55.0, "rate": 0.33, "range": 3.2,
		"dtype": "magic", "air": true, "ground": true, "stun": [1.0, 1.2], "slow": [0.5, 2.0], "color": Color(0.6, 0.85, 1.0), "sfx": "talent",
		"desc": "A great bell of ice and coral. Every toll freezes everything around it in place, then leaves it slowed."},
	"bone_colossus": {"name": "Bone Colossus", "tier": 4, "copies": 1, "cost": 480, "attack": "slam", "dmg": 330.0, "rate": 0.4, "range": 2.9,
		"dtype": "phys", "air": false, "ground": true, "splash": 1.8, "stun": [0.4, 1.0], "color": Color(0.85, 0.82, 0.7), "sfx": "stomp",
		"desc": "A giant of fused bones. Its fists smash whole groups and can stun them."},
	"blood_altar": {"name": "Blood Altar", "tier": 4, "copies": 1, "cost": 400, "attack": "aura_buff", "dmg": 0.0, "rate": 0.0, "range": 2.8,
		"buff": {"dmg": 0.35, "rate": 0.15}, "toll": 1, "color": Color(0.8, 0.15, 0.2),
		"desc": "Towers around it deal +35% damage and attack 15% faster. The price: after every wave it drinks 1 castle health."},
	"heart_tree": {"name": "Heart of the Forest", "tier": 4, "copies": 1, "cost": 420, "attack": "aura_buff", "dmg": 0.0, "rate": 0.0, "range": 3.0,
		"buff": {"dmg": 0.1}, "grow": 0.03, "grow_max": 0.45, "color": Color(0.5, 0.95, 0.45),
		"desc": "A living heart of the old wood. Towers around it deal +10% damage, +3% more for every wave it has stood (up to +55%)."},
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
	"gargoyle": {"name": "Gargoyle", "hp": 110.0, "speed": 0.8, "armor": 0.3, "resist": 0.1, "gold": 10, "leak": 2,
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
	{"id": "ability", "name": "Commander's Focus", "rarity": 1, "weight": 4, "desc": "Your commander's signature comes round 25% sooner."},
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
## Neutral buildings come on new tiles (as in Tower Dominion): once the tile is yours, they work for you. group: tower
## (empowers the towers next to it), economy (resources after every wave) or realm (a bonus to all your forces).
const NEUTRALS := {
	"ammo": {"name": "Ammo Depot", "group": "tower", "model": "bld_ammo_depot", "desc": "Towers next to it attack 25% faster."},
	"relay": {"name": "Relay Station", "group": "tower", "model": "bld_relay", "desc": "Towers next to it get +15% range."},
	"forge": {"name": "Smithy", "group": "tower", "model": "bld_forge", "desc": "Towers next to it deal +25% damage."},
	"scout": {"name": "Scout Hideout", "group": "tower", "model": "bld_scout", "desc": "Reveals camouflaged enemies within 4 tiles."},
	"supply": {"name": "Supply Point", "group": "economy", "model": "bld_supply", "desc": "+15 gold after every wave."},
	"mine": {"name": "Gold Mine", "group": "economy", "model": "bld_mine", "desc": "+25 gold after every wave."},
	"runes": {"name": "Rune Circle", "group": "economy", "model": "bld_runes", "desc": "+1 Rune every other wave."},
	"lumber": {"name": "Lumber Mill", "group": "economy", "model": "bld_lumber", "desc": "A free Builder every 4 waves."},
	"chapel": {"name": "Old Chapel", "group": "realm", "model": "bld_chapel", "desc": "All your towers deal +5% damage."},
	"barracks": {"name": "Barracks", "group": "realm", "model": "bld_barracks", "desc": "The castle repairs 2 health after every wave."},
	"tavern": {"name": "Tavern", "group": "realm", "model": "bld_tavern", "desc": "+10% gold from kills."},
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
## tower_dmg {tids, mult}, recon, detect_all, slow_mult, poison_mult, kill_gold
## sig: the commander's signature passive (Game._sig_*): trigger every / castle_hit / wave_start / mark / spread / renew /
## static, and for the triggered ones an effect kind haste / frenzy / arcane / root / blast / surge / reap
const HEROES := {
	"aldric": {"faction": "crown", "name": "Lord Marshal Aldric", "cost": 0, "portrait": "hero_aldric",
		"powers": ["All towers deal +10% damage.", "+5 castle health."],
		"sig": {"name": "Rally Cry", "trigger": "castle_hit", "kind": "haste", "power": 0.6, "duration": 6.0, "cooldown": 20.0,
			"desc": "When the castle is hit, all towers attack 60% faster for 6 seconds (at most every 20 seconds)."},
		"fx": {"phys": 0.1, "magic": 0.1, "hp": 5}},
	"seraphine": {"faction": "crown", "name": "Archmage Seraphine", "cost": 0, "portrait": "hero_seraphine",
		"powers": ["+20% magic damage.", "Arcane Spire blueprints give +1 copy."],
		"sig": {"name": "Arcane Tempest", "trigger": "every", "period": 30.0, "kind": "arcane", "damage": 25.0,
			"desc": "Every 30 seconds of a wave, arcane bolts strike every enemy, flyers too, for 25 magic damage (+20% per wave)."},
		"fx": {"magic": 0.2, "bonus_copies": {"arcane": 1}}},
	"brann": {"faction": "crown", "name": "Siegemaster Brann", "cost": 40, "portrait": "hero_brann",
		"powers": ["Ballista, Trebuchet and Bombard deal +30% damage.", "Start with a Trebuchet blueprint."],
		"sig": {"name": "Opening Barrage", "trigger": "wave_start", "kind": "frenzy", "power": 0.4, "duration": 12.0,
			"desc": "For the first 12 seconds of every wave, all towers deal +40% damage."},
		"fx": {"tower_dmg": {"tids": ["ballista", "trebuchet", "bombard"], "mult": 0.3}, "start_copies": {"trebuchet": 1}}},
	"elsa": {"faction": "crown", "name": "Scout-Captain Elsa", "cost": 60, "portrait": "hero_elsa",
		"powers": ["Every tower can detect camouflaged enemies.", "+1 Rune after every wave."],
		"sig": {"name": "Hunter's Mark", "trigger": "mark", "count": 6, "power": 0.5,
			"desc": "The first 6 enemies of every wave, and every boss, are marked: they take +50% damage."},
		"fx": {"detect_all": true, "recon": 1}},
	"thornwood": {"faction": "verdant", "name": "Elder Thornwood", "cost": 0, "portrait": "hero_thornwood",
		"powers": ["Slows are 30% stronger.", "Briar Thicket blueprints give +1 copy."],
		"sig": {"name": "Entangling Roots", "trigger": "every", "period": 25.0, "kind": "root", "duration": 2.0, "damage": 30.0,
			"desc": "Every 25 seconds of a wave, roots every ground enemy for 2 seconds and deals 30 damage (+15% per wave)."},
		"fx": {"slow_mult": 1.3, "bonus_copies": {"briar": 1}}},
	"lira": {"faction": "verdant", "name": "Moon-priestess Lira", "cost": 0, "portrait": "hero_lira",
		"powers": ["All towers attack 15% faster.", "Moonwell blueprints give +1 copy."],
		"sig": {"name": "Moonlit Renewal", "trigger": "renew", "heal": 2, "recon": 1,
			"desc": "After every wave the castle heals 2 health, and a wave with no leaks adds +1 Rune."},
		"fx": {"rate": 0.15, "bonus_copies": {"moonwell": 1}}},
	"oma": {"faction": "verdant", "name": "Grovekeeper Oma", "cost": 40, "portrait": "hero_oma",
		"powers": ["Poison deals +60% damage.", "Start with an extra Spore Mound."],
		"sig": {"name": "Overgrowth", "trigger": "spread", "count": 2,
			"desc": "When a poisoned enemy dies, its poison spreads to the 2 nearest enemies."},
		"fx": {"poison_mult": 1.6, "start_copies": {"spore": 1}}},
	"hunt": {"faction": "verdant", "name": "The Wild Hunt", "cost": 60, "portrait": "hero_hunt",
		"powers": ["+25% gold from kills.", "Start with an extra Wasp Hive blueprint."],
		"sig": {"name": "Call of the Wild", "trigger": "static", "tids": ["dire_bear", "treant", "hive", "mammoth"], "rate": 0.3,
			"desc": "Creature towers (Dire Bear, Elder Treant, Wasp Hive, Ancient Mammoth) attack 30% faster."},
		"fx": {"kill_gold": 0.25, "start_copies": {"hive": 1}}},
	"durgan": {"faction": "forge", "name": "Thane Durgan Ironbeard", "cost": 0, "portrait": "hero_durgan",
		"powers": ["Runic Hammer and Siege Mortar deal +25% damage.", "Start with a Siege Mortar blueprint."],
		"sig": {"name": "Forgefire Barrage", "trigger": "every", "period": 30.0, "kind": "blast", "damage": 50.0,
			"desc": "Every 30 seconds of a wave, every ground enemy takes 50 damage (+25% per wave)."},
		"fx": {"tower_dmg": {"tids": ["dwarf_hammer", "dwarf_mortar"], "mult": 0.25}, "start_copies": {"dwarf_mortar": 1}}},
	"nerissa": {"faction": "tide", "name": "Tidequeen Nerissa", "cost": 0, "portrait": "hero_nerissa",
		"powers": ["Slows are 25% stronger.", "+1 Rune after every wave."],
		"sig": {"name": "Tidal Surge", "trigger": "every", "period": 35.0, "kind": "surge", "push": 2.0, "duration": 3.0,
			"desc": "Every 35 seconds of a wave, every enemy is washed 2 tiles back down the road and slowed 40% for 3 seconds."},
		"fx": {"slow_mult": 1.25, "recon": 1}},
	"mortis": {"faction": "grave", "name": "Mortis, the Bone Lord", "cost": 0, "portrait": "hero_mortis",
		"powers": ["Poison deals +40% damage.", "+20% gold from kills."],
		"sig": {"name": "Reaping", "trigger": "every", "period": 40.0, "kind": "reap", "pct": 0.1,
			"desc": "Every 40 seconds of a wave, every enemy loses 10% of its max health (bosses 3%)."},
		"fx": {"poison_mult": 1.4, "kill_gold": 0.2}},
}

## ---- Tower specializations (chosen when a tower reaches level III) --------------------------
## fx: dmg / range / rate (multiplier add), multishot (extra targets), splash (tiles), slow, stun,
## dot [dps, dur], dot_mult, chain (extra jumps), detect, shred, buff_dmg / buff_rate (aura add)
const SPECS := {
	"archer": [{"name": "Longbow", "desc": "+30% range, +30% damage.", "fx": {"range": 0.3, "dmg": 0.3}},
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
		{"name": "Spotters", "desc": "Detects camouflaged enemies and +20% range.", "fx": {"detect": true, "range": 0.2}}],
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
	"soul_obelisk": [{"name": "Soul Harvest", "desc": "Rips out 18% of current health.", "fx": {"pct": 0.18}},
		{"name": "Twin Souls", "desc": "Hits one extra enemy.", "fx": {"multishot": 1}}],
	"hex_tomb": [{"name": "Doom", "desc": "The curse is 15% stronger.", "fx": {"curse": 0.15}},
		{"name": "Withering", "desc": "Cursed enemies are also slowed 25%.", "fx": {"slow": [0.25, 1.0]}}],
	"seraph": [{"name": "Radiant Spears", "desc": "+50% damage.", "fx": {"dmg": 0.5}},
		{"name": "Choir", "desc": "Each attack also hits 2 more enemies.", "fx": {"multishot": 2}}],
	"archangel": [{"name": "Wrath", "desc": "+50% damage.", "fx": {"dmg": 0.5}},
		{"name": "Judgment Day", "desc": "Smites stun twice as long and leave the ground burning.", "fx": {"stun": [1.0, 1.2], "dot": [30.0, 3.0]}}],
	"dire_bear": [{"name": "Rending Claws", "desc": "Bleeding is twice as strong.", "fx": {"dot_mult": 2.0}},
		{"name": "Grizzled", "desc": "+60% damage.", "fx": {"dmg": 0.6}}],
	"mammoth": [{"name": "Earthshaker", "desc": "Stomps reach 30% further.", "fx": {"range": 0.3}},
		{"name": "Old Tusker", "desc": "+60% damage.", "fx": {"dmg": 0.6}}],
	"magma_golem": [{"name": "Eruption", "desc": "Much bigger blasts.", "fx": {"splash": 0.8}},
		{"name": "Molten Core", "desc": "Burns 80% hotter.", "fx": {"dot_mult": 1.8}}],
	"fat_dragon": [{"name": "Inferno", "desc": "The fire burns twice as hot.", "fx": {"dot_mult": 2.0}},
		{"name": "Big Lungs", "desc": "The breath reaches 25% further.", "fx": {"range": 0.25}}],
	"snapjaw_crab": [{"name": "Shell Crusher", "desc": "Cracked shells take +40% damage instead.", "fx": {"vuln": [0.4, 3.0]}},
		{"name": "Pincers", "desc": "+70% damage.", "fx": {"dmg": 0.7}}],
	"kraken": [{"name": "Many Arms", "desc": "Seizes 2 more enemies at once.", "fx": {"grasp": 2}},
		{"name": "Crushing Grip", "desc": "+60% damage.", "fx": {"dmg": 0.6}}],
	"mass_grave": [{"name": "Grasping Dead", "desc": "Slows by 75%.", "fx": {"slow": [0.75, 1.0]}},
		{"name": "Rot", "desc": "+100% damage.", "fx": {"dmg": 1.0}}],
	"necromancer": [{"name": "Legion", "desc": "Up to 10 zombies at once.", "fx": {"raise_max": 5}},
		{"name": "Soul Bolts", "desc": "+60% damage, and zombies grab harder.", "fx": {"dmg": 0.6}}],
	"knight_hall": [{"name": "Paladins", "desc": "Knights strike 60% harder.", "fx": {"dmg": 0.6}},
		{"name": "Muster", "desc": "Up to 3 more knights at once, mustered 50% faster.", "fx": {"muster_max": 3, "rate": 0.5}}],
	"sunlance": [{"name": "Dawnfire", "desc": "The beam leaves its line burning: 30 damage/s for 3s.", "fx": {"dot": [30.0, 3.0]}},
		{"name": "Focused Lens", "desc": "+50% damage and a wider beam.", "fx": {"dmg": 0.5, "beam_w": 0.5}}],
	"doom_cannon": [{"name": "Earthshaker", "desc": "A much bigger blast.", "fx": {"splash": 1.0}},
		{"name": "Rapid Loader", "desc": "+60% attack speed.", "fx": {"rate": 0.6}}],
	"war_forge": [{"name": "Masterworks", "desc": "The aura grants an extra +15% damage.", "fx": {"buff_dmg": 0.15}},
		{"name": "Great Bellows", "desc": "The aura also grants +20% attack speed.", "fx": {"buff_rate": 0.2}}],
	"leviathan": [{"name": "Crushing Depths", "desc": "+50% damage.", "fx": {"dmg": 0.5}},
		{"name": "Riptide", "desc": "Washes walkers back much more often.", "fx": {"push": [0.7, 1.6]}}],
	"tidecaller": [{"name": "Deep Freeze", "desc": "The freeze lasts longer.", "fx": {"stun": [1.0, 1.9]}},
		{"name": "Undertow", "desc": "+50% damage and a 70% slow after the freeze.", "fx": {"dmg": 0.5, "slow": [0.7, 2.0]}}],
	"bone_colossus": [{"name": "Bonecrusher", "desc": "+50% damage.", "fx": {"dmg": 0.5}},
		{"name": "Earthquake", "desc": "Slams hit a much larger area.", "fx": {"splash": 0.8}}],
	"blood_altar": [{"name": "Exsanguinate", "desc": "The aura grants an extra +15% damage.", "fx": {"buff_dmg": 0.15}},
		{"name": "Dark Covenant", "desc": "The aura grants an extra +20% attack speed.", "fx": {"buff_rate": 0.2}}],
	"heart_tree": [{"name": "Deep Roots", "desc": "Grows twice as fast.", "fx": {"grow": 0.03}},
		{"name": "Canopy", "desc": "The aura also grants +15% attack speed.", "fx": {"buff_rate": 0.15}}],
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


## Tower tiers: later tiers cost more and hit much harder. A tier's blueprints can be offered from this wave on
## (towers you start with are always yours to build).
const TIER_WAVE := {1: 1, 2: 4, 3: 10, 4: 16}   # tier IV: each color's legendary late game
const TIER_NAMES := ["", "I", "II", "III", "IV"]


static func tier_of(tid: String) -> int:
	return int(TOWERS[tid].get("tier", 1))


## How many copies a blueprint pick grants (cheap towers come in bundles).
static func copies_for(tid: String) -> int:
	if TOWERS[tid].has("copies"):
		return int(TOWERS[tid]["copies"])
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
	"battery5": {"name": "5, two front guns", "cells": [[0, 0], [-1, 0], [0, -1], [1, -1], [0, 1]], "muzzles": [[1, -1], [-1, 0]]},
	"fan5": {"name": "5, fan", "cells": [[0, 0], [-1, 0], [0, -1], [1, -1], [1, 0]], "muzzles": [[0, 0]]},
}
## Melee towers reach their prey, and the blow lands where the model lands (Tower's sortie code and Strike; Blender
## towers only, and only once their model has the clips / strike file, so the rest attack as before). kind:
##   "lunge"  the beast (the tower's Head, with a "run" clip) charges out to its target, strikes it ("fire") and comes
##            home. speed: world units a second (it goes faster if it must: the attack rate is the tower's); reach:
##            it stops this far from its prey; hop: how high it leaps for each unit it has to cover (so a long dash
##            clears its own den and the towers between), up to hop_max; hit: seconds into "fire" when the blow lands.
##   "fly"    the same on the wing (a "fly" clip): it takes off, swoops on enemy after enemy, wheels overhead between
##            blows and goes home to roost when there's nothing left. alt: how high it wheels above its roost; hit:
##            how long before it arrives its "fire" clip starts.
##   "erupt"  a model of its own (assets/towers/<id>_strike.glb, clip "strike", built by the tower's Blender script's
##            build_strike) bursts up under the enemy. hit: seconds into the clip when the blow lands (auras: 0, the
##            pulse lands at once); max: the most an aura shows per pulse; scale: draws the model bigger.
const STRIKES := {
	"dire_bear": {"kind": "lunge", "speed": 11.0, "reach": 0.95, "hop": 0.26, "hop_max": 1.5, "hit": 0.2},
	"snapjaw_crab": {"kind": "lunge", "speed": 10.0, "reach": 1.25, "hop": 0.1, "hop_max": 0.5, "hit": 0.15},
	"bone_colossus": {"kind": "lunge", "speed": 9.0, "reach": 1.4, "hop": 0.4, "hop_max": 2.4, "hit": 0.3},
	"gryphon": {"kind": "fly", "speed": 13.0, "reach": 0.5, "alt": 2.2, "hit": 0.12},
	"treant": {"kind": "erupt", "hit": 0.3},
	"dwarf_hammer": {"kind": "erupt", "hit": 0.25},
	"kraken": {"kind": "erupt", "hit": 0.25},
	"mammoth": {"kind": "erupt", "hit": 0.0, "max": 8},
	"mass_grave": {"kind": "erupt", "hit": 0.0, "max": 6, "scale": 1.5},
	"briar": {"kind": "erupt", "hit": 0.0, "max": 6},
}

## tower -> [shape, firing arc in degrees (360 = all round)]. No tower covers more than 5 hexes: map tiles are 3 hexes
## along each edge (13 whole hexes, a road through the middle), so the big towers fit where neighboring tiles leave a
## clear, level patch together, and 6-7 hex shapes would hardly ever find one. Those shapes stay in SHAPES.
const FOOTPRINTS := {
	"archer": ["single", 360], "ballista": ["line3", 60], "arcane": ["pair", 360], "trebuchet": ["arrow5", 120],
	"chapel": ["fan4", 360], "banner": ["single", 360], "gryphon": ["wing3", 180], "bombard": ["battery5", 120],
	"thorn": ["single", 360], "spore": ["pair", 360], "briar": ["line4", 360], "treant": ["star5", 360],
	"storm": ["arrow3", 360], "hive": ["pair", 360], "moonwell": ["single", 360], "rootbinder": ["fan5", 360],
	"dwarf_flame": ["pair", 90], "dwarf_hammer": ["arrow3", 360], "dwarf_mortar": ["fan4", 360], "dwarf_gyro": ["wing3", 180],
	"mer_tide": ["single", 360], "mer_harpoon": ["line3", 60], "mer_whirl": ["arrow3", 360], "mer_siren": ["pair", 360],
	"bone_crypt": ["single", 360], "plague_cauldron": ["pair", 360], "soul_obelisk": ["pair", 360], "hex_tomb": ["fan4", 360],
	"seraph": ["arrow3", 360], "archangel": ["fan4", 360], "dire_bear": ["pair", 360], "mammoth": ["battery5", 360],
	"magma_golem": ["arrow3", 360], "fat_dragon": ["arrow5", 30], "snapjaw_crab": ["wing3", 360], "kraken": ["fan5", 360],
	"mass_grave": ["line4", 360], "necromancer": ["star5", 360],
	"knight_hall": ["arrow3", 360], "sunlance": ["pair", 360], "doom_cannon": ["arrow5", 120], "war_forge": ["fan4", 360],
	"leviathan": ["line4", 90], "tidecaller": ["arrow3", 360], "bone_colossus": ["fan5", 360], "blood_altar": ["pair", 360],
	"heart_tree": ["star5", 360],
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


## Towers aim, fire and measure range from their footprint's centroid. So that nothing loses reach, range gets this
## added (world units): the distance from the centroid to the old gun hex, or for an all-round aura the mean distance
## of its hexes from the centroid (a circle about as big as the old "reach from every hex" shape). 0 for one hex.
static func reach_offset(tid: String) -> float:
	var sh := shape_of(tid)
	var cells: Array = sh["cells"]
	if cells.size() < 2:
		return 0.0
	var mid := Vector3.ZERO
	for c in cells:
		mid += Hex.to_world(Vector2i(c[0], c[1]))
	mid /= float(cells.size())
	if String(TOWERS[tid]["attack"]).begins_with("aura") and arc_of(tid) >= 359.0:
		var sum := 0.0
		for c in cells:
			var w := Hex.to_world(Vector2i(c[0], c[1])) - mid
			sum += Vector2(w.x, w.z).length()
		return sum / cells.size()
	var best := 0.0
	for c in sh["muzzles"]:
		var w := Hex.to_world(Vector2i(c[0], c[1])) - mid
		best = maxf(best, Vector2(w.x, w.z).length())
	return best


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
## Castle talents: four paths bought with gold during a run (C). Economy, Arsenal and Keep are each faction's own (its
## color: White order and walls, Green growth and venom, Red fire and hoards, Blue tides and lore, Black blood-price and
## death); Slayers (pick any, twice) is shared. Each path unlocks in order; the last node is repeatable. A node's fx are
## applied by Game._apply_fx: mods keys add (cost_mult multiplies; interest / moat / turret / turret_rate take the
## higher), max_hp, gold_now, builders_now, diggers_now, recon_now; hero keys slow_mult / poison_mult / aura_mult
## multiply, water_dmg / death_burst / upgrade_discount / ponds add.
const TALENT_COSTS := [60, 110, 170, 250]
const SLAYERS := {"name": "Slayers", "color": Color(1.0, 0.45, 0.35), "desc": "Extra damage against what's coming", "pick": true, "nodes": [
	{"id": "sky", "name": "Sky Hunters", "desc": "+30% damage to flying enemies (per rank).", "cost": 80, "fx": {"vs_air": 0.3}},
	{"id": "pierce", "name": "Armor Piercers", "desc": "+30% damage to armored enemies (per rank).", "cost": 80, "fx": {"vs_armor": 0.3}},
	{"id": "breaker", "name": "Shield Breakers", "desc": "Shields break 60% faster (per rank).", "cost": 80, "fx": {"shield_break": 0.6}},
	{"id": "seers", "name": "Seers", "desc": "The castle sees camouflage 4 tiles further, +20% damage to camouflaged enemies (per rank).", "cost": 80,
		"fx": {"castle_detect": 4.0, "vs_camo": 0.2}},
	{"id": "giant", "name": "Giant Slayers", "desc": "+30% damage to bosses (per rank).", "cost": 100, "fx": {"vs_boss": 0.3}}]}
const FACTION_TALENTS := {
	"crown": {
		"economy": {"name": "Royal Treasury", "color": Color(1.0, 0.82, 0.35), "desc": "Taxes and trade", "nodes": [
			{"id": "tax", "name": "Tithes", "desc": "+20 gold after every wave.", "fx": {"treasury": 20}},
			{"id": "interest", "name": "Royal Bank", "desc": "Earn 6% interest on unspent gold after every wave (up to 45).", "fx": {"interest": 0.06}},
			{"id": "scouts", "name": "Heralds", "desc": "+1 Rune after every wave, and a free Builder every 3 waves.", "fx": {"recon_wave": 1, "builder_every": 3}},
			{"id": "mint", "name": "Crown Mint", "desc": "+30% gold from kills and +40 gold after every wave.", "fx": {"kill_gold": 0.3, "treasury": 40}},
			{"id": "caravan", "name": "Royal Caravans", "desc": "Buy a Builder and 2 Runes right now. Repeatable.", "repeat": true, "fx": {"builders_now": 1, "recon_now": 2}}]},
		"arsenal": {"name": "Order of the Spire", "color": Color(0.55, 0.8, 1.0), "desc": "Drilled, blessed towers", "nodes": [
			{"id": "guild", "name": "Guild Charters", "desc": "Towers and upgrades cost 10% less.", "fx": {"cost_mult": 0.9}},
			{"id": "drill", "name": "Drillmasters", "desc": "All towers attack 12% faster.", "fx": {"rate": 0.12}},
			{"id": "c_consecrate", "name": "Consecration", "desc": "Support auras (banners, chapels, moonwells...) are 25% stronger.", "fx": {"aura_mult": 1.25}},
			{"id": "masters", "name": "Paladin Corps", "desc": "Blueprints give +1 copy and all towers deal +15% damage.", "fx": {"extra_copies": 1, "dmg_all": 0.15}},
			{"id": "refine", "name": "Holy Steel", "desc": "All towers deal +6% damage. Repeatable.", "repeat": true, "fx": {"dmg_all": 0.06}}]},
		"keep": {"name": "Bastion", "color": Color(0.85, 0.85, 0.9), "desc": "Walls and the keep", "nodes": [
			{"id": "walls", "name": "Stone Walls", "desc": "+8 castle health.", "fx": {"max_hp": 8}},
			{"id": "turret", "name": "Keep Ballista", "desc": "The castle shoots enemies within 4 tiles.", "fx": {"turret": 1}},
			{"id": "c_sanctuary", "name": "Sanctuary", "desc": "The castle repairs 3 health after every wave.", "fx": {"repair": 3}},
			{"id": "citadel", "name": "Citadel", "desc": "The keep ballista fires twice as fast, and +6 castle health.", "fx": {"turret_rate": 2.0, "max_hp": 6}},
			{"id": "ramparts", "name": "Ramparts", "desc": "+4 castle health and the keep deals +25% damage. Repeatable.", "repeat": true, "fx": {"max_hp": 4, "turret_dmg": 0.25}}]},
	},
	"verdant": {
		"economy": {"name": "Grove Bounty", "color": Color(0.6, 0.9, 0.4), "desc": "Foraging and harvest", "nodes": [
			{"id": "v_forage", "name": "Forager Bands", "desc": "+15 gold after every wave and +15% gold from kills.", "fx": {"treasury": 15, "kill_gold": 0.15}},
			{"id": "v_groves", "name": "Sacred Groves", "desc": "+1 Rune after every wave.", "fx": {"recon_wave": 1}},
			{"id": "v_seed", "name": "Seed Vaults", "desc": "Earn 6% interest on unspent gold after every wave (up to 45).", "fx": {"interest": 0.06}},
			{"id": "v_circles", "name": "Druid Circles", "desc": "Blueprints give +1 copy, and a free Builder every 3 waves.", "fx": {"extra_copies": 1, "builder_every": 3}},
			{"id": "v_harvest", "name": "Bountiful Harvest", "desc": "+60 gold now and +10 gold after every wave. Repeatable.", "repeat": true, "fx": {"gold_now": 60, "treasury": 10}}]},
		"arsenal": {"name": "Wildwood", "color": Color(0.45, 0.8, 0.35), "desc": "Thorn, root and venom", "nodes": [
			{"id": "v_thornbark", "name": "Thornbark", "desc": "All towers deal +10% damage.", "fx": {"dmg_all": 0.1}},
			{"id": "v_roots", "name": "Deep Roots", "desc": "Slows are 20% stronger.", "fx": {"slow_mult": 1.2}},
			{"id": "v_venom", "name": "Venom Glands", "desc": "Poison deals 35% more damage.", "fx": {"poison_mult": 1.35}},
			{"id": "v_ancient", "name": "Ancient Growth", "desc": "All towers get +10% range.", "fx": {"range": 0.1}},
			{"id": "v_sap", "name": "Wildsap", "desc": "All towers deal +6% damage. Repeatable.", "repeat": true, "fx": {"dmg_all": 0.06}}]},
		"keep": {"name": "Living Wall", "color": Color(0.7, 0.6, 0.4), "desc": "Brambles round the keep", "nodes": [
			{"id": "v_hedge", "name": "Bramble Hedge", "desc": "+8 castle health.", "fx": {"max_hp": 8}},
			{"id": "v_vines", "name": "Strangling Vines", "desc": "Enemies within 5 tiles of the castle are slowed by 35%.", "fx": {"moat": 0.35}},
			{"id": "v_heartwood", "name": "Heartwood", "desc": "The castle repairs 3 health after every wave.", "fx": {"repair": 3}},
			{"id": "v_thornspit", "name": "Thornspitter Keep", "desc": "The castle spits thorns at enemies within 4 tiles, twice as fast as a ballista.", "fx": {"turret": 1, "turret_rate": 2.0}},
			{"id": "v_barkskin", "name": "Barkskin", "desc": "+4 castle health and the keep deals +25% damage. Repeatable.", "repeat": true, "fx": {"max_hp": 4, "turret_dmg": 0.25}}]},
	},
	"forge": {
		"economy": {"name": "Mountain Hold", "color": Color(1.0, 0.7, 0.3), "desc": "Ore, hoards and tunnels", "nodes": [
			{"id": "f_ore", "name": "Ore Veins", "desc": "+25 gold after every wave.", "fx": {"treasury": 25}},
			{"id": "f_hoard", "name": "Dwarven Hoard", "desc": "Earn 8% interest on unspent gold after every wave (up to 45).", "fx": {"interest": 0.08}},
			{"id": "f_tunnels", "name": "Tunnel Crews", "desc": "A Builder and a Digger now, and a free Builder every 3 waves.", "fx": {"builders_now": 1, "diggers_now": 1, "builder_every": 3}},
			{"id": "f_seams", "name": "Gold Seams", "desc": "+30% gold from kills and +1 Rune after every wave.", "fx": {"kill_gold": 0.3, "recon_wave": 1}},
			{"id": "f_delves", "name": "Deep Delves", "desc": "A Builder, a Digger and 50 gold right now. Repeatable.", "repeat": true, "fx": {"builders_now": 1, "diggers_now": 1, "gold_now": 50}}]},
		"arsenal": {"name": "Runesmiths", "color": Color(1.0, 0.5, 0.3), "desc": "Fire, powder and steel", "nodes": [
			{"id": "f_smiths", "name": "Master Smiths", "desc": "Upgrades cost 20% less.", "fx": {"upgrade_discount": 0.2}},
			{"id": "f_powder", "name": "Black Powder", "desc": "Blasts and slams hit a 25% wider area.", "fx": {"splash_mult": 0.25}},
			{"id": "f_iron", "name": "Hot Iron", "desc": "+15% physical damage.", "fx": {"phys": 0.15}},
			{"id": "f_engines", "name": "Runic Engines", "desc": "All towers attack 15% faster and deal +10% damage.", "fx": {"rate": 0.15, "dmg_all": 0.1}},
			{"id": "f_temper", "name": "Tempering", "desc": "All towers deal +6% damage. Repeatable.", "repeat": true, "fx": {"dmg_all": 0.06}}]},
		"keep": {"name": "Iron Keep", "color": Color(0.7, 0.6, 0.55), "desc": "Iron walls and a cannon", "nodes": [
			{"id": "f_walls", "name": "Iron Walls", "desc": "+10 castle health.", "fx": {"max_hp": 10}},
			{"id": "f_cannon", "name": "Keep Cannon", "desc": "The castle shoots enemies within 4 tiles, +25% keep damage.", "fx": {"turret": 1, "turret_dmg": 0.25}},
			{"id": "f_moat", "name": "Slag Moat", "desc": "Enemies within 5 tiles of the castle are slowed by 25%, and the keep deals +25% damage.", "fx": {"moat": 0.25, "turret_dmg": 0.25}},
			{"id": "f_citadel", "name": "Forge Citadel", "desc": "The keep fires twice as fast, and the castle repairs 2 health after every wave.", "fx": {"turret_rate": 2.0, "repair": 2}},
			{"id": "f_ramparts", "name": "Bulwarks", "desc": "+4 castle health and the keep deals +25% damage. Repeatable.", "repeat": true, "fx": {"max_hp": 4, "turret_dmg": 0.25}}]},
	},
	"tide": {
		"economy": {"name": "Tidal Trade", "color": Color(0.45, 0.8, 0.95), "desc": "Pearls and charts", "nodes": [
			{"id": "t_divers", "name": "Pearl Divers", "desc": "+20 gold after every wave.", "fx": {"treasury": 20}},
			{"id": "t_charts", "name": "Tide Charts", "desc": "+1 Rune after every wave.", "fx": {"recon_wave": 1}},
			{"id": "t_sunken", "name": "Sunken Treasure", "desc": "Earn 6% interest on unspent gold after every wave (up to 45).", "fx": {"interest": 0.06}},
			{"id": "t_markets", "name": "Coral Markets", "desc": "Blueprints give +1 copy and towers cost 5% less.", "fx": {"extra_copies": 1, "cost_mult": 0.95}},
			{"id": "t_fleet", "name": "Merchant Fleet", "desc": "2 Runes and 40 gold right now. Repeatable.", "repeat": true, "fx": {"recon_now": 2, "gold_now": 40}}]},
		"arsenal": {"name": "Deep Lore", "color": Color(0.35, 0.6, 1.0), "desc": "Undertow and riptide", "nodes": [
			{"id": "t_undertow", "name": "Undertow", "desc": "Slows are 20% stronger.", "fx": {"slow_mult": 1.2}},
			{"id": "t_lore", "name": "Wave Lore", "desc": "All towers get +8% range.", "fx": {"range": 0.08}},
			{"id": "t_riptide", "name": "Riptide", "desc": "Towers next to water deal a further +20% damage, and your tiles bring more ponds.", "fx": {"water_dmg": 0.2, "ponds": 0.15}},
			{"id": "t_abyss", "name": "Abyssal Pressure", "desc": "+20% magic damage and all towers attack 8% faster.", "fx": {"magic": 0.2, "rate": 0.08}},
			{"id": "t_currents", "name": "Strong Currents", "desc": "All towers deal +6% damage. Repeatable.", "repeat": true, "fx": {"dmg_all": 0.06}}]},
		"keep": {"name": "Seawall", "color": Color(0.6, 0.75, 0.85), "desc": "Breakers and a lighthouse", "nodes": [
			{"id": "t_seawall", "name": "Seawall", "desc": "+8 castle health.", "fx": {"max_hp": 8}},
			{"id": "t_moat", "name": "Tidal Moat", "desc": "Enemies within 5 tiles of the castle are slowed by 45%.", "fx": {"moat": 0.45}},
			{"id": "t_battery", "name": "Harpoon Battery", "desc": "The castle shoots enemies within 4 tiles.", "fx": {"turret": 1}},
			{"id": "t_lighthouse", "name": "Lighthouse", "desc": "The castle sees camouflage 6 tiles further, and the keep fires twice as fast.", "fx": {"castle_detect": 6.0, "turret_rate": 2.0}},
			{"id": "t_breakers", "name": "Breakwaters", "desc": "+4 castle health and the keep deals +25% damage. Repeatable.", "repeat": true, "fx": {"max_hp": 4, "turret_dmg": 0.25}}]},
	},
	"grave": {
		"economy": {"name": "Grave Tithes", "color": Color(0.75, 0.6, 0.95), "desc": "Plunder and blood-price", "nodes": [
			{"id": "g_robbers", "name": "Grave Robbers", "desc": "+30% gold from kills.", "fx": {"kill_gold": 0.3}},
			{"id": "g_soultax", "name": "Soul Tax", "desc": "+20 gold after every wave.", "fx": {"treasury": 20}},
			{"id": "g_blood", "name": "Blood Price", "desc": "Lose 4 max castle health; gain 160 gold right now.", "fx": {"max_hp": -4, "gold_now": 160}},
			{"id": "g_toll", "name": "Death Toll", "desc": "+1 Rune after every wave, and a free Builder every 3 waves.", "fx": {"recon_wave": 1, "builder_every": 3}},
			{"id": "g_bargain", "name": "Dark Bargain", "desc": "Lose 2 max castle health; gain 120 gold and a Rune. Repeatable.", "repeat": true, "fx": {"max_hp": -2, "gold_now": 120, "recon_now": 1}}]},
		"arsenal": {"name": "Necromancy", "color": Color(0.6, 0.85, 0.4), "desc": "Rot, curses and the reaper", "nodes": [
			{"id": "g_rot", "name": "Rot", "desc": "Poison deals 35% more damage.", "fx": {"poison_mult": 1.35}},
			{"id": "g_wither", "name": "Withering", "desc": "Enemies below 8% health die when hit.", "fx": {"execute": 0.08}},
			{"id": "g_burst", "name": "Plague Burst", "desc": "Poisoned enemies burst harder when they die (+10% of their max health).", "fx": {"death_burst": 0.1}},
			{"id": "g_lich", "name": "Lich Pact", "desc": "+20% magic damage, and blueprints give +1 copy.", "fx": {"magic": 0.2, "extra_copies": 1}},
			{"id": "g_dark", "name": "Dark Rites", "desc": "All towers deal +6% damage. Repeatable.", "repeat": true, "fx": {"dmg_all": 0.06}}]},
		"keep": {"name": "Ossuary", "color": Color(0.8, 0.78, 0.7), "desc": "Bone walls and grasping dead", "nodes": [
			{"id": "g_bones", "name": "Bone Walls", "desc": "+8 castle health.", "fx": {"max_hp": 8}},
			{"id": "g_grasp", "name": "Grasping Dead", "desc": "Enemies within 5 tiles of the castle are slowed by 35%.", "fx": {"moat": 0.35}},
			{"id": "g_ballista", "name": "Bone Ballista", "desc": "The castle shoots enemies within 4 tiles.", "fx": {"turret": 1}},
			{"id": "g_siphon", "name": "Soul Siphon", "desc": "The keep fires twice as fast, and the castle repairs 3 health after every wave.", "fx": {"turret_rate": 2.0, "repair": 3}},
			{"id": "g_ramparts", "name": "Charnel Ramparts", "desc": "+4 castle health and the keep deals +25% damage. Repeatable.", "repeat": true, "fx": {"max_hp": 4, "turret_dmg": 0.25}}]},
	},
}


## A faction's castle talent paths, in the order they're shown: its economy and arsenal, the shared slayers, its keep.
static func talents_for(fid: String) -> Dictionary:
	var ft: Dictionary = FACTION_TALENTS.get(fid, FACTION_TALENTS["crown"])
	return {"economy": ft["economy"], "arsenal": ft["arsenal"], "slayers": SLAYERS, "keep": ft["keep"]}
const TALENT_MAX_RANK := 2
const TALENT_REPEAT_COST := [200, 120]   # repeatable capstones: base, + this per rank owned


# ====================================================================== rewards after each wave
## Each option is a pair of items. Weights for rolling an item kind.
const REWARD_KINDS := {"blueprint": 40, "doctrine": 14, "builder": 12, "digger": 7, "gold": 12, "recon": 8, "masterwork": 6}
const START_BUILDERS := 2
const START_DIGGERS := 1
