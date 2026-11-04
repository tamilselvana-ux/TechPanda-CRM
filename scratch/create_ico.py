import struct
import io

# We will read favicon-32.png and favicon-192.png and write a compliant ICO file
with open('CRM/static/images/favicon-32.png', 'rb') as f:
    png32 = f.read()

with open('CRM/static/images/favicon.png', 'rb') as f:
    png192 = f.read()

entries = [
    (32, 32, png32),
    (192, 192, png192),
]

ico = io.BytesIO()
# ICONDIR
ico.write(struct.pack('<HHH', 0, 1, len(entries)))

offset = 6 + (16 * len(entries))
for w, h, data in entries:
    bw = 0 if w >= 256 else w
    bh = 0 if h >= 256 else h
    # bWidth, bHeight, bColorCount, bReserved, wPlanes, wBitCount, dwBytesInRes, dwImageOffset
    ico.write(struct.pack('<BBBBHHII', bw, bh, 0, 0, 1, 32, len(data), offset))
    offset += len(data)

for w, h, data in entries:
    ico.write(data)

with open('CRM/static/images/favicon.ico', 'wb') as f:
    f.write(ico.getvalue())

print(f"Wrote clean multi-frame favicon.ico ({len(ico.getvalue())} bytes)")
