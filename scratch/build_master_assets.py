"""
Master Brand Asset Generator for iTechPanda CRM:
Builds crystal-clear, unblurred vector SVG and multi-resolution PNG/ICO assets
matching the user-uploaded white circular badge with blue dot (•) and lowercase 't'.
"""

import os
from PIL import Image, ImageDraw

def get_svg_content(theme="standard"):
    """
    Returns scalable vector graphics XML.
    theme="standard": White circular badge, dark ring (#2b313d), navy glyphs (#174b89).
    theme="dark": Transparent / white ring, white glyphs.
    """
    if theme == "dark":
        badge_fill = "#1e293b"
        badge_stroke = "#ffffff"
        glyph_fill = "#ffffff"
    else:
        badge_fill = "#ffffff"
        badge_stroke = "#2b313d"
        glyph_fill = "#174b89"

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <!-- Circular Badge Container -->
  <circle cx="256" cy="256" r="236" fill="{badge_fill}" stroke="{badge_stroke}" stroke-width="14" stroke-opacity="0.95"/>
  
  <!-- Dot (•) at Upper Left -->
  <circle cx="166" cy="180" r="32" fill="{glyph_fill}"/>

  <!-- Lowercase Letter 't' -->
  <path d="
    M 252 144
    L 298 144
    L 298 198
    L 374 198
    L 374 242
    L 298 242
    L 298 322
    C 298 348 306 358 328 358
    C 342 358 358 354 372 344
    L 372 384
    C 354 394 332 400 310 400
    C 268 400 252 376 252 326
    L 252 242
    L 214 242
    L 214 198
    L 252 198
    Z
  " fill="{glyph_fill}"/>
</svg>'''

def render_badge(size, theme="standard"):
    """
    Renders high-definition anti-aliased PNG at exact target resolution
    using 4x supersampling and Lanczos downsampling.
    """
    supersample = 4
    w = size * supersample
    h = size * supersample
    scale = w / 512.0

    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    cx, cy = 256 * scale, 256 * scale
    r = 236 * scale
    stroke_w = int(14 * scale)

    if theme == "dark":
        badge_fill = (30, 41, 59, 255)
        badge_stroke = (255, 255, 255, 245)
        glyph_fill = (255, 255, 255, 255)
    else:
        badge_fill = (255, 255, 255, 255)
        badge_stroke = (43, 49, 61, 245)
        glyph_fill = (23, 75, 137, 255)

    # 1. Subtle soft drop shadow (for standard badge)
    if theme != "dark":
        shadow_offset = int(5 * scale)
        shadow_r = r + int(2 * scale)
        draw.ellipse(
            [cx - shadow_r, cy - shadow_r + shadow_offset, cx + shadow_r, cy + shadow_r + shadow_offset],
            fill=(0, 0, 0, 30)
        )

    # 2. Outer ring stroke
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=badge_stroke)

    # 3. Inner circle fill
    inner_r = r - stroke_w
    draw.ellipse([cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r], fill=badge_fill)

    # 4. Dot (•)
    dot_cx, dot_cy = 166 * scale, 180 * scale
    dot_r = 32 * scale
    draw.ellipse([dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r], fill=glyph_fill)

    # 5. Letter 't'
    def pt(x, y):
        return (x * scale, y * scale)

    t_points = []
    t_points.append(pt(252, 144))
    t_points.append(pt(298, 144))
    t_points.append(pt(298, 198))
    t_points.append(pt(374, 198))
    t_points.append(pt(374, 242))
    t_points.append(pt(298, 242))
    t_points.append(pt(298, 322))

    # Bezier curve to tail
    for i in range(1, 16):
        t = i / 15.0
        bx = (1-t)**3 * 298 + 3*(1-t)**2 * t * 298 + 3*(1-t) * t**2 * 306 + t**3 * 328
        by = (1-t)**3 * 322 + 3*(1-t)**2 * t * 348 + 3*(1-t) * t**2 * 358 + t**3 * 358
        t_points.append(pt(bx, by))

    for i in range(1, 11):
        t = i / 10.0
        bx = (1-t) * 328 + t * 372
        by = (1-t) * 358 + t * 344
        t_points.append(pt(bx, by))

    t_points.append(pt(372, 384))

    for i in range(1, 16):
        t = i / 15.0
        bx = (1-t)**2 * 372 + 2*(1-t)*t * 354 + t**2 * 310
        by = (1-t)**2 * 384 + 2*(1-t)*t * 398 + t**2 * 400
        t_points.append(pt(bx, by))

    for i in range(1, 16):
        t = i / 15.0
        bx = (1-t)**3 * 310 + 3*(1-t)**2 * t * 276 + 3*(1-t) * t**2 * 252 + t**3 * 252
        by = (1-t)**3 * 400 + 3*(1-t)**2 * t * 400 + 3*(1-t) * t**2 * 376 + t**3 * 326
        t_points.append(pt(bx, by))

    t_points.append(pt(252, 242))
    t_points.append(pt(214, 242))
    t_points.append(pt(214, 198))
    t_points.append(pt(252, 198))

    draw.polygon(t_points, fill=glyph_fill)

    return im.resize((size, size), Image.Resampling.LANCZOS)

def build_all_assets():
    static_img_dir = os.path.abspath('CRM/static/images')
    os.makedirs(static_img_dir, exist_ok=True)

    print("Generating pure vector SVGs...")
    std_svg = get_svg_content("standard")
    dark_svg = get_svg_content("dark")

    svg_targets = [
        'itechpanda_symbol.svg',
        'itechpanda_logo.svg',
        'digipanda_symbol.svg',
        'digipanda_logo.svg',
        'techpanda_logo.svg',
    ]
    for fn in svg_targets:
        with open(os.path.join(static_img_dir, fn), 'w', encoding='utf-8') as f:
            f.write(std_svg)

    dark_svg_targets = [
        'itechpanda_logo_white.svg',
        'digipanda_logo_dark.svg',
        'techpanda_logo_white.svg',
    ]
    for fn in dark_svg_targets:
        with open(os.path.join(static_img_dir, fn), 'w', encoding='utf-8') as f:
            f.write(dark_svg)

    print("Rendering HD raster PNGs...")
    img_1024 = render_badge(1024, "standard")
    img_512 = render_badge(512, "standard")
    img_256 = render_badge(256, "standard")
    img_192 = render_badge(192, "standard")
    img_128 = render_badge(128, "standard")
    img_64 = render_badge(64, "standard")
    img_32 = render_badge(32, "standard")

    dark_img_1024 = render_badge(1024, "dark")

    # Overwrite master PNGs
    master_targets = [
        'itechpanda_symbol.png',
        'itechpanda_logo.png',
        'digipanda_logo.png',
        'digipanda_crm_logo.png',
        'digipanda_email_logo.png',
        'digipanda_logo_hd.png',
        'digipanda_symbol.png',
        'digipanda_logo_whitebg.png',
        'digipanda_official_logo.png',
        'techpanda_logo.png',
    ]
    for fn in master_targets:
        img_1024.save(os.path.join(static_img_dir, fn), "PNG")
        print(f"  Saved {fn} (1024x1024)")

    # Dark mode PNGs
    dark_targets = [
        'itechpanda_logo_white.png',
        'digipanda_logo_dark.png',
        'digipanda_exact_darkmode.png',
    ]
    for fn in dark_targets:
        dark_img_1024.save(os.path.join(static_img_dir, fn), "PNG")
        print(f"  Saved {fn} (dark)")

    # Favicons
    img_512.save(os.path.join(static_img_dir, 'favicon.png'), "PNG")
    img_192.save(os.path.join(static_img_dir, 'favicon-192.png'), "PNG")
    img_32.save(os.path.join(static_img_dir, 'favicon-32.png'), "PNG")
    print("  Saved favicons (512, 192, 32)")

    # Multi-resolution ICO
    ico_path = os.path.join(static_img_dir, 'favicon.ico')
    img_256.save(
        ico_path,
        format='ICO',
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    )
    print("  Saved multi-resolution favicon.ico")

    print("\nALL MASTER BRAND ASSETS GENERATED SUCCESSFULLY WITH ZERO BLUR!")

if __name__ == '__main__':
    build_all_assets()
