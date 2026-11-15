#!/usr/bin/env python3
"""Generate apk/app/res/drawable/ic_launcher.png (512x512).

Design: red gradient rounded square, white hanzi 汉 (Noto Serif CJK SC Bold),
thin gold inner border. PIL + system CJK font.
"""
import argparse
from PIL import Image, ImageDraw, ImageFont

SIZE = 512
FONT = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    img = Image.new("RGB", (SIZE, SIZE), (127, 16, 16))
    d = ImageDraw.Draw(img)
    # vertical gradient: #7f1010 -> #b71c1c
    for y in range(SIZE):
        t = y / SIZE
        r = int(127 + (183 - 127) * t)
        g = int(16 + (28 - 16) * t)
        b = int(16 + (28 - 16) * t)
        d.line([(0, y), (SIZE, y)], fill=(r, g, b))
    # rounded corners: mask
    mask = Image.new("L", (SIZE, SIZE), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=112, fill=255)
    img.putalpha(mask)
    d = ImageDraw.Draw(img)
    # gold inner border
    d.rounded_rectangle([14, 14, SIZE - 15, SIZE - 15], radius=100, outline=(212, 175, 55), width=6)
    # white 汉, centered
    font = ImageFont.truetype(FONT, 300, index=1)  # index 1 = SC in the TTC
    text = "汉"
    bbox = d.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((SIZE - w) / 2 - bbox[0], (SIZE - h) / 2 - bbox[1] - 8), text, font=font, fill=(255, 255, 255))
    img.save(args.out)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
