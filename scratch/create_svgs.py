import base64
import os

def make_svg(png_path, svg_path, w, h):
    with open(png_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
    content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="100%">
  <image href="data:image/png;base64,{b64}" width="{w}" height="{h}" style="image-rendering: -webkit-optimize-contrast; image-rendering: crisp-edges;" />
</svg>'''
    with open(svg_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'Wrote {svg_path}')

os.makedirs('CRM/static/images', exist_ok=True)
make_svg('CRM/static/images/itechpanda_logo.png', 'CRM/static/images/itechpanda_logo.svg', 1048, 368)
make_svg('CRM/static/images/itechpanda_logo.png', 'CRM/static/images/digipanda_logo.svg', 1048, 368)
make_svg('CRM/static/images/itechpanda_logo_white.png', 'CRM/static/images/itechpanda_logo_white.svg', 1048, 368)
make_svg('CRM/static/images/itechpanda_logo_white.png', 'CRM/static/images/digipanda_logo_dark.svg', 1048, 368)
make_svg('CRM/static/images/itechpanda_symbol.png', 'CRM/static/images/itechpanda_symbol.svg', 512, 512)
make_svg('CRM/static/images/itechpanda_symbol.png', 'CRM/static/images/digipanda_symbol.svg', 512, 512)
print("All SVGs created successfully!")
