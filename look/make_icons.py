"""Apple TV-style full-tile icons for the CleanYourTV launcher.

Each icon is an opaque 1000 x 600 PNG (the launcher's dock tiles are 5:3, its grid tiles a little wider; the middle is kept) with
a diagonal gradient, a soft top highlight and a centred white glyph in CleanFrame's line style (24-unit viewBox, 1.6 stroke).
The YouTube mark is the Simple Icons path (CC0) that CleanFrame ships; the Apps glyph is CleanFrame's own drawing (MIT); the other
glyphs are drawn here.

    python make_icons.py <out_dir>
Writes <out_dir>/<app id>.png, which goes to /media/developer/cleanyourtv/icons/tile/ on the TV.
"""
import os
import sys

import resvg_py

W, H = 1000, 600
GLYPH = 230  # px, the glyph's box

STROKE = 'fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"'

ICONS = {
    # YouTube: white tile, red mark (the play triangle is cut out of the path, so the tile shows through)
    'youtube.leanback.v4': dict(
        bg=('#ffffff', '#e9e9ee'),
        glyph='<path fill="#ff0033" d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>',
        scale=1.15,
        gloss=0.0,
    ),
    # IPTV Smarters: a TV with an antenna and a play mark
    'com.smarterstvplayers.net': dict(
        bg=('#7b4dff', '#3a12b8'),
        glyph=f'<g {STROKE}><rect x="2.5" y="7.5" width="19" height="13" rx="2.6"/><path d="m8 3 4 4.2L16 3"/></g>'
        '<path fill="#fff" d="M10.2 11.2v5.6c0 .5.5.8.9.5l4.3-2.8c.4-.2.4-.8 0-1l-4.3-2.8c-.4-.3-.9 0-.9.5z"/>',
    ),
    # Web Browser: a globe
    'com.webos.app.browser': dict(
        bg=('#3aa0ff', '#0846c9'),
        glyph=f'<g {STROKE}><circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="3.8" ry="9"/>'
        '<path d="M3.4 9h17.2M3.4 15h17.2"/></g>',
    ),
    # Media Player (USB / network files): a play button in a frame
    'com.webos.app.mediadiscovery': dict(
        bg=('#ffb02e', '#ff2d6f'),
        glyph=f'<g {STROKE}><rect x="2.5" y="4.5" width="19" height="15" rx="3.2"/></g>'
        '<path fill="#fff" d="M10 8.6v6.8c0 .6.6.9 1.1.6l5.3-3.4c.5-.3.5-.9 0-1.2l-5.3-3.4c-.5-.3-1.1 0-1.1.6z"/>',
    ),
    # Apps (LG Content Store): CleanFrame's apps glyph
    'com.webos.app.discovery': dict(
        bg=('#4a4a50', '#18181b'),
        glyph=f'<g {STROKE}><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/>'
        '<rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></g>',
    ),
    # Homebrew Channel: a mug with foam
    'org.webosbrew.hbchannel': dict(
        bg=('#ffc23d', '#f26b00'),
        glyph=f'<g {STROKE}><path d="M5 9h11v9a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3z"/><path d="M16 11h1.6a2.6 2.6 0 0 1 0 5.2H16"/>'
        '<path d="M5.2 9A2.6 2.6 0 0 1 7.5 5a3.2 3.2 0 0 1 5.6-.4A2.6 2.6 0 0 1 16 9"/><path d="M9 13v4M12 13v4"/></g>',
    ),
    # CleanYourTV manager: sliders
    'com.cleanyourtv.manager': dict(
        bg=('#8e8e96', '#2c2c30'),
        glyph=f'<g {STROKE}><path d="M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1"/>'
        '<circle cx="15" cy="6" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="17" cy="18" r="2"/></g>',
    ),
    # Life's Good Without Spying: a shield with a tick
    'ooo.lew.lifesgoodwithoutspying': dict(
        bg=('#3ddc84', '#0a6b34'),
        glyph=f'<g {STROKE}><path d="M12 2.8 4.6 5.8v5.6c0 4.6 3.1 8.4 7.4 9.8 4.3-1.4 7.4-5.2 7.4-9.8V5.8z"/>'
        '<path d="m8.6 12.2 2.4 2.4 4.6-4.8"/></g>',
    ),
}


def svg_for(spec):
    top, bottom = spec['bg']
    s = GLYPH * spec.get('scale', 1)
    k = s / 24
    x, y = (W - s) / 2, (H - s) / 2
    gloss = spec.get('gloss', 0.16)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/>
    </linearGradient>
    <linearGradient id="gloss" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#fff" stop-opacity="{gloss}"/><stop offset="0.55" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <filter id="shadow" filterUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">
      <feDropShadow dx="0" dy="6" stdDeviation="10" flood-color="#000" flood-opacity="0.22"/>
    </filter>
  </defs>
  <rect width="{W}" height="{H}" fill="url(#bg)"/>
  <rect width="{W}" height="{H}" fill="url(#gloss)"/>
  <g filter="url(#shadow)"><g transform="translate({x:.1f} {y:.1f}) scale({k:.4f})">{spec['glyph']}</g></g>
</svg>'''


def main(out):
    os.makedirs(out, exist_ok=True)
    for app_id, spec in ICONS.items():
        png = resvg_py.svg_to_bytes(svg_string=svg_for(spec))
        with open(os.path.join(out, app_id + '.png'), 'wb') as f:
            f.write(bytes(png))
        print('wrote', app_id)


if __name__ == '__main__':
    main(sys.argv[1])
