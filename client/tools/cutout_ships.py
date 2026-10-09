"""Ritaglia gli sprite in media/ (sfondo bianco, JPEG) in PNG trasparenti in demo/assets/ships_new.

Lo sfondo è il bianco quasi neutro collegato al bordo, più le "tasche" bianche molto estese
racchiuse tra le sartie. Le vele color crema non vengono toccate perché hanno una dominante calda.
"""
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
MEDIA = ROOT / "media"
OUT = ROOT / "demo/assets/ships_new"
OUT.mkdir(parents=True, exist_ok=True)

# file in media -> nome di destinazione (fishing = peschereccio a un albero, cutter = un albero con lungo bompresso, brig = due alberi)
FILES = {
    "Gemini_Generated_Image_4ag5ps4ag5ps4ag5.jpeg": "fishing_net_two",
    "Gemini_Generated_Image_4ag5ps4ag5ps4ag5 (1).jpeg": "fishing_net_empty",
    "Gemini_Generated_Image_4ag5ps4ag5ps4ag5 (2).jpeg": "fishing_net_fish",
    "Gemini_Generated_Image_mijjbpmijjbpmijj.jpeg": "cutter_furled",
    "Gemini_Generated_Image_mijjbpmijjbpmijj (1).jpeg": "brig_open",
    "Gemini_Generated_Image_mijjbpmijjbpmijj (2).jpeg": "brig_furled",
    "Gemini_Generated_Image_mijjbpmijjbpmijj (3).jpeg": "fishing_furled",
    "Gemini_Generated_Image_s99bfds99bfds99b.jpeg": "brig_net",
}

# Lo sfondo collegato al bordo include anche l'alone grigio chiaro attorno agli scafi (soglia più bassa);
# le tasche interne sono più caute per non toccare le vele chiare.
EDGE_WHITE_MIN = 212
POCKET_WHITE_MIN = 232
NEUTRAL_MAX = 14   # differenza massima tra i canali per essere neutro (le vele crema sono più calde)
POCKET_MIN = 60    # aree bianche non collegate al bordo tra POCKET_MIN e POCKET_MAX px sono sfondo;
POCKET_MAX = 4000  # quelle più grandi sono vele bianche e restano
MARGIN = 6


def background_mask(img):
    w, h = img.size
    r, g, b = img.split()
    mn = ImageChops.darker(ImageChops.darker(r, g), b)
    mx = ImageChops.lighter(ImageChops.lighter(r, g), b)
    spread = ImageChops.subtract(mx, mn)
    neutral = spread.point(lambda v: 255 if v <= NEUTRAL_MAX else 0)
    loose = ImageChops.multiply(mn.point(lambda v: 255 if v >= EDGE_WHITE_MIN else 0), neutral).tobytes()
    strict = ImageChops.multiply(mn.point(lambda v: 255 if v >= POCKET_WHITE_MIN else 0), neutral).tobytes()
    data = loose
    bg = bytearray(w * h)
    seen = bytearray(w * h)

    def grow(seed):
        stack, comp = [seed], []
        seen[seed] = 1
        while stack:
            p = stack.pop()
            comp.append(p)
            x, y = p % w, p // w
            for q in ((p - 1) if x else -1, (p + 1) if x < w - 1 else -1, (p - w) if y else -1, (p + w) if y < h - 1 else -1):
                if q >= 0 and data[q] and not seen[q]:
                    seen[q] = 1
                    stack.append(q)
        return comp

    # Sfondo collegato al bordo.
    for x in range(w):
        for p in (x, (h - 1) * w + x):
            if data[p] and not seen[p]:
                for q in grow(p):
                    bg[q] = 1
    for y in range(h):
        for p in (y * w, y * w + w - 1):
            if data[p] and not seen[p]:
                for q in grow(p):
                    bg[q] = 1
    # Tasche bianche tra le sartie (solo bianco netto).
    data = strict
    for p in range(w * h):
        if data[p] and not seen[p]:
            comp = grow(p)
            if POCKET_MIN <= len(comp) <= POCKET_MAX:
                for q in comp:
                    bg[q] = 1
    return Image.frombytes("L", (w, h), bytes(v * 255 for v in bg))


def cutout(src):
    img = Image.open(src).convert("RGB")
    bg = background_mask(img)
    alpha = bg.point(lambda v: 0 if v else 255)
    alpha = alpha.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    out = img.convert("RGBA")
    out.putalpha(alpha)
    box = alpha.point(lambda v: 255 if v > 20 else 0).getbbox()
    box = (max(0, box[0] - MARGIN), max(0, box[1] - MARGIN), min(img.width, box[2] + MARGIN), min(img.height, box[3] + MARGIN))
    return out.crop(box)


for name, dest in FILES.items():
    img = cutout(MEDIA / name)
    img.save(OUT / f"{dest}.png")
    print(dest, img.size)
