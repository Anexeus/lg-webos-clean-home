"""Marks (white masks) for the LG apps in the CleanFrame port, in CleanFrame's own line style (24-unit viewBox, 1.6 stroke), and
their entries in assets/icons/metrics.js measured the way CleanFrame's build-icon-metrics.mjs does it (240 px render, alpha > 40
for the box, total ink / box area for fill).

    python make_cleanframe_marks.py <cleanframe-lg dir>
"""
import io
import json
import os
import re
import sys

import resvg_py
from PIL import Image

S = 'fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"'
PLAY = '<path fill="#fff" stroke="none" d="M10.2 11.2v5.6c0 .5.5.8.9.5l4.3-2.8c.4-.2.4-.8 0-1l-4.3-2.8c-.4-.3-.9 0-.9.5z"/>'
MARKS = {
    'iptv': f'<g {S}><rect x="2.5" y="7.5" width="19" height="13" rx="2.6"/><path d="m8 3 4 4.2L16 3"/></g>{PLAY}',
    'hdmi1': f'<g {S}><path d="M3 8.5h18v4.2l-2.6 2.8H5.6L3 12.7z"/><path d="M7 11.3h10"/></g>',
    'browser': f'<g {S}><circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="3.8" ry="9"/><path d="M3.4 9h17.2M3.4 15h17.2"/></g>',
    'media': f'<g {S}><rect x="2.5" y="4.5" width="19" height="15" rx="3.2"/></g>'
             '<path fill="#fff" d="M10 8.6v6.8c0 .6.6.9 1.1.6l5.3-3.4c.5-.3.5-.9 0-1.2l-5.3-3.4c-.5-.3-1.1 0-1.1.6z"/>',
    'lgstore': f'<g {S}><path d="M5 8h14l-1 11.2a1.6 1.6 0 0 1-1.6 1.4H7.6A1.6 1.6 0 0 1 6 19.2z"/><path d="M9 10V7a3 3 0 0 1 6 0v3"/></g>',
    'homebrew': f'<g {S}><path d="M5 9h11v9a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3z"/><path d="M16 11h1.6a2.6 2.6 0 0 1 0 5.2H16"/>'
                '<path d="M5.2 9A2.6 2.6 0 0 1 7.5 5a3.2 3.2 0 0 1 5.6-.4A2.6 2.6 0 0 1 16 9"/><path d="M9 13v4M12 13v4"/></g>',
    'privacy': f'<g {S}><path d="M12 2.8 4.6 5.8v5.6c0 4.6 3.1 8.4 7.4 9.8 4.3-1.4 7.4-5.2 7.4-9.8V5.8z"/><path d="m8.6 12.2 2.4 2.4 4.6-4.8"/></g>',
    'homesetup': f'<g {S}><path d="M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1"/>'
                 '<circle cx="15" cy="6" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="17" cy="18" r="2"/></g>',
}


def measure(svg):
    png = bytes(resvg_py.svg_to_bytes(svg_string=svg.replace('<svg ', '<svg width="240" height="240" ', 1)))
    a = Image.open(io.BytesIO(png)).convert('RGBA').split()[3]
    px = a.load()
    left, top, right, bottom, ink = 240, 240, -1, -1, 0.0
    for y in range(240):
        for x in range(240):
            v = px[x, y]
            ink += v / 255
            if v > 40:
                left, top, right, bottom = min(left, x), min(top, y), max(right, x), max(bottom, y)
    w, h = right - left + 1, bottom - top + 1
    return {'n': 240, 'x': left, 'y': top, 'w': w, 'h': h, 'fill': ink / (w * h)}


def main(d):
    icons = os.path.join(d, 'assets', 'icons')
    mfile = os.path.join(icons, 'metrics.js')
    text = open(mfile, encoding='utf-8').read()
    m = json.loads(re.search(r'window\.FrameIconMetrics = (\{.*\});', text, re.S).group(1))
    for name, body in MARKS.items():
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">{body}</svg>'
        open(os.path.join(icons, name + '.svg'), 'w', encoding='utf-8', newline='\n').write(svg + '\n')
        m[name] = measure(svg)
        print(name, m[name])
    m['youtube'] = m.get('youtube') or measure(open(os.path.join(icons, 'youtube.svg'), encoding='utf-8').read())
    open(mfile, 'w', encoding='utf-8', newline='\n').write(
        '/* Visible SVG ink measured at build time (LG marks added by make_cleanframe_marks.py). */\nwindow.FrameIconMetrics = '
        + json.dumps(m, separators=(',', ':')) + ';\n')


if __name__ == '__main__':
    main(sys.argv[1])
