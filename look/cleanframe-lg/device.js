/* CleanFrame on LG webOS: the FrameDevice interface of CleanFrame's Tizen device.js, backed by the CleanYourTV service that runs
   on this rooted TV (http://127.0.0.1:8765): its app list, app launch and HDMI input list. Same names and callbacks as the
   original, so main.js is unchanged apart from the app list. ES5, like the rest of CleanFrame. */
(function () {
  'use strict';
  var API = 'http://127.0.0.1:8765';
  /* CleanFrame brand id (an SVG in assets/icons/) -> LG app id */
  var IDS = {
    youtube: 'youtube.leanback.v4', iptv: 'com.smarterstvplayers.net', hdmi1: 'com.webos.app.hdmi1',
    browser: 'com.webos.app.browser', media: 'com.webos.app.mediadiscovery', lgstore: 'com.webos.app.discovery',
    homebrew: 'org.webosbrew.hbchannel', privacy: 'ooo.lew.lifesgoodwithoutspying'
  };
  /* LG ids of apps CleanFrame has a mark for, should they be installed later */
  var EXTRA_BRANDS = {
    netflix: 'netflix', amazon: 'primevideo', 'com.disney.disneyplus-prod': 'disneyplus', 'com.apple.appletv': 'appletv',
    'spotify-beehive': 'spotify', 'com.hbo.hbomax': 'hbomax', 'com.stremio.app': 'stremio', 'com.webos.app.hdmi2': 'hdmi1',
    'com.webos.app.hdmi3': 'hdmi1', 'com.webos.app.hdmi4': 'hdmi1'
  };
  /* never offered: LG's own system parts and the root autostart */
  var INTERNAL = ['com.webos.app.home', 'org.webosbrew.safeupdate', 'com.cleanyourtv.manager', 'com.lgtv.homesplash', 'com.webos.app.camera', 'com.webos.app.homeconnect',
    'com.webos.app.lifeonscreen', 'com.webos.app.sportsteamsettings'];

  function failure(text, detail) { return { message: text || 'The TV could not open this screen.', detail: detail || 'Try again, or press Home on the remote.' }; }
  function bounded(done, timeout) {
    var finished = false, timer = setTimeout(function () { finish(failure('The TV did not respond. Please try again.')); }, timeout || 8000);
    function finish(err, value) { if (finished) return; finished = true; clearTimeout(timer); done(err, value); }
    return finish;
  }
  function request(method, path, body, done) {
    var x = new XMLHttpRequest();
    try {
      x.open(method, API + path, true);
      x.onload = function () {
        var j = null;
        try { j = JSON.parse(x.responseText); } catch (e) { /* not JSON */ }
        if (x.status >= 200 && x.status < 300 && j) done(null, j); else done(failure('The TV service answered ' + x.status + '.'));
      };
      x.onerror = function () { done(failure('The home service on the TV is not running.', 'It starts with the TV; wait a moment and try again.')); };
      x.send(body ? JSON.stringify(body) : null);
    } catch (e) { done(failure('The home service on the TV is not reachable.')); }
  }

  function launchApp(id, done) {
    var finish = bounded(done);
    request('POST', '/api/launch', { id: id }, function (err, j) {
      if (err) return finish(err);
      if (j && j.returnValue === false) return finish(failure('The TV could not open this app.', j.errorText || ''));
      finish(null);
    });
  }
  function launch(brand, done) {
    if (!IDS[brand]) { done({ message: 'This app has no launch target.' }); return; }
    launchApp(IDS[brand], done);
  }
  /* LG has no Art Mode: kept so the interface stays complete */
  function art(done) { done(failure('Art Mode is a Samsung feature.', '')); }
  function home(done) { launchApp('com.webos.app.discovery', done); }
  function settings(done) { launchApp('com.palm.app.settings', done); }

  function apps(done) {
    var finish = bounded(done, 20000);
    request('GET', '/api/apps', null, function (err, j) {
      if (err) return finish(err);
      var known = {}, hidden = (j.config && j.config.hidden) || [], result = [], seen = {}, order = Object.keys(IDS);
      order.forEach(function (brand) { known[IDS[brand]] = brand; });
      (j.apps || []).forEach(function (a) {
        if (!a || !a.id || seen[a.id] || INTERNAL.indexOf(a.id) >= 0) return;
        var brand = known[a.id] || EXTRA_BRANDS[a.id] || '';
        if (!brand && hidden.indexOf(a.id) >= 0) return;
        seen[a.id] = true;
        result.push({
          appId: a.id, name: String(a.title || a.id), brand: brand, removable: a.removable === true,
          icon: API + '/icon/' + encodeURIComponent(a.id) + (a.iv ? '?v=' + a.iv : ''),
          rank: known[a.id] ? order.indexOf(known[a.id]) : 30
        });
      });
      result.sort(function (a, b) { return a.rank - b.rank || a.name.toLowerCase().localeCompare(b.name.toLowerCase()); });
      finish(null, result);
    });
  }

  /* uninstall through CleanYourTV's installer route (it refuses the Homebrew Channel and system apps) */
  function uninstall(id, done) {
    var finish = bounded(done, 60000);
    request('POST', '/api/apps/uninstall', { id: id }, function (err, j) {
      if (err) return finish(err);
      if (!j || j.returnValue !== true) return finish(failure('The TV could not uninstall this app.', (j && (j.error || j.errorText)) || ''));
      finish(null);
    });
  }

  /* Free memory: close every app running in the background (never Home), then report free memory before and after */
  function freeMemory(done) {
    var finish = bounded(done, 20000);
    request('GET', '/api/zram', null, function (e1, before) {
      request('GET', '/api/running', null, function (e2, running) {
        var n = running && running.apps ? running.apps.length : 0;
        request('POST', '/api/running/close', { all: true }, function (err) {
          if (err) return finish(err);
          setTimeout(function () {
            request('GET', '/api/zram', null, function (e3, after) {
              finish(null, { closed: n, before: before && before.memAvailable, after: after && after.memAvailable });
            });
          }, 1500);
        });
      });
    });
  }

  var sourceCancel = null;
  function cancelSource() { if (sourceCancel) sourceCancel(); }
  function sources(done) {
    var finish = bounded(done);
    request('GET', '/api/inputs', null, function (err, j) {
      if (err) return finish(err);
      var list = [];
      (j.devices || []).forEach(function (d) {
        var m = d && /hdmi(\d+)$/.exec(d.appId || '');
        if (!m) return;
        var n = Number(m[1]);
        list.push({ number: n, name: d.label || ('HDMI ' + n), connected: !!(d.connected || d.hdmiPlugIn), active: !!d.activate, source: d });
      });
      list.sort(function (a, b) { return a.number - b.number; });
      finish(null, list);
    });
  }
  function setSource(port, done) {
    cancelSource();
    if (typeof port !== 'number' || !isFinite(port) || port < 1 || Math.floor(port) !== port) { done({ message: 'This HDMI input is not available.' }); return; }
    var finished = false;
    function finish(err, value) { if (finished) return; finished = true; if (sourceCancel === cancel) sourceCancel = null; done(err, value); }
    function cancel() { finish({ message: 'Input change cancelled.', cancelled: true }); }
    sourceCancel = cancel;
    launchApp('com.webos.app.hdmi' + port, function (err) { finish(err, { number: port }); });
  }

  /* tell the CleanYourTV service that a Home page started (it only logs it) */
  request('POST', '/api/frontend-ok', { version: 'cleanframe-lg' }, function () {});

  window.FrameDevice = { launch: launch, launchApp: launchApp, art: art, home: home, settings: settings, apps: apps, uninstall: uninstall, freeMemory: freeMemory, sources: sources, setSource: setSource, cancelSource: cancelSource };
}());
