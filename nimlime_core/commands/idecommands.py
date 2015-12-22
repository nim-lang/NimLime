# coding=utf-8
"""
Commands and code to expose nimsuggest functionality to the user.
"""
from pprint import pprint

import sublime
from nimlime_core.utils.error_handler import catch_errors
from nimlime_core.utils.misc import send_self, get_next_method
from nimlime_core.utils.mixins import (NimLimeOutputMixin, NimLimeMixin,
                                       IdetoolMixin)
from sublime_plugin import ApplicationCommand


class NimGotoDefinition(NimLimeOutputMixin, IdetoolMixin, ApplicationCommand):
    """
    Goto definition of symbol at cursor.
    """
    settings_selector = 'idetools.find_definition'
    requires_nim_syntax = True

    # requires_nimsuggest = True

    @send_self
    @catch_errors
    def run(self):
        this = yield
        window = sublime.active_window()
        view = window.active_view()

        nimsuggest = self.get_nimsuggest_instance(view.file_name())
        ide_params = self.get_ide_parameters(window, view)
        nim_file, dirty_file, line, column = ide_params

        output, entries = yield nimsuggest.find_definition(
            nim_file, dirty_file, line, column, this.send
        )

        # Get the file and open it.
        if len(entries) > 0:
            # Retrieve the correct entry
            index = 0
            if len(entries) > 0:
                input_list = [
                    [e[5]+', '+e[6]+': '+e[3], e[4]] for e in entries
                ]
                index = yield window.show_quick_panel(input_list, this.send)
                if index == -1:
                    yield

            # Open the entry file and go to the point
            entry = entries[index]
            view = window.open_file(entry[4], sublime.TRANSIENT)
            while view.is_loading():
                yield sublime.set_timeout(get_next_method(this), 1000)
            view.show_at_center(view.text_point(int(entry[5]), int(entry[6])))
        else:
            sublime.status_message("NimLime: No definition found in project "
                                   "files.")

        yield


class NimShowDefinition(NimLimeOutputMixin, IdetoolMixin, ApplicationCommand):
    """
    Show definition of symbol at cursor.
    """
    settings_selector = 'idetools.find_definition'
    requires_nim_syntax = True

    # requires_nimsuggest = True

    @send_self
    @catch_errors
    def run(self):
        this = yield
        window = sublime.active_window()
        view = window.active_view()
        nimsuggest = self.get_nimsuggest_instance(view.file_name())

        ide_params = self.get_ide_parameters(window, view)
        nim_file, dirty_file, line, column = ide_params

        output, entries = yield nimsuggest.find_definition(
            nim_file, dirty_file, line, column, this.send
        )

        print(repr(output))
        pprint(entries)
        print("End")
        yield


class NimFindUsages(NimLimeOutputMixin, ApplicationCommand):
    """
    Find usages of symbol at cursor.
    """
    settings_selector = 'idetools.find_usages'
    requires_nim_syntax = True

    # requires_nimsuggest = True

    @send_self
    @catch_errors
    def run(self):
        this = yield
        window = sublime.active_window()
        view = window.active_view()
        nimsuggest = self.get_nimsuggest_instance(view.file_name())

        print("Here")
        nim_file, dirty_file, line, column = self.get_ide_parameters(window,
                                                                     view)
        output, entries = yield nimsuggest.find_definition(
            nim_file, dirty_file, line, column, this.send
        )
        yield


class NimFindUsagesInCurrentFile(NimLimeMixin, ApplicationCommand):
    settings_selector = 'idetools.find_current_file_usages'
    requires_nim_syntax = True

    # requires_nimsuggest = True

    @send_self
    @catch_errors
    def run(self):
        this = yield
        window = sublime.active_window()
        view = window.active_view()
        nimsuggest = self.get_nimsuggest_instance(view.file_name())

        nim_file, dirty_file, line, column = self.get_ide_parameters(window,
                                                                     view)
        output, entries = yield nimsuggest.find_definition(
            nim_file, dirty_file, line, column, this.send
        )
        print(repr(output))
        pprint(entries)
        yield


class NimGetSuggestions(NimLimeMixin, ApplicationCommand):
    settings_selector = 'idetools.get_suggestions'
    requires_nim_syntax = True

    # requires_nimsuggest = True

    @send_self
    @catch_errors
    def run(self):
        this = yield
        window = sublime.active_window()
        view = window.active_view()
        nimsuggest = self.get_nimsuggest_instance(view.file_name())

        print("Here")
        nim_file, dirty_file, line, column = self.get_ide_parameters(window,
                                                                     view)
        output, entries = yield nimsuggest.find_definition(
            nim_file, dirty_file, line, column, this.send
        )
        print(repr(output))
        pprint(entries)
        print("End")
        yield
