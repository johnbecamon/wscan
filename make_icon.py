#!/usr/bin/env python3
"""WSCAN Icon Generator"""
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 512, 512


def try_font(size):
    for name in ["Roboto-Bold.ttf", "Arial.ttf",
                 "/system/fonts/Roboto-Bold.ttf",
                 "/system/fonts/DroidSans-Bold.ttf"]:
        try: return ImageFont.truetype(name, size)
        except Exception: continue
    return ImageFont.load_default()


def create_icon():
    img = Image.new("RGB", (W, H), (10, 15, 25))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        draw.line([(0, y), (W, y)], fill=(int(10+10*t), int(15+15*t), int(25+35*t)))

    cx, cy = W // 2, int(H * 0.46)
    half = int(W * 0.31)
    top = cy - int(H * 0.33)
    bottom = cy + int(H * 0.33)

    pts = [(cx-half, top), (cx-half, top+120),
           (cx-half//2, top+220), (cx, bottom),
           (cx+half//2, top+220), (cx+half, top+120),
           (cx+half, top), (cx, top-40)]
    draw.polygon(pts, fill=(20, 60, 110), outline=(74, 158, 255))

    # Bolt
    bx, by = cx, cy + 5
    bolt = [(bx, by-70), (bx-38, by+10), (bx-7, by+10),
            (bx-25, by+70), (bx+38, by-14), (bx+7, by-14),
            (bx+25, by-70)]
    draw.polygon(bolt, fill=(63, 224, 124))

    # WSCAN text
    font_big = try_font(62)
    bbox = draw.textbbox((0, 0), "WSCAN", font=font_big)
    tx = (W - (bbox[2]-bbox[0])) // 2
    ty = int(H * 0.85)
    draw.text((tx+2, ty+2), "WSCAN", font=font_big, fill=(0, 0, 0))
    draw.text((tx, ty), "WSCAN", font=font_big, fill=(255, 255, 255))

    # Sub-text
    font_sm = try_font(18)
    bbox2 = draw.textbbox((0, 0), "SECURITY SCANNER", font=font_sm)
    sx = (W - (bbox2[2]-bbox2[0])) // 2
    draw.text((sx, int(H*0.95)), "SECURITY SCANNER", font=font_sm,
              fill=(140, 170, 200))

    img.save("icon.png", "PNG")
    print(f"✅ icon.png ({W}x{H})")


def create_splash():
    PW, PH = 1280, 720
    img = Image.new("RGB", (PW, PH), (10, 15, 25))
    draw = ImageDraw.Draw(img)
    for y in range(PH):
        t = y / PH
        draw.line([(0, y), (PW, y)], fill=(int(10+8*t), int(15+10*t), int(25+20*t)))
    if os.path.exists("icon.png"):
        try:
            ic = Image.open("icon.png").convert("RGB").resize((320, 320))
            img.paste(ic, ((PW-320)//2, (PH-320)//2 - 40))
        except Exception: pass
    font_big = try_font(48)
    bbox = draw.textbbox((0, 0), "WSCAN", font=font_big)
    tx = (PW - (bbox[2]-bbox[0])) // 2
    ty = (PH + 320) // 2 + 20
    draw.text((tx, ty), "WSCAN", font=font_big, fill=(255, 255, 255))
    img.save("presplash.png", "PNG")
    print(f"✅ presplash.png ({PW}x{PH})")


if __name__ == "__main__":
    print("🎨 Generating WSCAN icons...")
    create_icon()
    create_splash()
    print("✅ Done!")
