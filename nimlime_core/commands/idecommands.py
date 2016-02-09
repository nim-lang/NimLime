# coding=utf-8
"""
Commands and code to expose nimsuggest functionality to the user.
"""
import os
import tarfile
from pprint import pprint
from tempfile import mkdtemp
from zipfile import ZipFile

import sublime
from sublime_plugin import ApplicationCommand

import NimLime
from nimlime_core import configuration
from nimlime_core.utils.error_handler import catch_errors
from nimlime_core.utils.misc import (send_self, get_next_method, samefile,
                                     run_process, busy_frames)
from nimlime_core.utils.mixins import (NimLimeOutputMixin, IdetoolMixin,
                                       NimLimeMixin)


class NimIdeCommand(NimLimeOutputMixin, IdetoolMixin, ApplicationCommand):
    requires_nimsuggest = True
    requires_nim_syntax = True
    st2_compatible = False


class NimCompileInternalNimsuggest(NimLimeMixin, ApplicationCommand):
    """
    Compile the version of Nimsuggest bundled with NimLime.
    """
    requires_nim = True

    @send_self
    @catch_errors
    def run(self):
        this = yield
        window = sublime.active_window()
        view = window.active_view()

        frames = ["Compiling Internal Nimsuggest" + f for f in busy_frames]

        exe_path = yield window.show_input_panel(
            "Path to copy nimsuggest to? (Blank for temporary directory)", '',
            this.send, None, None
        )
        if exe_path == '':
            exe_path = mkdtemp()

        if not (os.path.exists(exe_path) and os.path.isdir(exe_path)):
            sublime.status_message("Invalid path.")
            yield

        nimlime_dir = os.path.dirname(NimLime.__file__)
        nimsuggest_file = os.path.join(
            nimlime_dir, 'nimsuggest', 'nimsuggest.nim'
        )
        if os.path.exists(nimsuggest_file):
            # Either we're using an actual file
            run_process(
                [configuration.nim_executable, 'c', nimsuggest_file]
            )
        else:
            # Or we're using a zipped version
            package_file = ZipFile(os.path.join(nimlime_dir))
            package_file.extract('nimsuggest.tar.gz', exe_path)
            tarfile.open(
                os.path.join(exe_path, 'nimsuggest.tar.gz')
            ).extractall(exe_path)


class NimGotoDefinition(NimIdeCommand):
    """
    Goto definition of symbol at cursor.
    """
    settings_selector = 'idetools.find_definition'
    setting_entries = (
        NimLimeOutputMixin.setting_entries,
        ('ask_on_multiple_results', '{0}.ask_on_multiple_results', True)
    )

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

        # Get the correct definition entry
        index = 0

        if len(entries) == 0:
            sublime.status_message(
                "NimLime: No definition found in project files."
            )
            yield
        elif len(entries) > 1 and not self.ask_on_multiple_results:
            input_list = [[e[5] + ', ' + e[6] + ': ' + e[3], e[4]] for e in
                          entries]
            index = yield window.show_quick_panel(input_list, this.send)
            if index == -1:
                yield

        # Open the entry file and go to the point
        entry = entries[index]
        target_view = window.open_file(entry[4])
        while target_view.is_loading():
            yield sublime.set_timeout(get_next_method(this), 1000)

        target_view.show_at_center(
            target_view.text_point(int(entry[5]), int(entry[6]))
        )

        yield


class NimShowDefinition(NimIdeCommand):
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

        # Get the file and open it.
        if len(entries) > 0:
            view.show_popup([e[3] for e in entries])
        yield


class NimFindUsages(NimIdeCommand):
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
        ide_params = self.get_ide_parameters(window, view)
        nim_file, dirty_file, line, column = ide_params

        output, entries = yield nimsuggest.find_definition(
            nim_file, dirty_file, line, column, this.send
        )

        # Get the file and open it.
        if len(entries):
            # Retrieve the correct entry
            index = 0
            if len(entries) > 1:
                input_list = [
                    [e[5] + ', ' + e[6] + ': ' + e[3], e[4]] for e in entries
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


class NimFindUsagesInCurrentFile(NimIdeCommand):
    settings_selector = 'idetools.find_current_file_usages'
    requires_nim_syntax = True

    @send_self
    @catch_errors
    def run(self):
        this = yield
        window = sublime.active_window()
        view = window.active_view()
        nimsuggest = self.get_nimsuggest_instance(view.file_name())

        nim_file, dirty_file, line, column = self.get_ide_parameters(window,
                                                                     view)
        output, entries = yield nimsuggest.find_usages(
            nim_file, dirty_file, line, column, this.send
        )

        index = 0
        while index < len(entries):
            entry = entries[index]
            filename = entry[4]
            if samefile(filename, view.file_name()):
                index += 1
            else:
                del (entries[index])

        index = yield window.show_quick_panel(
            ['({5},{6}) {3}'.format(*entry2) for entry2 in entries],
            lambda x: sublime.set_timeout(lambda: this.send(x))
        )

        if index != -1:
            entry = entries[index]
            view.show_at_center(
                view.text_point(int(entry[5]), int(entry[6]))
            )

        yield


class NimGetSuggestions(NimIdeCommand):
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

        nim_file, dirty_file, line, column = self.get_ide_parameters(window,
                                                                     view)
        output, entries = yield nimsuggest.get_suggestions(
            nim_file, dirty_file, line, column, this.send
        )
        pprint(entries)
        yield

# class NimOutputInvokation(NimIdeCommand):
