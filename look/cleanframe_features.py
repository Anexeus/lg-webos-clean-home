"""Extra features for the LG port of CleanFrame (run after port_cleanframe.py). Each change must match exactly once.

  * Inputs button at the top left, next to the clock (opens CleanFrame's HDMI input list).
  * Top right: All apps, Home settings (CleanFrame's own settings) and TV settings (LG's settings app).
  * Hold OK on an app (on Home or in All apps): Open, Move, Move to start, Remove from Home / Add to Home, Uninstall, Cancel.
    Move: the arrows carry the app along the dock, OK places it, Back puts it back where it was.
  * Uninstall goes through CleanYourTV's installer service and asks first.

    python cleanframe_features.py <cleanframe-lg dir>
"""
import os
import sys

MAIN = [
    # top controls
    ("  var UTIL = { art: ['Art Mode', 'art'], apps: ['All apps', 'apps'], arrange: ['Arrange', 'arrange'], settings: ['Settings', 'settings'] };",
     "  var UTIL = { inputs: ['Inputs', 'inputs'], art: ['Art Mode', 'art'], apps: ['All apps', 'apps'], arrange: ['Arrange', 'arrange'], settings: ['Home settings', 'sliders'], tvsettings: ['TV settings', 'settings'] };\n"
     "  var LEFT_UTILS = ['inputs'], HOLD_MS = 650;"),
    ("  var SVG = {\n",
     "  var SVG = {\n"
     "    inputs: '<path d=\"M10 4.5h7.5a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H10\"/><path d=\"M3.5 12h11M11 8.5l3.5 3.5-3.5 3.5\"/>',\n"
     "    sliders: '<path d=\"M4 6.5h9M17 6.5h3M4 12h3M11 12h9M4 17.5h11M19 17.5h1\"/><circle cx=\"15\" cy=\"6.5\" r=\"2\"/><circle cx=\"9\" cy=\"12\" r=\"2\"/><circle cx=\"17\" cy=\"17.5\" r=\"2\"/>',\n"),
    ("  function utils() { return ['apps', 'settings']; }", "  function utils() { return ['inputs', 'apps', 'settings', 'tvsettings']; }"),
    ("    if (u === 'art') perform('Art Mode', FrameDevice.art);",
     "    if (u === 'inputs') openInputs(true);\n    else if (u === 'tvsettings') perform('TV settings', FrameDevice.settings);\n    else if (u === 'art') perform('Art Mode', FrameDevice.art);"),
    ("  function openInputs() {\n    openAppearance('inputs'); var t = top(); t.inputs = []; loadInputs(t);",
     "  function openInputs(fromHome) {\n    openAppearance('inputs'); var t = top(); t.fromHome = !!fromHome; t.inputs = []; loadInputs(t);"),
    ("utilsEl = $('utils');", "utilsEl = $('utils'), utilsLeftEl = $('utilsLeft'), moveHint = $('moveHint');"),
    ("    U.forEach(function (u, i) { html += utilBtn('util', i, 'util.' + u, icon(UTIL[u][1], '', true) + '<span class=\"u-label\">' + UTIL[u][0] + '</span>', '', UTIL[u][0]); });\n"
     "    setHTML(utilsEl, html);\n"
     "    Array.prototype.forEach.call(utilsEl.querySelectorAll('.u'), function (b) {",
     "    var htmlL = '', clockEl = caption.querySelector('.clock');\n"
     "    U.forEach(function (u, i) { var b = utilBtn('util', i, 'util.' + u, icon(UTIL[u][1], '', true) + '<span class=\"u-label\">' + UTIL[u][0] + '</span>', '', UTIL[u][0]); if (LEFT_UTILS.indexOf(u) >= 0) htmlL += b; else html += b; });\n"
     "    setHTML(utilsEl, html); setHTML(utilsLeftEl, htmlL);\n"
     "    utilsLeftEl.className = utilsEl.className + ' utils-left';\n"
     "    utilsLeftEl.style.left = (caption.offsetLeft + (clockEl ? clockEl.offsetLeft + clockEl.offsetWidth : 120) + 36) + 'px';\n"
     "    Array.prototype.forEach.call(document.querySelectorAll('#utils .u, #utilsLeft .u'), function (b) {"),
    # hold OK
    ("      var f = t.f, h = S.c.home, U = utils(), x = axes(), i = ensureSel();\n      if (S.c.layout === 'list') { listHomeKey(t, k, i, U); return; }",
     "      var f = t.f, h = S.c.home, U = utils(), x = axes(), i = ensureSel();\n"
     "      if (t.moving) { moveKey(t, k, x, i); return; }\n"
     "      if (k === 'hold') { if (f.zone === 'apps' && h.length) appMenu(S.sel, 'home'); return; }\n"
     "      if (S.c.layout === 'list') { listHomeKey(t, k, i, U); return; }"),
    ("      var f = t.f, items = appsItems(), n = items.length, col = f.i % COLS, row = Math.floor(f.i / COLS);\n      if (k === 'back') { pop(); return; }",
     "      var f = t.f, items = appsItems(), n = items.length, col = f.i % COLS, row = Math.floor(f.i / COLS);\n"
     "      if (k === 'hold') { if (f.zone === 'grid' && n) appMenu(items[f.i], 'apps'); return; }\n"
     "      if (k === 'back') { pop(); return; }"),
    ("      else if (k === 'ok') { a = A[t.f.b][0]; pop(); if (a === 'samsung') perform('LG Apps', FrameDevice.home); }",
     "      else if (k === 'ok') { a = A[t.f.b][0]; pop(); if (t.onPick) t.onPick(a); else if (a === 'samsung') perform('LG Apps', FrameDevice.home); }"),
    ("        a.icon = safeIcon(entry.icon);", "        a.icon = safeIcon(entry.icon); a.removable = !!entry.removable;"),
    ("  function press(k) {\n    norm();\n    var t = top();\n    V[t.id].key(t, k);\n    norm();\n    render();\n",
     "  function press(k) {\n    norm();\n    var t = top();\n    V[t.id].key(t, k);\n    norm();\n    render();\n    renderMoveHint();\n"),
    ("    press(k);\n  });\n  document.addEventListener('keyup', function (ev) { delete heldKeys[ev.keyCode]; });\n  window.addEventListener('blur', function () { heldKeys = {}; });",
     "    if (k === 'ok' && holdable()) { clearTimeout(holdTimer); holdTimer = setTimeout(function () { holdTimer = 0; press('hold'); }, HOLD_MS); return; }\n"
     "    press(k);\n  });\n"
     "  document.addEventListener('keyup', function (ev) {\n"
     "    if (holdTimer && KEYS[ev.keyCode] === 'ok') { clearTimeout(holdTimer); holdTimer = 0; press('ok'); }\n"
     "    delete heldKeys[ev.keyCode];\n  });\n"
     "  window.addEventListener('blur', function () { heldKeys = {}; clearTimeout(holdTimer); holdTimer = 0; });"),
    ("  initialise();\n", "  initialise();\n  setTimeout(refreshCatalog, 1500); /* LG port: which apps can be uninstalled */\n"),
]
ALL = [("t.group === 'inputs' ? 'TV' : 'Settings'", "t.group === 'inputs' ? (t.fromHome ? 'Home' : 'TV') : 'Settings'")]

# new functions, inserted before the Dispatch section
FUNCS = r"""
  /* ---------- LG port: hold OK on an app ---------- */
  var holdTimer = 0;
  function holdable() {
    var t = top();
    if (t.id === 'home') return t.f.zone === 'apps' && !t.moving && S.c.home.length > 0;
    return t.id === 'apps' && t.f.zone === 'grid' && appsItems().length > 0;
  }
  function choose(title, line, actions, onPick) {
    push({ id: 'message', msg: 'menu', content: { title: title, line: line, note: '', actions: actions }, onPick: onPick, f: { b: 0 } });
  }
  function appMenu(id, from) {
    var a = app(id), on = onHome(id), acts = [['open', 'Open']];
    if (!a) return;
    if (from === 'home') acts.push(['move', 'Move'], ['first', 'Move to start']);
    acts.push(on ? ['remove', 'Remove from Home'] : ['add', 'Add to Home']);
    if (a.removable) acts.push(['uninstall', 'Uninstall']);
    acts.push(['cancel', 'Cancel']);
    choose(a.name, on ? 'Position ' + (S.c.home.indexOf(id) + 1) + ' of ' + S.c.home.length + ' on Home.' : 'Not on Home.', acts, function (k) {
      var h, t;
      if (k === 'open') launch(id);
      else if (k === 'move') { t = top(); if (t.id === 'home') { t.moving = { id: id, orig: S.c.home.slice(), snap: snap() }; t.f.zone = 'apps'; setSel(id); } }
      else if (k === 'first') { h = without(S.c.home, id); h.unshift(id); if (homeMove(h, id, snap())) setSel(id); }
      else if (k === 'remove') { if (!homeRemove(id) && S.note) message(a.name, S.note); else ensureSel(); }
      else if (k === 'add') { if (!homeAdd(id) && S.note) message(a.name, S.note); }
      else if (k === 'uninstall') confirmUninstall(id);
    });
  }
  function moveKey(t, k, x, i) {
    var m = t.moving, h = S.c.home.slice(), d = k === x.prev ? -1 : k === x.next ? 1 : 0, tmp;
    if (d) {
      if (i + d < 0 || i + d >= h.length) return;
      tmp = h[i + d]; h[i + d] = h[i]; h[i] = tmp;
      if (write(next(h, S.c.recent.slice()), 'Move ' + app(m.id).name)) setSel(m.id);
    } else if (k === 'ok') {
      if (!same(m.orig, S.c.home)) S.undo.push({ label: 'Move ' + app(m.id).name, snap: m.snap });
      t.moving = null;
    } else if (k === 'back') {
      write(next(m.orig.slice(), S.c.recent.slice()), 'Move cancelled'); setSel(m.id); t.moving = null;
    }
  }
  function renderMoveHint() {
    var t = S.stack[0], m = t.moving && top() === t;
    if (m) moveHint.textContent = 'Moving ' + app(t.moving.id).name + '   ·   arrows move it, OK places it, Back cancels';
    stage.classList[m ? 'add' : 'remove']('is-moving');
  }
  function confirmUninstall(id) {
    var a = app(id);
    choose('Uninstall ' + a.name + '?', 'It is removed from the TV. You can install it again from the LG Content Store or the Homebrew Channel.',
      [['cancel', 'Cancel'], ['uninstall', 'Uninstall']], function (k) {
        if (k !== 'uninstall') return;
        perform('Uninstall ' + a.name, function (done) {
          FrameDevice.uninstall(a.appId, function (err) {
            var h;
            if (!err && onHome(id)) { h = without(S.c.home, id); if (h.length) write(next(h, without(S.c.recent, id)), 'Uninstall ' + a.name); ensureSel(); }
            if (!err) refreshCatalog();
            done(err);
          });
        });
      });
  }

  /* ---------- Dispatch ---------- */"""

CSS = """
/* ---------- LG port: Inputs at the top left, hold-OK move ---------- */
.utils-left{right:auto!important;top:72px!important;bottom:auto!important;flex-direction:row!important}
.move-hint{position:absolute;left:50%;bottom:428px;transform:translateX(-50%);padding:14px 32px;border-radius:32px;background:rgba(16,20,24,.58);color:#f6f1e7;font-size:28px;font-weight:500;letter-spacing:-.2px;white-space:nowrap;opacity:0;transition:opacity 160ms linear;pointer-events:none;z-index:5}
.is-moving .move-hint{opacity:1}
.is-moving .plate{box-shadow:inset 0 0 0 3px rgba(255,255,255,.9)}
"""


def sub_once(s, old, new, what):
    n = s.count(old)
    if n != 1:
        raise SystemExit(f'{what}: expected one match, found {n}: {old[:80]!r}')
    return s.replace(old, new)


def main(d):
    p = os.path.join(d, 'main.js')
    s = open(p, encoding='utf-8').read()
    if 'LG port: hold OK' in s:
        print('features already in'); return
    for old, new in MAIN:
        s = sub_once(s, old, new, 'main.js')
    for old, new in ALL:
        if old not in s:
            raise SystemExit('main.js: not found ' + old)
        s = s.replace(old, new)
    s = sub_once(s, '\n  /* ---------- Dispatch ---------- */', FUNCS, 'main.js')
    open(p, 'w', encoding='utf-8', newline='\n').write(s)

    p = os.path.join(d, 'index.html')
    h = open(p, encoding='utf-8').read()
    h = sub_once(h, '<nav class="utils" id="utils" aria-label="Home controls"></nav>',
                 '<nav class="utils" id="utils" aria-label="Home controls"></nav>\n'
                 '          <nav class="utils utils-left" id="utilsLeft" aria-label="Inputs"></nav>\n'
                 '          <div class="move-hint" id="moveHint" aria-live="polite"></div>', 'index.html')
    open(p, 'w', encoding='utf-8', newline='\n').write(h)

    p = os.path.join(d, 'style.css')
    c = open(p, encoding='utf-8').read()
    if 'LG port: Inputs' not in c:
        open(p, 'a', encoding='utf-8', newline='\n').write(CSS)
    print('features added')


if __name__ == '__main__':
    main(sys.argv[1])
