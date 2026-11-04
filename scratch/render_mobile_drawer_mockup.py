import os
from PIL import Image, ImageDraw

# Mobile Canvas: 390 x 844
img = Image.new('RGB', (390, 844), (241, 245, 249))
draw = ImageDraw.Draw(img)

# Mock mobile background
draw.rectangle([0, 0, 390, 56], fill=(255, 255, 255))
draw.line([0, 56, 390, 56], fill=(226, 232, 240))
# Dim overlay
overlay = Image.new('RGBA', (390, 844), (15, 23, 42, 120))
img.paste(Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB'))
draw = ImageDraw.Draw(img)

# Bottom sheet drawer: sliding up from y=120 to y=844
sheet_y = 100
draw.rounded_rectangle([0, sheet_y, 390, 844], radius=24, fill=(255, 255, 255))

# Pull bar indicator
draw.rounded_rectangle([170, sheet_y + 10, 220, sheet_y + 14], radius=2, fill=(203, 213, 225))

# Header: Title & Close
draw.line([0, sheet_y + 56, 390, sheet_y + 56], fill=(241, 245, 249), width=1)
draw.rounded_rectangle([390 - 44, sheet_y + 18, 390 - 16, sheet_y + 46], radius=8, fill=(241, 245, 249))

# Horizontal Presets Scroll Strip
presets = ['Today', 'Yesterday', '7 Days', '30 Days', 'This Month', 'Last Month']
px = 16
for p in presets:
    pw = 65 if len(p) <= 6 else 85
    bg = (10, 83, 181) if p == 'This Month' else (241, 245, 249)
    border = (10, 83, 181) if p == 'This Month' else (226, 232, 240)
    draw.rounded_rectangle([px, sheet_y + 70, px + pw, sheet_y + 102], radius=16, fill=bg, outline=border)
    px += pw + 8

# Inputs row: From Date & To Date
draw.rounded_rectangle([16, sheet_y + 116, 190, sheet_y + 154], radius=8, fill=(255, 255, 255), outline=(10, 83, 181))
draw.rounded_rectangle([200, sheet_y + 116, 374, sheet_y + 154], radius=8, fill=(255, 255, 255), outline=(10, 83, 181))

# Single Month Calendar Grid (October 2026) - cells >= 44x44
cal_y = sheet_y + 170
cell_size = 46

for r in range(6):
    for c in range(7):
        cx = 18 + c * 51
        cy = cal_y + 50 + r * 50
        day_num = r * 7 + c - 3
        if 1 <= day_num <= 31:
            if day_num == 3:
                draw.rectangle([cx, cy, cx + cell_size, cy + cell_size], fill=(220, 235, 252))
                draw.rounded_rectangle([cx, cy, cx + cell_size, cy + cell_size], radius=23, fill=(10, 83, 181))
            elif day_num == 30:
                draw.rectangle([cx, cy, cx + cell_size, cy + cell_size], fill=(220, 235, 252))
                draw.rounded_rectangle([cx, cy, cx + cell_size, cy + cell_size], radius=23, fill=(10, 83, 181))
            elif 3 < day_num < 30:
                draw.rectangle([cx - 2, cy, cx + cell_size + 2, cy + cell_size], fill=(220, 235, 252))
            else:
                draw.rounded_rectangle([cx, cy, cx + cell_size, cy + cell_size], radius=8, fill=(255, 255, 255), outline=(241, 245, 249))

# Sticky Bottom Footer (Always in view on mobile)
draw.rectangle([0, 770, 390, 844], fill=(255, 255, 255))
draw.line([0, 770, 390, 770], fill=(226, 232, 240), width=1)
draw.rounded_rectangle([16, 784, 110, 830], radius=10, fill=(241, 245, 249), outline=(226, 232, 240))
draw.rounded_rectangle([120, 784, 374, 830], radius=10, fill=(10, 83, 181))

out_path = 'docs/qa/calendar_design/calendar_drawer_mobile_spec.png'
img.save(out_path)
print(f"Saved mobile mockup: {out_path} ({os.path.getsize(out_path):,} bytes)")
