"""Minimal Meshy REST client. Reads MESHY_API_KEY from the Windows user environment; never prints it.

usage:
  python meshy.py balance
  python meshy.py preview "<prompt>" [polycount]        -> prints task id
  python meshy.py refine <preview_task_id> "<texture prompt>"
  python meshy.py wait <task_id>                          -> polls until done, prints summary
  python meshy.py download <task_id> <out.glb>
"""
import json, os, sys, time, urllib.request, urllib.error, winreg

API = "https://api.meshy.ai"


def key() -> str:
    k = os.environ.get("MESHY_API_KEY")
    if not k:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as h:
            k, _ = winreg.QueryValueEx(h, "MESHY_API_KEY")
    return k


def call(method: str, path: str, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method, headers={
        "Authorization": "Bearer " + key(),
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode()[:500])
        sys.exit(1)


def main():
    cmd = sys.argv[1]
    if cmd == "balance":
        print("balance:", call("GET", "/openapi/v1/balance"))
    elif cmd == "preview":
        body = {
            "mode": "preview",
            "prompt": sys.argv[2],
            "ai_model": "latest",
            "topology": "triangle",
            "should_remesh": True,
            "target_polycount": int(sys.argv[3]) if len(sys.argv) > 3 else 6000,
        }
        print("task:", call("POST", "/openapi/v2/text-to-3d", body))
    elif cmd == "refine":
        body = {
            "mode": "refine",
            "preview_task_id": sys.argv[2],
            "texture_prompt": sys.argv[3],
            "enable_pbr": False,
            "texture_resolution": "2k",
        }
        print("task:", call("POST", "/openapi/v2/text-to-3d", body))
    elif cmd == "wait":
        tid = sys.argv[2]
        while True:
            t = call("GET", "/openapi/v2/text-to-3d/" + tid)
            print("status:", t.get("status"), "progress:", t.get("progress"), flush=True)
            if t.get("status") in ("SUCCEEDED", "FAILED", "CANCELED"):
                print("consumed_credits:", t.get("consumed_credits"))
                print("formats:", list((t.get("model_urls") or {}).keys()))
                if t.get("task_error"):
                    print("error:", t.get("task_error"))
                break
            time.sleep(8)
    elif cmd == "download":
        t = call("GET", "/openapi/v2/text-to-3d/" + sys.argv[2])
        url = t["model_urls"]["glb"]
        urllib.request.urlretrieve(url, sys.argv[3])
        print("saved", sys.argv[3], os.path.getsize(sys.argv[3]), "bytes")


if __name__ == "__main__":
    main()
