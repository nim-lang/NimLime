import sys
import os
from imp import reload

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

modules = set()
auto_reload = False


def add_module(module):
    modules.add(module)


def reload_modules():
    # Perform auto-reload
    for module_name in modules:
        mod = sys.modules.get(module_name)
        if mod is not None:
            reload(sys.modules[mod])
            print("Reloading '{}'".format(mod))