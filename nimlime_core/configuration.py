# coding=utf-8
"""
Global configuration
This file loads and verifies the more global and complex aspects of NimLime's
settings and configuration.
"""
import os
from subprocess import Popen

import sublime
from nimlime_core import settings


# Package state
def _check_debug_value():
    global in_debug_mode
    in_debug_mode = settings.get('debug_mode', False)


is_zipped = not os.path.isfile(__file__)
in_debug_mode = False
settings.run_on_load_and_change('debug_mode', _check_debug_value)

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


# Executable conditionals
def _update_nimble_value():
    global nimble_exe
    nimble_exe = settings.get('nimble.executable', 'nim')


def _update_nim_value():
    global nim_exe
    nim_exe = settings.get('nimble.executable', 'nimble')


def _update_nimsuggest_value():
    global nimsuggest_exe
    nimsuggest_exe = settings.get('nimsuggest.executable', 'nimble')


nimble_exe = 'nimble'
nim_exe = 'nim'
nimsuggest_exe = 'nimsuggest'
settings.run_on_load_and_change('nimble.executable', _update_nimble_value)
settings.run_on_load_and_change('nim.executable', _update_nim_value)
settings.run_on_load_and_change('nimsuggest.executable',
                                _update_nimsuggest_value)
