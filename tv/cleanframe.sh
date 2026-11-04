#!/bin/sh
# CleanFrame (ported to LG, see look/cleanframe-lg) as the Home page, in place of CleanYourTV's launcher page. CleanYourTV keeps
# doing the rest: its service (app list, launch, inputs) and the boot scripts that mount the page over LG's Home.
#   sh cleanframe.sh install   back up CleanYourTV's page once, put CleanFrame in its place, reload Home
#   sh cleanframe.sh check     the boot hook: put CleanFrame back if a CleanYourTV update replaced the page (reloads Home then)
#   sh cleanframe.sh undo      CleanYourTV's own launcher page back
# CleanFrame's files: /media/developer/lgtv-tune/cleanframe/ (copied there by .\lgtv.ps1 cleanframe).
export PATH=/usr/bin:/usr/sbin:/bin:/sbin:$PATH
L=/media/developer/cleanyourtv
CF=/media/developer/lgtv-tune/cleanframe
BK=$L/app.cytv-backup
ON=/media/developer/lgtv-tune/cleanframe.on
[ -d "$L/app" ] || { echo "CleanYourTV is not installed"; exit 1; }

is_cf() { grep -q '<title>CleanFrame</title>' "$L/app/index.html" 2>/dev/null; }

put() {
  [ -f "$CF/index.html" ] || { echo "CleanFrame files missing in $CF"; exit 1; }
  # back up CleanYourTV's own page, once (never a CleanFrame page)
  if [ ! -d "$BK" ] && ! is_cf; then cp -a "$L/app" "$BK" && echo "backed up CleanYourTV's page to $BK"; fi
  # app/: what CleanYourTV copies over the Home folder at every boot (top-level files only); keep its icons for the appinfo
  rm -f "$L"/app/*.html "$L"/app/*.js "$L"/app/*.css
  cp "$CF"/index.html "$CF"/main.js "$CF"/device.js "$CF"/style.css "$L/app/"
  # the Home folder that is mounted over LG's Home: CleanFrame with its assets
  rm -f "$L"/home-overlay/*.html "$L"/home-overlay/*.js "$L"/home-overlay/*.css
  cp "$CF"/index.html "$CF"/main.js "$CF"/device.js "$CF"/style.css "$L/home-overlay/"
  rm -rf "$L/home-overlay/assets" && cp -r "$CF/assets" "$L/home-overlay/assets"
  touch "$ON"
}

case "${1:-install}" in
  install)
    put
    sh "$L/reload-home.sh" >/dev/null 2>&1
    echo "CleanFrame is Home now" ;;
  check)
    [ -e "$ON" ] || exit 0
    if ! is_cf || ! grep -q '<title>CleanFrame</title>' "$L/home-overlay/index.html" 2>/dev/null || [ ! -d "$L/home-overlay/assets" ]; then
      put
      sh "$L/reload-home.sh" >/dev/null 2>&1
      echo "CleanFrame put back after a change to CleanYourTV's page"
    fi ;;
  undo)
    rm -f "$ON"
    [ -d "$BK" ] || { echo "no backup of CleanYourTV's page"; exit 1; }
    rm -rf "$L/app" && cp -a "$BK" "$L/app"
    rm -rf "$L/home-overlay/assets"
    sh "$L/stage-home.sh"
    sh "$L/reload-home.sh" >/dev/null 2>&1
    echo "CleanYourTV's launcher page is back" ;;
  *) echo "usage: $0 install|check|undo" >&2; exit 2 ;;
esac
