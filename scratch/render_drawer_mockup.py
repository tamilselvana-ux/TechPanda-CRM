import os
from PIL import Image, ImageDraw, ImageFont

# Canvas: 1366 x 768 (Desktop view with right drawer open)
img = Image.new('RGB', (1366, 768), (241, 245, 249))
draw = ImageDraw.Draw(img)

# 1. Background blurred/dimmed content
# Mock header
draw.rectangle([0, 0, 1366, 56], fill=(255, 255, 255))
draw.line([0, 56, 1366, 56], fill=(226, 232, 240), width=1)
# Mock sidebar
draw.rectangle([0, 56, 220, 768], fill=(255, 255, 255))
draw.line([220, 56, 220, 768], fill=(226, 232, 240), width=1)

# Mock cards on dashboard
for i in range(4):
    x = 240 + i * 270
    draw.rounded_rectangle([x, 80, x + 250, 180], radius=12, fill=(255, 255, 255), outline=(226, 232, 240), width=1)

# Mock table
draw.rounded_rectangle([240, 210, 1340, 740], radius=12, fill=(255, 255, 255), outline=(226, 232, 240), width=1)

# 2. Backdrop Overlay
overlay = Image.new('RGBA', (1366, 768), (15, 23, 42, 110))
img.paste(Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB'))
draw = ImageDraw.Draw(img)

# 3. Slide-over Drawer (Desktop >= 900px, 720px width, right-side)
drawer_w = 720
drawer_x = 1366 - drawer_w
draw.rectangle([drawer_x, 0, 1366, 768], fill=(255, 255, 255))
draw.line([drawer_x, 0, drawer_x, 768], fill=(226, 232, 240), width=2)

# Drawer Header
draw.rectangle([drawer_x, 0, 1366, 70], fill=(255, 255, 255))
draw.line([drawer_x, 70, 1366, 70], fill=(241, 245, 249), width=1)

# Title & Close
# Draw close button (X)
draw.rounded_rectangle([1366 - 46, 18, 1366 - 16, 48], radius=8, fill=(241, 245, 249))
draw.line([1366 - 36, 28, 1366 - 26, 38], fill=(100, 116, 139), width=2)
draw.line([1366 - 26, 28, 1366 - 36, 38], fill=(100, 116, 139), width=2)

# Presets Bar
presets = ['Today', 'Yesterday', 'Last 7 Days', 'Last 30 Days', 'This Month', 'Last Month', 'Custom']
px = drawer_x + 24
for idx, p in enumerate(presets):
    pw = 75 if len(p) <= 6 else (95 if len(p) <= 10 else 105)
    bg = (10, 83, 181) if p == 'This Month' else (241, 245, 249)
    border = (10, 83, 181) if p == 'This Month' else (226, 232, 240)
    draw.rounded_rectangle([px, 86, px + pw, 118], radius=16, fill=bg, outline=border, width=1)
    px += pw + 8

# Inputs row: From Date & To Date
draw.rounded_rectangle([drawer_x + 24, 136, drawer_x + 350, 180], radius=8, fill=(255, 255, 255), outline=(10, 83, 181), width=2)
draw.rounded_rectangle([drawer_x + 370, 136, drawer_x + 696, 180], radius=8, fill=(255, 255, 255), outline=(10, 83, 181), width=2)

# Two Months Side-by-Side Calendar Containers
m1_x = drawer_x + 24
m2_x = drawer_x + 370

draw.rounded_rectangle([m1_x, 200, m1_x + 326, 680], radius=12, fill=(248, 250, 252), outline=(226, 232, 240), width=1)
draw.rounded_rectangle([m2_x, 200, m2_x + 326, 680], radius=12, fill=(248, 250, 252), outline=(226, 232, 240), width=1)

# Calendar Grid 1 (October 2026)
# Month nav
draw.rectangle([m1_x + 12, 212, m1_x + 36, 236], fill=(226, 232, 240)) # prev arrow
draw.rectangle([m2_x + 290, 212, m2_x + 314, 236], fill=(226, 232, 240)) # next arrow

# Draw day cells and range highlight
cell_size = 40
start_col, start_row = 3, 2 # Oct 1
range_start_r, range_start_c = 2, 4 # Oct 3
range_end_r, range_end_c = 5, 5 # Oct 30

for r in range(6):
    for c in range(7):
        cx = m1_x + 18 + c * 42
        cy = 280 + r * 42
        # Check if in range
        day_num = r * 7 + c - 3
        if 1 <= day_num <= 31:
            if day_num == 3: # start date
                draw.rectangle([cx, cy, cx + cell_size, cy + cell_size], fill=(220, 235, 252))
                draw.rounded_rectangle([cx, cy, cx + cell_size, cy + cell_size], radius=20, fill=(10, 83, 181))
            elif day_num == 30: # end date
                draw.rectangle([cx, cy, cx + cell_size, cy + cell_size], fill=(220, 235, 252))
                draw.rounded_rectangle([cx, cy, cx + cell_size, cy + cell_size], radius=20, fill=(10, 83, 181))
            elif 3 < day_num < 30: # in range
                draw.rectangle([cx - 2, cy, cx + cell_size + 2, cy + cell_size], fill=(220, 235, 252))
            else:
                draw.rounded_rectangle([cx, cy, cx + cell_size, cy + cell_size], radius=6, fill=(255, 255, 255), outline=(241, 245, 249))

# Calendar Grid 2 (November 2026)
for r in range(5):
    for c in range(7):
        cx = m2_x + 18 + c * 42
        cy = 280 + r * 42
        draw.rounded_rectangle([cx, cy, cx + cell_size, cy + cell_size], radius=6, fill=(255, 255, 255), outline=(241, 245, 249))

# Sticky Footer
draw.rectangle([drawer_x, 700, 1366, 768], fill=(255, 255, 255))
draw.line([drawer_x, 700, 1366, 700], fill=(226, 232, 240), width=1)

# Clear button
draw.rounded_rectangle([drawer_x + 24, 714, drawer_x + 110, 754], radius=8, fill=(255, 255, 255), outline=(203, 213, 225), width=1)
# Cancel button
draw.rounded_rectangle([drawer_x + 480, 714, drawer_x + 580, 754], radius=8, fill=(241, 245, 249), outline=(226, 232, 240), width=1)
# Apply button
draw.rounded_rectangle([drawer_x + 590, 714, drawer_x + 696, 754], radius=8, fill=(10, 83, 181))

os.makedirs('docs/qa/calendar_design', exist_ok=True)
out_path = 'docs/qa/calendar_design/calendar_drawer_desktop_spec.png'
img.save(out_path)
print(f"Saved design mockup: {out_path} ({os.path.getsize(out_path):,} bytes)")
