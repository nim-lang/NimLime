# coding=utf-8
"""
Mixins used to give common functionality to NimLime commands.
"""
import os
from os import fdopen
from tempfile import mkstemp

import sublime
from nimlime_core import configuration
from nimlime_core import settings
from nimlime_core.utils.idetools import Nimsuggest

SUBLIME_VERSION = int(sublime.version())


class NimLimeMixin(object):
    """
    Mixin class for commands and event listeners that implements additional
    functionality for setting loading, requirements, etc.
    Note: The docstring for the command functions as the command description.
    """

    # Executable requirements.
    # Set these to 'true' in the implementing class in order to specify that
    # the command should only be visible/enabled when the stated condition is
    # true
    requires_nimble = False  # A valid Nimble executable is present.
    requires_nim = False  # A valid Nim executable is present.
    requires_nimsuggest = False  # A valid Nimsuggest executable is present.
    requires_nim_syntax = False  # The current view must be using Nim syntax.
    st2_compatible = True  # Runs on Sublime Text 2.
    st3_compatible = True  # Runs on Sublime Text 3.

    # Setting entries associated with the command or event listener.
    # Each entry should either be a tuple of the form
    #     (attribute_ident, entry_name, default_value)
    # or a tuple containing sub-entries of the same form.
    settings_selector = None
    setting_entries = (
        ('enabled', '{0}.enabled', True),
    )

    def __init__(self):
        self._reload_settings()

    def __getattr__(self, item):
        # This is to satisfy static checkers, to ignore settings accesses.
        pass

    def _reload_settings(self):
        self._load_settings()
        settings.run_on_load_and_change('reload', self._load_settings)

    def get_setting(self, key, default):
        """
        Retrieve the setting value associated with the given key, returning the
        given default if the setting doesn't exist. The key must have a format
        specifier of '{0}'!
        :type key: str
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

    def is_enabled(self, view=None):
        if view is None:
            view = sublime.active_window().active_view()
        syntax = view.settings().get('syntax', '')

        # Maybe change this to something more straightforward?
        result = bool(
            (
                (not self.requires_nim_syntax) or  # If self.requires_nim
                (syntax.find('Nim.'))
            ) and
            (
                (not self.requires_nim or not self.requires_nimsuggest) or
                configuration.nim_executable
            ) and
            (
                (not self.requires_nimble) or  # If self.requires_nimble
                configuration.nimble_executable
            ) and
            (
                (not self.requires_nimsuggest) or  # If self.requires_nimsuggest
                configuration.nimsuggest_executable
            ) and
            (
                (self.st2_compatible and (2 <= SUBLIME_VERSION < 3)) or
                (self.st3_compatible and (3 <= SUBLIME_VERSION))
            )
        )
        return result

    def is_visible(self):
        result = self.is_enabled()
        if not isinstance(result, bool):
            print("Return type for is_visible is {0}".format(type(result)))
        return self.is_enabled()

    def description(self, *args, **kwargs):
        return self.__doc__


del NimLimeMixin.__getattr__


class NimLimeOutputMixin(NimLimeMixin):
    """
    A mixin for commands that generate output.
    """
    # As long as any output mixin has a tag matching that of an output view,
    # that output view must stay in memory. We use manual refcounting
    # to make sure of this
    last_output_tag = ''
    last_console_view = None

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

    def _get_output_view(self, tag, window, view):
        if self.output_method == 'console':
            output_view = self.last_console_view
            if tag != self.last_output_tag:
                output_view = window.create_output_panel(tag)
                self.last_output_tag = tag
                self.last_console_view = output_view
            return window, output_view

        elif self.output_method == 'grouped':
            for output_window in sublime.windows():
                for output_view in window.views():
                    if view.settings().get('output_tag') == tag:
                        return output_window, output_view

        output_view = window.new_file()
        output_view.set_name(self.output_name)
        output_view.settings().set('ouput_tag', tag)
        output_view.set_scratch(True)
        return window, output_view

    def write_to_output(self, content, window, view):
        # First, get the format tag
        """
        Write the given content to an output view, as specified by the output
        settings.
        :type content: str
        :type window: sublime.Window
        :type view: sublime.View
        """
        if not self.send_output:
            return

        tag = self.output_tag.format(
            view_id=view.id(),
            buffer_id=view.id(),
            file_name=view.file_name(),
            view_name=view.name(),
            window_id=window.id()
        )

        # Then, get the window and view
        output_window, output_view = self._get_output_view(tag, window, view)

        # Output to the view
        if self.clear_output:
            output_view.run_command(
                'nimlime_output',
                dict(action='erase', args=(0, output_view.size()))
            )
        output_view.run_command(
            'nimlime_output',
            dict(action='insert', args=(output_view.size(), content))
        )

        # Show the view
        if self.output_method == 'console':
            tag = view.settings().get('output_tag')
            window.run_command("show_panel", {"panel": "output." + tag})
        elif self.output_method == 'grouped':
            window.focus_view(view)


class IdetoolMixin(object):
    """
    Mixin for classes needing to use nimsuggest.
    """
    nimsuggest_instances = {}
    tmp_files = {}

    def get_ide_parameters(self, window, view):
        """
        Retrieve most of the information needed for a nimsuggest call using
        the given window and view.
        :type window: sublime.Window
        :type view: sublime.View
        :rtype: tuple[str, str, int, int]
        """
        nim_file = view.file_name()

        tmp_pair = self.tmp_files.get(nim_file, None)
        if tmp_pair is None:
            a, b = mkstemp()
            tmp_pair = (fdopen(a, 'wb', 0), b)
            self.tmp_files[nim_file] = tmp_pair
        handle, dirty_file = tmp_pair

        handle.seek(0)
        handle.truncate(0)
        handle.write(
            view.substr(sublime.Region(0, view.size())).encode('utf-8'))
        handle.flush()

        line, column = view.rowcol(view.sel()[0].a)
        line += 1
        column += 1

        return nim_file, dirty_file, line, column

    def get_nimsuggest_instance(self, project_file):
        """
        Retrieve (or create) a nimsuggest instance associated with the given
        project file.
        :type project_file: str
        :rtype: nimlime_core.utils.idetools.IdeTool
        """
        canonical_project = os.path.normcase(os.path.normpath(project_file))
        instance = self.nimsuggest_instances.get(canonical_project)
        if instance is None:
            instance = Nimsuggest(canonical_project)
            self.nimsuggest_instances[canonical_project] = instance
        return instance
