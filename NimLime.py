import sys
import os
from imp import reload
from sublime_plugin import ApplicationCommand

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.profile_tools import print_profile_data

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


class PrintProfileData(ApplicationCommand):
    def run(self):
        print_profile_data()

    def is_visible(self):
        return False
