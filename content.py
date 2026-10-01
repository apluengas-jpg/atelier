"""
ATELIER · content.py
Lee los datos de /data (JSON) y los enriquece para las plantillas.

Los JSON se vuelven a leer solos cuando cambian en disco, así que puedes
editar artistas, espacios o eventos con la app corriendo y refrescar el navegador.
"""
import json
import unicodedata
from datetime import date
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
_cache = {}

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

# Categorías que representan disciplinas (las otras dos, "eventos" y "espacios", son tipos de punto).
DISCIPLINES = ["musica", "arte-visual", "graffiti", "artes-plasticas"]


def _load(name):
    path = DATA_DIR / f"{name}.json"
    mtime = path.stat().st_mtime
    hit = _cache.get(name)
    if not hit or hit[0] != mtime:
        with open(path, encoding="utf-8") as f:
            hit = (mtime, json.load(f))
        _cache[name] = hit
    return hit[1]


# --- Texto -------------------------------------------------------------------
def norm(text):
    """Minúsculas y sin acentos, para búsquedas."""
    text = unicodedata.normalize("NFD", str(text or "").lower())
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


def fecha_corta(iso):
    d = date.fromisoformat(iso)
    return f"{DIAS[d.weekday()][:3]} {d.day} {MESES[d.month - 1][:3]}"


def fecha_larga(iso):
    d = date.fromisoformat(iso)
    return f"{DIAS[d.weekday()].capitalize()} {d.day} de {MESES[d.month - 1]}"


def mes_label(ym):
    y, m = ym.split("-")
    return f"{MESES[int(m) - 1].capitalize()} {y}"


# --- Datos -------------------------------------------------------------------
def site():
    return _load("atelier")


def categories():
    return _load("categories")


def artists():
    cats = categories()
    return [{**a, "category_info": cats[a["category"]]} for a in _load("artists")]


def spaces():
    cats = categories()
    return [{**s, "category": "espacios", "category_info": cats["espacios"]} for s in _load("spaces")]


def events():
    cats = categories()
    sp = {s["slug"]: s for s in spaces()}
    ar = {a["slug"]: a for a in artists()}
    out = []
    for e in _load("events"):
        s, a = sp[e["space"]], ar[e["artist"]]
        out.append({**e, "space_obj": s, "artist_obj": a, "lat": s["lat"], "lng": s["lng"],
                    "category_info": cats[e["category"]], "month": e["date"][:7]})
    return sorted(out, key=lambda e: (e["date"], e["time"]))


def by_slug(items, slug):
    return next((i for i in items if i["slug"] == slug), None)


def upcoming(evs, today=None):
    """Eventos de hoy en adelante. Si ya no hay ninguno (datos demo viejos), devuelve todos."""
    today = (today or date.today()).isoformat()
    fut = [e for e in evs if e["date"] >= today]
    return fut or evs


def months(evs):
    return sorted({e["month"] for e in evs})


# --- Búsqueda ----------------------------------------------------------------
def search(q, limit=6):
    q = norm(q).strip()
    if len(q) < 2:
        return {"events": [], "artists": [], "spaces": []}

    def hit(*fields):
        return q in norm(" ".join(str(f) for f in fields))

    return {
        "events": [e for e in events() if hit(e["title"], e["format"], e["category_info"]["label"], e["description"],
                                              e["artist_obj"]["name"], e["space_obj"]["name"])][:limit],
        "artists": [a for a in artists() if hit(a["name"], a["discipline"], a["style"], a["tagline"], a["bio"])][:limit],
        "spaces": [s for s in spaces() if hit(s["name"], s["type"], s["address"], s["description"],
                                              " ".join(s["collab_types"]))][:limit],
    }
