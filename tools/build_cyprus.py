#!/usr/bin/env python3
"""Собирает данные для cyprus/: маршруты по дорогам и фото с атрибуцией.

  python3 tools/build_cyprus.py            # всё
  python3 tools/build_cyprus.py --routes   # только маршруты
  python3 tools/build_cyprus.py --photos   # только фото (уже скачанные пропускаются)

Пишет:
  cyprus/routes.js  — window.ROUTES[i] = {km, min, path:[[lat,lon],...]} для дня i+1
  cyprus/photos.js  — window.PHOTOS[name] = {src, author, license, url}
  cyprus/img/w/*.webp

Источники: OSRM (router.project-osrm.org), Wikipedia/Wikimedia Commons API.
Нужны: node, Pillow.
"""
import html, io, json, re, subprocess, sys, time, unicodedata, urllib.parse, urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent / "cyprus"
HOME = (34.6786, 33.0413)  # Лимассол — база
UA = {"User-Agent": "cyprus-guide-builder/1.0 (https://github.com/vmaiorov-collab/vmaiorov-collab.github.io)"}
WIDTH = 1200


def get(url, tries=8):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return r.read()
        except Exception as e:
            print(f"  retry {i + 1}: {e}", file=sys.stderr)
            time.sleep(5 * (i + 1))
    raise RuntimeError("failed: " + url)


def api(base, **q):
    if "wiki" in base:
        q.setdefault("format", "json")
    return json.loads(get(base + "?" + urllib.parse.urlencode(q)))


def load_days():
    js = ('global.window={};for(const f of["data1.js","data2.js","data3.js"])'
          'eval(require("fs").readFileSync(process.argv[1]+"/"+f,"utf8"));'
          'console.log(JSON.stringify(window.DAYS))')
    return json.loads(subprocess.check_output(["node", "-e", js, str(ROOT)]))


# ---------------- маршруты ----------------
def simplify(pts, eps=0.0004):
    """Дуглас–Пекер, eps в градусах (~40 м)."""
    if len(pts) < 3:
        return pts
    if pts[0] == pts[-1] or (abs(pts[0][0] - pts[-1][0]) + abs(pts[0][1] - pts[-1][1])) < 1e-6:
        m = len(pts) // 2  # замкнутая петля: делим пополам
        return simplify(pts[:m + 1], eps)[:-1] + simplify(pts[m:], eps)
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    n = (dx * dx + dy * dy) ** 0.5 or 1e-12
    dmax, idx = 0, 0
    for i in range(1, len(pts) - 1):
        d = abs(dy * pts[i][0] - dx * pts[i][1] + x2 * y1 - y2 * x1) / n
        if d > dmax:
            dmax, idx = d, i
    if dmax > eps:
        return simplify(pts[:idx + 1], eps)[:-1] + simplify(pts[idx:], eps)
    return [pts[0], pts[-1]]


def build_routes(days):
    out = []
    for i, d in enumerate(days, 1):
        stops = [HOME] + [tuple(p["ll"]) for p in d["places"] if p.get("ll") and not p.get("nomap")] + [HOME]
        coords = ";".join(f"{lon},{lat}" for lat, lon in stops)
        j = api(f"https://router.project-osrm.org/route/v1/driving/{coords}", overview="full", geometries="geojson")
        if j.get("code") != "Ok":
            raise RuntimeError(f"OSRM day {i}: {j}")
        r = j["routes"][0]
        path = [[round(lat, 5), round(lon, 5)] for lon, lat in r["geometry"]["coordinates"]]
        path = simplify(path)
        out.append({"km": round(r["distance"] / 1000), "min": round(r["duration"] / 60), "path": path})
        print(f"day {i}: {out[-1]['km']} km, {out[-1]['min']} min, {len(path)} pts")
        time.sleep(1)
    (ROOT / "routes.js").write_text(
        "// Сгенерировано tools/build_cyprus.py — маршруты по дорогам (OSRM), Лимассол → места дня → Лимассол\n"
        "window.ROUTES=" + json.dumps(out, separators=(",", ":")) + ";\n", encoding="utf-8")


# ---------------- фото ----------------
CYR = dict(zip("абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
               "a b v g d e e zh z i y k l m n o p r s t u f kh ts ch sh sch _ y _ e yu ya".split()))


def slug(s):
    s = "".join(CYR.get(c, c) for c in s.lower())
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:60]


def strip_html(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def resolve_files(titles):
    """wiki-статья → File:… (главное фото статьи)."""
    res = {}
    for k in range(0, len(titles), 10):
        chunk = titles[k:k + 10]
        j = api("https://en.wikipedia.org/w/api.php", action="query", redirects=1, prop="pageimages",
                piprop="name", titles="|".join(chunk))["query"]
        alias = {x["from"]: x["to"] for x in j.get("normalized", []) + j.get("redirects", [])}
        by = {p["title"]: p.get("pageimage") for p in j["pages"].values()}
        for t in chunk:
            key = t
            for _ in range(3):
                key = alias.get(key, key)
            if by.get(key):
                res[t] = "File:" + by[key]
        time.sleep(1)
    return res


def build_photos(days):
    out_dir = ROOT / "img" / "w"
    out_dir.mkdir(parents=True, exist_ok=True)
    places = [p for d in days for p in d["places"] if not p.get("local") and (p.get("photo") or p.get("wiki"))]
    files = resolve_files(sorted({p["wiki"] for p in places if p.get("wiki") and not p.get("photo")}))
    photos = {}
    old = {}
    pj = ROOT / "photos.js"
    if pj.exists():
        old = json.loads(pj.read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
    for p in places:
        f = p.get("photo") or files.get(p["wiki"])
        if not f:
            print("  no photo:", p["name"])
            continue
        name = slug(p["name"]) + ".webp"
        dst = out_dir / name
        if dst.exists() and p["name"] in old and old[p["name"]].get("file") == f:
            photos[p["name"]] = old[p["name"]]
            continue
        try:
            photos[p["name"]] = fetch_photo(f, dst, name)
        except RuntimeError as e:
            print("  FAILED (запустите ещё раз):", p["name"], e)
            continue
        save_photos(pj, photos)
        print(f"  {p['name']}: {dst.stat().st_size // 1024} KB · {photos[p['name']]['author']} · {photos[p['name']]['license']}")
        time.sleep(2)
    save_photos(pj, photos)


def fetch_photo(f, dst, name):
    info = api("https://commons.wikimedia.org/w/api.php", action="query", titles=f, prop="imageinfo",
               iiprop="url|extmetadata", iiurlwidth=WIDTH)
    page = next(iter(info["query"]["pages"].values()))
    if "imageinfo" not in page:
        raise RuntimeError("missing on commons: " + f)
    ii = page["imageinfo"][0]
    meta = ii.get("extmetadata", {})
    img = Image.open(io.BytesIO(get(ii.get("thumburl") or ii["url"]))).convert("RGB")
    if img.width > WIDTH:
        img = img.resize((WIDTH, round(img.height * WIDTH / img.width)), Image.LANCZOS)
    img.save(dst, "WEBP", quality=74, method=6)
    return {
        "src": f"img/w/{name}",
        "file": f,
        "url": ii["descriptionurl"],
        "author": strip_html(meta.get("Artist", {}).get("value"))[:80] or "неизвестен",
        "license": strip_html(meta.get("LicenseShortName", {}).get("value")) or "см. страницу файла",
    }

def save_photos(pj, photos):
    pj.write_text("// Сгенерировано tools/build_cyprus.py — фото с Wikimedia Commons\n"
                  "window.PHOTOS=" + json.dumps(photos, ensure_ascii=False, indent=0) + ";\n", encoding="utf-8")


if __name__ == "__main__":
    days = load_days()
    args = set(sys.argv[1:])
    if not args or "--routes" in args:
        build_routes(days)
    if not args or "--photos" in args:
        build_photos(days)
