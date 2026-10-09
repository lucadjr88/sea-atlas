"""Assembla gli sprite finali in demo/assets/ships_clean e scrive meta.json.

Per ogni modello: <nome>_sail (in movimento, con scia), <nome>_furled (ferma) e <nome>_net0.. (flotta in scanning SDU).
Tre modelli usano gli sprite ad alta risoluzione di demo/assets/ships_new (vedi cutout_ships.py):
  peschereccio -> fishing_*, cutter_war -> cutter_furled, small_brig -> brig_*.
Per gli altri la rete si copia (gru, cavi e rete) dal peschereccio sullo scafo con vele chiuse.
"""
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageStat

import fix_ships as fx

NEW = fx.ROOT / "demo/assets/ships_new"
OUT = fx.OUT
TARGET_W = 320  # larghezza degli sprite ad alta risoluzione (gli originali sono larghi circa 150 px)

# Zona (nelle coordinate di fishing_net_empty) che contiene gru, cavi e rete; il resto è lo scafo.
CRANE_AREA = [(95, 300), (300, 300), (300, 615), (235, 625), (245, 743), (0, 743), (0, 585), (95, 515)]
CRANE_BASE = (260, 590)  # piede della gru, punto di aggancio sullo scafo di destinazione


def load_new(name):
    return Image.open(NEW / f"{name}.png").convert("RGBA")


def scaled(img, factor):
    return img.resize((max(1, round(img.width * factor)), max(1, round(img.height * factor))), Image.LANCZOS)


def register(base, other, search=30, q=4):
    """Offset (rx, ry): il pixel (u, v) di `other` corrisponde a (u + rx, v + ry) di `base`.

    Si confronta solo la metà alta (alberi e vele), dove la rete non interferisce.
    """
    a = base.getchannel("A").resize((base.width // q, base.height // q))
    b = other.getchannel("A").resize((other.width // q, other.height // q))
    region = (0, 0, a.width, int(a.height * 0.5))
    a_top = a.crop(region)
    best = None
    for dy in range(-search, search + 1):
        for dx in range(-search, search + 1):
            canvas = Image.new("L", a.size, 0)
            canvas.paste(b, (dx, dy))
            score = ImageStat.Stat(ImageChops.difference(a_top, canvas.crop(region))).sum[0]
            if best is None or score < best[0]:
                best = (score, dx, dy)
    return best[1] * q, best[2] * q


def extract_net_overlay():
    """Estrae gru e rete dal peschereccio (differenza tra lo sprite con rete e quello senza)."""
    base = load_new("fishing_furled")
    net = load_new("fishing_net_empty")
    rx, ry = register(base, net)
    base_in_net = Image.new("RGBA", net.size, (0, 0, 0, 0))
    base_in_net.paste(base, (-rx, -ry))
    diff = ImageChops.difference(net.convert("RGB"), base_in_net.convert("RGB"))
    r, g, b = diff.split()
    colour = ImageChops.lighter(ImageChops.lighter(r, g), b).point(lambda v: 255 if v > 55 else 0)
    new_pixels = ImageChops.multiply(base_in_net.getchannel("A").point(lambda v: 255 if v < 128 else 0), net.getchannel("A"))
    area = Image.new("L", net.size, 0)
    ImageDraw.Draw(area).polygon(CRANE_AREA, fill=255)
    mask = ImageChops.multiply(ImageChops.lighter(colour, new_pixels), area).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    overlay = net.copy()
    overlay.putalpha(ImageChops.multiply(net.getchannel("A"), mask))
    box = overlay.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox()
    anchor_base = (CRANE_BASE[0] + rx, CRANE_BASE[1] + ry)
    return {
        "image": overlay.crop(box),
        "anchor": (CRANE_BASE[0] - box[0], CRANE_BASE[1] - box[1]),
        "frac": (anchor_base[0] / base.width, anchor_base[1] / base.height),
        "ref_w": base.width,
    }


def with_net(hull, ov):
    """Copia la gru con la rete sullo scafo `hull`; restituisce l'immagine (può estendersi in basso)."""
    s = hull.width / ov["ref_w"]
    img = scaled(ov["image"], s)
    px = round(ov["frac"][0] * hull.width - ov["anchor"][0] * s)
    py = round(ov["frac"][1] * hull.height - ov["anchor"][1] * s)
    px, py = max(0, px), max(0, py)
    canvas = Image.new("RGBA", (max(hull.width, px + img.width), max(hull.height, py + img.height)), (0, 0, 0, 0))
    canvas.alpha_composite(hull)
    canvas.alpha_composite(img, (px, py))
    return canvas


def main():
    for f in OUT.glob("*"):
        f.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    meta = {"models": {}, "textures": {}}
    overlay = extract_net_overlay()
    proc = fx.load_procedural()

    def hires(name, factor=None):
        img = load_new(name)
        f = factor or TARGET_W / img.width
        return scaled(img, f), f

    for name, p in proc.items():
        sail, furled, bottom = p["sail"], p["furled"], p["bottom"]
        ref = sail.width / fx.span(bottom)  # larghezza dello sprite di classe / larghezza dello scafo
        # stato -> lista di (immagine, contorno dello scafo, in movimento)
        variants = {"sail": [(sail, bottom, True)], "furled": [(furled, bottom, False)], "net": []}

        if name == "peschereccio":
            base, f = hires("fishing_furled")
            b = fx.hull_bottom(base)
            variants["sail"] = [(base, b, True)]
            variants["furled"] = [(base, b, False)]
            base_full = load_new("fishing_furled")
            for net in ("fishing_net_empty", "fishing_net_fish", "fishing_net_two"):
                other = load_new(net)
                rx, ry = register(base_full, other)
                img = scaled(other, f)
                shift = (round(rx * f), round(ry * f))
                variants["net"].append((img, {x - shift[0]: y - shift[1] for x, y in b.items()}, False))
        elif name == "small_brig":
            opened, f = hires("brig_open")
            variants["sail"] = [(opened, fx.hull_bottom(opened), True)]
            furled_hr, _ = hires("brig_furled")
            variants["furled"] = [(furled_hr, fx.hull_bottom(furled_hr), False)]
            other = load_new("brig_net")
            rx, ry = register(load_new("brig_open"), other)
            shift = (round(rx * f), round(ry * f))
            net_img = scaled(other, f)
            b = variants["sail"][0][1]
            variants["net"] = [(net_img, {x - shift[0]: y - shift[1] for x, y in b.items()}, False)]
        else:
            if name == "cutter_war":
                hull, _ = hires("cutter_furled")
                furled, bottom = hull, fx.hull_bottom(hull)
                variants["furled"] = [(furled, bottom, False)]
            variants["net"] = [(with_net(furled, overlay), bottom, False)]

        for state, items in variants.items():
            for i, (img, b, moving) in enumerate(items):
                key = f"{name}_{state}" + (str(i) if state == "net" else "")
                canvas, m = fx.compose(img, b, moving, key)
                canvas.save(OUT / f"{key}.png")
                meta["textures"][key] = {"w": round(m["span"] * ref, 2), "oy": m["oy"], "top": m["top"]}
        meta["models"][name] = {"nets": len(variants["net"])}
        print(name, {k: len(v) for k, v in variants.items()})
    (OUT / "meta.json").write_text(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
