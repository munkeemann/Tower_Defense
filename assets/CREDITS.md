# Asset credits

All third-party models are CC0 (public domain). No attribution is required, but thanks to:

- **Kenney** (kenney.nl): Tower Defense Kit (`td/`), Castle Kit (`castle/`), Nature Kit (`nature/`)
- **Quaternius** (quaternius.com): Ultimate Monsters (`monsters/`)
- **Kay Lousberg / KayKit** (kaylousberg.com): Character Pack: Skeletons (`skeletons/`), and in `kaykit/`: Medieval
  Hexagon Pack (Extra), Adventurers (Extra), Mystery Monthly Series 4 and 5, Character Animations, Skeletons, Fantasy
  Weapons Bits, Dungeon Pack and Forest Nature Pack (`chars/`, `anims/`, `hex/`, `gear/`)

## AI-generated (`custom/`)

Generated with Meshy for this project: concept image, then image-to-3D, then auto-rig and animation for humanoids.
Prompts and task IDs are in `custom/manifest.json`, and the concept art is in `custom/concepts/`.
`tools/meshy_batch.py` regenerates any of them (it reads `MESHY_API_KEY` from your environment).
`moonwell_meshy.glb` was an earlier text-to-3D test.
