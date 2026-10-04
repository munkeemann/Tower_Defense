# Tower Realms

A fantasy tower defense roguelite in Godot 4.7, inspired by Tower Dominion.
You grow a hex map one terrain tile per wave, then defend every road end it opens.

## Play

- Double-click `Play Tower Realms.bat`, or
- open Godot, choose **Import**, pick this folder's `project.godot`, then press F5.

## How a run works

1. **Pick a color and a commander** (see *The color pie* below). Every commander has two powers. Some are
   free; the others are unlocked with Renown.
2. **Expand the realm**: before every wave you're offered **one** random hexagonal terrain tile, which always
   fits somewhere. Place it next to an open road end, or cast 1 **Rune** to reroll it. Press **R** to turn it
   (6 ways). Tiles can carry high ground, ley crystals, trees, rocks and neutral buildings.
   - Each tile is a hexagon 3 small hexes along each edge (`Hex.K = 4`): 13 whole hexes plus a half hex in the
     middle of each side, where the road enters. When two tiles meet, their halves merge into whole hexes; only
     those shared halves match, the rest of each tile keeps its own height. Tiles are often a level above or below
     the road they join (3 levels in all) and often carry a raised patch, so the map climbs and dips; roads ramp
     between levels. Tiles carry few trees and rocks so there's room for the bigger towers, and ponds only cross a
     road where it runs straight (a bridge can't bend).
   - Entrances sit at side midpoints. A tile has 2 to 6 of them, usually 2 (50% 2, 27% 3, 13% 4, 7% 5, 3% 6).
     Once you're holding several battlefronts, tiles that would only add more get rarer.
   - **Sides that touch placed tiles must match**: entrance to entrance, wall to wall.
   - **Every open entrance is an enemy spawn** (a battlefront). Each enemy picks one at random and walks the
     shortest road to your castle. Extra entrances add battlefronts; lining a tile up with more than one open end
     merges them.
3. **Build** towers on your own tiles, then press **Start Wave** (Space).
   Every tower needs a **blueprint copy**: building one uses a copy, selling it gives the copy back.
   Towers take 1 to 5 hexes, all clear and level; the big ones usually fit where two or three tiles meet.
   Press **R** while placing to turn them. Some fire all around; directional ones (Ballista, Trebuchet, Flame
   Belcher, Coral Harpooner...) only fire inside an arc in front of them, and the Fat Dragon only in a straight
   line. Towers aim and measure range from the middle of their footprint. The placement preview marks each hex
   green or red on its own; a selected tower gets a gold outline and a hovered one a white outline. While placing
   or selecting a tower, the **hexes it reaches light up** (road hexes brighter).
   - **Tiers**: towers are Tier I, II or III. Later tiers cost a lot more and hit much harder. Tier II blueprints
     can be offered from wave 4, Tier III from wave 10 (`GameData.TIER_WAVE`); your starting towers are always
     available.
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

Each color has its own towers plus a shared pool (Archer, Ballista, Trebuchet, Royal Bombard), its own ability
(F) and its own commanders. Every color also has two **creatures** (one Tier II, one Tier III):

| Color | Towers | Creatures |
|---|---|---|
| White | Arcane Spire, Chapel of Dawn, War Banner, Gryphon Roost | **Seraph** (spears of light, +75% vs flyers, sees camo), **Archangel** (smites the strongest enemy: stun + splash, +50% vs bosses) |
| Green | Thornspitter, Spore Mound, Briar Thicket, Elder Treant, Stormcaller Oak, Wasp Hive, Moonwell, Rootbinder Shrine | **Dire Bear** (mauls and bleeds), **Ancient Mammoth** (stomps: damages and stuns everything around it) |
| Red | Flame Belcher, Runic Hammer, Siege Mortar, Flak Battery | **Magma Golem** (burning boulders), **Fat Dragon** (too heavy to move: breathes fire in a straight line where it faces) |
| Blue | Tide Spire, Coral Harpooner, Whirlpool Shrine, Siren Rock | **Snapjaw Crab** (two claws; cracked shells take +25% damage), **Kraken** (seizes and holds up to 3 enemies) |
| Black | Bone Crypt, Plague Cauldron, Soul Obelisk, Hex Tomb | **Mass Grave** (a trench of grasping hands that slows), **Necromancer** (walkers dying in its reach rise as zombies that shamble back down the road and grab the next enemy) |

### Castle talents (C)

Spend gold during a run on four talent paths, reacting to what's in front of you:

- **Treasury** (resource generation): +gold per wave, interest on unspent gold, extra Runes and Builders, a
  Royal Mint. Capstone: **Trade Caravans** (buy a Builder and 2 Runes, repeatable).
- **Artificers** (stronger, cheaper towers): cheaper towers, faster attacks, more range, extra blueprint copies.
  Capstone: **Refinement** (+6% damage for all towers, repeatable).
- **Slayers** (answer the threats): +damage vs flyers, armored, camouflaged or bosses; faster shield breaking.
  Take any, up to twice each.
- **Bulwark** (castle defense): walls, a keep ballista that shoots nearby enemies, a slowing moat, a Citadel.
  Capstone: **Ramparts** (more castle health and keep damage, repeatable).

Treasury, Artificers and Bulwark unlock in order. Early gold is tight, so every talent is a choice between towers
now and a stronger realm later.

### Threats (per run, not per wave)

Each run rolls 4 threats that join the invasion on waves 4, 9, 15 and 21. Each one is revealed in the
**Threat Intel** panel 3 waves before it arrives, so you can draft counters. Examples:

- **Shielded** enemies (blue bubble): shields soak damage. Magic strips them 1.5x faster, shield-breaker
  towers (Arcane Spire, Stormcaller Oak, some specializations) 2.5x faster.
- **Camo** enemies (ghostly): towers can only target them inside a detector's range. Detectors are Chapel of Dawn,
  Gryphon Roost, Moonwell, some specializations, Scout Hideouts, and the castle itself (3 tiles).
- **Swift** enemies move 40% faster.
- Flyers (harpies, wasps, gargoyles), splitting slimes, healing shamans and armored ironclads.

### Neutral buildings and discoveries

- **Ammo Depot**: towers next to it attack 25% faster. **Relay Station**: +20% range.
  **Scout Hideout**: detects camo within 4 tiles. **Supply Point**: +15 gold per wave.
- Discoveries sometimes turn up on a tile you just placed (about 1 in 3): chests (gold, a Rune), shrines (a free
  doctrine), mines (+20 gold per wave), ruins (2 blueprint copies) and rune caches (+3 Runes). A golden beam
  marks them. Claim one by reaching it with a tower's range.

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

- A tower gets **+15% range per level** of ground it stands on.
- **Builders** (B, or G) put up timber scaffolding that raises an empty hex, or every hex under a tower, by one
  level (max 3). **Diggers** (N) take one down a level. Both are items: you start with 2 Builders and 1 Digger
  and earn more from wave rewards (and the Treasury path).

## Controls

| Input | Action |
|---|---|
| WASD / arrows / right-drag | Move camera |
| Mouse wheel, Q / E | Zoom, rotate |
| Tile placement | Click a glowing spot. R turns it. The Reroll button swaps the tile for 1 Rune |
| 1-9, R, click | Pick a tower, turn it, build it (hold Shift to keep building) |
| Click tower | Select it (U upgrade, X sell, T targeting mode) |
| F | Faction ability |
| B (or G) / N then click | Builder raises ground (high ground = more range) / Digger lowers it |
| C | Castle talents |
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

## Sound

The sound effects in `assets/audio/` were generated with ElevenLabs by `tools/sfx_batch.py`. It reads your
key from the `ELEVENLABS_API_KEY` Windows user variable and never prints it. Each file is mixed to mono,
trimmed, and level-matched to the procedural sound it replaces (`tools/sfx_levels.json`), so the volume table in
`scripts/audio.gd` still balances.

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
  pie/race/strengths/weakness texts, a `passive` fx dict, starting blueprints (`start_copies`) and an ability.
- **Castle talent**: add a node to a path in `TALENTS` and its effect in `Game._apply_talent`.
- **Reward item**: weights are `REWARD_KINDS`; rolling and granting are `Game._roll_item` / `Game._grant`.
- **Tower**: add an entry to `TOWERS` (with its `tier` and blueprint `copies`), a footprint to `FOOTPRINTS`
  (shape from `SHAPES` + firing arc) and two specializations to `SPECS`. The attack kinds are `arrow`, `bolt`,
  `orb`, `lob`, `chain`, `slam`, `smite` (a strike on the target with splash), `breath` (a fixed straight line
  ahead; `line` is its width in tiles, `static` towers never turn), `grasp` (seizes `grasp` enemies at once),
  `aura_dmg`, `aura_buff` and `aura_curse`. Flags and extras: `detect`, `shred`, `push` ([chance, tiles]), `pct`
  (share of current health), `curse`, `vuln` ([extra damage taken, seconds]), `boss_bonus`, `target` (default
  targeting mode) and `raise` (Necromancer zombies, `scripts/thrall.gd`).
- **Hero**: add to `HEROES` (faction, cost, portrait, two power texts, and `fx`).
- **Threat**: add to `THREATS` (enemy id, optional trait `shield` / `camo` / `swift`).
- **Terrain tiles** are rolled in code (`Board.make_tile`): entrance count from `ENTRANCE_ODDS`, winding roads,
  and random features. Hex math lives in `scripts/hex.gd`.
- **Neutral building / discovery / doctrine / War Council upgrade**: `NEUTRALS`, `DISCOVERIES`, `BOONS`,
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
  - **Sea and shore** (`Board._kk_sea`): a clean ring of beach hexes in the palette's sand color around the island
    (a plain hex with its UVs pinned to the pack's sand, `Board._kk_sand_material`), grassy hills and mountains now
    and then on the shore (`KK_SHORE`), and open water a level below the island with lilies and reeds. It's redrawn
    as the island grows, so holes between your tiles show as bays. (`KK_COASTS` / `tools/kaykit_coasts.gd` map the
    pack's coast tiles, which looked ragged hex to hex and are no longer used for the ring.)
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
  The other towers keep their Meshy footprint art.
- `--no-kaykit` runs with the models from before the KayKit swap, for before/after checks.
- `tools/tower_sheet.gd` draws towers on their hexes into a PNG with no window (a small software rasterizer in
  `tools/snap.gd`), so tower art can be checked in headless runs; `tools/map_sheet.gd` does the same for a grown
  map (add `--bridge` to force pond crossings). `scripts/models.gd` maps each
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
and `--biome=<id>` to pick the biome) and `--inputtest` (simulates tile placement, hotkeys, click-to-build, upgrade and raise).
Test runs never write your save file.

Bot results at the time of writing (Normal): Crown won all 30 waves; Verdant fell on wave 22 after a
rough threat roll (two camo threats plus swift Frost Imps). The bot drafts counters to revealed threats but
does not plan detection per battlefront the way a player can.
