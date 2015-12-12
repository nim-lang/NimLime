# coding=utf-8
"""
Mixins used to give common functionality to NimLime commands.
"""
import sublime
from nimlime_core import configuration
from nimlime_core import settings
from nimlime_core.utils.output import (
    get_output_view, show_view
)


class NimLimeMixin(object):
    """
    Mixin class for commands and event listeners that implements additional
    functionality for setting loading, requirements, etc.
    Note: The docstring for the command functions as the command description.
    """

    # Executable requirements.
    # Set these to 'true' in the implementing class in order to specify that
    # the command should only be enabled when the given executable is present.
    # in the system
    requires_nimble = False
    requires_nim = False
    requires_nimsuggest = False

    # Setting entries associated with the command or event listener.
    # Each entry should either be a tuple of the form
    #     (attribute_ident, entry_name, default_value)
    # or a tuple containing sub-entries of the same form.
    setting_entries = (
        ('enabled', '{0}.enabled', True),
    )

    def __init__(self):
        self._reload_settings()

    def _reload_settings(self):
        self._load_settings()
        settings.run_on_load_and_change('reload', self._load_settings)

    def get_setting(self, key, default):
        """
        Retrieve the setting value associated with the given key, returning the
        given default if the setting doesn't exist. The key must have a format
        specifier of '{0}'!
        :type key: string
        :type default: Any
        :rtype: Any
        """
        formatted_key = key.format(self.settings_selector)
        result = settings.get(formatted_key, default)
        return result

    def _load_settings(self):
        def _is_setting_entry(entry):
            return (
                len(entry) == 3 and
                isinstance(entry[0], str) and
                isinstance(entry[1], str)
            )

        def _load_entry(entry):
            if _is_setting_entry(entry):
                setattr(self, entry[0], self.get_setting(entry[1], entry[2]))
            elif isinstance(entry, tuple):
                for sub_entry in entry:
                    _load_entry(sub_entry)
            else:
                raise Exception("Bad setting entry type")

        _load_entry(self.setting_entries)

    def is_enabled(self):
        result = (
            self.enabled and
            ((not self.requires_nim) or configuration.nim_executable) and
            ((not self.requires_nimble) or configuration.nimble_executable)
        )
        return result

    def is_visible(self):
        result = self.is_enabled()
        if not isinstance(result, bool):
            print("Return type for is_visible is {0}".format(type(result)))
        return self.is_enabled()

    def description(self, *args, **kwargs):
        return self.__doc__


class NimLimeOutputMixin(NimLimeMixin):
    """
    A mixin for commands that generate output.
    """
    # As long as any output mixin has a tag matching that of an output view,
    # that output view must stay in memory. We use manual refcounting
    # to make sure of this
    last_output_tag = ''
    console_view = None

    setting_entries = (
        NimLimeMixin.setting_entries,
        ('clear_output', '{0}.output.clear', True),
        ('output_method', '{0}.output.method', 'grouped'),
        ('send_output', '{0}.output.send', True),
        ('show_output', '{0}.output.show', True),
        ('output_tag', '{0}.output.tag', 'nimlime'),
        ('raw_output', '{0}.output.raw', True),
        ('output_name', '{0}.output.name', 'nimlime'),
    )

    def get_output_view(self, window, view):
        tag = self.output_tag.format(
                view_id=view.id(),
                buffer_id=view.id(),
                file_name=view.file_name(),
                view_name=view.name(),
                window_id=window.id()
        )

        if self.output_method == 'console':
            output_view = self.console_view
            if tag != self.last_output_tag:
                output_view = window.create_output_panel(tag)
                self.last_output_tag = tag
                self.console_view = output_view
                return window, output_view

        elif self.output_method == 'grouped':
            for output_window in sublime.windows():
                for output_view in window.views():
                    if view.settings().get('output_tag') == tag:
                        return output_window, output_view

    def write_to_output_2(self, content, window, view):
        # First, get the format tag so we know what view to retrieve
        output_view = self.console_view
        tag = format_tag(self.output_tag, )
        if tag != self.last_output_tag:
            output_view = window.create_output_panel(tag)
            self.last_output_tag = tag
            self.console_view = output_view

        if self.output_method == 'console':
            # Use a simple per-command view pseudo-cache.
            # Trying to create a true cache would be too complicated
            output_view = self.console_view
            if tag != self.last_output_tag:
                output_view = window.create_output_panel(tag)
                self.last_output_tag = tag
                self.console_view = output_view

        else:
            for window in sublime.windows():
                for view in window.views():
                    if view.settings().get('output_tag') == tag:
                        output_view = view
                        break

    def write_to_output(self, content, source_window, source_view):
        # First, get the format tag so we know what view to retrieve

        tag = self.output_tag.format(
                view_id=view.id(),
                buffer_id=view.id(),
                file_name=view.file_name(),
                view_name=view.name(),
                window_id=window.id()
        )

        output_window, output_view = get_output_view(
                tag, self.output_method, self.output_name, self.show_output,
                source_window
        )

        if self.clear_output:
            output_view.run_command(
                    'nimlime_output',
                    dict(action='erase', args=(0, output_view.size()))
            )
        output_view.run_command(
                'nimlime_output',
                dict(action='insert', args=(output_view.size(), content))
        )

        if self.show_output:
            output_view.settings().set('output_tag', tag)
            is_console = (self.output_method == 'console')
            show_view(output_window, output_view, is_console)
