"""Effetti sugli sprite delle navi: riempimento delle vele, vele chiuse, schiuma e scia.

Libreria usata da build_ships.py, che assembla gli sprite finali in demo/assets/ships_clean.
"""

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "demo/assets/ships2"
OUT = ROOT / "demo/assets/ships_clean"

# Solo sprite interi con la prua in basso a destra (gli altri sono tagliati o invertiti).
SHIPS = ["barque", "cutter_war", "ketch", "lougre_grande", "nave_della_neve", "peschereccio",
         "pink", "sloop", "sloop_guerra_grande", "small_brig", "spritsail_barge"]

DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
FILL_RAY = 12      # distanza massima per cercare il bordo opaco
FILL_MIN_DIRS = 6  # direzioni (su 8) che devono trovare un pixel opaco per riempire un buco


def is_cream(r, g, b):
    return (r + g + b) / 3 > 140 and r - b > 15 and r >= g >= b - 10


def fill_holes(img):
    """Riempie i buchi di trasparenza interni alle vele (sono racchiusi da pixel opachi in quasi tutte le direzioni)."""
    w, h = img.size
    px = img.load()
    opaque = [[px[x, y][3] > 128 for x in range(w)] for y in range(h)]
    new = []
    for y in range(h):
        for x in range(w):
            if opaque[y][x]:
                continue
            hits = 0
            for dx, dy in DIRS:
                for step in range(1, FILL_RAY + 1):
                    xx, yy = x + dx * step, y + dy * step
                    if not (0 <= xx < w and 0 <= yy < h):
                        break
                    if opaque[yy][xx]:
                        hits += 1
                        break
            if hits >= FILL_MIN_DIRS:
                new.append((x, y))
    for x, y in new:
        # Si riempie solo dentro le vele: colore medio dei pixel crema vicini.
        pool = []
        for yy in range(max(0, y - 6), min(h, y + 7)):
            for xx in range(max(0, x - 6), min(w, x + 7)):
                if opaque[yy][xx] and is_cream(*px[xx, yy][:3]):
                    pool.append(px[xx, yy][:3])
        if len(pool) < 6:
            continue
        n = len(pool)
        px[x, y] = (sum(p[0] for p in pool) // n, sum(p[1] for p in pool) // n, sum(p[2] for p in pool) // n, 255)
    return img


def soften_edges(img):
    """Bordo con trasparenza graduata: i colori si propagano di 2px oltre il bordo per evitare aloni scuri."""
    w, h = img.size
    px = img.load()
    for _ in range(2):
        grow = []
        for y in range(h):
            for x in range(w):
                if px[x, y][3] > 0:
                    continue
                acc = [px[xx, yy] for xx in range(max(0, x - 1), min(w, x + 2))
                       for yy in range(max(0, y - 1), min(h, y + 2)) if px[xx, yy][3] > 0]
                if acc:
                    n = len(acc)
                    grow.append((x, y, (sum(p[0] for p in acc) // n, sum(p[1] for p in acc) // n, sum(p[2] for p in acc) // n)))
        for x, y, c in grow:
            px[x, y] = (*c, 1)
    alpha = img.getchannel("A").point(lambda v: 255 if v > 1 else 0).filter(ImageFilter.GaussianBlur(0.7))
    img.putalpha(alpha.point(lambda v: min(255, int(v * 1.5))))
    return img


def furl_sails(img):
    """Chiude le vele: ogni vela (componente crema) si riduce a un rotolo lungo il suo bordo superiore."""
    w, h = img.size
    px = img.load()
    cream = [[px[x, y][3] > 128 and is_cream(*px[x, y][:3]) for x in range(w)] for y in range(h)]
    seen = [[False] * w for _ in range(h)]
    out = img.copy()
    opx = out.load()
    for sy in range(h):
        for sx in range(w):
            if not cream[sy][sx] or seen[sy][sx]:
                continue
            stack, comp = [(sx, sy)], []
            seen[sy][sx] = True
            while stack:
                x, y = stack.pop()
                comp.append((x, y))
                for dx, dy in DIRS[:4]:
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < w and 0 <= yy < h and cream[yy][xx] and not seen[yy][xx]:
                        seen[yy][xx] = True
                        stack.append((xx, yy))
            if len(comp) < 120:
                continue
            cols = {}
            for x, y in comp:
                cols.setdefault(x, []).append(y)
                opx[x, y] = (0, 0, 0, 0)
            xs = sorted(cols)
            for x in xs:
                ys = cols[x]
                top, n = min(ys), len(ys)
                thick = max(3, int(n * 0.16))
                tie = ((x - xs[0]) // 9) % 4 == 3
                base = px[x, top][:3]
                for k in range(thick):
                    t = k / max(1, thick - 1)
                    shade = 1.08 - 0.42 * t - (0.18 if tie else 0)
                    c = tuple(max(0, min(255, int(v * shade))) for v in base)
                    if top + k < h:
                        opx[x, top + k] = (*c, 255)
    return out


def hull_bottom(img):
    """Contorno inferiore dello scafo: per ogni colonna, il pixel opaco più basso (con almeno 3 pixel contigui)."""
    w, h = img.size
    px = img.load()
    bottom = {}
    for x in range(w):
        for y in range(h - 1, 2, -1):
            if px[x, y][3] > 128 and px[x, y - 1][3] > 128 and px[x, y - 2][3] > 128:
                bottom[x] = y
                break
    return bottom


def span(bottom):
    return max(bottom) - min(bottom)


def foam_layer(size, bottom, moving, rng, k):
    """Schiuma attorno allo scafo, più scia a poppa e onda di prua se la nave è in movimento. `k` scala gli effetti."""
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    xs = sorted(bottom)
    x0, x1 = xs[0], xs[-1]
    n = len(xs)
    # pendenza media della chiglia: la scia prosegue lungo l'asse della nave
    slope = (bottom[x1] - bottom[x0]) / max(1, x1 - x0)

    def blob(cx, cy, rx, ry, alpha):
        d.ellipse((cx - rx * k, cy - ry * k, cx + rx * k, cy + ry * k), fill=(255, 255, 255, max(0, min(255, alpha))))

    ring = 150 if moving else 70
    for x in xs[:: max(1, int(k))]:
        yb = bottom[x]
        edge = min(x - x0, x1 - x) / max(1, n / 6)
        for _ in range(2):
            blob(x + rng.uniform(-1, 1) * k, yb + rng.uniform(-1, 4) * k, rng.uniform(2, 4.5), rng.uniform(1.5, 3), int(ring * min(1, 0.35 + edge) * rng.uniform(0.6, 1)))
    if moving:
        length = 56 * k
        i = 0.0
        while i < length:
            f = i / length
            spread = (3 + 11 * f) * k
            for _ in range(3):
                blob(x0 - i + rng.uniform(-2, 2) * k, bottom[x0] - i * slope + rng.uniform(-spread, spread) * 0.8 + 3 * k, rng.uniform(1.5, 3.5), rng.uniform(1, 2.2), int(140 * (1 - f) ** 1.3 * rng.uniform(0.5, 1)))
            i += 2 * k
        length = 22 * k
        i = 0.0
        while i < length:
            f = i / length
            for _ in range(3):
                blob(x1 + i * 0.8 + rng.uniform(-2, 2) * k, bottom[x1] - i * 0.35 + rng.uniform(-3, 5) * k, rng.uniform(2, 4), rng.uniform(1.5, 3), int(190 * (1 - f) * rng.uniform(0.6, 1)))
            i += 2 * k
    return layer.filter(ImageFilter.GaussianBlur(0.6 * k))


def compose(ship, bottom, moving, seed):
    """Nave con schiuma su un'immagine con margini trasparenti.

    Il perno (punto di ancoraggio in mappa) è a metà dello scafo, sulla linea di galleggiamento, e cade al centro
    orizzontale dell'immagine. Restituisce (immagine, meta) con meta = {span, oy, top}: larghezza dello scafo in px,
    ordinata del perno (0..1) e distanza in px dal perno alla cima dello sprite.
    """
    w, h = ship.size
    x0, x1 = min(bottom), max(bottom)
    sp = x1 - x0
    k = sp / 140
    pivx = (x0 + x1) / 2
    pivy = bottom[min(bottom, key=lambda x: abs(x - pivx))] - 0.07 * sp
    pad_x, pad_top, pad_bottom = round(0.4 * sp), round(0.05 * sp), round(0.12 * sp)
    half = max(pivx, w - pivx) + pad_x
    W, H = round(2 * half), h + pad_top + pad_bottom
    dx = round(half - pivx)
    rng = random.Random(seed)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shifted = {x + dx: y + pad_top for x, y in bottom.items()}
    canvas.alpha_composite(foam_layer((W, H), shifted, moving, rng, k))
    canvas.alpha_composite(ship, (dx, pad_top))
    # sottile riga di schiuma davanti alla linea di galleggiamento
    front = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(front)
    for x, y in shifted.items():
        fd.line((x, y - k, x, y), fill=(255, 255, 255, 120 if moving else 60), width=max(1, round(k)))
    canvas.alpha_composite(front.filter(ImageFilter.GaussianBlur(0.5 * k)))
    meta = {"span": sp, "oy": round((pad_top + pivy) / H, 4), "top": round(pad_top + pivy, 1)}
    return canvas, meta


def load_procedural():
    """Per ogni nave in SHIPS: sprite con vele spiegate, con vele chiuse e contorno dello scafo."""
    out = {}
    for name in SHIPS:
        base = Image.open(SRC / f"{name}.png").convert("RGBA")
        sail = soften_edges(fill_holes(base.copy()))
        furled = soften_edges(furl_sails(fill_holes(base.copy())))
        out[name] = {"sail": sail, "furled": furled, "bottom": hull_bottom(sail)}
    return out
