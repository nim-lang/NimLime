# coding=utf-8
"""
Hotkey wiring for NimLime.

This file selectively turns off hotkeys
"""
import sublime
from sublime_plugin import EventListener

from ...core import settings


class HotkeySyncer(EventListener):
    """Synchronizes certain settings keys with view settings."""

    setting_entries = (
        ("doccontinue.enabled", True),
        ("doccontinue.autostop", True)
    )

    def sync_on_change(self):
        view = sublime.active_window().active_view()
        self.sync(view)

    def sync(self, view):
        print('Hello!')
        view_settings = view.settings()
        for key, default in self.setting_entries:
            value = settings.get(key, default)
            view_settings.set(key, value)

    def on_new(self, view):
        self.sync(view)

    def on_activated(self, view):
        self.sync(view)

    def on_clone(self, view):
        self.sync(view)

    def on_load(self, view):
        self.sync(view)
