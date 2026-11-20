"""Build the landing page in web/ (deployed to Cloudflare Pages).

    python scripts/build_web.py
    npx wrangler pages deploy web --project-name holdfast

Needs a local checkout of holdfast-app next to this repo (brand files and screenshots).
Copy brand assets, fonts and resized screenshots into holdfast-packs/site/assets,
and inline six skill drawings into site/index.html (placeholders {{skill:<dir>/<file>}})."""
import re
import shutil
from pathlib import Path

from fontTools.ttLib import TTFont
from PIL import Image

PACKS = Path(__file__).resolve().parents[1]
APP = PACKS.parent / "holdfast-app"
BRAND = APP / "branding"
SITE = PACKS / "web"
A = SITE / "assets"
TEMPLATE = PACKS / "web-src" / "index.template.html"

for sub in ("fonts", "img", "brand"):
    (A / sub).mkdir(parents=True, exist_ok=True)

# Fonts: self-hosted (no Google Fonts request), woff2, Latin only.
from fontTools import subset
for weight in ("Regular", "Semibold", "Bold"):
    src = BRAND / "06_Colors_and_Type" / "fonts" / f"OpenSans-{weight}.ttf"
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga"]
    font = TTFont(src)
    s = subset.Subsetter(opts)
    s.populate(unicodes=list(range(0x20, 0x7F)) + list(range(0xA0, 0x100)) + [0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2026, 0x2190, 0x2192, 0x203A])
    s.subset(font)
    font.flavor = "woff2"
    font.save(A / "fonts" / f"open-sans-{weight.lower()}.woff2")
lic = BRAND / "06_Colors_and_Type" / "licenses"
for f in lic.iterdir():
    shutil.copy(f, A / "fonts" / f.name)

# Brand
for f in ("favicon.svg", "favicon.ico", "apple-touch-icon-180.png"):
    shutil.copy(BRAND / "03_App_Icons" / "web" / f, A / "brand" / f)
shutil.copy(BRAND / "01_Logos_SVG" / "horizontal" / "holdfast-horizontal-reverse.svg", A / "brand" / "logo-reverse.svg")
shutil.copy(BRAND / "04_Social_and_Media" / "backgrounds" / "holdfast-pattern-dark-1920x1080.svg", A / "brand" / "pattern-dark.svg")
shutil.copy(BRAND / "04_Social_and_Media" / "share-card" / "holdfast-share-card-dark-1200x630.png", A / "brand" / "share-card.png")

# Screenshots: 720 wide WebP (and 360 for small screens)
shots = {
    "home": APP / "docs/store/ios/screenshots-6.9/01-home.png",
    "map": APP / "docs/store/android/screenshots/1-map-topo.png",
    "library": APP / "docs/store/android/screenshots/2-library-answer.png",
    "plan": APP / "docs/store/android/screenshots/3-plan.png",
    "inventory": APP / "docs/store/android/screenshots/6-inventory.png",
}
for name, src in shots.items():
    im = Image.open(src).convert("RGB")
    for w in (360, 720):
        h = round(im.height * w / im.width)
        im.resize((w, h), Image.LANCZOS).save(A / "img" / f"{name}-{w}.webp", "WEBP", quality=82, method=6)
    print(name, im.size)

# Inline drawings
html = TEMPLATE.read_text(encoding="utf-8")


def inline(m):
    svg = (PACKS / "packs/core/sources/skills" / m.group(1)).read_text(encoding="utf-8")
    svg = re.sub(r"<\?xml[^>]*\?>\s*", "", svg)
    svg = re.sub(r"\s*<title>.*?</title>", "", svg)
    svg = svg.replace("<svg ", '<svg aria-hidden="true" focusable="false" ', 1)
    return svg.strip()


html = re.sub(r"\{\{skill:([^}]+)\}\}", inline, html)
(SITE / "index.html").write_text(html, encoding="utf-8", newline="\n")
total = sum(f.stat().st_size for f in A.rglob("*") if f.is_file())
print("assets", total // 1024, "KB; index", (SITE / "index.html").stat().st_size // 1024, "KB")
