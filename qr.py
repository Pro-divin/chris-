"""
Modern, beautiful QR code generator.

Generates a stylish QR code for the given URL with:
  - Rounded module shapes
  - Smooth radial gradient color
  - Soft drop shadow on a clean background
  - Optional center logo / caption card

Requirements:
    pip install qrcode[pil] pillow
"""

from __future__ import annotations

from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from qrcode.constants import ERROR_CORRECT_H
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import RadialGradiantColorMask
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer


URL = "https://pro-divin.github.io/chris-/"
CAPTION = "Chris Portfolio"
SUBCAPTION = ""
OUTPUT = Path(__file__).with_name("chris_portfolio_qr.png")
LOGO_PATH = Path(r"C:\Users\peril ops\Desktop\chris\Gemini_Generated_Image_5d4l1q5d4l1q5d4l-removebg-preview.png")


# Brand palette (gold colors)
CENTER_COLOR = (255, 215, 0)      # gold
EDGE_COLOR = (184, 134, 11)       # dark gold
BACK_COLOR = (255, 255, 255)
CARD_BG = (255, 255, 255)
PAGE_BG_TOP = (245, 247, 255)
PAGE_BG_BOTTOM = (255, 240, 250)


def make_qr_image() -> Image.Image:
    """Build the styled QR image (rounded modules + radial gradient)."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_H,  # high EC so center logo is safe
        box_size=18,
        border=2,
    )
    qr.add_data(URL)
    qr.make(fit=True)

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(radius_ratio=1),
        color_mask=RadialGradiantColorMask(
            back_color=BACK_COLOR,
            center_color=CENTER_COLOR,
            edge_color=EDGE_COLOR,
        ),
    ).convert("RGBA")
    return img


def add_center_logo(qr_img: Image.Image) -> Image.Image:
    """Embed the brand logo in a circular white badge at the QR center."""
    w, h = qr_img.size
    badge_d = int(min(w, h) * 0.22)

    # white circle backing with subtle border
    badge = Image.new("RGBA", (badge_d, badge_d), (0, 0, 0, 0))
    d = ImageDraw.Draw(badge)
    d.ellipse((0, 0, badge_d - 1, badge_d - 1), fill=(255, 255, 255, 255))

    # load and fit logo inside the badge with padding
    logo = Image.open(LOGO_PATH).convert("RGBA")
    logo_pad = int(badge_d * 0.14)
    logo_size = badge_d - logo_pad * 2
    logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

    # circular clip mask for logo
    logo_mask = Image.new("L", (logo_size, logo_size), 0)
    ImageDraw.Draw(logo_mask).ellipse((0, 0, logo_size - 1, logo_size - 1), fill=255)
    logo_clipped = Image.new("RGBA", (logo_size, logo_size), (0, 0, 0, 0))
    logo_clipped.paste(logo, (0, 0), mask=logo_mask)

    badge.alpha_composite(logo_clipped, (logo_pad, logo_pad))

    qr_img.alpha_composite(badge, ((w - badge_d) // 2, (h - badge_d) // 2))
    return qr_img


def _load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = (
        ["segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"]
        if bold
        else ["segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"]
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _vertical_gradient(size: tuple[int, int], top, bottom) -> Image.Image:
    w, h = size
    base = Image.new("RGB", (1, h), top)
    px = base.load()
    for y in range(h):
        t = y / max(1, h - 1)
        px[0, y] = (
            int(top[0] + (bottom[0] - top[0]) * t),
            int(top[1] + (bottom[1] - top[1]) * t),
            int(top[2] + (bottom[2] - top[2]) * t),
        )
    return base.resize((w, h))


def _rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, size[0], size[1]), radius=radius, fill=255
    )
    return mask


def compose_poster(qr_img: Image.Image) -> Image.Image:
    """Place the QR onto a soft gradient page with a card + captions."""
    qr_size = 900
    qr_img = qr_img.resize((qr_size, qr_size), Image.LANCZOS)

    pad_x = 120
    pad_top = 110
    pad_bottom = 210
    W = qr_size + pad_x * 2
    H = qr_size + pad_top + pad_bottom

    # page background gradient
    page = _vertical_gradient((W, H), PAGE_BG_TOP, PAGE_BG_BOTTOM).convert("RGBA")

    # white card with rounded corners + drop shadow
    card_pad = 60
    card_size = (qr_size + card_pad * 2, qr_size + card_pad * 2)
    radius = 56

    shadow = Image.new("RGBA", (card_size[0] + 80, card_size[1] + 80), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle(
        (40, 50, 40 + card_size[0], 50 + card_size[1]),
        radius=radius,
        fill=(30, 30, 60, 90),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(28))

    card = Image.new("RGBA", card_size, CARD_BG + (255,))
    card.putalpha(_rounded_mask(card_size, radius))

    card_x = (W - card_size[0]) // 2
    card_y = pad_top - card_pad
    page.alpha_composite(shadow, (card_x - 40, card_y - 40))
    page.alpha_composite(card, (card_x, card_y))
    page.alpha_composite(qr_img, (card_x + card_pad, card_y + card_pad))

    # logo below QR card (small, centred)
    try:
        small_logo = Image.open(LOGO_PATH).convert("RGBA")
        logo_h = 80
        logo_w = int(small_logo.width * logo_h / small_logo.height)
        small_logo = small_logo.resize((logo_w, logo_h), Image.LANCZOS)
        logo_x = (W - logo_w) // 2
        logo_y = card_y + card_size[1] + 28
        page.alpha_composite(small_logo, (logo_x, logo_y))
        title_y = logo_y + logo_h + 22
    except Exception:
        title_y = card_y + card_size[1] + 36

    # captions
    draw = ImageDraw.Draw(page)
    title_font = _load_font(64, bold=True)

    _centered_text(draw, CAPTION, title_font, W, title_y, fill=(20, 20, 60, 255))

    return page


def _centered_text(draw, text, font, width, y, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    draw.text(((width - tw) // 2 - bbox[0], y), text, font=font, fill=fill)


def main() -> None:
    qr_img = make_qr_image()
    qr_img = add_center_logo(qr_img)
    poster = compose_poster(qr_img)
    poster.convert("RGB").save(OUTPUT, "PNG", optimize=True)
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
