import os, base64
from PIL import Image
import numpy as np

os.makedirs('CRM_Integrated_v2/CRM/scratch', exist_ok=True)
images_dir = 'CRM_Integrated_v2/CRM/static/images'

# Load tight d
d_tight = Image.open('CRM_Integrated_v2/CRM/scratch/d_tight.png')
w, h = d_tight.size

# 1. Generate digipanda_symbol.png (512x512 square transparent)
canvas_size = 512
# We want the d to occupy ~80% of canvas height (around 410px)
target_h = 410
target_w = int(w * (target_h / h))
d_resized = d_tight.resize((target_w, target_h), Image.Resampling.LANCZOS)

symbol_canvas = Image.new('RGBA', (canvas_size, canvas_size), (0, 0, 0, 0))
paste_x = (canvas_size - target_w) // 2
paste_y = (canvas_size - target_h) // 2
symbol_canvas.paste(d_resized, (paste_x, paste_y), mask=d_resized.split()[3])

symbol_path = os.path.join(images_dir, 'digipanda_symbol.png')
symbol_canvas.save(symbol_path, 'PNG', optimize=True)
print('Saved digipanda_symbol.png:', symbol_path, symbol_canvas.size)

# Also save digipanda_logo.png (so any legacy or current reference gets the d logo)
d_logo_path = os.path.join(images_dir, 'digipanda_logo.png')
symbol_canvas.save(d_logo_path, 'PNG', optimize=True)
print('Saved digipanda_logo.png (using d logo):', d_logo_path)

# 2. Dark mode symbol:
d_dark_path = os.path.join(images_dir, 'digipanda_logo_dark.png')
symbol_canvas.save(d_dark_path, 'PNG', optimize=True)
print('Saved digipanda_logo_dark.png:', d_dark_path)

# 3. Favicon.png (64x64) and Favicon.ico
fav_64 = symbol_canvas.resize((64, 64), Image.Resampling.LANCZOS)
fav_64_path = os.path.join(images_dir, 'favicon.png')
fav_64.save(fav_64_path, 'PNG')
print('Saved favicon.png:', fav_64_path)

fav_ico_path = os.path.join(images_dir, 'favicon.ico')
fav_64.save(fav_ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
print('Saved favicon.ico:', fav_ico_path)

# 4. Generate SVG vectors wrapping the clean high-res d mark
with open(symbol_path, 'rb') as f:
    b64_symbol = base64.b64encode(f.read()).decode('ascii')

svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <image href="data:image/png;base64,{b64_symbol}" width="512" height="512" />
</svg>'''

for svg_name in ['digipanda_symbol.svg', 'digipanda_logo.svg', 'digipanda_logo_dark.svg']:
    with open(os.path.join(images_dir, svg_name), 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print(f'Saved {svg_name}')

print('All d logo brand assets generated successfully.')
