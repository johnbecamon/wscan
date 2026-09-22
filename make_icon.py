#!/usr/bin/env python3
"""WSCAN Icon Generator — FIXED VERSION"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 512, 512
OUT = "icon.png"
OUT_SPLASH = "presplash.png"


def try_font(size):
    for name in ["Roboto-Bold.ttf", "Arial.ttf",
                 "/system/fonts/Roboto-Bold.ttf",
                 "/system/fonts/DroidSans-Bold.ttf"]:
        try: return ImageFont.truetype(name, size)
        except Exception: continue
    return ImageFont.load_default()


def draw_shield(draw, cx, cy, w, h, fill, outline):
    half = w // 2
    top = cy - h // 2
    bottom = cy + h // 2
    pts = [(cx-half, top+h*0.15), (cx-half, top+h*0.40),
           (cx-half*0.85, top+h*0.65), (cx-half*0.55, top+h*0.85),
           (cx, bottom), (cx+half*0.55, top+h*0.85),
           (cx+half*0.85, top+h*0.65), (cx+half, top+h*0.40),
           (cx+half, top+h*0.15), (cx, top)]
    draw.polygon(pts, fill=fill)
    for i in range(3):
        draw.line(pts + [pts[0]], fill=outline, width=3)


def draw_bolt(draw, cx, cy, size, color):
    pts = [(cx, cy-size), (cx-size*0.55, cy+size*0.15),
           (cx-size*0.1, cy+size*0.15), (cx-size*0.35, cy+size),
           (cx+size*0.55, cy-size*0.2), (cx+size*0.1, cy-size*0.2),
           (cx+size*0.35, cy-size)]
    draw.polygon(pts, fill=color)


def create_icon():
    # RGB mode para sa icon
    img = Image.new("RGB", (W, H), (10, 15, 20))
    draw = ImageDraw.Draw(img)

    # Gradient
    for y in range(H):
        t = y / H
        draw.line([(0, y), (W, y)],
                  fill=(int(10+10*t), int(15+15*t), int(25+30*t)))

    # Glow
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W*0.15, H*0.15, W*0.85, H*0.85], fill=(15, 40, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(40))
    img = Image.blend(img, glow, 0.35)
    draw = ImageDraw.Draw(img)

    # Shield
    cx, cy = W // 2, int(H * 0.46)
    draw_shield(draw, cx, cy, int(W*0.62), int(H*0.66),
                (20, 60, 110), (74, 158, 255))

    # Bolt
    draw_bolt(draw, cx, cy+5, 70, (63, 224, 124))

    # Text WSCAN
    font_big = try_font(64)
    bbox = draw.textbbox((0, 0), "WSCAN", font=font_big)
    tx = (W - (bbox[2]-bbox[0])) // 2
    ty = int(H * 0.84)
    draw.text((tx+2, ty+2), "WSCAN", font=font_big, fill=(0, 0, 0))
    draw.text((tx, ty), "WSCAN", font=font_big, fill=(255, 255, 255))

    # Sub-text
    font_sm = try_font(20)
    bbox2 = draw.textbbox((0, 0), "SECURITY SCANNER", font=font_sm)
    sx = (W - (bbox2[2]-bbox2[0])) // 2
    draw.text((sx, int(H*0.94)), "SECURITY SCANNER", font=font_sm,
              fill=(140, 170, 200))

    img.save(OUT, "PNG")
    print(f"✅ {OUT} ({W}x{H})")


def create_splash():
    """Presplash — FIXED (no transparency mask)."""
    PW, PH = 1280, 720
    img = Image.new("RGB", (PW, PH), (10, 15, 25))
    draw = ImageDraw.Draw(img)

    # Gradient
    for y in range(PH):
        t = y / PH
        draw.line([(0, y), (PW, y)],
                  fill=(int(10+8*t), int(15+10*t), int(25+20*t)))

    # Paste icon — FIXED: convert to RGB (no mask!)
    if os.path.exists(OUT):
        try:
            ic = Image.open(OUT).convert("RGB").resize((320, 320))
            # Paste WITHOUT transparency mask
            img.paste(ic, ((PW-320)//2, (PH-320)//2 - 40))
        except Exception as e:
            print(f"⚠  Icon paste error: {e}")

    # Text WSCAN
    font_big = try_font(48)
    bbox = draw.textbbox((0, 0), "WSCAN", font=font_big)
    tx = (PW - (bbox[2]-bbox[0])) // 2
    ty = (PH + 320) // 2 + 20
    draw.text((tx, ty), "WSCAN", font=font_big, fill=(255, 255, 255))

    # Sub-text
    font_sm = try_font(20)
    bbox2 = draw.textbbox((0, 0), "Loading scanner...", font=font_sm)
    sx = (PW - (bbox2[2]-bbox2[0])) // 2
    draw.text((sx, ty+70), "Loading scanner...", font=font_sm,
              fill=(140, 170, 200))

    img.save(OUT_SPLASH, "PNG")
    print(f"✅ {OUT_SPLASH} ({PW}x{PH})")


if __name__ == "__main__":
    print("🎨 Generating WSCAN icons...")
    create_icon()
    create_splash()
    print("")
    print("✅ Tapos! Ngayon, upload sa Colab:")
    print("   - main.py")
    print("   - buildozer.spec")
    print("   - icon.png")
    print("   - presplash.png")