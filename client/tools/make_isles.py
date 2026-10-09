"""Ritaglia le isole in media/ in PNG con bordo sfumato (maschera ellittica)."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "demo/assets/isles"
OUT.mkdir(parents=True, exist_ok=True)
WIDTH = 480

# file -> (centro x, centro y, raggio x, raggio y) in frazioni dell'immagine
ISLES = {
    "isle01.jpg": (0.50, 0.52, 0.44, 0.42),
    "isle02.jpg": (0.50, 0.50, 0.49, 0.49),
    "isle03.jpg": (0.50, 0.50, 0.49, 0.49),
}

for name, (cx, cy, rx, ry) in ISLES.items():
    img = Image.open(ROOT / "media" / name).convert("RGBA")
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).ellipse((w * (cx - rx), h * (cy - ry), w * (cx + rx), h * (cy + ry)), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(min(w, h) * 0.05))
    img.putalpha(mask)
    img = img.resize((WIDTH, round(h * WIDTH / w)), Image.LANCZOS)
    img.save(OUT / name.replace(".jpg", ".png"))
    print(name, img.size)
