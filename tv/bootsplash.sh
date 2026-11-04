#!/bin/sh
# Cold boot without LG's Home. With "Home Auto Launch" off (TV Settings > General > System > Additional Settings > Home Settings),
# LG's boot manager (bootd) opens the app named in bootd_last_foreground_app_id.json instead of LG's Home. That file is kept
# naming the splash app (com.lgtv.homesplash: CleanFrame's photo and clock), so a cold boot goes webOS logo -> splash ->
# CleanFrame, and LG's Home never shows. LG's own later writes of that file go to a copy in RAM (a bind mount), so the file on
# flash keeps naming the splash; nothing else of LG's is changed.
#   sh bootsplash.sh boot     the boot hook: pin the splash, then hand over to Home once CleanYourTV has put CleanFrame in place
#   sh bootsplash.sh off      LG's own boot behaviour back (the file names LG's Home again)
#   sh bootsplash.sh status
export PATH=/usr/bin:/usr/sbin:/bin:/sbin:$PATH
SPLASH=com.lgtv.homesplash
P=/var/luna/preferences/bootd_last_foreground_app_id.json
RAM=/tmp/lgtv-bootd-last.json
LOG=/var/lib/webosbrew/lgtv-tune.log
log() { echo "[$(date '+%F %T')] bootsplash: $*" >>"$LOG"; }
luna() { timeout 15 script -q -c "luna-send -n 1 $1 '$2'" /dev/null </dev/null 2>/dev/null | tr -d '\r'; }
AM=luna://com.webos.service.applicationmanager
fg() { luna $AM/getForegroundAppInfo '{}' | sed -n 's/.*"appId":"\([^"]*\)".*/\1/p'; }
installed() { [ -f /media/developer/apps/usr/palm/applications/$SPLASH/appinfo.json ]; }
mounted() { grep -q " $P " /proc/mounts; }

pin() {
  installed || { log "splash app not installed; LG's boot left alone"; return 1; }
  mounted && return 0
  printf '{"lastAppId":"%s"}' "$SPLASH" >"$P.lgtv" && chmod 600 "$P.lgtv" && mv "$P.lgtv" "$P"
  cp "$P" "$RAM" && mount --bind "$RAM" "$P" && log "next cold boot opens the splash"
}

handover() {
  # CleanYourTV mounts CleanFrame over LG's Home and restarts the app manager ("sam restarted" in its boot log), then reopens Home
  # 8 seconds later if nothing is in front. When the splash is in front it leaves it, so do it here.
  for i in $(seq 1 150); do grep -q "sam restarted" /tmp/cleanyourtv-boot.log 2>/dev/null && break; sleep 1; done
  sleep 12
  for i in 1 2 3 4 5 6 7 8 9 10; do
    case "$(fg)" in
      "$SPLASH" | "") luna $AM/launch '{"id":"com.webos.app.home"}' >/dev/null; log "handed over to Home" ;;
      *) break ;;
    esac
    sleep 3
  done
  pid=$(luna $AM/running '{}' | tr '{' '\n' | grep "\"id\":\"$SPLASH\"" | sed -n 's/.*"processid":"\([^"]*\)".*/\1/p')
  [ -n "$pid" ] && luna $AM/close "{\"processId\":\"$pid\"}" >/dev/null && log "splash closed"
}

case "${1:-status}" in
  boot) pin; handover ;;
  off)
    mounted && umount "$P"
    printf '{"lastAppId":"com.webos.app.home"}' >"$P" && log "off: LG's boot behaviour back"
    echo "LG's own boot behaviour is back (turn Home Auto Launch on again in the TV settings if you like)" ;;
  status)
    echo "splash app: $(installed && echo installed || echo missing)"
    echo "on flash:   $(cat "$P" 2>/dev/null)"
    mounted && echo "LG's writes go to RAM ($RAM): $(cat "$RAM")"
    luna luna://com.webos.settingsservice/getSystemSettings '{"category":"general","keys":["homeAutoLaunch"]}' | sed -n 's/.*"homeAutoLaunch":"\([^"]*\)".*/Home Auto Launch: \1 (must be off)/p' ;;
  *) echo "usage: $0 boot|off|status" >&2; exit 2 ;;
esac
