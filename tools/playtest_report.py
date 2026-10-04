"""Summarizes a playtest matrix (tools/playtest_matrix.py) into <out>/report.md: win rates by skill and difficulty, every
faction's results, what killed the losing runs, which towers carry each color, and pacing signals for "fun" (close
calls, flawless stretches, unspent gold, build cadence, wave length, Tier IV impact).

    python tools/playtest_report.py <out dir>
"""
import json, math, os, sys
from collections import defaultdict

SK = ["low", "mid", "high"]
DIFF = ["Normal", "Hard", "Brutal"]
FAC = ["crown", "verdant", "forge", "tide", "grave"]
T4 = ["knight_hall", "sunlance", "doom_cannon", "war_forge", "leviathan", "tidecaller", "bone_colossus", "blood_altar", "heart_tree"]


def load(out):
    return [json.loads(l) for l in open(os.path.join(out, "results.jsonl"), encoding="utf-8")]


def pct(a, b):
    return "%d%%" % round(100.0 * a / b) if b else "-"


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else 0.0


def bracket(w):
    return 0 if w <= 10 else (1 if w <= 20 else 2)


def main():
    out = sys.argv[1]
    runs = load(out)
    L = []
    P = L.append
    P("# Playtest report: %d runs\n" % len(runs))
    # ---- win rates
    P("## Win rate by skill and difficulty (runs reaching wave 30)\n")
    P("| Skill | " + " | ".join(DIFF) + " |")
    P("|---|---|---|---|")
    for s in SK:
        row = []
        for d in range(3):
            rs = [r for r in runs if r["skill"] == s and r["difficulty"] == d]
            wins = sum(1 for r in rs if r["victory"])
            row.append("%s (%d/%d), avg wave %.1f" % (pct(wins, len(rs)), wins, len(rs), mean(r["wave"] for r in rs)))
        P("| %s | %s |" % (s, " | ".join(row)))
    P("")
    # ---- every cell
    P("## Every run (W = won, number = wave reached, hp = health left)\n")
    P("| Faction | Skill | " + " | ".join(DIFF) + " |")
    P("|---|---|---|---|---|")
    for f in FAC:
        for s in SK:
            cells = []
            for d in range(3):
                rs = sorted([r for r in runs if r["faction"] == f and r["skill"] == s and r["difficulty"] == d], key=lambda r: r["seed"])
                cells.append(", ".join(("W %d/%d hp" % (r["hp"], r["max_hp"])) if r["victory"] else ("died w%d" % r["wave"]) for r in rs))
            P("| %s | %s | %s |" % (f, s, " | ".join(cells)))
    P("")
    # ---- faction strength
    P("## Faction strength (all skills)\n")
    P("| Faction | Normal | Hard | Brutal | avg wave (Hard+Brutal) |")
    P("|---|---|---|---|---|")
    for f in FAC:
        row = []
        for d in range(3):
            rs = [r for r in runs if r["faction"] == f and r["difficulty"] == d]
            row.append(pct(sum(r["victory"] for r in rs), len(rs)))
        hb = [r["wave"] for r in runs if r["faction"] == f and r["difficulty"] > 0]
        P("| %s | %s | %.1f |" % (f, " | ".join(row), mean(hb)))
    P("")
    # ---- what kills
    P("## What killed the losing runs\n")
    leak_by = defaultdict(int)
    death_waves = defaultdict(list)
    for r in runs:
        if r["victory"]:
            continue
        death_waves[(r["skill"], r["difficulty"])].append(r["wave"])
        for w in r["waves"][-3:]:
            for k, v in (w.get("leaks") or {}).items():
                leak_by[k] += v
    P("Leaks in the last three waves of every lost run, by enemy: " +
      ", ".join("%s %d" % kv for kv in sorted(leak_by.items(), key=lambda x: -x[1])) + "\n")
    for k in sorted(death_waves):
        P("- %s / %s: died on waves %s" % (k[0], DIFF[k[1]], sorted(death_waves[k])))
    P("")
    # ---- bosses
    P("## Boss waves (10 / 20 / 30): health lost, among runs that got there\n")
    for s in SK:
        parts = []
        for bw in (10, 20, 30):
            losses = []
            for r in runs:
                if r["skill"] != s:
                    continue
                for w in r["waves"]:
                    if w["w"] == bw:
                        losses.append(100.0 * (w["hp0"] - w["hp1"]) / max(1, r["max_hp"]))
            parts.append("w%d: %.0f%% of max hp on average (%d runs)" % (bw, mean(losses), len(losses)))
        P("- %s: %s" % (s, "; ".join(parts)))
    P("")
    # ---- towers
    P("## Who carries each color (share of all tower damage, all runs)\n")
    for f in FAC:
        dmg = defaultdict(float)
        built = defaultdict(int)
        for r in runs:
            if r["faction"] != f:
                continue
            for k, v in r["dmg"].items():
                dmg[k] += v
            for k, v in r["count"].items():
                built[k] += v
        tot = sum(dmg.values()) or 1
        top = sorted(dmg.items(), key=lambda x: -x[1])
        P("- **%s**: " % f + ", ".join("%s %d%% (%d built)" % (k, round(100 * v / tot), built[k]) for k, v in top))
    P("")
    # damage per tower built (how hard each one hits once on the field)
    P("## Damage per tower built (mean per copy, all runs; Tier IV marked *)\n")
    per = defaultdict(list)
    for r in runs:
        for t in r.get("towers", []):
            per[t[0]].append(t[4])
    rows = sorted(per.items(), key=lambda x: -mean(x[1]))
    P(", ".join("%s%s %dk (%d)" % (k, "*" if k in T4 else "", round(mean(v) / 1000), len(v)) for k, v in rows))
    P("")
    # ---- Tier IV
    P("## Tier IV\n")
    for t4 in T4:
        n_runs = [r for r in runs if t4 in r["owned"] or any(t[0] == t4 for t in r.get("towers", []))]
        builds = [(t[1], t[4]) for r in runs for t in r.get("towers", []) if t[0] == t4]
        unpl = sum(1 for r in runs for u in r.get("unplaced", []) if u[0] == t4)
        shares = []
        for r in runs:
            tot = sum(r["dmg"].values()) or 1
            if t4 in r["dmg"]:
                shares.append(100.0 * r["dmg"][t4] / tot)
        P("- %s: drafted in %d runs, %d built (avg wave %.1f), %.0f%% of its run's damage on average; no place to build it at the end in %d runs"
          % (t4, len(n_runs), len(builds), mean(b[0] for b in builds), mean(shares), unpl))
    unpl_all = defaultdict(int)
    for r in runs:
        for u in r.get("unplaced", []):
            unpl_all[u[0]] += 1
    P("\nBlueprints with nowhere to build at the end of a run (runs): " + ", ".join("%s %d" % kv for kv in sorted(unpl_all.items(), key=lambda x: -x[1])))
    P("")
    # ---- pacing / fun
    P("## Pacing and \"fun\" signals\n")
    P("| Skill / difficulty | waves with no damage | close calls (lost >=20% hp in a wave) | first hp lost (wave) | unspent gold at wave start, w1-10 / 11-20 / 21-30 | towers built per wave, w1-10 / 11-20 / 21-30 | wave length s, w1-10 / 11-20 / 21-30 | distinct towers built | top tower's share |")
    P("|---|---|---|---|---|---|---|---|---|")
    for s in SK:
        for d in range(3):
            rs = [r for r in runs if r["skill"] == s and r["difficulty"] == d]
            if not rs:
                continue
            ws = [w for r in rs for w in r["waves"]]
            clean = sum(1 for w in ws if w["hp1"] >= w["hp0"])
            close = sum(1 for r in rs for w in r["waves"] if (w["hp0"] - w["hp1"]) >= 0.2 * r["max_hp"] and w["hp1"] > 0)
            first = [next((w["w"] for w in r["waves"] if w["hp1"] < w["hp0"]), None) for r in rs]
            first = [x for x in first if x]
            gold = ["%.0f" % mean(w["gold0"] for w in ws if bracket(w["w"]) == b) for b in range(3)]
            secs = ["%.0f" % mean(w["t"] for w in ws if bracket(w["w"]) == b) for b in range(3)]
            bpw = []
            for b in range(3):
                n_w = sum(1 for w in ws if bracket(w["w"]) == b)
                n_b = sum(1 for r in rs for t in r.get("towers", []) if bracket(max(1, t[1])) == b)
                bpw.append("%.1f" % (n_b / n_w if n_w else 0))
            distinct = mean(len(set(t[0] for t in r.get("towers", []))) for r in rs)
            tops = []
            for r in rs:
                tot = sum(r["dmg"].values()) or 1
                if r["dmg"]:
                    tops.append(100.0 * max(r["dmg"].values()) / tot)
            P("| %s / %s | %s | %d in %d runs | %.1f | %s | %s | %s | %.1f | %.0f%% |" % (
                s, DIFF[d], pct(clean, len(ws)), close, len(rs), mean(first), " / ".join(gold), " / ".join(bpw), " / ".join(secs), distinct, mean(tops)))
    P("")
    P("Signature passives fired %.1f times per run on average; talents bought per run: %s." % (
        mean(r["sig"] for r in runs), ", ".join("%s %.1f" % (s, mean(len(r["talents"]) for r in runs if r["skill"] == s)) for s in SK)))
    open(os.path.join(out, "report.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
