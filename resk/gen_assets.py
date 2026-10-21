"""Regenerate every RustDesk icon/logo from the Resk artwork in resk/source.
Run from the repo root: python3 resk/gen_assets.py (needs Pillow)."""
from pathlib import Path
from PIL import Image, ImageDraw

SRC = "resk/source"
INK = (5, 5, 5, 255)          # Resk black, the app-icon tile
icon = Image.open(f"{SRC}/resk-icon-512.png").convert("RGBA")

# Isolate the bone "R" from the black tile: keep light pixels, alpha by luminance.
gray = icon.convert("L")
mark = Image.new("RGBA", icon.size, (0, 0, 0, 0))
bone = Image.new("RGBA", icon.size, icon.getpixel((256, 120)))  # sample the R's fill
alpha = gray.point(lambda v: 0 if v < 40 else min(255, int((v - 40) * 255 / 160)))
mark = Image.composite(bone, mark, alpha)
mark = mark.crop(mark.getbbox())

def tile(size, radius_ratio=0.22, mark_ratio=0.62, round_=False):
    """Black rounded tile (or circle) with the R centred optically."""
    s = size * 4
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    mask = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(mask)
    if round_:
        d.ellipse((0, 0, s - 1, s - 1), fill=255)
    else:
        d.rounded_rectangle((0, 0, s - 1, s - 1), radius=int(s * radius_ratio), fill=255)
    im.paste(Image.new("RGBA", (s, s), INK), (0, 0), mask)
    h = int(s * mark_ratio)
    m = mark.resize((int(mark.width * h / mark.height), h), Image.LANCZOS)
    # The R's bowl is heavier on the left; nudge right 1.5% so it reads centred.
    x = (s - m.width) // 2 + int(s * 0.015)
    y = (s - m.height) // 2
    im.alpha_composite(m, (x, y))
    return im.resize((size, size), Image.LANCZOS)

def foreground(size):
    """Adaptive-icon foreground: R only, inside the 66% safe zone."""
    s = size * 4
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    h = int(s * 0.40)
    m = mark.resize((int(mark.width * h / mark.height), h), Image.LANCZOS)
    im.alpha_composite(m, ((s - m.width) // 2 + int(s * 0.01), (s - m.height) // 2))
    return im.resize((size, size), Image.LANCZOS)

def ico(path, sizes):
    tile(256).save(path, sizes=[(n, n) for n in sizes])

# Windows / desktop
ico("flutter/windows/runner/resources/app_icon.ico", [16, 20, 24, 32, 40, 48, 64, 128, 256])
ico("res/icon.ico", [16, 24, 32, 48, 64, 128, 256])
ico("res/tray-icon.ico", [16, 20, 24, 32, 48])
for n, p in [(32, "res/32x32.png"), (64, "res/64x64.png"), (128, "res/128x128.png"),
             (256, "res/128x128@2x.png"), (512, "res/icon.png"), (1024, "res/mac-icon.png")]:
    tile(n).save(p)
tile(512).save("flutter/assets/icon.png")

# In-app wordmark (RustDesk loads these if present; max 300x60)
for src, dst in [("resk-logo.png", "logo_light.png"), ("resk-logo-white.png", "logo_dark.png"),
                 ("resk-logo.png", "logo.png")]:
    im = Image.open(f"{SRC}/{src}").convert("RGBA")
    # The source files carry a near-invisible (alpha 3) fill; drop it so no box shows.
    im.putalpha(im.getchannel("A").point(lambda v: 0 if v <= 8 else v))
    im = im.crop(im.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox())
    im.thumbnail((600, 120), Image.LANCZOS)   # 2x of the 300x60 slot
    im.save(f"flutter/assets/{dst}")

# Android launcher
for dpi, n in [("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)]:
    base = f"flutter/android/app/src/main/res/mipmap-{dpi}"
    tile(n).save(f"{base}/ic_launcher.png")
    tile(n, round_=True).save(f"{base}/ic_launcher_round.png")
    foreground(n * 9 // 4).save(f"{base}/ic_launcher_foreground.png")
print("assets regenerated")

# Windows installer (WiX) artwork. Dialog: 493x312, WiX draws its text on the
# right of x=164, so only the left panel carries the mark. Banner: 493x58, text
# sits on the left, the mark on the right.
Path("resk/msi").mkdir(parents=True, exist_ok=True)
PAPER = (255, 254, 252)
INK_RGB = (21, 21, 19)
dlg = Image.new("RGB", (493, 312), PAPER)
dlg.paste(Image.new("RGB", (164, 312), INK_RGB), (0, 0))
m = mark.resize((int(mark.width * 96 / mark.height), 96), Image.LANCZOS)
dlg.paste(m, ((164 - m.width) // 2 + 2, (312 - m.height) // 2), m)
dlg.save("resk/msi/WixUIDialogBmp.bmp")
ban = Image.new("RGB", (493, 58), PAPER)
t = tile(40)
ban.paste(t, (493 - 40 - 12, 9), t)
ban.save("resk/msi/WixUIBannerBmp.bmp")
print("installer artwork regenerated")

# icon.svg is the fallback some screens load directly; embed the same R tile.
import base64
_b = base64.b64encode(Path("flutter/assets/icon.png").read_bytes()).decode()
Path("flutter/assets/icon.svg").write_text(
    '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
    f'viewBox="0 0 512 512" width="512" height="512"><image width="512" height="512" '
    f'xlink:href="data:image/png;base64,{_b}"/></svg>\n')
print("icon.svg regenerated")
