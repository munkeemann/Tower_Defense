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

STYLE = "fantasy tower defense game sound effect, clean, no music, no voice"
# name -> (prompt, seconds). Names match Audio.SOUNDS in scripts/audio.gd.
SOUNDS = {
    "arrow": ("a single wooden arrow loosed from a longbow, quick bowstring twang and whoosh", 0.6),
    "bolt": ("a heavy ballista firing a large bolt, deep bowstring thunk and whoosh", 0.8),
    "orb": ("a glowing arcane orb launched from a wizard tower, shimmering magical whoosh", 0.8),
    "lob": ("a catapult arm swinging and hurling a heavy stone, wooden creak and thump", 1.0),
    "boom": ("a cannonball exploding on impact, punchy explosion with debris", 1.2),
    "chain": ("crackling chain lightning arcing between targets, sharp electric zap", 0.8),
    "slam": ("a giant hammer slamming into the ground, heavy earth thud with a short rumble", 1.0),
    "pulse": ("a soft magical aura pulse, low warm hum swelling and fading", 0.8),
    "hit": ("a small arrow striking a monster, short dull thwack", 0.5),
    "die": ("a small goblin creature dying, short cartoonish grunt", 0.7),
    "gold": ("a few gold coins clinking, bright small pickup", 0.5),
    "build": ("a wooden defense tower built quickly, a few hammer knocks and a solid thud", 1.0),
    "upgrade": ("a magical upgrade, rising sparkle chime", 1.0),
    "sell": ("gold coins poured into a leather pouch", 0.8),
    "horn": ("a regal herald trumpet fanfare announcing the start of battle: two bright brass trumpets play a short rising "
             "call from a castle wall, crisp and triumphant", 2.5),
    "boss": ("an ominous giant monster roar with a deep war drum hit", 3.0),
    "portal": ("a dark magic portal opening, swirling vortex whoosh", 1.5),
    "leak": ("a monster striking the castle gate, heavy wooden impact and a warning bell", 1.0),
    "click": ("a soft wooden user interface button click", 0.5),
    "victory": ("a short triumphant medieval fanfare with brass and drums", 4.0),
    "defeat": ("a short somber defeat sting, low brass and a slow drum", 4.0),
    "tile": ("a large slab of land dropping into place, heavy stone thump with dust and rumble", 1.0),
    "chest": ("a wooden treasure chest creaking open with sparkling coins", 1.5),
    "card": ("a parchment card flipped over, quick paper swish", 0.5),
    "shield": ("a magic shield absorbing a hit, glassy energy ping", 0.6),
    # new sounds for newer features (hooked up in code once they exist)
    "scaffold": ("carpenters quickly knocking together wooden scaffolding, a few hammer knocks and creaks", 1.2),
    "dig": ("a shovel digging into earth, dirt scrape and thud", 1.0),
    "rune": ("casting a glowing rune stone, mystical chime and shimmer", 1.0),
    "talent": ("a castle upgrade, deep bell toll with an uplifting chime", 1.5),
    "fire": ("a short burst of fire breath from a flamethrower, whoosh and crackle", 1.0),
    "surge": ("a wave of water surging forward and crashing", 1.5),
    # creature towers, zombies and other effects (2026-09-29)
    "breath": ("a huge dragon exhaling a long roaring stream of fire, deep whoosh and crackling flames", 1.5),
    "smite": ("a holy pillar of light crashing down from the sky, a bright angelic choir swell and a thunderous impact", 1.4),
    "spear": ("a radiant spear of light hurled through the air, a shimmering whoosh with a bright bell-like chime", 0.6),
    "grasp": ("giant wet tentacles lashing out and squeezing, slimy slaps and a water splash", 1.0),
    "stomp": ("a giant mammoth stomping the ground, a heavy earth-shaking thud with a rumble and a short trumpet call", 1.2),
    "maul": ("a huge bear roaring and swiping its claws, a growl and a heavy slash", 0.9),
    "claw": ("giant crab claws snapping shut with a hard shell crunch", 0.6),
    "magma": ("a molten boulder hurled from a volcano golem, a fiery whoosh and a lava sizzle", 1.0),
    "raise": ("a zombie clawing its way out of the ground, cracking dirt, a hollow groan and a ghostly whoosh", 1.2),
    "grab": ("a zombie lunging and grabbing someone, a snarl and a short struggle", 0.8),
    "crumble": ("a skeleton crumbling to dust, bones clattering to the ground", 0.8),
    "graves": ("dead hands clawing up through the dirt of a grave, scraping earth and faint moans", 1.0),
    "wings": ("a flying monster swooping overhead, heavy leathery wing flaps and a whoosh", 1.0),
    "splat": ("a glob of bubbling poison splattering on the ground, a wet splat and a hiss", 0.7),
    "wave_clear": ("a short triumphant victory sting for a cleared wave: a quick brass flourish and a drum hit with coins jingling", 1.5),
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
                       "prompt_influence": 0.5}).encode()
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
