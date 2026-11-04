"""Scenes for the CleanFrame theme from CleanFrame's photographs (Unsplash License, credits in CleanFrame's docs/asset-sources.md).

For each photo: <id>.jpg, the photo at 1920 x 1080 with a soft dark gradient at the top (clock, buttons) and the bottom (dock), and
<id>-glass.jpg, a blurred, slightly darkened copy the launcher uses for the frosted cards.

    python make_scenes.py <CleanFrame wallpapers dir> <out dir>
"""
import os
import sys

from PIL import Image, ImageFilter

PHOTOS = ['valley', 'cove', 'alpine', 'misty', 'bridge', 'night', 'peaks', 'ridge', 'summit', 'golden']
W, H = 1920, 1080


def shade(im):
    """Darken towards the top and bottom edges: 0..0.42 over the top 32%, 0..0.55 over the bottom 45%."""
    mask = Image.new('L', (1, H))
    for y in range(H):
        t = y / H
        a = 0.0
        if t < 0.32:
            a = 0.42 * (1 - t / 0.32) ** 1.6
        if t > 0.55:
            a = max(a, 0.55 * ((t - 0.55) / 0.45) ** 1.4)
        mask.putpixel((0, y), int(a * 255))
    mask = mask.resize((W, H))
    return Image.composite(Image.new('RGB', (W, H), 'black'), im, mask)


def main(src, out):
    os.makedirs(out, exist_ok=True)
    for n in PHOTOS:
        im = Image.open(os.path.join(src, n + '.jpg')).convert('RGB').resize((W, H), Image.LANCZOS)
        shade(im).save(os.path.join(out, n + '.jpg'), quality=86, optimize=True, progressive=True)
        glass = im.filter(ImageFilter.GaussianBlur(36))
        glass = Image.blend(glass, Image.new('RGB', (W, H), 'black'), 0.18)
        glass.save(os.path.join(out, n + '-glass.jpg'), quality=80, optimize=True)
        print(n, os.path.getsize(os.path.join(out, n + '.jpg')) // 1024, 'KB')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
