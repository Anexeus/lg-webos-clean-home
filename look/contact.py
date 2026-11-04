"""Contact sheet of PNG/JPG files in a folder, for checking icons and scenes by eye.  python contact.py <dir> <out.png> [cols]"""
import os
import sys

from PIL import Image, ImageDraw

d, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 4
names = sorted(n for n in os.listdir(d) if n.lower().endswith(('.png', '.jpg')))
W, H, PAD = 400, 240, 24
rows = (len(names) + cols - 1) // cols
sheet = Image.new('RGB', (cols * (W + PAD) + PAD, rows * (H + PAD + 20) + PAD), '#101012')
dr = ImageDraw.Draw(sheet)
for i, n in enumerate(names):
    im = Image.open(os.path.join(d, n)).convert('RGB').resize((W, H))
    mask = Image.new('L', (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, W - 1, H - 1), radius=40, fill=255)  # the launcher's tile corners
    x, y = PAD + (i % cols) * (W + PAD), PAD + (i // cols) * (H + PAD + 20)
    sheet.paste(im, (x, y), mask)
    dr.text((x, y + H + 4), n, fill='#aaaaaa')
sheet.save(out)
print(out)
