#!/usr/bin/env python3
"""Generate high-resolution (1200x630) Open Graph cover image for evchargingcost.online."""
from __future__ import annotations

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SRC_DIR = Path(__file__).resolve().parent
OUT = SRC_DIR / "og-image.png"

W, H = 1200, 630

def create_og_image():
    # 1. Base canvas
    img = Image.new("RGBA", (W, H), (9, 13, 22, 255))
    draw = ImageDraw.Draw(img)

    # 2. Ambient radial lighting
    # Top-right emerald glow
    glow_top = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow_top)
    cx1, cy1 = 1050, 100
    for r in range(450, 0, -5):
        alpha = int(45 * (1 - r / 450) ** 1.5)
        g_draw.ellipse([cx1 - r, cy1 - r, cx1 + r, cy1 + r], fill=(16, 185, 129, alpha))
    img = Image.alpha_composite(img, glow_top)

    # Bottom-left cyan glow
    glow_bot = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gb_draw = ImageDraw.Draw(glow_bot)
    cx2, cy2 = 120, 560
    for r in range(350, 0, -5):
        alpha = int(35 * (1 - r / 350) ** 1.5)
        gb_draw.ellipse([cx2 - r, cy2 - r, cx2 + r, cy2 + r], fill=(56, 189, 248, alpha))
    img = Image.alpha_composite(img, glow_bot)

    draw = ImageDraw.Draw(img)

    # Subtle grid lines in background
    grid_color = (255, 255, 255, 8)
    for x in range(60, W, 60):
        draw.line([(x, 0), (x, H)], fill=grid_color, width=1)
    for y in range(60, H, 60):
        draw.line([(0, y), (W, y)], fill=grid_color, width=1)

    # Outer decorative card border with rounded corners
    card_inset = 24
    draw.rounded_rectangle(
        [card_inset, card_inset, W - card_inset, H - card_inset],
        radius=20,
        outline=(255, 255, 255, 30),
        width=1,
    )
    # Emerald corner accent line on the border
    draw.rounded_rectangle(
        [card_inset, card_inset, card_inset + 180, card_inset + 4],
        radius=2,
        fill=(16, 185, 129, 220),
    )

    # Fonts
    def get_font(name_bold: bool, size: int):
        font_files = ["segoeuib.ttf" if name_bold else "segoeui.ttf",
                      "arialbd.ttf" if name_bold else "arial.ttf",
                      "DejaVuSans-Bold.ttf" if name_bold else "DejaVuSans.ttf"]
        for f in font_files:
            try:
                return ImageFont.truetype(f, size)
            except Exception:
                continue
        return ImageFont.load_default()

    font_brand = get_font(True, 34)
    font_domain = get_font(False, 18)
    font_h1 = get_font(True, 54)
    font_sub = get_font(False, 23)
    font_card_val = get_font(True, 32)
    font_card_lbl = get_font(False, 16)
    font_card_sub = get_font(False, 15)
    font_tag = get_font(False, 17)

    # 3. Logo Icon (72x72)
    icon_x, icon_y = 70, 65
    icon_w, icon_h = 68, 68
    # Emerald rounded rectangle
    draw.rounded_rectangle(
        [icon_x, icon_y, icon_x + icon_w, icon_y + icon_h],
        radius=16,
        fill=(16, 185, 129, 255),
        outline=(52, 211, 153, 200),
        width=2,
    )
    # Lightning bolt polygon (scaled to fit nicely)
    bolt_pts = [
        (icon_x + 39, icon_y + 10),
        (icon_x + 18, icon_y + 38),
        (icon_x + 32, icon_y + 38),
        (icon_x + 28, icon_y + 58),
        (icon_x + 50, icon_y + 30),
        (icon_x + 36, icon_y + 30),
    ]
    draw.polygon(bolt_pts, fill=(255, 255, 255, 255))

    # Brand Title next to logo
    draw.text((icon_x + 85, icon_y + 6), "EV Charging", font=font_brand, fill=(255, 255, 255, 255))
    text_bbox = draw.textbbox((icon_x + 85, icon_y + 6), "EV Charging", font=font_brand)
    draw.text((text_bbox[2] + 10, icon_y + 6), "Cost Calculator", font=font_brand, fill=(52, 211, 153, 255))

    # Domain pill in top-right
    pill_text = "evchargingcost.online"
    pb = draw.textbbox((0, 0), pill_text, font=font_domain)
    pw = pb[2] - pb[0] + 32
    ph = pb[3] - pb[1] + 16
    px = W - 70 - pw
    py = icon_y + 14
    draw.rounded_rectangle([px, py, px + pw, py + ph], radius=14, fill=(15, 23, 42, 220), outline=(52, 211, 153, 120), width=1)
    # tiny green dot in pill
    draw.ellipse([px + 12, py + (ph // 2) - 4, px + 20, py + (ph // 2) + 4], fill=(16, 185, 129, 255))
    draw.text((px + 28, py + 8), pill_text, font=font_domain, fill=(226, 232, 240, 255))

    # 4. Main Headline
    draw.text((70, 168), "EV & Gas Charging Cost Calculator", font=font_h1, fill=(248, 250, 252, 255))

    # Subtitle
    subhead = "Compare Home & Supercharger Rates · 50 U.S. States · Real-Time Savings Simulator"
    draw.text((70, 240), subhead, font=font_sub, fill=(148, 163, 184, 255))

    # 5. Three Highlight Cards (y=300 to y=490)
    card_y = 300
    card_h = 190
    card_w = 330
    gap = 35
    start_x = 70

    cards_data = [
        {
            "badge": "TESLA MODEL Y LR",
            "val": "$19.24",
            "val_sub": " / full home charge",
            "desc": "357 mi EPA range · ~$69/mo at 1k mi",
            "tag": "Home L2 vs Supercharger",
            "color": (16, 185, 129),
        },
        {
            "badge": "ANNUAL FUEL SAVINGS",
            "val": "+$1,200+",
            "val_sub": " / year",
            "desc": "Electric vs 30 MPG petrol benchmark",
            "tag": "EV vs Hybrid vs Gas",
            "color": (56, 189, 248),
        },
        {
            "badge": "ALL 50 STATES + DC",
            "val": "EIA Form 861M",
            "val_sub": "",
            "desc": "Ranked by residential electricity rate",
            "tag": "State-by-State Energy Index",
            "color": (167, 139, 250),
        },
    ]

    for i, c in enumerate(cards_data):
        cx = start_x + i * (card_w + gap)
        # Card background
        draw.rounded_rectangle(
            [cx, card_y, cx + card_w, card_y + card_h],
            radius=16,
            fill=(15, 23, 42, 210),
            outline=(255, 255, 255, 25),
            width=1,
        )
        # Top accent bar
        draw.rounded_rectangle(
            [cx + 1, card_y + 1, cx + card_w - 1, card_y + 4],
            radius=2,
            fill=(*c["color"], 220),
        )
        # Badge label
        draw.text((cx + 22, card_y + 20), c["badge"], font=font_card_lbl, fill=(*c["color"], 255))
        # Main value
        draw.text((cx + 22, card_y + 50), c["val"], font=font_card_val, fill=(255, 255, 255, 255))
        if c["val_sub"]:
            vb = draw.textbbox((cx + 22, card_y + 50), c["val"], font=font_card_val)
            draw.text((vb[2] + 4, card_y + 62), c["val_sub"], font=font_card_sub, fill=(148, 163, 184, 255))

        # Description
        draw.text((cx + 22, card_y + 104), c["desc"], font=font_card_sub, fill=(203, 213, 225, 255))

        # Category pill
        draw.rounded_rectangle([cx + 20, card_y + 144, cx + card_w - 20, card_y + 172], radius=8, fill=(255, 255, 255, 10))
        draw.text((cx + 32, card_y + 149), c["tag"], font=font_card_lbl, fill=(148, 163, 184, 255))

    # 6. Bottom Trust / Feature Bar
    draw.line([(70, 520), (W - 70, 520)], fill=(255, 255, 255, 18), width=1)
    tags = [
        "100% Free Web Utility",
        "EPA & EIA Form 861M Grounded",
        "Instant Calculations",
        "Zero Sign-Up Required",
    ]
    tag_x = 70
    for t in tags:
        draw.text((tag_x, 545), "✓ " + t, font=font_tag, fill=(148, 163, 184, 255))
        tb = draw.textbbox((tag_x, 545), "✓ " + t, font=font_tag)
        tag_x = tb[2] + 36

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, format="PNG", optimize=True)
    print(f"Generated OG image: {OUT} ({W}x{H}, {OUT.stat().st_size} bytes)")

if __name__ == "__main__":
    create_og_image()
