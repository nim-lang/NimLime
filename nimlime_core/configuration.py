# Global configuration
# This file loads and verifies the more global and complex aspects of NimLime's
# settings and configuration.
import os

import sublime
from nimlime_core import settings
from nimlime_core.utils.misc import find_file, format_msg

not_found_msg = format_msg("""
The {0} executable could not be found.\\n
NimLime commands requiring a working {0} install are disabled.\\n
Please make sure that either the {0} executable is in your PATH
environment variable, or that the '{1}.executable' entry in
NimLime's settings is set to a valid path.\\n
To disable this message, set the '{1}.check_configuration' setting
in NimLime's settings file to 'False'.
""")


def gen_exe_check(program_name, setting_prefix, default_exe):
    """
    Generates a function that checks if a program is on the path, based off
    of settings. May also notify the user.
    """

    def load():
        # Get the current executable, and look for the file.
        # Consider that the path given in the settings may be the executable's
        # directory, or its path+name.
        current_exe = settings.get(setting_prefix + '.executable', default_exe)
        executable_path = (
            find_file(current_exe) or
            find_file(os.path.join(current_exe, default_exe))
        )

        # Optionally notify the user.
        if executable_path is None and current_exe != load.old_exe:
            if settings.get(setting_prefix + '.check_configuration', True):
                sublime.error_message(
                    not_found_msg.format(program_name, setting_prefix)
                )

        # Store the old path, so that we don't end up notifying the user twice
        # over an unchanged path.
        load.old_exe = current_exe
        return executable_path

    load.old_exe = ''
    return load


nimble_executable = 'nimble'
nim_executable = 'nim'
nimsuggest_executable = 'nimsuggest'

_nimble_exe_check = gen_exe_check('Nimble', 'nimble', 'nimble.exe')
_nim_exe_check = gen_exe_check('Nim', 'nim', 'nim.exe')
_nimsuggest_exe_check = gen_exe_check('Nimsuggest', 'nimsuggest',
                                      'nimsuggest.exe')


def nimble_exe_check():
    global nimble_executable
    nimble_executable = _nimble_exe_check()


def nim_exe_check():
    global nim_executable
    nim_executable = _nim_exe_check()


def nimsuggest_exe_check():
    global nimsuggest_executable
    nimsuggest_executable = _nimsuggest_exe_check()


settings.run_on_load_and_change('nimble.executable', nimble_exe_check)
settings.run_on_load_and_change('nim.executable', nim_exe_check)
settings.run_on_load_and_change('nimsuggest.executable', nimsuggest_exe_check)
