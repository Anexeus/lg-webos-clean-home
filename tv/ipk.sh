#!/bin/sh
# Install / remove apps through LG's own installer (the same call the Homebrew Channel uses).
#   sh ipk.sh install /tmp/app.ipk   install or update an .ipk (homebrew apps from repo.webosbrew.org, your own builds)
#   sh ipk.sh remove <appId>         uninstall a homebrew app or an app from the LG Content Store
#   sh ipk.sh list                   apps you can remove
export PATH=/usr/bin:/usr/sbin:/bin:/sbin:$PATH
IS=luna://com.webos.appInstallService
# luna-send prints nothing without a terminal on this firmware, so it runs under script(1)
once() { timeout 30 script -q -c "luna-send -n 1 $1 '$2'" /dev/null </dev/null 2>/dev/null | tr -d '\r'; }
# watch <secs> <uri> <json> <done-marker>: follow the installer's subscription (-i) and stop it as soon as it reports the end.
# The subscription never ends by itself, so it runs in the background into a file that is read every second.
watch() {
  out=/tmp/lgtv-ipk.$$
  : >"$out"
  timeout "$1" script -q -c "luna-send -i $2 '$3'" /dev/null </dev/null >"$out" 2>/dev/null &
  w=$!
  shown=''
  result=timeout
  while kill -0 $w 2>/dev/null; do
    sleep 1
    state=$(tr -d '\r' <"$out" | sed -n 's/.*"state":"\([^"]*\)".*/\1/p' | tail -n 1)
    [ -n "$state" ] && [ "$state" != "$shown" ] && { echo "  $state"; shown=$state; }
    if grep -q "$4" "$out"; then result=ok; break; fi
    if grep -q -E '"returnValue":false|FAILED|"state":"failed"' "$out"; then result=failed; break; fi
  done
  kill $w 2>/dev/null
  pkill -f "luna-send -i $2" 2>/dev/null
  [ $result = failed ] && echo "FAILED: $(tr -d '\r' <"$out" | grep -m1 -E '"returnValue":false|FAILED|failed')"
  [ $result = timeout ] && echo "no answer from the installer"
  rm -f "$out"
  [ $result = ok ]
}

case "$1" in
  install)
    f="$2"
    [ -f "$f" ] || { echo "no such file: $f" >&2; exit 1; }
    echo "installing $f ..."
    watch 300 $IS/dev/install "{\"id\":\"com.ares.defaultName\",\"ipkUrl\":\"$f\",\"subscribe\":true}" '"state":"installed"' && echo "installed"
    rc=$?
    rm -f "$f"
    exit $rc
    ;;
  remove)
    id="$2"
    [ -n "$id" ] || { echo "usage: $0 remove <appId>" >&2; exit 2; }
    case "$id" in
      org.webosbrew.hbchannel | org.webosbrew.safeupdate)
        echo "refusing to remove $id: it keeps the TV rooted" >&2; exit 1 ;;
    esac
    dir=$(once luna://com.webos.service.applicationmanager/getAppInfo "{\"id\":\"$id\"}" | sed -n 's/.*"folderPath":"\([^"]*\)".*/\1/p')
    case "$dir" in
      /media/developer/*) svc=$IS/dev/remove ;;
      /media/cryptofs/*) svc=$IS/remove ;;
      "") echo "$id is not installed" >&2; exit 1 ;;
      *) echo "$id is a built-in app ($dir): it cannot be uninstalled" >&2; exit 1 ;;
    esac
    watch 120 $svc "{\"id\":\"$id\",\"subscribe\":true}" '"state":"removed"' && echo "removed $id"
    ;;
  list)
    once luna://com.webos.service.applicationmanager/listApps '{}' | node -e '
      var s = ""; process.stdin.on("data", function (d) { s += d; }).on("end", function () {
        JSON.parse(s).apps.filter(function (a) { return a.removable; }).forEach(function (a) {
          console.log(a.id + "  (" + a.title + ")" + (/^\/media\/developer/.test(a.folderPath) ? "  [homebrew]" : "  [LG store]"));
        });
      });'
    ;;
  *) echo "usage: $0 install <file.ipk> | remove <appId> | list" >&2; exit 2 ;;
esac
