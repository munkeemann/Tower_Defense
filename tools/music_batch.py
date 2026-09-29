"""Generate a battle music track for each color (faction) with the ElevenLabs music API.

Usage:
  python tools/music_batch.py list
  python tools/music_batch.py gen [ids...] [--seconds=120]     (ids: the five factions, and "menu")
      Writes assets/audio/music_<faction>.mp3. The game loops it with a crossfade (scripts/audio.gd).

Reads the key the same way as tools/sfx_batch.py (ELEVENLABS_API_KEY) and never prints it.
"""
import json, os, sys, urllib.error, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sfx_batch import api_key, OUT  # noqa: E402

COMMON = ("Instrumental background battle music for a fantasy tower defense game. Starts immediately at full energy "
          "with no intro, no ending and no fade out, so it can loop. Steady tempo and consistent intensity the whole way "
          "through, leaving room for sound effects. No vocals.")
TRACKS = {
    "crown": "White, the Aurelian Crown (disciplined human knights): heroic medieval orchestral march, noble brass "
             "fanfares, snare drum cadence, bright strings, determined and proud, about 110 BPM.",
    "verdant": "Green, the Verdant Circle (forest elves): mystical woodland music, flowing flutes and woodwinds, harp "
               "arpeggios, hand drums and frame drums, lush strings, magical but driving, about 100 BPM.",
    "forge": "Red, the Deep Forge (dwarven engineers): heavy and stomping, pounding war drums, rhythmic anvil strikes, "
             "deep brass and low cellos, gritty and fiery, industrial forge energy, about 95 BPM.",
    "tide": "Blue, the Tidal Court (merfolk of the deep): oceanic and flowing, shimmering celesta and harp, swelling "
            "strings like waves, rolling toms, airy synth pads, mysterious and majestic, about 100 BPM.",
    "grave": "Black, the Bone Legion (undead skeletons): dark and sinister, pipe organ, low staccato strings, rattling "
             "bone percussion and marimba, pounding timpani, eerie and relentless, about 105 BPM.",
    "menu": "Main title theme for the realm (the menu screen, calmer than the battle tracks): a memorable heroic melody "
            "on horns and strings with hints of all five realms - woodland flutes, dwarven drums, oceanic harp, a dark "
            "organ and noble brass - epic, warm and inviting, about 90 BPM.",
}


def compose(prompt: str, seconds: int, model: str) -> tuple:
    body = json.dumps({"prompt": prompt + " " + COMMON, "music_length_ms": seconds * 1000,
                       "model_id": model, "force_instrumental": True}).encode()
    req = urllib.request.Request("https://api.elevenlabs.io/v1/music?output_format=mp3_44100_128", data=body,
                                 method="POST", headers={"xi-api-key": api_key(), "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return r.read(), r.headers.get("character-cost", "?")


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] == "list":
        for k, v in TRACKS.items():
            print("%-8s %s" % (k, v))
        return
    if args[0] == "gen":
        seconds = 120
        ids = []
        for a in args[1:]:
            if a.startswith("--seconds="):
                seconds = int(a.split("=", 1)[1])
            else:
                ids.append(a)
        ids = ids or list(TRACKS)
        for fid in ids:
            data, cost = None, "?"
            for model in ("music_v2_5", "music_v1"):
                try:
                    data, cost = compose(TRACKS[fid], seconds, model)
                    break
                except urllib.error.HTTPError as e:
                    msg = e.read()[:300].decode("utf-8", "replace")
                    print("  %s with %s failed (%d): %s" % (fid, model, e.code, msg))
            if data is None:
                sys.exit("giving up on " + fid)
            path = os.path.join(OUT, "music_%s.mp3" % fid)
            with open(path, "wb") as f:
                f.write(data)
            print("%-8s %s  %.1f MB  cost %s" % (fid, model, len(data) / 1e6, cost))
        return
    sys.exit(__doc__)


if __name__ == "__main__":
    main()
