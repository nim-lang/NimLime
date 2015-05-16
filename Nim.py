import sys

import NimLime
import sublime


auto_reload = False

st_version = 2
if int(sublime.version()) > 3000:
    st_version = 3

auto_reload = False
if auto_reload:
    # Perform auto-reload
    reload_mods = []
    for mod in sys.modules:
        if mod[0:7] == 'NimLime' and sys.modules[mod] != None:
            reload_mods.append(mod)

    # Reload modules
    mods_load_order = [
        'Project',
        'Nim',
        'Lookup',
        'Documentation',
        'Nimble',
        'AutoComplete'
    ]

    mod_load_prefix = ''
    if st_version == 3:
        mod_load_prefix = 'NimLime.'
        from imp import reload

    for mod in mods_load_order:
        if mod in reload_mods:
            reload(sys.modules[mod])
            print("reloading " + mod)