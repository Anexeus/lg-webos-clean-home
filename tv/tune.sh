#!/bin/sh
# lgtv-tune: reversible debloat + speed tweaks for a rooted LG webOS TV (Homebrew Channel). RAM-only: nothing on the system
# partition is changed. Settings in lgtv-tune.conf next to this script.
#   sh tune.sh apply     everything below (what the boot hook runs a minute after boot)
#   sh tune.sh status    what is applied now
# Undo: sh undo.sh (or delete the boot hook and reboot).
export PATH=/usr/bin:/usr/sbin:/bin:/sbin:$PATH
D=$(cd "$(dirname "$0")" && pwd)
. "$D/lgtv-tune.conf"
LOG=/var/lib/webosbrew/lgtv-tune.log
RUN=/tmp/lgtv-tune
mkdir -p "$RUN"

log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }
# luna-send prints nothing without a terminal on this firmware: give it one with script(1). JSON must not contain single quotes.
# </dev/null: script(1) reads stdin, and inside a `while read` loop it would swallow the rest of the loop's input.
luna() { timeout 20 script -q -c "luna-send -n 1 $1 '$2'" /dev/null </dev/null 2>/dev/null | tr -d '\r'; }
AM=luna://com.webos.service.applicationmanager
PM=luna://com.webos.service.preloadmanager

# keep the log small
[ -f "$LOG" ] && [ "$(wc -c <"$LOG")" -gt 65536 ] && tail -n 300 "$LOG" >"$LOG.tmp" && mv "$LOG.tmp" "$LOG"

do_units() {
  for u in $STOP_UNITS; do
    if [ "$(systemctl is-active "$u.service" 2>/dev/null)" = active ]; then
      systemctl --no-block stop "$u.service" && log "stopped $u"
    fi
  done
}

do_preload() {
  [ -n "$NO_PRELOAD" ] || return 0
  luna $PM/getPreloadPolicy '{}' >"$RUN/preload.now.json"
  # first run of this boot: keep LG's policy so undo.sh can put it back
  [ -s "$RUN/preload.orig.json" ] || cp "$RUN/preload.now.json" "$RUN/preload.orig.json"
  for id in $NO_PRELOAD; do
    body=$(node -e '
      var j = JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"));
      var a = (j.applications || []).filter(function (x) { return x.id === process.argv[2]; })[0];
      if (!a || a.isEnabled === false) process.exit(1);
      console.log(JSON.stringify({ application: { id: a.id, isEnabled: false, isAllowed: a.isAllowed,
        preloadMode: a.preloadMode, preloadType: a.preloadType }, permanent: false }));
    ' "$RUN/preload.now.json" "$id") || continue
    if luna $PM/setPreloadPolicy "$body" | grep -q '"returnValue":true'; then log "preload off: $id"; else log "preload: refused for $id"; fi
  done
}

do_close() {
  [ -n "$CLOSE_APPS" ] || return 0
  fg=$(luna $AM/getForegroundAppInfo '{}' | sed -n 's/.*"appId":"\([^"]*\)".*/\1/p')
  luna $AM/running '{}' >"$RUN/running.json"
  for id in $CLOSE_APPS; do
    [ "$id" = "$fg" ] && continue
    pid=$(node -e '
      var r = JSON.parse(require("fs").readFileSync(process.argv[1], "utf8")).running || [];
      var a = r.filter(function (x) { return x.id === process.argv[2]; })[0];
      if (a && a.processid) console.log(a.processid);
    ' "$RUN/running.json" "$id")
    [ -n "$pid" ] || continue
    if luna $AM/close "{\"processId\":\"$pid\"}" | grep -q '"returnValue":true'; then log "closed $id"; fi
  done
}

do_zram() {
  [ -e /sys/block/zram0/disksize ] || { log "zram: not in this kernel"; return 0; }
  if grep -q '^/dev/zram0 ' /proc/swaps; then return 0; fi
  [ "${ZRAM_MB:-0}" -gt 0 ] 2>/dev/null || return 0
  echo 1 >/sys/block/zram0/reset 2>/dev/null
  grep -q lz4 /sys/block/zram0/comp_algorithm && echo lz4 >/sys/block/zram0/comp_algorithm
  echo $((ZRAM_MB * 1048576)) >/sys/block/zram0/disksize || { log "zram: size refused"; return 1; }
  if mkswap /dev/zram0 >/dev/null 2>&1 && swapon -p 10 /dev/zram0; then
    log "zram on: ${ZRAM_MB} MB lz4, ahead of the eMMC swap"
  else
    echo 1 >/sys/block/zram0/reset
    log "zram: swapon failed"
  fi
}

do_trim() {
  [ "${TRIM:-0}" = 1 ] || return 0
  stamp="$D/trim.last"
  now=$(date +%s)
  last=$(cat "$stamp" 2>/dev/null || echo 0)
  [ $((now - last)) -ge 604800 ] || return 0
  # writable ext4 partitions on the built-in flash, once each, never the key/certificate partitions
  awk '$1 ~ /^\/dev\/mmcblk[0-9]+p[0-9]+$/ && $3 == "ext4" && $4 ~ /(^|,)rw(,|$)/ && $2 !~ /uhdcp|ciplus|authcxt|keystore|\/key/ && !seen[$1]++ {print $2}' /proc/mounts |
    while read -r m; do
      out=$(fstrim -v "$m" 2>&1) && log "trim $out" || log "trim $m failed: $out"
    done
  echo "$now" >"$stamp"
}

# Home bar order. Built-in apps are on the read-only system partition and cannot be uninstalled, and LG's app manager reads
# the app list before any boot hook runs, so they cannot be hidden either. Instead the apps in APPS_FIRST go to the front and
# those in APPS_LAST to the back, through the app manager's own moveLaunchPoint (what Edit App List does). LG keeps the order.
do_order() {
  [ -n "$APPS_FIRST$APPS_LAST" ] || return 0
  luna $AM/listLaunchPoints '{}' >"$RUN/lp.json"
  node -e '
    var lp = JSON.parse(require("fs").readFileSync(process.argv[1], "utf8")).launchPoints || [];
    var first = process.argv[2].split(" ").filter(Boolean), last = process.argv[3].split(" ").filter(Boolean);
    // LG pins the Apps (Content Store) button at the front and refuses to move it
    lp = lp.filter(function (x) { return x.id !== "com.webos.app.discovery"; });
    var ids = lp.map(function (x) { return x.id; });
    var pick = function (want) { return want.filter(function (id) { return ids.indexOf(id) >= 0; }); };
    var order = pick(first);
    ids.forEach(function (id) { if (order.indexOf(id) < 0 && last.indexOf(id) < 0) order.push(id); });
    order = order.concat(pick(last));
    // one move per launch point, front to back: the app manager inserts at the position given
    var pos = 0;
    order.forEach(function (id) {
      lp.forEach(function (x) { if (x.id === id) console.log(x.launchPointId + " " + pos++); });
    });
  ' "$RUN/lp.json" "$APPS_FIRST" "$APPS_LAST" |
    while read -r lpid pos; do
      luna $AM/moveLaunchPoint "{\"launchPointId\":\"$lpid\",\"position\":$pos}" | grep -q '"returnValue":true' || log "order: $lpid refused"
    done
  log "home order: first [$APPS_FIRST] last [$APPS_LAST]"
}

status() {
  echo "== services"; for u in $STOP_UNITS; do echo "  $u: $(systemctl is-active "$u.service" 2>/dev/null)"; done
  echo "== preload (enabled = LG keeps it half-started in the background)"
  luna $PM/getPreloadPolicy '{}' | node -e '
    var s = ""; process.stdin.on("data", function (d) { s += d; }).on("end", function () {
      JSON.parse(s).applications.filter(function (a) { return a.isAllowed; })
        .forEach(function (a) { console.log("  " + a.id + ": " + (a.isEnabled ? "enabled" : "off")); });
    });'
  echo "== home bar order"
  luna $AM/listLaunchPoints '{}' | node -e '
    var s = ""; process.stdin.on("data", function (d) { s += d; }).on("end", function () {
      console.log("  " + JSON.parse(s).launchPoints.map(function (x) { return x.title; }).join(" | "));
    });'
  echo "== memory"; free -m | sed 's/^/  /'
  echo "== swap"; sed 's/^/  /' /proc/swaps
  echo "== last trim"; [ -f "$D/trim.last" ] && date -d "@$(cat "$D/trim.last")" '+  %F %T' 2>/dev/null || echo "  never"
}

case "${1:-apply}" in
  apply)
    log "== apply"
    do_order; do_units; do_preload; do_close; do_zram; do_trim
    # Home: CleanFrame (cleanframe.sh), put back if an update of CleanYourTV replaced the page; otherwise CleanYourTV's own
    # page with the CleanFrame dock style (patch-launcher.sh)
    if [ -e "$D/cleanframe.on" ]; then
      sh "$D/cleanframe.sh" check | while read -r l; do log "cleanframe: $l"; done
    elif [ -f "$D/patch-launcher.sh" ]; then
      sh "$D/patch-launcher.sh" check | while read -r l; do log "launcher: $l"; done
    fi
    log "== done" ;;
  status) status ;;
  *) echo "usage: $0 apply|status" >&2; exit 2 ;;
esac
