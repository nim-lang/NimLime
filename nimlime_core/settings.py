# coding=utf-8
"""
This module handles loading settings for the NimLime plugin
"""
from collections import defaultdict

import sublime

_settings = None

add_on_change_callbacks = defaultdict(set)
run_on_load_callbacks = set()


def _load():
    global _settings, add_on_change_callbacks, run_on_load_callbacks
    if _settings is not None:
        return

    s = sublime.load_settings('NimLime.sublime-settings')
    if s.get('nimlime.has_loaded', True) is None:
        sublime.set_timeout(_load, 1000)
        return

    # Settings have loaded
    _settings = s
    for callback in run_on_load_callbacks:
        callback()
    for key in add_on_change_callbacks:
        for callback in add_on_change_callbacks[key]:
            s.add_on_change(key, callback)

    # Cleanup functions and variables
    add_on_change_callbacks = None
    run_on_load_callbacks = None


def run_on_load(callback):
    """
    Run the given callback when settings are loaded.
    :type callback: () -> None
    """
    if _settings is None:
        run_on_load_callbacks.add(callback)
    else:
        callback()


def add_on_change(key, callback):
    """
    Sets the callback to run when the given settings key changes.
    :type key: str
    :type callback: () -> None
    """
    if _settings is None:
        add_on_change_callbacks[key].add(callback)
    else:
        _settings.add_on_change(key, callback)


def run_on_load_and_change(key, callback):
    """
    Runs the given callback when settings are loaded,
    then again whenever the given settings key changes.
    :type key: str
    :type callback: () -> None
    """
    run_on_load(callback)
    add_on_change(key, callback)


def get(key, default=None):
    """
    Gets the given setting, returning the given default if the setting key
    doesn't exist.
    :type default: Any
    :type key: str
    """
    if _settings is None:
        return default
    else:
        return _settings.get(key, default)


_load()
