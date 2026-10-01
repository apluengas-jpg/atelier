"""
ATELIER · beta funcional
El arte también tiene un mapa.

Ejecutar:   python app.py
Abrir en:   http://127.0.0.1:5000
"""
from collections import defaultdict
from math import cos, sin, pi
import os

from flask import Flask, Response, abort, jsonify, render_template, request, url_for

import art
import content
import db

app = Flask(__name__)
app.json.ensure_ascii = False          # respeta acentos en las respuestas JSON
app.config["TEMPLATES_AUTO_RELOAD"] = True
db.init_db()

# Interruptor de la barra "Beta · contenido demo". Ponlo en False para ocultarla.
SHOW_DEMO_BAR = True


# ------------------------------------------------------------------ Plantillas
@app.template_global()
def img(image, kind, seed):
    """URL de imagen: foto real si existe en el JSON; si no, ilustración demo generada."""
    if image:
        if image.startswith(("http://", "https://", "/")):
            return image
        return url_for("static", filename=image)
    return url_for("arte", kind=kind, seed=seed)


app.add_template_filter(content.fecha_corta, "fecha_corta")
app.add_template_filter(content.fecha_larga, "fecha_larga")
app.add_template_filter(content.mes_label, "mes_label")
app.add_template_filter(content.norm, "norm")


@app.template_filter("hora")
def hora(t):
    return f"{t} h"


@app.context_processor
def globals_for_templates():
    site = content.site()
    cats = content.categories()
    return {
        "site": site,
        "categories": cats,
        "disciplines": content.DISCIPLINES,
        "show_demo_bar": SHOW_DEMO_BAR,
        # Datos que necesita el JavaScript (modal de colaboración, colores del mapa)
        "boot": {
            "categories": cats,
            "artists": [{"slug": a["slug"], "name": a["name"]} for a in content.artists()],
            "spaces": [{"slug": s["slug"], "name": s["name"]} for s in content.spaces()],
            "spaceTypes": site["space_types"],
            "collabTypes": site["collab_types"],
            "disciplines": [cats[k]["label"] for k in content.DISCIPLINES],
        },
    }


# ---------------------------------------------------------------------- Páginas
@app.route("/")
def home():
    evs = content.events()
    artists, spaces = content.artists(), content.spaces()
    featured = [e for e in evs if e.get("featured")][:3] or evs[:3]
    feat_artists = [a for a in artists if a.get("featured")][:4] or artists[:4]
    feat_spaces = [s for s in spaces if s.get("featured")][:3] or spaces[:3]
    return render_template(
        "home.html", section="inicio", featured=featured,
        upcoming=content.upcoming(evs)[:6], artists=feat_artists, spaces=feat_spaces,
        hero_event=featured[0], hero_artist=feat_artists[0], hero_space=feat_spaces[0],
    )


@app.route("/mapa")
def mapa():
    evs = content.events()
    ms = content.months(evs)
    current = content.upcoming(evs)[0]["month"] if evs else (ms[0] if ms else "")
    return render_template("mapa.html", section="mapa", months=ms, current_month=current)


@app.route("/eventos")
def eventos():
    return render_template("eventos.html", section="inicio", events=content.events())


@app.route("/evento/<slug>")
def evento(slug):
    evs = content.events()
    e = content.by_slug(evs, slug) or abort(404)
    more = [x for x in content.upcoming(evs) if x["slug"] != slug][:3]
    return render_template("evento.html", section="inicio", e=e, more=more)


@app.route("/artistas")
def artistas():
    return render_template("artistas.html", section="artistas", artists=content.artists())


@app.route("/artista/<slug>")
def artista(slug):
    a = content.by_slug(content.artists(), slug) or abort(404)
    evs = [e for e in content.events() if e["artist"] == slug]
    return render_template("artista.html", section="artistas", a=a, events=evs)


@app.route("/espacios")
def espacios():
    return render_template("espacios.html", section="espacios", spaces=content.spaces())


@app.route("/espacio/<slug>")
def espacio(slug):
    s = content.by_slug(content.spaces(), slug) or abort(404)
    evs = [e for e in content.events() if e["space"] == slug]
    return render_template("espacio.html", section="espacios", s=s, events=evs)


@app.route("/atelier")
def atelier():
    return render_template("atelier.html", section="atelier", artists=content.artists()[:4])


@app.route("/buscar")
def buscar():
    q = request.args.get("q", "").strip()
    return render_template("buscar.html", section="inicio", q=q, results=content.search(q, limit=30))


@app.route("/solicitudes")
def solicitudes():
    """Vista interna de la beta: muestra las propuestas enviadas desde los formularios demo."""
    return render_template("solicitudes.html", section="atelier", items=db.all_requests())


@app.route("/comentarios")
def comentarios():
    """Vista interna de la beta: opiniones dejadas por quien navega el sitio."""
    avg, n = db.feedback_average()
    return render_template("comentarios.html", section="atelier", items=db.all_feedback(), avg=avg, n=n)


@app.errorhandler(404)
def not_found(_):
    return render_template("404.html", section="inicio"), 404


# -------------------------------------------------------------------------- API
def _point_from_event(e):
    return {"id": f"event:{e['slug']}", "kind": "event", "slug": e["slug"], "name": e["title"],
            "category": e["category"], "category_label": e["category_info"]["label"],
            "color": e["category_info"]["color"], "sub": e["format"],
            "date": e["date"], "date_label": content.fecha_larga(e["date"]), "time": e["time"], "month": e["month"],
            "place": f"{e['space_obj']['name']}, {e['space_obj']['address']}",
            "lat": e["lat"], "lng": e["lng"],
            "image": img(e.get("image"), e["category"], e["slug"]),
            "url": url_for("evento", slug=e["slug"])}


def _point_from_space(s):
    return {"id": f"space:{s['slug']}", "kind": "space", "slug": s["slug"], "name": s["name"],
            "category": "espacios", "category_label": s["type"], "color": s["category_info"]["color"],
            "sub": s["type"], "date": None, "date_label": None, "time": None, "month": None,
            "place": s["address"], "lat": s["lat"], "lng": s["lng"],
            "image": img(s.get("image"), "espacio", s["slug"]),
            "url": url_for("espacio", slug=s["slug"])}


@app.get("/api/puntos")
def api_puntos():
    """Puntos del mapa (eventos + espacios). ?only=event:slug o ?only=space:slug para uno solo."""
    pts = [_point_from_space(s) for s in content.spaces()] + [_point_from_event(e) for e in content.events()]
    only = request.args.get("only")
    if only:
        pts = [p for p in pts if p["id"] == only]

    # Si varios puntos comparten coordenadas, se separan un poco para que ninguno quede tapado.
    groups = defaultdict(list)
    for p in pts:
        groups[(round(p["lat"], 5), round(p["lng"], 5))].append(p)
    for group in groups.values():
        if len(group) > 1:
            for i, p in enumerate(group):
                ang = 2 * pi * i / len(group)
                p["lat"] += 0.00032 * sin(ang)
                p["lng"] += 0.00032 * cos(ang)
    return jsonify(pts)


@app.get("/api/eventos")
def api_eventos():
    """Eventos por slug (los usa el panel 'Guardados'). ?slugs=a,b,c"""
    wanted = [s for s in request.args.get("slugs", "").split(",") if s]
    out = []
    for e in content.events():
        if e["slug"] in wanted:
            out.append({"slug": e["slug"], "title": e["title"], "category": e["category_info"]["label"],
                        "color": e["category_info"]["color"], "date": content.fecha_corta(e["date"]),
                        "time": e["time"], "place": e["space_obj"]["name"],
                        "image": img(e.get("image"), e["category"], e["slug"]),
                        "url": url_for("evento", slug=e["slug"])})
    return jsonify(out)


@app.get("/api/buscar")
def api_buscar():
    r = content.search(request.args.get("q", ""), limit=5)
    return jsonify({
        "events": [{"name": e["title"], "sub": f"{content.fecha_corta(e['date'])}, {e['space_obj']['name']}",
                    "url": url_for("evento", slug=e["slug"]), "image": img(e.get("image"), e["category"], e["slug"])}
                   for e in r["events"]],
        "artists": [{"name": a["name"], "sub": f"{a['discipline']}, {a['style']}",
                     "url": url_for("artista", slug=a["slug"]), "image": img(a.get("image"), a["category"], a["slug"])}
                    for a in r["artists"]],
        "spaces": [{"name": s["name"], "sub": f"{s['type']}, {s['address']}",
                    "url": url_for("espacio", slug=s["slug"]), "image": img(s.get("image"), "espacio", s["slug"])}
                   for s in r["spaces"]],
    })


@app.post("/api/solicitudes")
def api_solicitudes():
    """Guarda una propuesta o registro enviado desde el modal de colaboración."""
    d = request.get_json(silent=True) or {}
    nombre, contacto = str(d.get("nombre", "")).strip(), str(d.get("contacto", "")).strip()
    if len(nombre) < 2 or len(contacto) < 3:
        return jsonify({"ok": False, "error": "Faltan tu nombre y una forma de contactarte."}), 400
    db.add_request(
        modo=str(d.get("modo", ""))[:30], nombre=nombre[:120], contacto=contacto[:160],
        rol=str(d.get("rol", ""))[:80], destino=str(d.get("destino", ""))[:160], mensaje=str(d.get("mensaje", ""))[:2000],
    )
    return jsonify({"ok": True})


@app.post("/api/comentarios")
def api_comentarios():
    """Guarda una opinión enviada desde el botón flotante 'Tu opinión'."""
    d = request.get_json(silent=True) or {}
    try:
        cal = int(d.get("calificacion", 0))
    except (TypeError, ValueError):
        cal = 0
    mensaje = str(d.get("mensaje", "")).strip()
    if cal < 1 or cal > 5:
        return jsonify({"ok": False, "error": "Elige una calificación de 1 a 5 estrellas."}), 400
    if len(mensaje) < 3:
        return jsonify({"ok": False, "error": "Cuéntanos un poco más en tu comentario."}), 400
    db.add_feedback(calificacion=cal, mensaje=mensaje[:2000], pagina=str(d.get("pagina", ""))[:200],
                     nombre=str(d.get("nombre", "")).strip()[:120])
    return jsonify({"ok": True})


@app.route("/arte/<kind>/<seed>.svg")
def arte(kind, seed):
    """Ilustración demo generada (ver art.py)."""
    return Response(art.render(kind, seed), mimetype="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=86400"})


if __name__ == "__main__":
    # host="0.0.0.0" permite abrir la beta desde otros dispositivos de la misma red
    # (celular, tablet, otra computadora) usando la IP local de esta máquina.
    # PORT lo define automáticamente el servicio de hosting (Render, Railway, etc.);
    # en tu computadora, si no existe esa variable, usa 5000 como antes.
    # Ver el manual, sección "Compartir la beta en otros dispositivos".
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
