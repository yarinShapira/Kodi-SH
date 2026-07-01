#!/usr/bin/env python3
"""Final guard: confirm the repacked APK carries the NEW package id and
zero references to the OLD package id in critical runtime forms.

Run after the binary package swap, before zipalign/sign, so a broken rename
fails the build loudly instead of shipping a crash-looping APK.

Usage:
    verify_apk_package.py <apk> <old/slash/pkg> <new/slash/pkg>
e.g. verify_apk_package.py unsigned.apk org/xbmc/kodi org/xbmc/povi
"""
import sys
import zipfile


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    apk, old_slash, new_slash = sys.argv[1], sys.argv[2], sys.argv[3]
    old_forms = {
        'slash': old_slash.encode('ascii'),
        'dotted': old_slash.replace('/', '.').encode('ascii'),
        'dash': old_slash.replace('/', '-').encode('ascii'),
        'underscore': old_slash.replace('/', '_').encode('ascii'),
    }
    new_forms = {
        'slash': new_slash.encode('ascii'),
        'dotted': new_slash.replace('/', '.').encode('ascii'),
        'dash': new_slash.replace('/', '-').encode('ascii'),
        'underscore': new_slash.replace('/', '_').encode('ascii'),
    }
    main_class = new_forms['slash'] + b'/Main'
    z = zipfile.ZipFile(apk)
    names = [n for n in z.namelist() if n.startswith('classes') and n.endswith('.dex')]
    if not names:
        sys.exit('ERROR: no classes*.dex in ' + apk)
    total_new = 0
    found_main = False
    # The bundled wizard intentionally keeps historical package ids in
    # APK_PACKAGE_IDS so old Kodi-SH/Kodi package names continue to receive
    # migration/update prompts. It may also mention older package IDs in
    # changelog prose. Those text/config literals are not Android runtime
    # package references and must not be binary-rewritten or fail this guard.
    allowed_old_refs = {
        'assets/addons/plugin.program.kodipovilwizard/uservar.py',
        'assets/addons/plugin.program.kodipovilwizard/changelog.txt',
    }
    for n in z.namelist():
        data = z.read(n)
        if n not in allowed_old_refs:
            for label, old_value in old_forms.items():
                if data.count(old_value):
                    sys.exit('ERROR: {0} still references old {1} package form: {2}'.format(
                        n, label, old_value.decode('ascii')))
        total_new += data.count(new_forms['slash'])
        if n.startswith('classes') and n.endswith('.dex') and data.count(main_class):
            found_main = True
    if not found_main:
        sys.exit('ERROR: {0}/Main not found in any dex'.format(new_slash))
    print('FINAL APK PACKAGE OK: {0} x{1}, zero {2} refs, Main present'.format(
        new_slash, total_new, old_slash))


if __name__ == '__main__':
    main()
