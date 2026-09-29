"""Batch asset pipeline for Meshy: concept image -> image-to-3D -> (humanoids) rig + death animation.

State lives in assets/custom/manifest.json so the pipeline can be resumed without re-spending credits.
Reads MESHY_API_KEY from the environment / Windows user environment; never prints it.

  python meshy_batch.py concepts [names...]   submit concept images (text-to-image) for assets without one
  python meshy_batch.py models [names...]     submit image-to-3D for assets whose concept is done
  python meshy_batch.py rig [names...]        submit rigging for humanoids whose model is done
  python meshy_batch.py death [names...]      submit the death animation for rigged humanoids
  python meshy_batch.py poll                  refresh every in-flight task, download finished files
  python meshy_batch.py status                table of where every asset is
  python meshy_batch.py reset <stage> <names> forget a stage's result so it can be redone
  python meshy_batch.py library <search>      search the animation library
"""
import json, os, sys, time, urllib.request, urllib.error, urllib.parse, winreg

API = "https://api.meshy.ai"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "custom")
CONCEPTS = os.path.join(OUT, "concepts")
MANIFEST = os.path.join(OUT, "manifest.json")

STYLE = ("Stylized hand-painted fantasy game asset for a 3D tower defense game. Chunky low-poly proportions, "
         "bold simple shapes, clean readable silhouette, saturated colors with soft painted shading. "
         "Single object, centered, entire object visible, three-quarter view from slightly above, "
         "plain white background, no text, no ground shadow.")
STYLE_CHAR = ("Stylized hand-painted fantasy game character for a 3D tower defense game. Chunky low-poly proportions, "
              "bold simple shapes, clean readable silhouette, saturated colors with soft painted shading. "
              "Full body, standing in A-pose, facing the viewer, plain white background, no text.")
TEXTURE = ("Stylized hand-painted game art with saturated colors and soft simple shading, clean shapes, "
           "matching a colorful low poly fantasy strategy game. No photorealism, no noise.")
IMAGE_MODEL = "nano-banana-2"
DEATH_ACTION = 187  # "Knock Down" (Fighting / Dying) in Meshy's animation library


def key() -> str:
    k = os.environ.get("MESHY_API_KEY")
    if not k:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as h:
            k, _ = winreg.QueryValueEx(h, "MESHY_API_KEY")
    return k


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method, headers={
        "Authorization": "Bearer " + key(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_body": e.read().decode()[:300]}


def load():
    with open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


def save(m):
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(m, f, indent=1)


def pick(m, names):
    return [a for a in m["assets"] if not names or a["name"] in names]


def fetch(url, path):
    urllib.request.urlretrieve(url, path)
    return os.path.getsize(path)


def submit(path, body, a, field):
    r = call("POST", path, body)
    if "result" in r:
        a[field] = r["result"]
        print(f"  {a['name']}: {field} -> submitted")
        return True
    print(f"  {a['name']}: {field} FAILED {r}")
    return False


def cmd_concepts(m, names):
    for a in pick(m, names):
        if a.get("concept_task"):
            continue
        style = STYLE_CHAR if a["kind"] == "humanoid" else STYLE
        if a["kind"] in ("texture", "icon"):
            style = ""   # these carry their full prompt
        body = {"ai_model": IMAGE_MODEL, "prompt": (a["prompt"] + " " + style).strip()}
        if a["kind"] == "humanoid":
            body["pose_mode"] = "a-pose"
        if not submit("/openapi/v1/text-to-image", body, a, "concept_task"):
            break
        save(m)
        time.sleep(1)


def cmd_models(m, names):
    for a in pick(m, names):
        if a.get("model_task") or not a.get("concept_done") or a["kind"] in ("texture", "icon"):
            continue
        body = {"input_task_id": a["concept_task"], "ai_model": "latest", "topology": "triangle",
                "should_remesh": True, "target_polycount": a.get("polys", 8000), "should_texture": True,
                "enable_pbr": False, "texture_prompt": TEXTURE, "texture_resolution": "2k"}
        if a["kind"] == "humanoid":
            body["pose_mode"] = "a-pose"
        if not submit("/openapi/v1/image-to-3d", body, a, "model_task"):
            break
        save(m)
        time.sleep(1)


def cmd_rig(m, names):
    for a in pick(m, names):
        if a["kind"] != "humanoid" or a.get("rig_task") or not a.get("model_done"):
            continue
        body = {"input_task_id": a["model_task"], "height_meters": a.get("height", 1.7)}
        if not submit("/openapi/v1/rigging", body, a, "rig_task"):
            break
        save(m)
        time.sleep(1)


def cmd_death(m, names):
    action = m.get("_death_action") or DEATH_ACTION
    if action is None:
        print("no death action id set in manifest (_death_action); use `library death` first")
        return
    for a in pick(m, names):
        if a["kind"] != "humanoid" or a.get("death_task") or not a.get("rig_done"):
            continue
        body = {"rig_task_id": a["rig_task"], "action_id": action}
        if not submit("/openapi/v1/animations", body, a, "death_task"):
            break
        save(m)
        time.sleep(1)


def _find_url(obj, *want):
    """Depth-first search for the first string value under any of the wanted keys."""
    if isinstance(obj, dict):
        for k in want:
            v = obj.get(k)
            if isinstance(v, str) and v.startswith("http"):
                return v
        for v in obj.values():
            u = _find_url(v, *want)
            if u:
                return u
    elif isinstance(obj, list):
        for v in obj:
            u = _find_url(v, *want)
            if u:
                return u
    return None


def cmd_poll(m, _names):
    os.makedirs(CONCEPTS, exist_ok=True)
    spent = 0
    for a in m["assets"]:
        n = a["name"]
        if a.get("concept_task") and not a.get("concept_done"):
            t = call("GET", "/openapi/v1/text-to-image/" + a["concept_task"])
            if t.get("status") == "SUCCEEDED":
                dest = os.path.join(CONCEPTS, n + ".png")
                if a["kind"] in ("texture", "icon"):
                    sub = os.path.join(OUT, a["kind"] + "s")
                    os.makedirs(sub, exist_ok=True)
                    dest = os.path.join(sub, n + ".png")
                fetch(t["image_urls"][0], dest)
                a["concept_done"] = True
                spent += t.get("consumed_credits") or 0
                print(f"  {n}: concept done")
            elif t.get("status") in ("FAILED", "CANCELED"):
                print(f"  {n}: concept {t.get('status')} {t.get('task_error')}")
                a["concept_task"] = None
        if a.get("model_task") and not a.get("model_done"):
            t = call("GET", "/openapi/v1/image-to-3d/" + a["model_task"])
            if t.get("status") == "SUCCEEDED":
                size = fetch(t["model_urls"]["glb"], os.path.join(OUT, n + ".glb"))
                a["model_done"] = True
                spent += t.get("consumed_credits") or 0
                print(f"  {n}: model done ({size // 1024} KB)")
            elif t.get("status") in ("FAILED", "CANCELED"):
                print(f"  {n}: model {t.get('status')} {t.get('task_error')}")
                a["model_task"] = None
            else:
                print(f"  {n}: model {t.get('status')} {t.get('progress')}%")
        if a.get("rig_task") and not a.get("rig_done"):
            t = call("GET", "/openapi/v1/rigging/" + a["rig_task"])
            if t.get("status") == "SUCCEEDED":
                res = t.get("result") or {}
                walk = _find_url(res, "walking_glb_url")
                rigged = _find_url(res, "rigged_character_glb_url")
                if walk:
                    fetch(walk, os.path.join(OUT, n + "_walk.glb"))
                if rigged:
                    fetch(rigged, os.path.join(OUT, n + "_rigged.glb"))
                a["rig_done"] = True
                a["rig_keys"] = list(res.keys())
                spent += t.get("consumed_credits") or 0
                print(f"  {n}: rig done (walk={'yes' if walk else 'no'})")
            elif t.get("status") in ("FAILED", "CANCELED"):
                print(f"  {n}: rig {t.get('status')} {t.get('task_error')}")
                a["rig_task"] = None
                a["rig_failed"] = True
            else:
                print(f"  {n}: rig {t.get('status')} {t.get('progress')}%")
        if a.get("death_task") and not a.get("death_done"):
            t = call("GET", "/openapi/v1/animations/" + a["death_task"])
            if t.get("status") == "SUCCEEDED":
                url = _find_url(t, "animation_glb_url")
                if url:
                    fetch(url, os.path.join(OUT, n + "_death.glb"))
                a["death_done"] = True
                spent += t.get("consumed_credits") or 0
                print(f"  {n}: death anim done")
            elif t.get("status") in ("FAILED", "CANCELED"):
                print(f"  {n}: death {t.get('status')} {t.get('task_error')}")
                a["death_task"] = None
    save(m)
    bal = call("GET", "/openapi/v1/balance")
    print(f"credits spent this poll: {spent}   balance now: {bal.get('balance')}")


def cmd_status(m, _names):
    for a in m["assets"]:
        stages = []
        for s in ("concept", "model", "rig", "death"):
            if a.get(s + "_done"):
                stages.append(s + ":ok")
            elif a.get(s + "_task"):
                stages.append(s + ":...")
        print(f"  {a['name']:<16} {a['kind']:<9} {' '.join(stages)}")


def cmd_reset(m, names):
    stage, names = names[0], names[1:]
    order = ["concept", "model", "rig", "death"]
    for a in pick(m, names):
        for s in order[order.index(stage):]:
            a.pop(s + "_task", None)
            a.pop(s + "_done", None)
        print(f"  {a['name']}: reset from {stage}")
    save(m)


def cmd_library(m, names):
    q = urllib.parse.quote(" ".join(names))
    r = call("GET", "/openapi/v1/animations/library?search=" + q)
    items = r if isinstance(r, list) else r.get("result") or r.get("data") or r
    print(json.dumps(items, indent=1)[:3000])


if __name__ == "__main__":
    c, args = sys.argv[1], sys.argv[2:]
    m = load()
    {"concepts": cmd_concepts, "models": cmd_models, "rig": cmd_rig, "death": cmd_death, "poll": cmd_poll,
     "status": cmd_status, "reset": cmd_reset, "library": cmd_library}[c](m, args)
