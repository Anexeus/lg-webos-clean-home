#!/bin/sh
# Put launcher-patch.css (next to this script) into CleanYourTV's launcher page, between /* lgtv-look:start */ and
# /* lgtv-look:end */ markers in its <style>, in app/ (what CleanYourTV copies at boot) and home-overlay/ (what is mounted as Home).
#   sh patch-launcher.sh         apply or update; reloads Home when something changed
#   sh patch-launcher.sh check   apply only if missing (the boot hook, after a CleanYourTV update replaced the page)
#   sh patch-launcher.sh remove  take it out again
export PATH=/usr/bin:/usr/sbin:/bin:/sbin:$PATH
D=$(cd "$(dirname "$0")" && pwd)
C=/media/developer/cleanyourtv
[ -f "$C/app/index.html" ] || { echo "CleanYourTV launcher not installed"; exit 0; }
mode=${1:-apply}
css=$D/launcher-patch.css
[ "$mode" = remove ] && css=/dev/null
changed=0
for f in "$C/app/index.html" "$C/home-overlay/index.html"; do
  [ -f "$f" ] || continue
  if [ "$mode" = check ] && grep -q 'lgtv-look:start' "$f"; then continue; fi
  r=$(node -e '
    var fs = require("fs"), f = process.argv[1], mode = process.argv[3];
    var html = fs.readFileSync(f, "utf8"), css = mode === "remove" ? "" : fs.readFileSync(process.argv[2], "utf8");
    var start = "/* lgtv-look:start */", end = "/* lgtv-look:end */";
    var a = html.indexOf(start), b = html.indexOf(end);
    var base = a >= 0 && b > a ? html.slice(0, a) + html.slice(b + end.length) : html;
    var out = base;
    if (css) {
      var i = base.lastIndexOf("</style>");
      if (i < 0) { console.log("no-style"); process.exit(0); }
      out = base.slice(0, i) + start + "\n" + css + "\n" + end + base.slice(i);
    }
    if (out === html) { console.log("same"); process.exit(0); }
    fs.writeFileSync(f + ".tmp", out); fs.renameSync(f + ".tmp", f);
    console.log("written");
  ' "$f" "$css" "$mode")
  echo "$f: $r"
  [ "$r" = written ] && changed=1
done
if [ $changed = 1 ]; then
  sh "$C/reload-home.sh" >/dev/null 2>&1
  echo "Home reloaded"
fi
