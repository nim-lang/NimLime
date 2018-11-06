# coding=utf-8
"""Mixins used to give common functionality to NimLime commands."""
import inspect

import sublime

from NimLime.core import settings

SUBLIME_VERSION = int(sublime.version())
EXE_NOT_FOUND_MSG = ('Unable to run command, the following executables could '
                     'not be found: ')
NO_SETTINGS_SELECTOR_MSG = ("NimLime command {0} in {1} has no settings "
                            "selector.")


class NimLimeMixin(object):
    """
    Mixin class for commands and event listeners.

    Implements additional functionality for setting loading, requirements,
    etc.
    Note: The docstring for the command functions as the command description.
    """

    # Executable requirements.
    # Set these to 'true' in the implementing class in order to specify that
    # the command should only be visible/enabled when the stated condition is
    # true
    requires_nim_syntax = False  # The current view must be using Nim syntax.
    st2_compatible = True  # Runs on Sublime Text 2.
    st3_compatible = True  # Runs on Sublime Text 3.

    # Setting entries associated with the command or event listener.
    # Each entry should either be a tuple of the form
    #     (attribute_name, setting_name, default_value)
    # or a tuple containing sub-entries of the same form.
    settings_selector = None
    setting_entries = (
        ('enabled', '{0}.enabled', False),
    )

    def __getattr__(self, item):
        """Used to satisfy static checkers."""
        pass

    def __init__(self):
        # print("Creating", self)
        settings.notify_on_change(self._load_settings)
        self._load_settings()

    def _get_setting(self, key, default):
        """
        Retrieve a setting value.

        Retrieve the setting value associated with the given key, returning the
        given default if the setting doesn't exist.
        The key must have a format specifier of '{0}'!
        """
        # import traceback;traceback.print_stack()
        if self.settings_selector is None:
            raise Exception(NO_SETTINGS_SELECTOR_MSG.format(
                self.__class__.__name__, inspect.getfile(self.__class__)
            ))
        formatted_key = key.format(self.settings_selector)
        result = settings.get(formatted_key, default)
        return result

    def _load_settings(self):
        # Recursively load settings
        def _is_setting_entry(entry):
            return (
                len(entry) == 3 and
                isinstance(entry[0], str) and
                isinstance(entry[1], str)
            )

        def _load_entry(entry):
            if _is_setting_entry(entry):
                attr_name, setting_name, default = entry
                value = self._get_setting(setting_name, default)
                setattr(self, attr_name, value)
            elif isinstance(entry, tuple):
                for sub_entry in entry:
                    _load_entry(sub_entry)
            else:
                raise Exception('Bad setting entry type')

        _load_entry(self.setting_entries)

    def is_enabled(self, view=None):
        if not self.enabled:
            return False
        return True

        if view is None:
            view = sublime.active_window().active_view()

        syntax = view.settings().get('syntax', '')
        result = True
        if self.requires_nim_syntax and not syntax.find('Nim.'):
            result = False
        elif (2 <= SUBLIME_VERSION < 3) and not self.st2_compatible:
            result = False
        elif (3 <= SUBLIME_VERSION) and not self.st3_compatible:
            result = False

        return result

    def is_visible(self):
        return self.is_enabled()

    def description(self, *args, **kwargs):
        return self.__doc__


del NimLimeMixin.__getattr__


class NimLimeOutputMixin(NimLimeMixin):
    """A mixin for commands that generate output."""

    output_panel = None
    output_panel_tag = None

    setting_entries = (
        NimLimeMixin.setting_entries,
        # ('output_limit', '{0}.output.limit', 0),
        ('show_output', '{0}.output.show', True),
        ('send_output', '{0}.output.send', True),
        ('output_tag', '{0}.output.tag', 'nimlime'),
        ('output_panel_theme', '{0}.output.panel_theme', '')
    )

    def _refresh_output_panel(self, view):
        window = view.window()
        tag = self.output_tag.format(
            view_id=view.id(),
            buffer_id=view.id(),
            file_name=view.file_name(),
            view_name=view.name(),
            window_id=window.id()
        )
        self.output_panel = window.create_output_panel(tag)

        # TODO Find a way to be more reactive
        output_panel_theme = self.output_panel_theme
        if not output_panel_theme:
            output_panel_theme = view.settings().get("color_scheme")

        self.output_panel.settings().set('color_scheme', output_panel_theme)
        self.output_panel.settings().set('word_wrap', True)
        return tag

    def write_to_output(self, content, view):
        """Write the given content to an output view."""
        window = view.window()
        tag = self._refresh_output_panel(view)

        # Output to the view
        # if False and self.clear_output:
        #     self.output_panel.run_command(
        #         'nimlime_output',
        #         dict(
        #             action='erase',
        #             args=(0, self.output_panel.size())
        #         )
        #     )

        self.output_panel.run_command(
            'append',
            dict(characters = content)
        )

        # Show the view
        if self.show_output:
            window.run_command(
                'show_panel',
                {'panel': 'output.' + tag}
            )
