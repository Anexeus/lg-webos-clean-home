"""Port CleanFrame's main.js from Samsung Tizen to this LG TV: the app list, the visible Samsung wording, the Art Mode control and
the icon URLs. Everything else in CleanFrame (layout, dock, glass, wallpapers, settings, arrange, all apps) is unchanged.
Re-runnable on a fresh copy of CleanFrame's app/ folder (each replacement must match exactly once, or nothing is written).

    python port_cleanframe.py <cleanframe-lg dir>
"""
import os
import sys

LG_APPS = """  var PRIMARY_APPS = [
    { id: 'youtube', name: 'YouTube', mark: true, appId: 'youtube.leanback.v4' },
    { id: 'iptv', name: 'IPTV', mark: true, appId: 'com.smarterstvplayers.net' },
    { id: 'hdmi1', name: 'HDMI 1', mark: true, appId: 'com.webos.app.hdmi1' },
    { id: 'browser', name: 'Browser', mark: true, appId: 'com.webos.app.browser' },
    { id: 'media', name: 'Media', mark: true, appId: 'com.webos.app.mediadiscovery' },
    { id: 'lgstore', name: 'LG Apps', mark: true, appId: 'com.webos.app.discovery' },
    { id: 'homebrew', name: 'Homebrew', mark: true, appId: 'org.webosbrew.hbchannel' },
    { id: 'privacy', name: 'Privacy', mark: true, appId: 'ooo.lew.lifesgoodwithoutspying' }
  ];
  /* brands with a mark in assets/icons/ that a saved app record may carry */
  var MARKS = ['hbomax', 'spotify', 'tubi', 'netflix', 'primevideo', 'disneyplus', 'appletv', 'stremio', 'hdmi1', 'homesetup'];
"""

REPLACEMENTS = [
    # the app list: LG apps instead of the Samsung/Australian streaming apps
    (None, None),  # placeholder for the PRIMARY_APPS block (handled below)
    ("brand: ['hbomax', 'spotify', 'tubi'].indexOf(a.brand) >= 0 ? a.brand : '', mark: ['hbomax', 'spotify', 'tubi'].indexOf(a.brand) >= 0,",
     "brand: MARKS.indexOf(a.brand) >= 0 ? a.brand : '', mark: MARKS.indexOf(a.brand) >= 0,"),
    # app icons come from the TV's home service
    ("/^(?:\\/[^\\/]|file:\\/\\/\\/|wgt-package:\\/\\/\\/)/.test(path)",
     "/^(?:\\/[^\\/]|file:\\/\\/\\/|wgt-package:\\/\\/\\/|http:\\/\\/127\\.0\\.0\\.1:8765\\/)/.test(path)"),
    # no Art Mode on LG: the top-right controls are All apps and Settings
    ("function utils() { return ['art', 'apps', 'settings']; }", "function utils() { return ['apps', 'settings']; }"),
    # wording
    ("line: 'Open Samsung Home?', note: '', actions: [['stay', 'Stay'], ['samsung', 'Samsung Home']]",
     "line: 'Open the LG Content Store?', note: '', actions: [['stay', 'Stay'], ['samsung', 'LG Apps']]"),
    ("{ id: 'samsung', label: 'Samsung', value: 'Home and TV settings' }", "{ id: 'samsung', label: 'TV', value: 'Inputs, LG apps and TV settings' }"),
    ("samsung: 'Samsung', inputs: 'Inputs'", "samsung: 'TV', inputs: 'Inputs'"),
    ("{ action: 'samsung.home', label: 'Samsung Home', description: 'Open Samsung’s Home screen' }",
     "{ action: 'samsung.home', label: 'LG Apps', description: 'Open the LG Content Store' }"),
    ("perform('Samsung Home', FrameDevice.home); }", "perform('LG Apps', FrameDevice.home); }"),
    ("else if (item.action === 'samsung.home') perform('Samsung Home', FrameDevice.home);",
     "else if (item.action === 'samsung.home') perform('LG Apps', FrameDevice.home);"),
]
ALL = [("t.group === 'inputs' ? 'Samsung' : 'Settings'", "t.group === 'inputs' ? 'TV' : 'Settings'")]  # every occurrence


def main(d):
    p = os.path.join(d, 'main.js')
    s = open(p, encoding='utf-8').read()
    if "appId: 'youtube.leanback.v4'" in s:
        print('already ported'); return
    a = s.index('  var PRIMARY_APPS = [')
    b = s.index('  ];\n', a) + len('  ];\n')
    s = s[:a] + LG_APPS + s[b:]
    for old, new in REPLACEMENTS[1:]:
        n = s.count(old)
        if n != 1:
            raise SystemExit(f'expected one match, found {n}: {old[:70]}')
        s = s.replace(old, new)
    for old, new in ALL:
        if old not in s:
            raise SystemExit('not found: ' + old)
        s = s.replace(old, new)
    left = [l.strip()[:100] for l in s.splitlines() if 'Samsung' in l]
    open(p, 'w', encoding='utf-8', newline='\n').write(s)
    print('ported main.js; lines still mentioning Samsung:', left)


if __name__ == '__main__':
    main(sys.argv[1])
