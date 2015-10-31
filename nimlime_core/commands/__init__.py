# This package automatically exports all commands found in immediate submodules
# This used by the root NimLime plugin to automatically export
import inspect
import sys
from pkgutil import iter_modules

import sublime
from sublime_plugin import ApplicationCommand, WindowCommand, TextCommand

__all__ = []
collision_message = format("""
Error: Command collision detected while loading the NimLime plugin.\\n
Please file an issue at https://github.com/Varriount/NimLime
""")


def load_submodules():
    """
    Load all submodules, adding all commands and event listeners to this
    module's global namespace.
    """
    for module_data in iter_modules(__path__, __name__ + '.'):
        loader, module_name, is_pkg = module_data

        if not is_pkg and module_name != __name__:
            # We look in sys.modules to avoid importing a module twice
            # (causing a reload)
            module = (
                sys.modules.get(module_name) or
                loader.find_module(module_name).load_module(module_name)
            )
            for class_name, class_def in inspect.getmembers(module):
                if inspect.isclass(class_def):
                    valid_command = (
                        issubclass(class_def, ApplicationCommand) or
                        issubclass(class_def, WindowCommand) or
                        issubclass(class_def, TextCommand)
                    )
                    if valid_command:
                        if class_name in __all__:
                            sublime.error_message("Error: ")
                        globals()[class_name] = class_def
                        __all__.append(class_name)


load_submodules()
