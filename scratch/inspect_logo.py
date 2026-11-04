from PIL import Image
im = Image.open('C:/Users/tamil/.gemini/antigravity/brain/364306a8-735f-4286-9c22-bb9e159eba4d/.user_uploaded/media_1793339423541_b9d845c3.png')
# find green pixels (where G is high and B, R are lower)
greens = []
for p in im.getdata():
    if p[3] > 200 and p[1] > p[0] + 50 and p[1] > p[2] + 50:
        greens.append(f"#{p[0]:02x}{p[1]:02x}{p[2]:02x}")
from collections import Counter
print("Dominant Greens:", Counter(greens).most_common(5))
