"""Generate WhatsApp Bridge brand assets and README screenshots."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "custom_components" / "whatsapp_bridge" / "brand"
DOCS = ROOT / "docs"
BRAND.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)

GREEN = (37, 211, 102)         # WhatsApp brand green
GREEN_DARK = (18, 140, 126)
WHITE = (255, 255, 255)
NEUTRAL_BG = (245, 247, 250)
PILL_AMBER = (245, 158, 11)
PILL_GREEN = (22, 163, 74)
PILL_RED = (220, 38, 38)
TEXT_DARK = (17, 24, 39)
TEXT_MUTED = (107, 114, 128)
DIVIDER = (229, 231, 235)


def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = (
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    )
    for c in candidates:
        if Path(c).exists():
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()


def speech_bubble(img: Image.Image, draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int) -> None:
    """Draw a stylised speech bubble centred on (cx, cy) with radius r."""
    box = [cx - r, cy - r, cx + r, cy + r]
    draw.rounded_rectangle(box, radius=int(r * 0.42), fill=WHITE)
    # tail
    tail = [
        (cx - int(r * 0.45), cy + int(r * 0.55)),
        (cx - int(r * 0.05), cy + int(r * 0.55)),
        (cx - int(r * 0.55), cy + int(r * 0.95)),
    ]
    draw.polygon(tail, fill=WHITE)


def make_icon(size: int, out: Path) -> None:
    img = Image.new("RGBA", (size, size), GREEN + (255,))
    draw = ImageDraw.Draw(img)
    pad = int(size * 0.12)
    bubble_r = int(size * 0.32)
    speech_bubble(img, draw, size // 2, size // 2 - int(size * 0.02), bubble_r)
    # "W" mark inside bubble
    font = _font(int(size * 0.34), bold=True)
    text = "W"
    tw, th = draw.textbbox((0, 0), text, font=font)[2:]
    draw.text(
        ((size - tw) / 2, (size - th) / 2 - int(size * 0.06)),
        text,
        font=font,
        fill=GREEN_DARK,
    )
    img.save(out, "PNG")


def make_logo(width: int, height: int, out: Path) -> None:
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # left badge
    badge = height
    draw.rounded_rectangle([0, 0, badge, height], radius=int(height * 0.22), fill=GREEN)
    speech_bubble(img, draw, badge // 2, height // 2, int(height * 0.32))
    font_w = _font(int(height * 0.34), bold=True)
    tw, th = draw.textbbox((0, 0), "W", font=font_w)[2:]
    draw.text(((badge - tw) / 2, (height - th) / 2 - int(height * 0.05)), "W", font=font_w, fill=GREEN_DARK)
    # text
    title_font = _font(int(height * 0.4), bold=True)
    sub_font = _font(int(height * 0.22))
    tx = badge + int(height * 0.18)
    draw.text((tx, int(height * 0.12)), "WhatsApp Bridge", font=title_font, fill=TEXT_DARK)
    draw.text((tx, int(height * 0.6)), "Home Assistant", font=sub_font, fill=TEXT_MUTED)
    img.save(out, "PNG")


def _round_card(draw, box, radius=12, fill=WHITE, shadow=True):
    if shadow:
        sh = [box[0] + 2, box[1] + 4, box[2] + 2, box[3] + 4]
        draw.rounded_rectangle(sh, radius=radius, fill=(0, 0, 0, 24))
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def _qr_grid(draw, x, y, size, modules=21):
    cell = size // modules
    # draw a fake QR-ish pattern (deterministic)
    import hashlib
    seed = hashlib.sha256(b"whatsapp-bridge-qr").digest()
    for r in range(modules):
        for c in range(modules):
            byte = seed[(r * modules + c) % len(seed)]
            on = ((byte >> ((r + c) % 7)) & 1) == 1
            if on:
                draw.rectangle([x + c * cell, y + r * cell, x + (c + 1) * cell, y + (r + 1) * cell], fill=(0, 0, 0))
    # finder squares
    for fx, fy in ((x, y), (x + (modules - 7) * cell, y), (x, y + (modules - 7) * cell)):
        draw.rectangle([fx, fy, fx + 7 * cell, fy + 7 * cell], fill=WHITE)
        draw.rectangle([fx, fy, fx + 7 * cell, fy + 7 * cell], outline=(0, 0, 0), width=cell)
        draw.rectangle([fx + 2 * cell, fy + 2 * cell, fx + 5 * cell, fy + 5 * cell], fill=(0, 0, 0))


def make_qr_card_screenshot(out: Path) -> None:
    W, H = 720, 540
    img = Image.new("RGB", (W, H), NEUTRAL_BG)
    draw = ImageDraw.Draw(img)

    # card
    card_box = [80, 60, W - 80, H - 60]
    _round_card(draw, card_box, radius=14)

    # header
    title = _font(20, bold=True)
    draw.text((card_box[0] + 24, card_box[1] + 18), "WhatsApp Bridge", font=title, fill=TEXT_DARK)
    # divider
    draw.rectangle([card_box[0] + 24, card_box[1] + 56, card_box[2] - 24, card_box[1] + 57], fill=DIVIDER)

    # status pill
    pill_x = card_box[0] + 24
    pill_y = card_box[1] + 76
    pill_text = "Waiting for QR scan"
    pill_font = _font(13, bold=True)
    pw, ph = draw.textbbox((0, 0), pill_text, font=pill_font)[2:]
    draw.rounded_rectangle([pill_x, pill_y, pill_x + pw + 28, pill_y + ph + 12], radius=999, fill=PILL_AMBER)
    draw.text((pill_x + 14, pill_y + 5), pill_text, font=pill_font, fill=WHITE)

    # QR
    qr_size = 256
    qr_x = (W - qr_size) // 2
    qr_y = card_box[1] + 130
    draw.rounded_rectangle([qr_x - 8, qr_y - 8, qr_x + qr_size + 8, qr_y + qr_size + 8], radius=10, fill=WHITE, outline=DIVIDER, width=1)
    _qr_grid(draw, qr_x, qr_y, qr_size, modules=29)

    # footer warning
    warn_font = _font(11)
    draw.text(
        (card_box[0] + 24, card_box[3] - 50),
        "Unofficial WhatsApp client — your account may be banned.",
        font=warn_font,
        fill=TEXT_MUTED,
    )
    draw.text(
        (card_box[0] + 24, card_box[3] - 32),
        "Use a secondary number, not your primary.",
        font=warn_font,
        fill=TEXT_MUTED,
    )

    img.save(out, "PNG")


def make_panel_screenshot(out: Path) -> None:
    W, H = 1024, 600
    img = Image.new("RGB", (W, H), NEUTRAL_BG)
    draw = ImageDraw.Draw(img)

    # header bar
    draw.rectangle([0, 0, W, 56], fill=GREEN_DARK)
    head_font = _font(18, bold=True)
    draw.text((24, 16), "WhatsApp Bridge", font=head_font, fill=WHITE)

    # tab nav
    tabs = ["Contacts", "Conversations", "Settings"]
    tx = 16
    ty = 72
    for i, t in enumerate(tabs):
        font = _font(14, bold=(i == 0))
        tw, th = draw.textbbox((0, 0), t, font=font)[2:]
        bw = tw + 28
        bh = th + 16
        if i == 0:
            draw.rounded_rectangle([tx, ty, tx + bw, ty + bh], radius=6, fill=GREEN)
            draw.text((tx + 14, ty + 7), t, font=font, fill=WHITE)
        else:
            draw.text((tx + 14, ty + 7), t, font=font, fill=TEXT_DARK)
        tx += bw + 8

    # divider under nav
    draw.rectangle([0, 116, W, 117], fill=DIVIDER)

    # toolbar
    draw.text((40, 140), "3 contacts", font=_font(15, bold=True), fill=TEXT_DARK)
    btn_font = _font(13)
    btn_x = W - 220
    draw.rounded_rectangle([btn_x, 134, btn_x + 90, 162], radius=6, outline=DIVIDER, width=1, fill=WHITE)
    draw.text((btn_x + 24, 142), "Refresh", font=btn_font, fill=TEXT_DARK)
    btn_x += 100
    draw.rounded_rectangle([btn_x, 134, btn_x + 110, 162], radius=6, fill=GREEN)
    draw.text((btn_x + 14, 142), "Add contact", font=btn_font, fill=WHITE)

    # table
    headers = ("Name", "Phone", "Notes", "")
    cols = (40, 220, 460, 800)
    draw.text((cols[0], 188), headers[0], font=_font(13, bold=True), fill=TEXT_DARK)
    draw.text((cols[1], 188), headers[1], font=_font(13, bold=True), fill=TEXT_DARK)
    draw.text((cols[2], 188), headers[2], font=_font(13, bold=True), fill=TEXT_DARK)
    draw.rectangle([20, 212, W - 20, 213], fill=DIVIDER)

    rows = [
        ("Mom", "+972 50 123 4567", "Daily check-in"),
        ("Front desk", "+972 4 999 1234", "Office hours only"),
        ("Adi (marketing)", "+972 54 765 4321", "Project updates"),
    ]
    y = 230
    row_font = _font(13)
    code_font = _font(12)
    for name, phone, notes in rows:
        draw.text((cols[0], y + 10), name, font=row_font, fill=TEXT_DARK)
        draw.text((cols[1], y + 10), phone, font=code_font, fill=TEXT_DARK)
        draw.text((cols[2], y + 10), notes, font=row_font, fill=TEXT_MUTED)
        # row actions
        ax = cols[3]
        for label, fill, fg in (("Send", GREEN, WHITE), ("Edit", WHITE, TEXT_DARK), ("Delete", PILL_RED, WHITE)):
            tw = draw.textbbox((0, 0), label, font=_font(12, bold=False))[2]
            bw = tw + 20
            outline = DIVIDER if fill == WHITE else fill
            draw.rounded_rectangle([ax, y + 4, ax + bw, y + 30], radius=5, outline=outline, width=1, fill=fill)
            draw.text((ax + 10, y + 9), label, font=_font(12), fill=fg)
            ax += bw + 6
        y += 44
        draw.rectangle([20, y - 6, W - 20, y - 5], fill=DIVIDER)

    img.save(out, "PNG")


def main() -> None:
    make_icon(256, BRAND / "icon.png")
    make_icon(512, BRAND / "icon@2x.png")
    make_logo(480, 80, BRAND / "logo.png")
    make_logo(960, 160, BRAND / "logo@2x.png")
    make_qr_card_screenshot(DOCS / "qr-card.png")
    make_panel_screenshot(DOCS / "panel.png")
    for p in (
        BRAND / "icon.png",
        BRAND / "icon@2x.png",
        BRAND / "logo.png",
        BRAND / "logo@2x.png",
        DOCS / "qr-card.png",
        DOCS / "panel.png",
    ):
        print(f"OK  {p.relative_to(ROOT)}  {p.stat().st_size} bytes")


if __name__ == "__main__":
    main()
