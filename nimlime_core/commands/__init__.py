# coding=utf-8
"""
This package automatically exports all commands found in immediate submodules
This used by the root NimLime plugin to automatically export
"""
import inspect
import sys
from pkgutil import iter_modules

import sublime
from nimlime_core.utils.misc import format_msg
from sublime_plugin import ApplicationCommand, WindowCommand, TextCommand, \
    EventListener

__all__ = []
collision_message = format_msg("""
Error: Command collision detected while loading the NimLime plugin.\\n
Please file an issue at https://github.com/Varriount/NimLime with the below
information:\\n
Old command: {0}\\n
New command: {1}
""")


def is_child_class(child, parent):
    return issubclass(child, parent) and child is not parent


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
                        is_child_class(class_def, ApplicationCommand) or
                        is_child_class(class_def, WindowCommand) or
                        is_child_class(class_def, TextCommand) or
                        is_child_class(class_def, EventListener)
                    )
                    if valid_command:
                        if class_name in __all__:
                            sublime.error_message(
                                collision_message.format(
                                    globals()[class_name], class_def
                                )
                            )
                        globals()[class_name] = class_def
                        __all__.append(class_name)


load_submodules()
