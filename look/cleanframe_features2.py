"""More features for the LG port of CleanFrame (run after cleanframe_features.py). Each change must match exactly once.

  * Free memory, next to Inputs at the top left: closes every app running in the background (never Home) and says how much
    memory is free before and after.

    python cleanframe_features2.py <cleanframe-lg dir>
"""
import os
import sys

MAIN = [
    ("  var LEFT_UTILS = ['inputs'], HOLD_MS = 650;",
     "  var LEFT_UTILS = ['inputs', 'clean'], HOLD_MS = 650;\n  UTIL.clean = ['Free memory', 'clean'];"),
    ("  var SVG = {\n",
     "  var SVG = {\n"
     "    clean: '<path d=\"M12 3.5v3M12 17.5v3M3.5 12h3M17.5 12h3M6 6l2.1 2.1M15.9 15.9 18 18M18 6l-2.1 2.1M8.1 15.9 6 18\"/><circle cx=\"12\" cy=\"12\" r=\"2.6\"/>',\n"),
    ("  function utils() { return ['inputs', 'apps', 'settings', 'tvsettings']; }",
     "  function utils() { return ['inputs', 'clean', 'apps', 'settings', 'tvsettings']; }"),
    ("    if (u === 'inputs') openInputs(true);\n",
     "    if (u === 'inputs') openInputs(true);\n"
     "    else if (u === 'clean') perform('Free memory', function (done) {\n"
     "      FrameDevice.freeMemory(function (err, r) {\n"
     "        if (!err) message('Memory cleaned', 'Closed ' + r.closed + (r.closed === 1 ? ' app' : ' apps') + ' running in the background.',\n"
     "          r.before && r.after ? 'Free memory: ' + r.before + ' MB before, ' + r.after + ' MB now.' : '');\n"
     "        done(err);\n"
     "      });\n"
     "    });\n"),
]


def main(d):
    p = os.path.join(d, 'main.js')
    s = open(p, encoding='utf-8').read()
    if "UTIL.clean = " in s:
        print('features2 already in'); return
    for old, new in MAIN:
        n = s.count(old)
        if n != 1:
            raise SystemExit(f'expected one match, found {n}: {old[:80]!r}')
        s = s.replace(old, new)
    open(p, 'w', encoding='utf-8', newline='\n').write(s)
    print('features2 added')


if __name__ == '__main__':
    main(sys.argv[1])
