"""Build a webOS .ipk (an ar archive of debian-binary, control.tar.gz and data.tar.gz) from an app folder with appinfo.json.

    python build_ipk.py <app dir> <out.ipk>
"""
import io, json, os, sys, tarfile


def tgz(files):
    b = io.BytesIO()
    with tarfile.open(fileobj=b, mode='w:gz', format=tarfile.GNU_FORMAT) as t:
        for name, data in files:
            ti = tarfile.TarInfo(name); ti.size = len(data); ti.mode = 0o644; ti.uid = ti.gid = 0
            t.addfile(ti, io.BytesIO(data))
    return b.getvalue()


def main(app, out):
    info = json.load(open(os.path.join(app, 'appinfo.json'), encoding='utf-8'))
    app_id, ver = info['id'], info.get('version', '1.0.0')
    data = []
    for root, _, files in os.walk(app):
        for f in sorted(files):
            p = os.path.join(root, f)
            rel = os.path.relpath(p, app).replace(os.sep, '/')
            data.append((f'./usr/palm/applications/{app_id}/{rel}', open(p, 'rb').read()))
    data.append((f'./usr/palm/packages/{app_id}/packageinfo.json', json.dumps({'id': app_id, 'version': ver, 'app': app_id}).encode()))
    ctl = (f'Package: {app_id}\nVersion: {ver}\nSection: misc\nPriority: optional\nArchitecture: all\nInstalled-Size: 1\n'
           f'Maintainer: lgtv-tune <nobody@example.com>\nDescription: {info.get("title", app_id)}\n'
           'webOS-Package-Format-Version: 2\nwebOS-Packager-Version: x.y.x\n').encode()
    parts = [('debian-binary', b'2.0\n'), ('control.tar.gz', tgz([('./control', ctl)])), ('data.tar.gz', tgz(data))]
    blob = b'!<arch>\n'
    for n, d in parts:
        blob += (f'{n + "/":<16}{0:<12}{0:<6}{0:<6}{"100644":<8}{len(d):<10}`\n').encode() + d + (b'\n' if len(d) % 2 else b'')
    open(out, 'wb').write(blob)
    print(out, len(blob), 'bytes')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
