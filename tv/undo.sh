#!/bin/sh
# Undo tune.sh for this boot: start the services again, give LG back its preload policy, switch zram off.
# The Home bar order is not undone (it is LG's own setting): change it with Edit App List on the Home screen.
# The boot hook is left in place; to stop it re-applying at the next boot: touch /media/developer/lgtv-tune/DISABLE
# (or .\lgtv.ps1 remove on the PC, which deletes everything).
export PATH=/usr/bin:/usr/sbin:/bin:/sbin:$PATH
D=$(cd "$(dirname "$0")" && pwd)
. "$D/lgtv-tune.conf"
LOG=/var/lib/webosbrew/lgtv-tune.log
RUN=/tmp/lgtv-tune
log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }
luna() { timeout 20 script -q -c "luna-send -n 1 $1 '$2'" /dev/null </dev/null 2>/dev/null | tr -d '\r'; }
log "== undo"

for u in $STOP_UNITS; do systemctl --no-block start "$u.service" && log "started $u"; done

if [ -s "$RUN/preload.orig.json" ]; then
  node -e '
    var j = JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"));
    (j.applications || []).forEach(function (a) {
      console.log(JSON.stringify({ application: { id: a.id, isEnabled: a.isEnabled, isAllowed: a.isAllowed,
        preloadMode: a.preloadMode, preloadType: a.preloadType }, permanent: false }));
    });' "$RUN/preload.orig.json" |
    while read -r body; do
      case " $NO_PRELOAD " in *" $(echo "$body" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p') "*) ;; *) continue ;; esac
      luna luna://com.webos.service.preloadmanager/setPreloadPolicy "$body" >/dev/null && log "preload restored: $body"
    done
fi

if grep -q '^/dev/zram0 ' /proc/swaps; then
  # pages come back into RAM or go to the eMMC swap: needs free memory, can take a while
  swapoff /dev/zram0 && echo 1 >/sys/block/zram0/reset && log "zram off"
fi

# appinfo.json mounts left by version 1 of this script (hiding apps that way did not work: the app list is read at boot)
for m in $(awk '$2 ~ /^\/usr\/palm\/applications\/[^\/]+\/appinfo\.json$/ {print $2}' /proc/mounts); do umount "$m" && log "unhidden: $m"; done

log "== undo done (a reboot also restores LG Home's app list)"
