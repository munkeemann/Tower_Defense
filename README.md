# Tower Realms

A fantasy tower defense roguelite in Godot 4.7, inspired by Tower Dominion.
You grow a hex map one terrain tile per wave, then defend every road end it opens.

## Play

- Double-click `Play Tower Realms.bat`, or
- open Godot, choose **Import**, pick this folder's `project.godot`, then press F5.

## How a run works

1. **Pick a color and a commander** (see *The color pie* below). Every commander has two powers and a
   **signature** passive of their own (shown bottom left in a run). Some are free; the others are unlocked with
   Renown.
2. **Expand the realm**: before every wave you're offered **one** random hexagonal terrain tile, which always
   fits somewhere. Point at a glowing spot to see it there as a hologram (the real tile, see-through: roads,
   ramps, ponds, high ground; red where it won't fit), then click to place it. **R** / **Shift+R** turn it (6 ways);
   **F** casts 1 **Rune** to reroll it. Tiles can carry high ground, ley crystals, trees, rocks and neutral buildings.
   - Each tile is a hexagon 3 small hexes along each edge (`Hex.K = 4`): 13 whole hexes plus a half hex in the
     middle of each side, where the road enters. When two tiles meet, their halves merge into whole hexes; only
     those shared halves match, the rest of each tile keeps its own height. Every hex of a placed tile is buildable,
     the ones on the edge of your land too; if a spot won't take a tower, the hint line says why. Tiles are often a level above or below
     the road they join (3 levels in all) and often carry a raised patch, so the map climbs and dips; roads ramp
     between levels, only where they run straight (a ramp can't bend: a tile takes another height, or doesn't fit,
     rather than turn its road on one). Tiles carry at most one tree or rock, small ponds and small plateaus, so
     there's room for the bigger towers (lone pines and stumps are only clutter: building clears them), and ponds
     only cross a road where it runs straight (a bridge can't bend). Blueprints for 4-5 hex towers that fit nowhere
     on your map right now come up rarely.
   - Entrances sit at side midpoints. A tile has 2 to 6 of them, usually 2 (50% 2, 27% 3, 13% 4, 7% 5, 3% 6).
     Once you're holding several battlefronts, tiles that would only add more get rarer.
   - **Sides that touch placed tiles must match**: entrance to entrance, wall to wall.
   - **Every open entrance is an enemy spawn** (a battlefront). Each enemy picks one at random, then one of the
     roads from there to your castle (`Board.routes_from`: every route that never doubles back, up to 12): shorter
     ones are likelier (one half again as long comes up about half as often), so forks and loops split a wave, and a
     stretch every route shares is your chokepoint. Extra entrances add battlefronts; lining a tile up with more than
     one open end merges them.
3. **Build** towers on your own tiles, then press **Start Wave** (Space).
   Every tower needs a **blueprint copy**: building one uses a copy, selling it gives the copy back.
   Towers take 1 to 5 hexes, all clear and level; the big ones usually fit where two or three tiles meet.
   Press **R** while placing to turn them. Some fire all around; directional ones (Ballista, Trebuchet, Flame
   Belcher, Coral Harpooner...) only fire inside an arc in front of them, and the Fat Dragon only in a straight
   line. Towers aim and measure range from the middle of their footprint. The placement preview marks each hex
   green or red on its own; a selected tower gets a gold outline and a hovered one a white outline. While placing
   or selecting a tower, the **hexes it reaches light up** (road hexes brighter).
   - **Tiers**: towers are Tier I, II, III or IV. Later tiers cost a lot more and hit much harder. Tier II
     blueprints can be offered from wave 4, Tier III from wave 10 and Tier IV, each color's two legendary late-game
     towers, from wave 16 (`GameData.TIER_WAVE`); the first reward after that leads with a Tier IV blueprint. Your
     starting towers are always available.
   - **Waves** arrive spread over a spawn window, 2 s for the smallest waves up to 10 s for the biggest, with the
     enemy types mixed (`WaveBuilder.SPAWN_WINDOW`). Enemies split evenly across road ends.
   - **Fliers ignore the road**: they fly straight from their road end to the castle, high over everything. The
     build phase shows their flight lines (dashed) when the next wave has fliers.
4. **After each wave**: pick one of 3 **pairs** of rewards. Cards show only icons; hover one to see what's in it.
   Items: tower blueprints (1 to 3 copies), doctrines (global boons), masterworks (+30% damage for one tower
   type), Builders, Diggers, gold and Runes. Rerolling costs 1 Rune. You get +1 Rune per wave, plus 1 more for
   each extra battlefront (up to +3).
5. **Level III specializations**: upgrading a tower to level III makes you choose one of two specializations
   (for example Archer: Longbow or Volley).
6. Bosses arrive on waves 10, 20 and 30, in a random order each run. Survive 30 waves to win.
7. **Menu** sets the run aside, frozen, and the main menu offers **Resume**. Starting a new run abandons it (it
   doesn't survive quitting the game).

### The color pie

| Color | Race | Plays like | Passive |
|---|---|---|---|
| **White**: The Aurelian Crown | Humans | Support auras, reliable all-round defense | Auras 30% stronger, +5 castle health |
| **Green**: The Verdant Circle | Elves | Slows, poison, crowd control | Slows and poison 20% stronger |
| **Red**: The Deep Forge | Dwarves | Huge damage and splash, crushes armor; weak to flyers and camo | +15% physical damage, upgrades 15% cheaper |
| **Blue**: The Tidal Court | Merfolk | Slows, pushback, stuns; loves water | Towers next to water deal +30%; tiles bring more ponds |
| **Black**: The Bone Legion | Skeletons | Attrition, poison, % health damage vs big enemies | Poisoned enemies burst on death (15% of their max health) |

Each color has its own towers plus a shared pool (Archer, Ballista, Trebuchet, Royal Bombard), its own castle
talents and its own commanders. Every color also has two **creatures** (one Tier II, one Tier III) and two
**Tier IV legendaries** for the late game.

Commander signatures (`HEROES[...]["sig"]`, run by `Game._sig_*`) are passives, no button to press:

| Commander | Signature |
|---|---|
| Lord Marshal Aldric | **Rally Cry**: when the castle is hit, all towers attack 60% faster for 6 s (at most every 20 s) |
| Archmage Seraphine | **Arcane Tempest**: every 30 s of a wave, arcane bolts hit every enemy, flyers too |
| Siegemaster Brann | **Opening Barrage**: the first 12 s of every wave, all towers deal +40% damage |
| Scout-Captain Elsa | **Hunter's Mark**: the first 6 enemies of each wave, and every boss, take +50% damage |
| Elder Thornwood | **Entangling Roots**: every 25 s of a wave, every ground enemy is rooted 2 s and hurt |
| Moon-priestess Lira | **Moonlit Renewal**: the castle heals 2 after every wave; a wave with no leaks adds a Rune |
| Grovekeeper Oma | **Overgrowth**: a poisoned enemy's poison spreads to the 2 nearest when it dies |
| The Wild Hunt | **Call of the Wild**: Dire Bear, Elder Treant, Wasp Hive and Ancient Mammoth attack 30% faster |
| Thane Durgan Ironbeard | **Forgefire Barrage**: every 30 s of a wave, every ground enemy is blasted |
| Tidequeen Nerissa | **Tidal Surge**: every 35 s of a wave, every enemy is washed 2 tiles back and slowed |
| Mortis, the Bone Lord | **Reaping**: every 40 s of a wave, every enemy loses 10% of its max health (bosses 3%) |

The towers by color:

| Color | Towers | Creatures | Tier IV (wave 16+) |
|---|---|---|---|
| White | Arcane Spire, Chapel of Dawn, War Banner, Gryphon Roost | **Seraph** (spears of light, +75% vs flyers, sees camo), **Archangel** (smites the strongest enemy: stun + splash, +50% vs bosses) | **Hall of Knights** (musters up to 5 knights onto the road ahead of the foe; each pins and strikes three times), **Sunlance Lighthouse** (a beam that burns everything on a straight line, flyers too; sees camo) |
| Green | Thornspitter, Spore Mound, Briar Thicket, Elder Treant, Stormcaller Oak, Wasp Hive, Moonwell, Rootbinder Shrine | **Dire Bear** (mauls and bleeds), **Ancient Mammoth** (stomps: damages and stuns everything around it) | **Heart of the Forest** (aura: +10% damage, +3% more for every wave it has stood, up to +55%) |
| Red | Flame Belcher, Runic Hammer, Siege Mortar, Flak Battery | **Magma Golem** (burning boulders), **Fat Dragon** (too heavy to move: breathes fire in a straight line where it faces) | **Doomsday Cannon** (colossal range, huge stunning blasts), **Forge of Ages** (aura: +30% damage, and hits set enemies burning) |
| Blue | Tide Spire, Coral Harpooner, Whirlpool Shrine, Siren Rock | **Snapjaw Crab** (two claws; cracked shells take +25% damage), **Kraken** (seizes and holds up to 3 enemies) | **Leviathan** (a piercing water jet that slows and washes walkers back), **Tidecaller Spire** (every toll freezes everything around it, then slows it) |
| Black | Bone Crypt, Plague Cauldron, Soul Obelisk, Hex Tomb | **Mass Grave** (a trench of grasping hands that slows), **Necromancer** (walkers dying in its reach rise as zombies that shamble back down the road and grab the next enemy) | **Bone Colossus** (fists that smash and stun whole groups), **Blood Altar** (aura: +35% damage and +15% attack speed, but it drinks 1 castle health after every wave) |

### Castle talents (C)

Spend gold during a run on four talent paths, reacting to what's in front of you. Three are your color's own
(`FACTION_TALENTS`); **Slayers** is shared:

| Color | Economy | Arsenal | Keep |
|---|---|---|---|
| White | Royal Treasury: tithes, a bank, heralds, a mint | Order of the Spire: charters, drill, Consecration (+25% auras), Paladin Corps | Bastion: walls, keep ballista, Sanctuary repairs, Citadel |
| Green | Grove Bounty: foragers, sacred groves, seed vaults, druid circles | Wildwood: thornbark, deep roots (+20% slows), venom glands (+35% poison), ancient growth (+10% range) | Living Wall: hedge, strangling vines (moat), heartwood repairs, a thornspitter keep |
| Red | Mountain Hold: ore, a dwarven hoard (8% interest), tunnel crews, gold seams | Runesmiths: master smiths (-20% upgrades), black powder (+25% blast area), hot iron, runic engines | Iron Keep: iron walls, keep cannon, slag moat, forge citadel |
| Blue | Tidal Trade: pearl divers, tide charts, sunken treasure, coral markets | Deep Lore: undertow, wave lore, riptide (water bonus, more ponds), abyssal pressure | Seawall: seawall, a 45% tidal moat, harpoon battery, lighthouse (sees camo) |
| Black | Grave Tithes: grave robbers, soul tax, **blood price** (castle health for gold), death toll | Necromancy: rot, withering (execute below 8%), plague burst, lich pact | Ossuary: bone walls, grasping dead, bone ballista, soul siphon |

Each faction path unlocks in order and ends in a repeatable capstone. **Slayers** (+damage vs flyers, armored,
camouflaged or bosses; faster shield breaking) can be taken in any order, twice each. Early gold is tight, so
every talent is a choice between towers now and a stronger realm later.

### Threats (per run, not per wave)

Each run rolls 4 threats that join the invasion on waves 4, 9, 15 and 21. Each one is revealed in the
**Threat Intel** panel 3 waves before it arrives, so you can draft counters. Examples:

- **Shielded** enemies (blue bubble): shields soak damage. Magic strips them 1.5x faster, shield-breaker
  towers (Arcane Spire, Stormcaller Oak, some specializations) 2.5x faster.
- **Camo** enemies (ghostly): towers can only target them inside a detector's range. Detectors are Chapel of Dawn,
  Gryphon Roost, Moonwell, some specializations, Scout Hideouts, and the castle itself (3 tiles).
- **Swift** enemies move 40% faster.
- Flyers (harpies, wasps, gargoyles), splitting slimes, healing shamans and armored ironclads.

### Neutral buildings

About half the tiles carry a neutral building (`NEUTRALS`), as in Tower Dominion; once the tile is yours it works
for you. The tile bar names it before you place it, a toast says what it does, and hovering it explains it.

| Kind | Buildings |
|---|---|
| Empowers the towers next to it | **Ammo Depot** (+25% attack speed), **Relay Station** (+15% range), **Smithy** (+25% damage), **Scout Hideout** (detects camo within 4 tiles) |
| Resources after every wave | **Supply Point** (+15 gold), **Gold Mine** (+25 gold), **Rune Circle** (+1 Rune every other wave), **Lumber Mill** (a free Builder every 4 waves) |
| Empowers your whole realm | **Old Chapel** (all towers +5% damage), **Barracks** (the castle repairs 2 a wave), **Tavern** (+10% kill gold) |

They stack: two Gold Mines pay twice. (The old map pickups claimed by tower range are gone.)

### Difficulty

Normal, Hard and Brutal toughen and enlarge the waves, and open more roads out of the castle at the start: one,
two or three, on neighbouring sides, each with its first tile laid and +150 gold for every road past the first.
Holding out until you can join them into one chokepoint is half the game. Hard and Brutal ease in: their extra health
(x1.7 / x2.3) and wave size (x1.25 / x1.4) grow from nothing on wave 1 to full strength by wave 18
(`GameData.DIFF_RAMP`), and their kills pay 10% / 15% more gold.

### War Council (between runs)

Every run earns **Renown**: 1 per wave reached (x1.5 on Hard, x2 on Brutal), +40 for a victory. Spend it in
the War Council (main menu) on permanent upgrades (starting gold, Runes, extra starting blueprints, castle
health), or on unlocking heroes.

### The map is your tiles

A run starts with just the castle tile, a raised board over plain grass. Every tile you place becomes part of the
map: a raised hex block with rounded edges and earthen sides that brings its own terrain (roads, height, plateaus, trees, rocks, ley crystals,
neutral buildings and sometimes a pond, which the road may cross on a bridge). Some tile cards are **raised** (one
level above the road they join) or **lowland** (one level below). Where a new tile touches an old one, the edge
hexes copy the old tile's height so the seam is flat. The grass around your tiles is only backdrop, with a tree
line on the horizon (with the KayKit terrain, which is on by default, the board is instead an island of KayKit hex
tiles over a dark floor; see Art). The biome (Greenvale, Highlands, Lakelands,
Deepwood) changes how often tiles are raised and how many ponds they carry.

- A tower gets **+10% range per level** of ground it stands on. Ranges are short on purpose (2026-10-04): ranged
  towers reach 3-5 tiles and melee and aura towers 2-3, so where you build matters. The long guns (Trebuchet,
  Siege Mortar, Doomsday Cannon) reach 7-8.5 tiles but can't hit anything within 2.5-3 tiles of them: build
  them back from the road with a long stretch in view. The range display leaves their dead zone out.
- **Builders** (B, or G) put up timber scaffolding that raises an empty hex, or every hex under a tower, by one
  level (max 3). **Diggers** (N) take one down a level. Both are items: you start with 2 Builders and 1 Digger
  and earn more from wave rewards (and the Treasury path).

## Controls

| Input | Action |
|---|---|
| WASD / arrows / right-drag | Move camera |
| Mouse wheel, Q / E | Zoom, rotate |
| Tile placement | Point at a glowing spot (hologram), click to place. R / Shift+R turn it. F rerolls it for 1 Rune |
| 1-9, R / Shift+R, click | Pick a tower, turn it (either way), build it (hold Shift to keep building) |
| Click tower | Select it (U upgrade, X sell, T targeting mode) |
| F | Between waves: reroll the tile or the rewards |
| B (or G) / N then click | Builder raises ground (high ground = more range) / Digger lowers it |
| C | Castle talents |
| K | Damage chart (top right): shown, see-through, hidden |
| J | Compendium: every tower, enemy, boss, neutral building and commander (pauses the run; also on the main menu) |
| Space / V / P / M | Start wave / game speed / pause / sound on-off |
| Menu button | Set the run aside; Resume it from the main menu |
| F11 or Alt+Enter | Fullscreen on / off (remembered; also a button on the main menu) |
| Esc or right-click | Cancel |

## Look

The visual style follows Tower Dominion's clean readability:
- **Raised board on plain grass:** the grass outside your tiles is a muted, untextured green shaded by value
  noise (`backdrop_col` in `shaders/terrain.gdshader`), 1.6 units below the board (`Board.BACKDROP_Y`), and the
  board's walls are drawn as a stone lip over earth (`edge_lip`, `edge_soil`). The old spotlight decal is still
  there behind `Board.spotlight`.
- **Calm ground and roads:** flat colors with only a hint of texture (`detail`, `shaders/road.gdshader`), and
  sparse grass and flowers.
- **Color coding:** your towers get a rim light in your color's accent (`shaders/rim.gdshader`), and enemies are
  darkened with a hot rim (`shaders/foe.gdshader`) so they stand out.
- **Camera:** a long, narrow lens (`CameraRig.FOV` 32) under a warm key light with soft shadows. Hexes read
  big on screen: the opening view and the closest zoom sit `CameraRig.CELL_ZOOM` (1.35x) nearer.
- **UI:** Windows' built-in Bahnschrift font, loaded from the system and not bundled (other systems fall back to
  Godot's font). Panels are near-black, buttons are slanted, and titles are bold and italic.

### UI skin

The HUD wears Kenney's UI Pack: RPG Expansion (CC0, `assets/ui/kenney_rpg`): wooden frames for panels, slate
stone buttons that warm to wood when hovered and turn gold when live, parchment tooltips, cards tinted in their
faction's or reward's color, and the gauntlet cursor. `scripts/ui_skin.gd` builds the nine-slice styles and
`Hud._make_theme` / `_card_box` / `_panel_box` use them. `--no-kenney` brings back the flat dark look.
`tools/ui_snap.gd` draws the real HUD headless into PNGs (menu, heroes, council, run, tile, rewards, info, castle, end):
`Godot --headless --path . --script res://tools/ui_snap.gd -- <out dir> [screens] [--hover] [--deck] [--no-kenney]`.

## Sound

The sound effects in `assets/audio/` were generated with ElevenLabs by `tools/sfx_batch.py`. It reads your
key from the `ELEVENLABS_API_KEY` Windows user variable and never prints it. Each file is mixed to mono,
trimmed, and level-matched to the procedural sound it replaces (`tools/sfx_levels.json`), so the volume table in
`scripts/audio.gd` still balances.

- The second set (2026-10-04) aims at half grounded medieval foley (wood, steel, stone, leather, bells), half
  stylized punch; the first set, all-cartoon, is kept in `assets/audio/v1/` (copy a file back to restore it).
- `python tools/sfx_batch.py list` shows every sound and its prompt.
- `python tools/sfx_batch.py gen boom horn --takes=3` regenerates just those sounds (about 5 credits per second
  of audio on pay-as-you-go); takes land in `assets/audio/takes/`, and take 1 is used.
- `python tools/sfx_batch.py pick boom 2` switches to another take.
- Delete a file in `assets/audio/` to go back to the built-in procedural version (`scripts/audio.gd`). Any `.ogg`,
  `.wav` or `.mp3` named after a sound replaces it.

**Music**: every color has its own 2-minute battle track (`assets/audio/music_<faction>.mp3`), and the menu has a
main theme (`music_menu.mp3`), all made with ElevenLabs by `tools/music_batch.py`
(`python tools/music_batch.py gen forge` remakes one; about 825 credits per 2-minute track). A run crossfades into
its color's track, and tracks loop by crossfading into their own start, so there's no seam. Loudness is evened out
with `TRACK_TRIM` in `scripts/audio.gd`. A color without a track falls back to the procedural loop.

## Adding content

Everything is data in `scripts/game_data.gd`:

- **Color (faction)**: add an entry to `FACTIONS` with its unique tower ids (the shared ones are `SHARED_TOWERS`),
  pie/race/strengths/weakness texts, a `passive` fx dict, starting blueprints (`start_copies`), and its castle
  talent paths in `FACTION_TALENTS`.
- **Castle talent**: add a node (with its `fx`) to a path in `FACTION_TALENTS` or `SLAYERS`; `Game._apply_fx`
  applies the keys, so a new kind of effect means a new key there.
- **Commander**: an entry in `HEROES` with its powers (`fx`) and a `sig` (trigger + effect kind, see the comment).
- **Reward item**: weights are `REWARD_KINDS`; rolling and granting are `Game._roll_item` / `Game._grant`.
- **Tower**: add an entry to `TOWERS` (with its `tier` and blueprint `copies`), a footprint to `FOOTPRINTS`
  (shape from `SHAPES` + firing arc) and two specializations to `SPECS`. The attack kinds are `arrow`, `bolt`,
  `orb`, `lob`, `chain`, `slam`, `smite` (a strike on the target with splash), `breath` (a fixed straight line
  ahead; `line` is its width in tiles, `static` towers never turn), `grasp` (seizes `grasp` enemies at once),
  `beam` (a straight line from the tower through its target to the end of its reach, `beam_w` tiles wide),
  `muster` (knights march onto the target's road: `muster` gives their cap, life, stun and hits), `aura_dmg`,
  `aura_buff` and `aura_curse`. Flags and extras: `detect`, `shred`, `push` ([chance, tiles]), `pct`
  (share of current health), `curse`, `vuln` ([extra damage taken, seconds]), `boss_bonus`, `target` (default
  targeting mode) and `raise` (Necromancer zombies, `scripts/thrall.gd`). Support extras: `burn` ([dps, seconds]
  for the towers it buffs), `toll` (castle health it drinks after every wave) and `grow` / `grow_max` (extra
  damage buff for every wave since it was built).
- **Hero**: add to `HEROES` (faction, cost, portrait, two power texts, and `fx`).
- **Threat**: add to `THREATS` (enemy id, optional trait `shield` / `camo` / `swift`).
- **Terrain tiles** are rolled in code (`Board.make_tile`): entrance count from `ENTRANCE_ODDS`, winding roads,
  and random features. Hex math lives in `scripts/hex.gd`.
- **Neutral building / doctrine / War Council upgrade**: `NEUTRALS` (with its `group` and a model in `Models.KK_FIT`), `BOONS`,
  `META_UPGRADES`.

## Art

3D models come from CC0 packs by Kenney, Quaternius and KayKit, plus Meshy-generated towers, enemies, props,
neutral buildings, discoveries and hero portraits. See `assets/CREDITS.md`.

KayKit (Kay Lousberg, CC0, in `assets/kaykit`, wrapped by `scripts/kaykit.gd`) sets the main look:
- **Terrain**: the map looks like the pack's samples: your tiles are an island of Medieval Hexagon tiles, one tile
  thick, floating over a dark hex floor (`shaders/void_hex.gdshader`), with no meadow, skirt or forest ring around
  it. Drawn one batch per tile model (`Board._kk_rebuild`). Road cells get the piece whose exits match the road
  (`Board.KK_ROADS`, generated by `tools/kaykit_roads.gd`), ramps get sloped road, raised ground stands on earth
  pieces, and roads cross ponds on stone bridges (half bridges where the road turns). Forests are pine groves and
  rocks rocky knolls (`Board.KK_PROPS`, at the pack's own scale). The lighting is plain and bright so the pack's
  colors read as painted (`Game._kaykit_look`: no film curve, no haze, light contact shadows).
  - **Sea and shore** (`Board._kk_sea`): a level below the island, a ring of beaches and coast tiles turned so their
    grass meets the land (`Board.KK_COASTS`, generated by `tools/kaykit_coasts.gd`), grassy hills and mountains now
    and then on the shore (`KK_SHORE`), and open water one hex further out with lilies and reeds. It's redrawn as
    the island grows, so holes between your tiles show as bays.
  - **Details**: open grass hexes sometimes get a grassy knoll with dirt sides, a stone or a lone pine
    (`KK_DECOR`, cleared when you build there); every grass hex is a shade lighter or darker than its neighbors;
    ponds carry lilies.
  - **Palettes**: the pack's alternate textures by biome (`Board.KK_PALETTE`): Greenvale is Summer green,
    Deepwood Fall orange, Highlands Winter white, Lakelands the default yellow-green.
  Set `Board.KAYKIT_TERRAIN = false` to go back to the generated board and the old look.
- **Castle and buildings** take your color's KayKit team color (`KayKit.TEAM`: blue, green, red or yellow).
- **Enemies**: humanoid enemies are KayKit characters with real walk and death animations, their pack's weapons in
  hand and, where it suits them, an alternate skin (`Models.KK_ENEMY`, `KayKit.hold`, `KayKit.reskin`). The early
  waves are an orc warband: grey orcs with clubs (Goblin), green orcs with axes (Orc Brute) and war-drummer orcs
  (Goblin Shaman); then a blue horned imp (Frost Imp), a vampire lord (Hexguard), a black knight (Ironclad) and a
  fur-clad barbarian with a spiked shield (Spikeback). The Orc Raider's file has no texture of its own, so it always
  takes one of its two skins. All characters share one animation library per rig (`KayKit.library`).
- **Towers**: 17 towers are built from KayKit buildings and props laid on their footprint hexes, with a crew
  member (archer, knight, mage, dwarf engineer, druid, skeleton...) holding real gear. The crew turns to aim and
  plays an attack animation on every shot (`Models.KK_TOWER`, `Tower._crew_act`). Bombards turn both cannons.
  Magic and Grave towers are built from props of the Mystery packs: the Arcane Spire and the Stormcaller Oak have
  floating, spinning crystals (the Vampire's gems), the Soul Obelisk a soul gem on a tall pillar, the Plague
  Cauldron the Witch's cauldron and potion station with a skeleton alchemist, the Hex Tomb a crypt wall, pillars
  and the Vampire's throne, the Spore Mound giant mushrooms, the Chapel a golden paladin statue. Towers can stand
  on a hex stone plinth spanning their footprint (`plinth`), and pieces can float, spin and bob (`Tower._spinners`).
  The other towers (gryphon, treant, hive, flak battery, whirlpool, siren and the creatures) keep their Meshy art.
- **Blender-made towers** (`assets/towers/<id>.glb`) win over the KayKit composites and the Meshy art. All 47 towers
  have one (rebuilt in October 2026 to one design idea per tower: a single building, machine or creature that owns its
  footprint, with the team color on top). A few of them:
  - **Archer Tower**: a round stone tower with a timber hoarding and banners; the ranger stands in its open top.
  - **Trebuchet** / **Royal Bombard**: a counterweight trebuchet in a palisaded yard; a clover-plan stone fort whose
    two bombards sit on one turntable.
  - **Gryphon Roost**: a stone eyrie with a nest deck. The gryphon and its rider take off and swoop on enemy after
    enemy, then roost again.
  - **Dire Bear**, **Snapjaw Crab**, **Bone Colossus**: the beast leaps out to its target, strikes it beside it and
    comes home; the den, tidal flat or ossuary it leaves reads on its own.
  - **Elder Treant**, **Runic Hammer**, **Kraken**, **Mammoth**, **Mass Grave**, **Briar Thicket**: roots, a spectral
    hammer, a tentacle, rock spikes, grasping hands or thorn vines burst up under the enemy they hit.
  - The rest, by color: the Crown's arcane spire, chapel, war banner, seraph and archangel shrines, hall of knights and
    sunlance lighthouse; the Verdant thornspitter, spore mound, stormcaller oak, wasp hive, moonwell, rootbinder shrine
    and heart of the forest; the Forge's flame belcher, siege mortar, flak battery, magma golem, fat dragon on its
    hoard, doomsday cannon and forge of ages; the Tide's tide spire, coral harpooner, whirlpool shrine, siren rock,
    leviathan and tidecaller; the Grave's bone crypt, plague cauldron, soul obelisk, hex tomb, necromancer and blood
    altar.

  How it works:
  - Each GLB has a `Head` (it turns to aim), `Muzzle` markers (shots leave there) and an optional `Crew` marker
    (`Models.BLENDER_CREW` stands a KayKit character there).
  - Its rig plays `idle`, plus `fire` (and `reload`) on every attack, sped up to fit between shots
    (`Tower._rig_act`).
  - The scripts in `tools/blender/` build them: `kk_helpers.py`, `angel_common.py` (KayKit characters turned into
    angels: extra wing, halo and weapon bones, and the pack's clips baked with wing beats), a `<name>_common.py` of
    shared parts per family of towers (siege, castle, forge guns, tide spires, grave shrines...) and one
    `<id>_build.py` per tower. Clips are keyed at 30 frames a second (`start_tower` sets the scene to it).
  - `blender -b assets/towers/src/gallery.blend --python tools/blender/gallery_sync.py` adds any tower that isn't in
    the gallery yet.
  - `python tools/blender/build.py <id> [<id> ...] --out <preview dir>` builds them in a background Blender at low
    priority (it runs `build_tower.py`, and prints `OK <id> tris=N` or the traceback). Each build saves
    `assets/towers/src/<id>.blend`, exports the GLB and renders `<id>_sheet.png`: the three-quarter view, the game
    camera's view, the back, a strip of animation frames, close-ups (`PREVIEW["extra"]`) and the strike's frames.
    `assets/towers/src/gallery.blend` links them all side by side.
  - Before the export, `finalize_tower()` applies the bevels, cuts big faces smaller and bakes soft contact shade
    into a vertex color attribute (`bake_ao`), which the materials multiply in. In game, `Models._atlas_mat(team,
    shade)` and `Models.ground_mat_for()` read it wherever a surface carries vertex colors.
  - `kk_helpers.py` ends with a modelling kit: `Kit` (geometry gathered by color: any atlas swatch, `"team!"`,
    `"glow:r,g,b"`, `"ground"`), coursed stonework (`round_tower`, `bm_block_wall`, `bm_arch`, `bm_merlons`), tiled
    roofs (`bm_tile_cone`, `bm_tile_slope`), plank decks, faceted rocks and foliage (`bm_boulder`, `bm_blob`),
    lofted bodies and limbs with soft skinning for creatures (`bm_loft`, `oval`, `bm_tube`, `skin_soft`,
    `paint_faces`), flags that wave (`flag_bones`, `flag_part`, `wave_flag`) and paving (`bm_flagstones`).
    `dire_bear_build.py` and `gryphon_build.py` are the reference towers.
  - **Melee towers reach their prey** (`GameData.STRIKES`, `Tower._sortie_*`, `scripts/strike.gd`): the blow lands
    where the model lands.
    - "lunge": the beast is the `Head`; it leaps out to its target, strikes it and comes home (clips `idle`, `run`,
      `fire`): the Dire Bear, the Snapjaw Crab, the Bone Colossus.
    - "fly": the Gryphon takes off with its rider, swoops on enemy after enemy, wheels overhead between blows and
      goes home to roost (clip `fly`).
    - "erupt": a model of its own bursts up under the enemy (`build_strike()` in the tower's script exports
      `<id>_strike.glb` with a `strike` clip): the Elder Treant's roots, the Runic Hammer's spectral hammer, the
      Kraken's tentacles, and for the auras the Mammoth's rock spikes, the Mass Grave's hands and the Briar's vines.
    - A tower only does this once its GLB has the clips (or the strike file); until then it attacks as before.
  - Shots look like what fired them (`Projectile.LOOKS`): wasps, thorns, spears of light, flak shells, bone bolts,
    harpoons, the Leviathan's water jet.
  - `blender -b --factory-startup --python tools/blender/audit_normals.py -- <id> [<id> ...]` lists inside-out
    pieces (faces wound inward, which the game's single-sided materials cull, so you see the far side's inside).
  - The `.blend` files are git-ignored like all art, since they hold KayKit meshes. Tweak them in Blender and
    re-export with `export_tower()`.
  - Our own geometry is UV-mapped into the hex pack's atlas, so it shares KayKit's colors. Faces on the `kk_team`
    material slide along the atlas's team row to your color (`Models._atlas_mat`).
  - A tower's hexes (the plinth, on the `kk_ground` material, painted like the pack's hex tiles) take the map's
    palette in game: `Tower.setup` gives them `Board.ground_material()`, the tiles' own material for the biome. KayKit
    composites do the same with their hex-pack buildings. `--towertest` checks it.
  - `--no-blender` goes back to the KayKit composites.
- `--no-kaykit` runs with the models from before the KayKit swap, for before/after checks.
- `tools/tower_sheet.gd` draws towers on their hexes into a PNG with no window (a small software rasterizer in
  `tools/snap.gd`), so tower art can be checked in headless runs (`--biome=<id>` draws them in that biome's
  palette); `tools/map_sheet.gd` does the same for a grown
  map (add `--bridge` to force pond crossings), and `tools/ramp_test.gd` grows a dozen maps and fails if any ramp's
  road bends. `scripts/models.gd` maps each
tower and enemy to its model, and falls back to simple shapes if a file is missing. Multi-hex towers with their
own footprint-shaped model (the `fp2_*` set: one per multi-hex tower, each drawn to fill its footprint's silhouette)
are listed in `Models.FOOTPRINT_ART` with a yaw, a height cap and a stretch allowance (plus optional tilt / spin /
grow for models that came out standing up or turned); set `Models.FOOTPRINT_ART_V2 = false` to go back to the
first set. `tools/fp_preview.gd` renders them on their footprints from above and at an angle for checking facing,
and `--fpshot --faction=<id> --shotdir=<dir>` photographs every multi-hex tower of a faction in a real run.

Map dressing: terrain edges are rounded wherever the ground drops (`Board._bevel_at`: tile rims, cliffs, plateaus,
pond shores), roads are smooth cobbled lanes with dirt verges (`Board._rebuild_roads`), ponds have sand shores and
reeds, roads over water get one continuous plank boardwalk (`Board._rebuild_bridges`), grass tufts / flowers /
mushrooms are scattered per tile in small batches that fade out when zoomed far away, and signposts mark road
junctions. The terrain shader keeps colors calm (flat base color with the painted textures as light detail) and
paints the backdrop meadow a flat, muted green so the tiles stand out.

## Testing

Headless play-through with a bot, printing a line per wave:

```
Godot_v4.7.1-stable_win64_console.exe --headless --path . -- --autotest=crown --maxwave=30
```

Extra flags: `--difficulty=0|1|2` (without it the bot plays your saved difficulty), `--seed=<n>`, `--no-kaykit`, `--hero=<id>`, `--shotdir=<folder>` (saves screenshots at key moments;
don't combine it with `--headless`), `--menushot` (menu, hero select, War Council), `--mapshot` (a grown
late-game map, plus close-ups of a bridge, the castle and a lakeshore; add `--bridgetest` to force a lake crossing
and `--biome=<id>` to pick the biome), `--inputtest` (drives the mouse and keys through tile placement, hotkeys,
click-to-build, select, upgrade, Builder, Digger and the castle; prints `INPUTTEST FAIL` lines and exits 1 on
failure) and `--towertest=<id>` (builds that tower where it covers the most road, walks goblins into its arc, checks
that its head turns, that every shot plays its `fire` animation and leaves from its muzzle, and for the melee
towers that every blow lands beside its prey, then sells it and checks the refund; exits 1 on failure). Add
`--ttshots=<dir>` to draw the tower, the enemies and any strike models at the telling moments of an attack into
`<dir>/<id>_tt.png` with the software rasterizer (no window).
Test runs never write your save file.

**Playtest bots** (`scripts/playtest.gd`): `--skill=low|mid|high` picks how the autotest bot plays.
- low plays like a newcomer: slow to react, random drafts, facings and tiles, few upgrades.
- mid is the original bot: it builds near the least-defended road, upgrades sometimes and goes for long roads when
  placing tiles.
- high plays like a veteran. It searches every spot near the road for the most coverage of every route (weighted by
  how likely enemies take it, with diminishing returns where the road is already defended) and values towers by
  damage per gold (discounting overkill). It saves for better towers, picks the stronger specialization, raises its
  best towers with Builders and guards the flight lines before fliers come. It plans tiles for its big blueprints:
  it previews each placement's ground (`Board.plan_ground`), rerolls with Runes when nothing makes room, and levels
  nearly-flat patches with Builders and Diggers.

Add `--fresh` to ignore your saved profile (no War Council upgrades), and `--give=<tower>[:n]` / `--gold=N` to hand
the bot blueprints or gold. Every run prints a `PLAYTEST {json}` line. `python tools/playtest_matrix.py <out>
--seeds 1,2,3` runs every skill x color x difficulty in parallel headless processes, and
`python tools/playtest_report.py <out>` summarizes win rates, what kills runs, who carries each color, damage per
tower, Tier IV use, unplaceable blueprints and pacing (waves without damage, close calls, unspent gold, wave
length).

Playtest results (2026-10-04, 135 runs: every skill x color x difficulty, three seeds), win rates low / mid / high:
Normal 67 / 93 / 80%, Hard 33 / 60 / 80%, Brutal 7 / 27 / 73%. That was before balance round 5 (boss health by
type, Brutal gold, Hall of Knights) and buildable edge hexes, which haven't been measured yet. The baseline that
started it: Normal 20 / 70 / 70%, Hard 10 / 10 / 50%, Brutal 0 / 0 / 0%.
