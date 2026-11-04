"""CleanFrame-style dock icons: a white glyph with the app's name under it on a transparent background.

The launcher's dock tile is made see-through by patch-launcher.sh, so these float on the glass dock exactly like CleanFrame's,
and the focused one gets a soft light glass box behind it. Size: twice the dock tile of the lgtv-cleanframe theme (dock.w x dock.h
= 205 x 170), drawn with object-fit: fill, so the ratio must match the theme.

Glyphs: YouTube is the Simple Icons path CleanFrame ships (CC0); Apps is CleanFrame's drawing (MIT); the rest are drawn here in
the same 24-unit, 1.6-stroke line style. Names are set in Geist (SIL OFL 1.1, from CleanFrame's assets).

    python make_glass_icons.py <out_dir> <Geist ttf>
"""
import os
import sys

import resvg_py

TILE_W, TILE_H = 205, 170          # CSS px, must match theme dock.w / dock.h
SCALE = 2                          # render at 2x for the 4K panel
W, H = TILE_W * SCALE, TILE_H * SCALE
GLYPH = 62 * SCALE                 # glyph box
GLYPH_TOP = 34 * SCALE
LABEL_Y = 140 * SCALE              # text baseline
LABEL_SIZE = 27 * SCALE

STROKE = 'fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"'
TRI = '<path fill="#fff" d="M10.2 11.2v5.6c0 .5.5.8.9.5l4.3-2.8c.4-.2.4-.8 0-1l-4.3-2.8c-.4-.3-.9 0-.9.5z"/>'

ICONS = {
    'youtube.leanback.v4': ('YouTube', '<path fill="#fff" d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>'),
    'com.smarterstvplayers.net': ('IPTV', f'<g {STROKE}><rect x="2.5" y="7.5" width="19" height="13" rx="2.6"/><path d="m8 3 4 4.2L16 3"/></g>{TRI}'),
    'com.webos.app.browser': ('Browser', f'<g {STROKE}><circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="3.8" ry="9"/><path d="M3.4 9h17.2M3.4 15h17.2"/></g>'),
    'com.webos.app.mediadiscovery': ('Media', f'<g {STROKE}><rect x="2.5" y="4.5" width="19" height="15" rx="3.2"/></g>'
                                     '<path fill="#fff" d="M10 8.6v6.8c0 .6.6.9 1.1.6l5.3-3.4c.5-.3.5-.9 0-1.2l-5.3-3.4c-.5-.3-1.1 0-1.1.6z"/>'),
    'com.webos.app.discovery': ('Apps', f'<g {STROKE}><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/>'
                                '<rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></g>'),
    'org.webosbrew.hbchannel': ('Homebrew', f'<g {STROKE}><path d="M5 9h11v9a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3z"/><path d="M16 11h1.6a2.6 2.6 0 0 1 0 5.2H16"/>'
                                '<path d="M5.2 9A2.6 2.6 0 0 1 7.5 5a3.2 3.2 0 0 1 5.6-.4A2.6 2.6 0 0 1 16 9"/><path d="M9 13v4M12 13v4"/></g>'),
    'ooo.lew.lifesgoodwithoutspying': ('Privacy', f'<g {STROKE}><path d="M12 2.8 4.6 5.8v5.6c0 4.6 3.1 8.4 7.4 9.8 4.3-1.4 7.4-5.2 7.4-9.8V5.8z"/>'
                                       '<path d="m8.6 12.2 2.4 2.4 4.6-4.8"/></g>'),
    'com.cleanyourtv.manager': ('Home setup', f'<g {STROKE}><path d="M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1"/>'
                                '<circle cx="15" cy="6" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="17" cy="18" r="2"/></g>'),
}


def svg_for(label, glyph):
    k = GLYPH / 24
    x = (W - GLYPH) / 2
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <g transform="translate({x:.1f} {GLYPH_TOP}) scale({k:.4f})" opacity="0.96">{glyph}</g>
  <text x="{W / 2}" y="{LABEL_Y}" text-anchor="middle" font-family="Geist" font-weight="500" font-size="{LABEL_SIZE}"
        fill="#fff" fill-opacity="0.94">{label}</text>
</svg>'''


def main(out, font):
    os.makedirs(out, exist_ok=True)
    for app_id, (label, glyph) in ICONS.items():
        png = resvg_py.svg_to_bytes(svg_string=svg_for(label, glyph), font_files=[font], skip_system_fonts=True)
        with open(os.path.join(out, app_id + '.png'), 'wb') as f:
            f.write(bytes(png))
        print('wrote', app_id, label)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
