"""
ATELIER · art.py
Genera ilustraciones SVG demo con la paleta de Atelier.

Sirven como imagen de reemplazo mientras no existan fotografías reales.
Son deterministas: la misma "semilla" siempre produce la misma imagen.

Para usar fotos reales no toques este archivo: pon la ruta en el campo
"image" del JSON correspondiente (ver /static/images/LEEME.txt).
"""
import math
import random
import zlib

# --- Paleta (mismos tonos desaturados del CSS) -------------------------------
P = {
    "noche": "#2F3E56", "azul": "#46607E", "azul_gris": "#8FA4B5", "azul_cl": "#D7E0E8",
    "verde": "#6E8C7E", "verde_cl": "#C9D6CD", "mauve": "#B98CA0", "rosa": "#EBD9E0",
    "lav": "#9C97C4", "lav_cl": "#DEDBEE", "beige": "#DCCDB8", "crema": "#F4EEE4",
    "tierra": "#B39C82", "tierra_osc": "#8A735E", "gris": "#CFC8C1",
}

# (fondo A, fondo B, acento 1, acento 2, acento 3, acento 4)
PALETTES = {
    "musica": [
        ("azul_cl", "lav_cl", "azul", "noche", "mauve", "crema"),
        ("noche", "azul", "azul_gris", "lav", "rosa", "crema"),
        ("lav_cl", "azul_cl", "lav", "azul", "rosa", "noche"),
    ],
    "arte-visual": [
        ("rosa", "crema", "mauve", "lav", "azul_gris", "tierra"),
        ("crema", "rosa", "mauve", "azul", "lav_cl", "verde_cl"),
        ("lav_cl", "rosa", "lav", "mauve", "azul_gris", "beige"),
    ],
    "graffiti": [
        ("verde_cl", "azul_cl", "verde", "noche", "mauve", "crema"),
        ("azul_cl", "verde_cl", "azul", "verde", "rosa", "noche"),
        ("beige", "verde_cl", "verde", "tierra_osc", "lav", "crema"),
    ],
    "artes-plasticas": [
        ("beige", "crema", "tierra", "tierra_osc", "mauve", "azul_gris"),
        ("crema", "azul_cl", "tierra", "azul", "rosa", "tierra_osc"),
        ("beige", "rosa", "tierra_osc", "lav", "verde_cl", "crema"),
    ],
    "espacio": [
        ("crema", "beige", "azul_gris", "verde", "tierra", "rosa"),
        ("azul_cl", "crema", "azul", "verde_cl", "mauve", "beige"),
        ("rosa", "beige", "lav", "azul_gris", "verde", "crema"),
    ],
}
KINDS = ["musica", "arte-visual", "graffiti", "artes-plasticas", "espacio"]


# --- Utilidades --------------------------------------------------------------
def _blob(rng, cx, cy, r, n=7, jitter=0.32):
    """Path de una forma orgánica suave alrededor de (cx, cy)."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n + rng.uniform(-0.2, 0.2)
        rr = r * (1 + rng.uniform(-jitter, jitter))
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    mids = [((pts[i][0] + pts[(i + 1) % n][0]) / 2, (pts[i][1] + pts[(i + 1) % n][1]) / 2) for i in range(n)]
    d = f"M{mids[-1][0]:.1f},{mids[-1][1]:.1f}"
    for i in range(n):
        d += f" Q{pts[i][0]:.1f},{pts[i][1]:.1f} {mids[i][0]:.1f},{mids[i][1]:.1f}"
    return d + "Z"


def _arch(x, y, w, h):
    """Arco (puerta/ventana) con base plana."""
    r = w / 2
    return f"M{x},{y + h} V{y + r} A{r},{r} 0 0 1 {x + w},{y + r} V{y + h} Z"


# --- Motivos por disciplina --------------------------------------------------
def _musica(rng, c):
    out = []
    cx, cy = rng.uniform(360, 640), rng.uniform(400, 560)
    R = rng.uniform(150, 210)
    out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{R:.0f}" fill="url(#rad)"/>')
    for i in range(1, 6):
        out.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{R + i * 52:.0f}" fill="none" '
                   f'stroke="{c[3]}" stroke-width="{3 if i % 2 else 1.5}" opacity="{0.55 - i * 0.08:.2f}"/>')
    out.append(f'<circle cx="{cx + rng.uniform(-260, 260):.0f}" cy="{cy + rng.uniform(-200, 220):.0f}" '
               f'r="{rng.uniform(40, 80):.0f}" fill="{c[4]}" opacity=".85"/>')
    x = 90
    while x < 920:
        h = rng.uniform(50, 260)
        out.append(f'<line x1="{x}" y1="930" x2="{x}" y2="{930 - h:.0f}" stroke="{c[5] if rng.random() < .3 else c[3]}" '
                   f'stroke-width="16" stroke-linecap="round" opacity=".5"/>')
        x += 40
    return "".join(out)


def _arte_visual(rng, c):
    out = []
    for _ in range(6):
        col = rng.choice([c[2], c[3], c[4], c[5]])
        out.append(f'<path d="{_blob(rng, rng.uniform(200, 800), rng.uniform(250, 750), rng.uniform(110, 260))}" '
                   f'fill="{col}" opacity="{rng.uniform(.55, .85):.2f}" style="mix-blend-mode:multiply"/>')
    for _ in range(3):
        x1, y1 = rng.uniform(80, 400), rng.uniform(200, 800)
        x2, y2 = rng.uniform(600, 930), rng.uniform(200, 800)
        out.append(f'<path d="M{x1:.0f},{y1:.0f} C{rng.uniform(200, 500):.0f},{rng.uniform(100, 900):.0f} '
                   f'{rng.uniform(500, 800):.0f},{rng.uniform(100, 900):.0f} {x2:.0f},{y2:.0f}" fill="none" '
                   f'stroke="{rng.choice([c[2], c[3], c[5]])}" stroke-width="{rng.uniform(22, 56):.0f}" '
                   f'stroke-linecap="round" opacity=".55"/>')
    out.append(f'<circle cx="{rng.uniform(300, 700):.0f}" cy="{rng.uniform(300, 700):.0f}" r="{rng.uniform(90, 150):.0f}" '
               f'fill="none" stroke="{P["crema"]}" stroke-width="3" opacity=".8"/>')
    return "".join(out)


def _graffiti(rng, c):
    out = [f'<rect y="820" width="1000" height="180" fill="{c[3]}" opacity=".16"/>']
    # trama de puntos (halftone)
    x0, y0 = rng.uniform(560, 700), rng.uniform(120, 260)
    for i in range(9):
        for j in range(9):
            r = max(1.5, 11 - (i + j) * 0.6)
            out.append(f'<circle cx="{x0 + i * 26:.0f}" cy="{y0 + j * 26:.0f}" r="{r:.1f}" fill="{c[2]}" opacity=".45"/>')
    out.append(f'<circle cx="{rng.uniform(250, 450):.0f}" cy="{rng.uniform(380, 520):.0f}" r="230" '
               f'fill="{c[4]}" opacity=".35" filter="url(#soft)"/>')
    # letras abstractas: trazo grueso con contorno
    for k in range(4):
        x = 130 + k * 200 + rng.uniform(-20, 20)
        y = rng.uniform(430, 560)
        d = (f"M{x:.0f},{y + 190:.0f} C{x - 60:.0f},{y - 40:.0f} {x + 120:.0f},{y - 90:.0f} {x + 110:.0f},{y + 60:.0f} "
             f"S{x + 20:.0f},{y + 170:.0f} {x + 150:.0f},{y + 190:.0f}")
        out.append(f'<path d="{d}" fill="none" stroke="{c[3]}" stroke-width="96" stroke-linecap="round" opacity=".9"/>')
        col = [c[2], c[4], c[5], c[2]][k]
        out.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="66" stroke-linecap="round"/>')
        # goteo
        gx = x + rng.uniform(20, 120)
        gl = rng.uniform(50, 160)
        out.append(f'<rect x="{gx:.0f}" y="{y + 190:.0f}" width="12" height="{gl:.0f}" rx="6" fill="{col}"/>')
        out.append(f'<circle cx="{gx + 6:.0f}" cy="{y + 190 + gl + 6:.0f}" r="10" fill="{col}"/>')
    return "".join(out)


def _artes_plasticas(rng, c):
    out = [f'<rect y="700" width="1000" height="300" fill="{c[1]}" opacity=".9"/>',
           f'<ellipse cx="500" cy="720" rx="420" ry="34" fill="{c[3]}" opacity=".16"/>']
    # arcos
    x = rng.uniform(120, 200)
    for i in range(3):
        w, h = rng.uniform(150, 210), rng.uniform(260, 420)
        col = [c[2], c[4], c[5]][i]
        out.append(f'<path d="{_arch(x, 715 - h, w, h)}" fill="{col}" opacity=".92"/>')
        out.append(f'<path d="{_arch(x + w * .22, 715 - h * .62, w * .56, h * .62)}" fill="{c[0]}" opacity=".55"/>')
        x += w + rng.uniform(30, 80)
    # esfera con volumen
    sx, sy, sr = rng.uniform(600, 780), rng.uniform(300, 400), rng.uniform(90, 140)
    out.append(f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="{sr:.0f}" fill="url(#sph)"/>')
    out.append(f'<ellipse cx="{sx:.0f}" cy="{sy + sr + 30:.0f}" rx="{sr * .9:.0f}" ry="12" fill="{c[3]}" opacity=".18"/>')
    # cilindro
    cx_, cw, ch = rng.uniform(130, 300), 110, rng.uniform(150, 230)
    out.append(f'<rect x="{cx_:.0f}" y="{715 - ch:.0f}" width="{cw}" height="{ch:.0f}" fill="{c[3]}" opacity=".85"/>')
    out.append(f'<ellipse cx="{cx_ + cw / 2:.0f}" cy="{715 - ch:.0f}" rx="{cw / 2}" ry="18" fill="{c[5]}" opacity=".9"/>')
    return "".join(out)


def _espacio(rng, c):
    out = [f'<rect y="760" width="1000" height="240" fill="{c[4]}" opacity=".28"/>']
    n = rng.choice([3, 4])
    w = 190
    gap = (1000 - n * w) / (n + 1)
    for i in range(n):
        x = gap + i * (w + gap)
        h = rng.uniform(380, 520)
        out.append(f'<path d="{_arch(x, 770 - h, w, h)}" fill="{c[2]}" opacity=".28"/>')
        out.append(f'<path d="{_arch(x + 16, 770 - h + 16, w - 32, h - 16)}" fill="url(#luz)"/>')
    # lámparas colgantes
    for _ in range(3):
        lx, ll = rng.uniform(150, 850), rng.uniform(120, 260)
        out.append(f'<line x1="{lx:.0f}" y1="0" x2="{lx:.0f}" y2="{ll:.0f}" stroke="{c[3]}" stroke-width="3" opacity=".6"/>')
        out.append(f'<path d="M{lx - 44:.0f},{ll + 40:.0f} A44,44 0 0 1 {lx + 44:.0f},{ll + 40:.0f}Z" fill="{c[4]}"/>')
    # hojas
    px = rng.uniform(80, 200)
    for k in range(5):
        a = -60 + k * 30
        out.append(f'<ellipse cx="{px + 30 * math.sin(math.radians(a)):.0f}" cy="{770 - 60:.0f}" rx="22" ry="{80 + k % 3 * 20}" '
                   f'fill="{c[3]}" opacity=".85" transform="rotate({a} {px:.0f} 770)"/>')
    return "".join(out)


_MOTIFS = {"musica": _musica, "arte-visual": _arte_visual, "graffiti": _graffiti,
           "artes-plasticas": _artes_plasticas, "espacio": _espacio}


# --- API pública -------------------------------------------------------------
def render(kind: str, seed: str) -> str:
    """Devuelve el SVG (texto) de una ilustración para `kind` y `seed`."""
    rng = random.Random(zlib.crc32(f"{kind}:{seed}".encode()))
    motif = kind if kind in _MOTIFS else rng.choice(KINDS)
    names = rng.choice(PALETTES[motif])
    c = [P[n] for n in names]

    defs = (
        f'<linearGradient id="bg" x1="0" y1="0" x2=".8" y2="1"><stop offset="0" stop-color="{c[0]}"/>'
        f'<stop offset="1" stop-color="{c[1]}"/></linearGradient>'
        f'<radialGradient id="rad" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="{c[4]}"/>'
        f'<stop offset="1" stop-color="{c[2]}"/></radialGradient>'
        f'<radialGradient id="sph" cx=".35" cy=".3" r=".85"><stop offset="0" stop-color="{c[5]}"/>'
        f'<stop offset=".6" stop-color="{c[4]}"/><stop offset="1" stop-color="{c[3]}"/></radialGradient>'
        f'<linearGradient id="luz" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c[5]}" stop-opacity=".95"/>'
        f'<stop offset="1" stop-color="{c[1]}" stop-opacity=".6"/></linearGradient>'
        '<filter id="soft"><feGaussianBlur stdDeviation="40"/></filter>'
        '<filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" '
        'baseFrequency=".85" numOctaves="1" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 .18 0 0 0 0 .2 0 0 0 0 .26 0 0 0 .55 0"/></filter>'
    )
    body = _MOTIFS[motif](rng, c)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000" preserveAspectRatio="xMidYMid slice">'
        f"<defs>{defs}</defs>"
        '<rect width="1000" height="1000" fill="url(#bg)"/>'
        f"{body}"
        '<rect width="1000" height="1000" filter="url(#grain)" opacity=".28"/>'
        "</svg>"
    )
