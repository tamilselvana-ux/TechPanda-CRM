"""
Generator for crystal-clear, unblurred vector and raster badge logos:
- White circular badge with crisp outline
- Deep navy blue dot (•) at upper left (#1c4982)
- Lowercase letter 't' with crossbar and smooth curved base (#1c4982)
- Multi-resolution PNGs (1024, 512, 256, 192, 128, 64, 32)
- Multi-layer ICO favicon
"""

import math
from PIL import Image, ImageDraw

def create_badge_svg(size=512):
    """
    Constructs mathematically pure SVG paths for the •t circular badge.
    Coordinate system 0 0 512 512.
    """
    # Center of badge: (256, 256)
    # Circle radius: 232 (leaving 24px margin for clean antialiased 12px stroke)
    # Total glyph (•t) width in 512 space: ~260px, height: ~260px
    # Dot: center (164, 182), radius 34
    # 't' stem: x from 254 to 304 (width 50)
    # 't' top: y = 144
    # 't' crossbar: x from 210 to 384, y from 196 to 244 (height 48)
    # 't' base curve: outer curve goes down to y = 372, curves right to x = 384, y = 352
    
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <filter id="badge-shadow" x="-8%" y="-8%" width="120%" height="120%">
      <feDropShadow dx="0" dy="4" stdDeviation="8" flood-color="#000000" flood-opacity="0.18"/>
    </filter>
  </defs>
  <!-- Outer Circular Badge -->
  <circle cx="256" cy="256" r="236" fill="#ffffff" stroke="#2b313d" stroke-width="14" filter="url(#badge-shadow)"/>
  
  <!-- Top-Left Dot (•) -->
  <circle cx="166" cy="180" r="32" fill="#174b89"/>

  <!-- Letter 't' -->
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
  " fill="#174b89"/>
</svg>'''
    return svg

def render_high_res_badge(size=1024):
    """
    Renders the badge directly onto a high-res RGBA PIL Image with 4x supersampling
    for ultra-smooth, unblurred, crystal-clear edges.
    """
    supersample = 4
    w = size * supersample
    h = size * supersample
    scale = w / 512.0

    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    # Coordinates scaled
    cx, cy = 256 * scale, 256 * scale
    r = 236 * scale
    stroke_w = int(14 * scale)

    # 1. Subtle drop shadow
    shadow_offset = int(6 * scale)
    shadow_r = r + int(2 * scale)
    draw.ellipse(
        [cx - shadow_r, cy - shadow_r + shadow_offset, cx + shadow_r, cy + shadow_r + shadow_offset],
        fill=(0, 0, 0, 35)
    )

    # 2. Outer dark border
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(43, 49, 61, 255))

    # 3. Inner crisp white circle
    inner_r = r - stroke_w
    draw.ellipse([cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r], fill=(255, 255, 255, 255))

    # 4. Dot (•)
    dot_cx, dot_cy = 166 * scale, 180 * scale
    dot_r = 32 * scale
    draw.ellipse([dot_cx - dot_r, dot_cy - dot_r, dot_cx + dot_r, dot_cy + dot_r], fill=(23, 75, 137, 255))

    # 5. Letter 't' polygon / curved points
    # We generate dense points along the cubic bezier curves
    t_points = []

    def pt(x, y):
        return (x * scale, y * scale)

    # Top stem to crossbar
    t_points.append(pt(252, 144))
    t_points.append(pt(298, 144))
    t_points.append(pt(298, 198))
    t_points.append(pt(374, 198))
    t_points.append(pt(374, 242))
    t_points.append(pt(298, 242))
    t_points.append(pt(298, 322))

    # Curve 1: (298, 322) -> C (298, 348), (306, 358) -> (328, 358)
    for i in range(1, 16):
        t = i / 15.0
        # B(t) = (1-t)^3 P0 + 3(1-t)^2 t P1 + 3(1-t) t^2 P2 + t^3 P3
        bx = (1-t)**3 * 298 + 3*(1-t)**2 * t * 298 + 3*(1-t) * t**2 * 306 + t**3 * 328
        by = (1-t)**3 * 322 + 3*(1-t)**2 * t * 348 + 3*(1-t) * t**2 * 358 + t**3 * 358
        t_points.append(pt(bx, by))

    # Curve 2: (328, 358) -> (372, 344)
    for i in range(1, 11):
        t = i / 10.0
        bx = (1-t) * 328 + t * 372
        by = (1-t) * 358 + t * 344
        t_points.append(pt(bx, by))

    t_points.append(pt(372, 384))

    # Curve 3: (372, 384) -> C (354, 394), (332, 400) -> (310, 400)
    for i in range(1, 16):
        t = i / 15.0
        bx = (1-t)**2 * 372 + 2*(1-t)*t * 354 + t**2 * 310
        by = (1-t)**2 * 384 + 2*(1-t)*t * 398 + t**2 * 400
        t_points.append(pt(bx, by))

    # Curve 4: (310, 400) -> C (268, 400), (252, 376) -> (252, 326)
    for i in range(1, 16):
        t = i / 15.0
        bx = (1-t)**3 * 310 + 3*(1-t)**2 * t * 276 + 3*(1-t) * t**2 * 252 + t**3 * 252
        by = (1-t)**3 * 400 + 3*(1-t)**2 * t * 400 + 3*(1-t) * t**2 * 376 + t**3 * 326
        t_points.append(pt(bx, by))

    t_points.append(pt(252, 242))
    t_points.append(pt(214, 242))
    t_points.append(pt(214, 198))
    t_points.append(pt(252, 198))

    draw.polygon(t_points, fill=(23, 75, 137, 255))

    # Downsample with Lanczos high-quality resampling for anti-aliasing
    final_im = im.resize((size, size), Image.Resampling.LANCZOS)
    return final_im

if __name__ == '__main__':
    svg_data = create_badge_svg(512)
    with open('CRM/scratch/test_badge.svg', 'w', encoding='utf-8') as f:
        f.write(svg_data)
    
    img = render_high_res_badge(512)
    img.save('CRM/scratch/test_badge.png')
    print("SUCCESS: Rendered test_badge.svg and test_badge.png")
