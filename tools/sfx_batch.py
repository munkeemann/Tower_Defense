"""Generate game sound effects with the ElevenLabs sound-generation API.

Usage:
  python tools/sfx_batch.py list                  # show every sound, its prompt, and the credit estimate
  python tools/sfx_batch.py gen [names...] [--takes=2]
      Generates each sound (or just the named ones) into assets/audio/takes/<name>_<k>.wav and copies take 1
      to assets/audio/<name>.wav, which the game loads instead of its procedural sound.
  python tools/sfx_batch.py pick <name> <k>       # use take k for a sound
  python tools/sfx_batch.py level                 # re-apply the loudness targets in tools/sfx_levels.json

Reads ELEVENLABS_API_KEY (or ELEVENLABS) from the environment / Windows user environment; never prints it.
Audio comes back as raw 16-bit PCM, interleaved stereo at 22050 Hz; it is mixed to mono, trimmed, faded and
loudness-matched here, then written as a mono WAV.
"""
import array, json, math, os, shutil, sys, urllib.error, urllib.request, wave, winreg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "audio")
TAKES = os.path.join(OUT, "takes")
RATE = 22050
CREDITS_PER_SECOND = 5    # measured on pay-as-you-go (the API's character-cost header); plans may differ

STYLE = "medieval fantasy game sound effect: grounded, weighty foley with a light stylized punch, crisp and clean, no music, no voice"
# name -> (prompt, seconds). Names match Audio.SOUNDS in scripts/audio.gd. Second set (2026-10-04): the first leaned
# all-cartoon; these aim at half grounded medieval foley (wood, steel, stone, leather, bells), half stylized punch.
SOUNDS = {
    "arrow": ("a longbow arrow released: a taut bowstring snap and a fast fletching whoosh", 0.6),
    "bolt": ("a siege ballista firing: heavy torsion arms slamming forward, a deep wooden thunk and a heavy bolt whooshing away", 0.8),
    "orb": ("a wizard's arcane orb launched: a soft magical hum rising into a shimmering whoosh with a faint crystal ring", 0.8),
    "lob": ("a trebuchet arm swinging: creaking timber, straining rope and a heavy stone thrown with a low whoosh", 1.0),
    "boom": ("a cannonball striking the ground: a punchy black-powder explosion with earth and stone debris raining down", 1.2),
    "chain": ("arcane lightning leaping between foes: sharp crackling electric snaps with a magical sizzle tail", 0.8),
    "slam": ("a massive war hammer smashing into the ground: a deep earth-shaking thud, cracking stone and a short rumble", 1.0),
    "pulse": ("a holy aura pulsing outward: a warm low choir-like hum swelling and fading", 0.8),
    "hit": ("an arrow striking a leather-armored soldier: a short meaty thwack", 0.5),
    "die": ("a goblin soldier falling in battle: a short guttural grunt and the clatter of dropped gear", 0.7),
    "gold": ("a few gold coins dropping into a palm: a bright metallic clink", 0.5),
    "build": ("carpenters raising a timber tower: two quick hammer blows, creaking beams and a solid wooden thud", 1.0),
    "upgrade": ("a tower reinforced: a blacksmith hammer ringing on an anvil, then a rising magical shimmer", 1.0),
    "sell": ("a leather sack of gold coins emptied onto a table: heavy coins clattering", 0.8),
    "horn": ("a regal herald trumpet fanfare announcing the start of battle: two bright brass trumpets play a short rising "
             "call from a castle wall, crisp and triumphant", 2.5),
    "boss": ("a colossal monster's deep roar echoing across a battlefield, with one heavy war drum hit", 3.0),
    "portal": ("a dark sorcerous rift tearing open: a low swirling rumble and a ghostly rushing whoosh", 1.5),
    "leak": ("a monster battering a castle gate: a heavy timber gate impact and an alarm bell clanging", 1.0),
    "click": ("a soft wooden click, like a game piece set on a board", 0.5),
    "victory": ("a short triumphant medieval fanfare: brass horns, a snare roll and a cymbal swell", 4.0),
    "defeat": ("a short somber medieval sting: a low mournful horn and a slow muffled war drum", 4.0),
    "tile": ("a great slab of earth and stone settling into place: a deep thump, crunching gravel and falling dust", 1.0),
    "chest": ("an old iron-bound wooden chest creaking open, coins shifting inside", 1.5),
    "card": ("a parchment scroll unrolled and flipped: a crisp paper rustle", 0.5),
    "shield": ("a magic ward absorbing a blow: a glassy energy ping over a metallic shield ring", 0.6),
    "scaffold": ("builders lashing wooden scaffolding: rope creaks, a few hammer knocks and planks set down", 1.2),
    "dig": ("a shovel biting into earth: a dirt scrape and a heavy clod tossed aside", 1.0),
    "rune": ("a rune stone igniting: carved stone grinding and a mystical chime", 1.0),
    "talent": ("a castle bell tolling once, deep and resonant, with a bright uplifting shimmer", 1.5),
    "fire": ("a short gout of flame from a dwarven fire engine: a pressurized whoosh and crackling fire", 1.0),
    "surge": ("a wave of seawater surging forward and crashing against stone", 1.5),
    "breath": ("a huge dragon exhaling a roaring stream of fire: a deep rumble, a long whoosh and crackling flames", 1.5),
    "smite": ("a holy pillar of light striking down: a bright angelic choir swell and a thunderous impact", 1.4),
    "spear": ("a radiant spear of light hurled: a shimmering whoosh ending in a bright bell-like chime", 0.6),
    "grasp": ("giant kraken tentacles lashing out and squeezing: wet slaps, creaking and a splash of water", 1.0),
    "stomp": ("a war mammoth stomping: a heavy earth-shaking thud, a rumble and a short trumpeting call", 1.2),
    "maul": ("a great bear roaring and swiping: a deep growl and a heavy claw slash", 0.9),
    "claw": ("giant crab claws snapping shut: a hard shell crack and crunch", 0.6),
    "magma": ("a molten boulder hurled by a lava golem: a fiery whoosh and a hissing lava sizzle", 1.0),
    "raise": ("a corpse clawing out of a grave: cracking dirt, a hollow groan and a ghostly whoosh", 1.2),
    "grab": ("a zombie lunging and seizing someone: a guttural snarl and a short struggle", 0.8),
    "crumble": ("a skeleton collapsing: dry bones clattering onto stone", 0.8),
    "graves": ("dead hands clawing up through grave dirt: scraping earth and faint distant moans", 1.0),
    "wings": ("a winged beast swooping low: heavy leathery wing beats and a rushing whoosh", 1.0),
    "splat": ("a glob of bubbling poison splattering: a wet splat and an acidic hiss", 0.7),
    "wave_clear": ("a short victorious sting: a quick brass flourish, a war drum hit and coins jingling", 1.5),
}


def api_key() -> str:
    for n in ("ELEVENLABS_API_KEY", "ELEVENLABS"):
        k = os.environ.get(n)
        if k:
            return k.strip()
    for n in ("ELEVENLABS_API_KEY", "ELEVENLABS"):
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as h:
                k, _ = winreg.QueryValueEx(h, n)
                if k:
                    return str(k).strip()
        except OSError:
            pass
    sys.exit("No ELEVENLABS_API_KEY found in the environment or Windows user environment.")


def generate(text: str, seconds: float) -> bytes:
    body = json.dumps({"text": text + ". " + STYLE, "duration_seconds": max(0.5, seconds),
                       "prompt_influence": 0.7}).encode()
    req = urllib.request.Request("https://api.elevenlabs.io/v1/sound-generation?output_format=pcm_22050",
                                 data=body, method="POST",
                                 headers={"xi-api-key": api_key(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        # the error body never contains the key; show it so failures are diagnosable
        raise SystemExit("ElevenLabs error %d: %s" % (e.code, e.read()[:400].decode("utf-8", "replace")))


## Target loudness (RMS) per sound: the level of the procedural sound it replaces, so the game's volume table
## (tuned by ear on those) still balances. Measured from Audio._make; see tools/sfx_levels.json.
LEVELS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfx_levels.json")))


def polish(pcm: bytes, name: str) -> array.array:
    """Mix to mono, trim leading silence, fade the tail, and match loudness so the game's volume table still applies."""
    a = array.array("h")
    a.frombytes(pcm[: len(pcm) // 4 * 4])
    if sys.byteorder != "little":
        a.byteswap()
    return shape(to_mono(a), LEVELS.get(name, 0.2 * 32767))


def to_mono(a: array.array) -> array.array:
    """The API's PCM is interleaved stereo (left, right, left, right...)."""
    return array.array("h", ((a[i] + a[i + 1]) // 2 for i in range(0, len(a) - 1, 2)))


def shape(a: array.array, target_rms: float) -> array.array:
    thresh = 600
    start = next((i for i, v in enumerate(a) if abs(v) > thresh), 0)
    a = a[max(0, start - int(RATE * 0.005)):]
    end = len(a)
    while end > 0 and abs(a[end - 1]) < thresh // 3:
        end -= 1
    a = a[: min(len(a), end + int(RATE * 0.05))]
    fade = min(len(a), int(RATE * 0.06))
    for i in range(fade):
        a[len(a) - fade + i] = int(a[len(a) - fade + i] * (1.0 - i / fade))
    if not a:
        return a
    peak = max(abs(v) for v in a) or 1
    rms = math.sqrt(sum(v * v for v in a) / len(a)) or 1.0
    gain = min(0.89 * 32767 / peak, target_rms / rms)   # match the target level, never past -1 dBFS peak
    return array.array("h", (max(-32767, min(32767, int(v * gain))) for v in a))


def write_wav(path: str, a: array.array) -> None:
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(a.tobytes())


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] == "list":
        total = 0.0
        for n, (p, s) in SOUNDS.items():
            total += s
            print("%-9s %4.1fs  %s" % (n, s, p))
        print("\n%d sounds, %.1f s total, about %d credits per take" % (len(SOUNDS), total, round(total * CREDITS_PER_SECOND)))
        return
    if args[0] == "level":
        # re-level every generated file (after changing sfx_levels.json)
        for path in [os.path.join(OUT, n + ".wav") for n in SOUNDS] + [os.path.join(TAKES, f) for f in os.listdir(TAKES) if f.endswith(".wav")]:
            if not os.path.exists(path):
                continue
            n = os.path.basename(path)[:-4].rsplit("_", 1)[0] if os.path.dirname(path) == TAKES else os.path.basename(path)[:-4]
            w = wave.open(path)
            a = array.array("h", w.readframes(w.getnframes()))
            w.close()
            write_wav(path, shape(a, LEVELS.get(n, 0.2 * 32767)))
        print("re-levelled")
        return
    if args[0] == "pick":
        n, k = args[1], int(args[2])
        shutil.copyfile(os.path.join(TAKES, "%s_%d.wav" % (n, k)), os.path.join(OUT, n + ".wav"))
        print("using %s take %d" % (n, k))
        return
    if args[0] == "gen":
        takes = 2
        names = []
        for a in args[1:]:
            if a.startswith("--takes="):
                takes = int(a.split("=", 1)[1])
            else:
                names.append(a)
        names = names or list(SOUNDS)
        unknown = [n for n in names if n not in SOUNDS]
        if unknown:
            sys.exit("unknown sounds: " + ", ".join(unknown))
        os.makedirs(TAKES, exist_ok=True)
        open(os.path.join(TAKES, ".gdignore"), "a").close()   # Godot skips the takes folder
        spent = 0
        for n in names:
            p, s = SOUNDS[n]
            for k in range(1, takes + 1):
                a = polish(generate(p, s), n)
                write_wav(os.path.join(TAKES, "%s_%d.wav" % (n, k)), a)
                spent += round(max(0.5, s) * CREDITS_PER_SECOND)
            shutil.copyfile(os.path.join(TAKES, "%s_1.wav" % n), os.path.join(OUT, n + ".wav"))
            print("%-9s done (%d take%s)   ~%d credits so far" % (n, takes, "" if takes == 1 else "s", spent))
        return
    sys.exit(__doc__)


if __name__ == "__main__":
    main()
