#!/usr/bin/env python3
"""Black Hack theme for Bruce firmware.

Layout (per user request):
  - Background = fond.png (hooded hacker at a laptop, drawn on the left).
  - Only the CURRENT item's icon is shown, sat on the hacker's back (the hood).
  - Right side = a vertical text menu: the current label in WHITE, centred; the
    previous label above it (smaller, grey); the next label below (smaller, grey).
  - Big, squarish font (Krungthep).

Each menu entry is a full-screen image with everything baked in (label:0,
border:0). Neighbours follow Bruce's real T-Embed CC1101 carousel order.
16 images x 4 sizes + a json per size. Reuses draw_icon/ITEMS/ORDER from the
Fallout theme generator.
"""
import os, json, importlib.util
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "fg", os.path.join(HERE, "../Bruce-theme-fallout/generate_theme.py"))
fg = importlib.util.module_from_spec(spec); spec.loader.exec_module(fg)
fg.GREEN = (255, 255, 255)                       # white pictos

SS = 3                                           # supersample
BG = os.path.join(HERE, "fond.png")
FONT = "/System/Library/Fonts/Supplemental/Krungthep.ttf"   # square & chunky
FONT_FALLBACK = "/System/Library/Fonts/Supplemental/Arial Black.ttf"

ITEMS = fg.ITEMS
ORDER = fg.ORDER
SIZES = {"105px": (240, 105), "140px": (320, 140),
         "180px": (320, 180), "192px": (320, 192)}

WHITE = (255, 255, 255)
GREY  = (120, 122, 128)
BLACK = (0, 0, 0)

# laptop screen back (measured inner black area, white outline excluded):
#   black runs y 0.571..0.886h, centre column ; true centre (0.226w, 0.729h),
#   min inner width ~0.204w. Icon scaled to a SAFE box inside it (margin ~5px)
# so it stays centred and never bites the white screen outline.
PIC_TCX, PIC_TCY = 0.226, 0.729
SAFE_W, SAFE_H = 0.175, 0.240       # fraction of canvas w/h the picto may occupy
TXT_CX = 0.70                                    # centre of the right text column
CUR_PX, SUB_PX = 0.30, 0.125                     # current / neighbour font size (in h)
OFF = 0.30                                       # prev/next vertical offset (in h)


def rgb565(r, g, b):
    return format(((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3), "04x")


def neighbours(key):
    if key in ORDER:
        i = ORDER.index(key); n = len(ORDER)
        return ITEMS[ORDER[i-1]][1], ITEMS[ORDER[(i+1) % n]][1]
    return None, None


def font(px):
    path = FONT if os.path.exists(FONT) else FONT_FALLBACK
    return ImageFont.truetype(path, int(px))


def fit(text, px, maxw):
    s = px
    while s > 7:
        f = font(s)
        if f.getlength(text) <= maxw:
            return f
        s -= 1
    return font(7)


def render(key, W, H):
    w, h = W * SS, H * SS
    bg = Image.open(BG).convert("RGB").resize((w, h), Image.LANCZOS).convert("RGBA")
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # current icon: draw large on its own layer, crop to its true bbox, scale it
    # to fit the SAFE box, then paste centred on the screen panel. This keeps
    # every picto centred (H+V) and clear of the white screen outline.
    ps = 0.16 * h
    ic = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    fg.draw_icon(key, ImageDraw.Draw(ic), 0.5 * w, 0.5 * h, ps,
                 max(2, int(0.16 * ps)))
    bb = ic.getbbox()
    if bb:
        crop = ic.crop(bb)
        bw, bh = crop.size
        scale = min(SAFE_W * w / bw, SAFE_H * h / bh)
        nw, nh = max(1, int(round(bw * scale))), max(1, int(round(bh * scale)))
        crop = crop.resize((nw, nh), Image.LANCZOS)
        px0 = int(round(PIC_TCX * w - nw / 2))
        py0 = int(round(PIC_TCY * h - nh / 2))
        layer.alpha_composite(crop, (px0, py0))
        d = ImageDraw.Draw(layer)

    # right-hand vertical text menu
    cx = TXT_CX * w
    maxw = 0.56 * w
    label = ITEMS[key][1]
    prev, nxt = neighbours(key)

    cf = fit(label, CUR_PX * h, maxw)
    d.text((cx, 0.5 * h), label, font=cf, fill=WHITE + (255,), anchor="mm",
           stroke_width=max(1, int(CUR_PX * h * 0.05)), stroke_fill=BLACK + (255,))
    if prev:
        sf = fit(prev, SUB_PX * h, maxw)
        d.text((cx, (0.5 - OFF) * h), prev, font=sf, fill=GREY + (255,), anchor="mm")
    if nxt:
        sf = fit(nxt, SUB_PX * h, maxw)
        d.text((cx, (0.5 + OFF) * h), nxt, font=sf, fill=GREY + (255,), anchor="mm")

    img = Image.alpha_composite(bg, layer).convert("RGB")
    return img.resize((W, H), Image.LANCZOS)


def main():
    if not os.path.exists(BG):
        raise SystemExit("Missing fond.png")
    out = os.path.join(HERE, "Black_Hack")
    for szname, (W, H) in SIZES.items():
        folder = os.path.join(out, szname)
        os.makedirs(folder, exist_ok=True)
        j = {}
        for key, (fname, _) in ITEMS.items():
            render(key, W, H).save(os.path.join(folder, fname))
            j[key] = fname
        j.update({
            "priColor": rgb565(*WHITE), "secColor": rgb565(*GREY),
            "bgColor": rgb565(*BLACK), "border": 0, "label": 0,
            "name": "Black Hack", "author": "koua29",
        })
        with open(os.path.join(folder, "Theme_Black_Hack.json"), "w") as f:
            json.dump(j, f, indent=2)
        print(f"  {szname}: {len(ITEMS)} icons + json")
    print("done ->", out)


if __name__ == "__main__":
    main()
