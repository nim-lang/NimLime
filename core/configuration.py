# coding=utf-8
"""
Global configuration
This file loads and verifies the more global and complex aspects of NimLime's
settings and configuration.
"""
import os
import sys
from pprint import pformat

import sublime

# Package state
is_zipped = not os.path.isfile(__file__)


# Global settings
def plugin_loaded():
    global nim_exe
    settings = sublime.load_settings('NimLime.sublime-settings')
    nim_exe = settings.get("nim.executable", "nim")


nim_exe = 'nim'

# OS Conditionals
on_windows = False
on_linux = False
on_mac = False

platform = sublime.platform()

if platform == 'windows':
    on_windows = True
elif platform == 'linux':
    on_linux = True
elif platform == 'osx':
    on_mac = True


# Debug mode
in_debug_mode = False


def debug_print(*args):
    """
    Print when debugging.

    :type args: Any
    """
    if in_debug_mode:
        module_name = sys._getframe(0).f_globals['__name__']
        res = []
        for o in args:
            if isinstance(o, str):
                res.append(o)
            else:
                res.append(pformat(o))
        print(module_name, ':', ' '.join(res))
