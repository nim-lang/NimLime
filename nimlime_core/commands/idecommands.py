# coding=utf-8
"""
Commands and code to expose nimsuggest functionality to the user.
"""
import os
import subprocess
from shutil import copytree
from tempfile import mkdtemp
from zipfile import ZipFile

import NimLime
import sublime
from nimlime_core import configuration
from nimlime_core.utils.error_handler import catch_errors
from nimlime_core.utils.idetools import Nimsuggest
from nimlime_core.utils.internal_tools import debug_print
from nimlime_core.utils.misc import (send_self, get_next_method, samefile,
                                     run_process, busy_frames, format_msg,
                                     loop_status_msg, start_file,
                                     handle_process_error)
from nimlime_core.utils.mixins import (NimLimeOutputMixin, IdetoolMixin,
                                       NimLimeMixin)
from nimlime_core.utils.project import get_nim_project
from sublime_plugin import ApplicationCommand

setup_error_msg = format_msg("""
Nimsuggest doesn't appear to have been setup correctly.\\n
Please look at the output of the debug console (ctrl+`) for more information.
""")


class NimIdeCommand(NimLimeOutputMixin, IdetoolMixin):
    """A Nimsuggest command."""
    requires_nim_syntax = True
    st2_compatible = False

    nimsuggest_function = None
    not_found_msg = ""

    @send_self
    @catch_errors
    def run(self):
        this = yield
        window = sublime.active_window()
        view = window.active_view()

        nimsuggest = self.get_nimsuggest_instance(get_nim_project(window, view))
        ide_params = self.get_ide_parameters(window, view)
        nim_file, dirty_file, line, column = ide_params

        output, entries = yield self.nimsuggest_function(
            nimsuggest, nim_file, dirty_file, line, column, this.send
        )
        if entries is None:
            sublime.status_message("Error: Nimsuggest exited unexpectedly.")
            yield
        elif len(entries) == 0:
            sublime.status_message(self.not_found_msg)
            yield

        yield self.process_entries(window, view, output, entries)

    def process_entries(self, window, view, output, entries):
        raise NotImplementedError()


class NimCompileInternalNimsuggest(NimLimeMixin, ApplicationCommand):
    """
    Compile the version of Nimsuggest bundled with NimLime.
    """
    settings_selector = 'compile_nimsuggest'

    st2_compatible = False

    @send_self
    @catch_errors
    def run(self):
        this = yield
        window = sublime.active_window()

        # Retrieve and check the destination path for the Nimsuggest executable
        exe_output_dir = yield window.show_input_panel(
            'Path to copy nimsuggest to? (Blank for home directory)', '',
            this.send, None, None
        )

        exe_output_dir = exe_output_dir or os.path.expanduser('~')
        debug_print('exe_dir: ', exe_output_dir)

        if not (os.path.exists(exe_output_dir) or not os.path.isdir(
            exe_output_dir)):
            sublime.error_message('Invalid path for nimsuggest executable.')
            yield

        # Signal that we are compiling Nimsuggest
        frames = ['Compiling Internal Nimsuggest' + f for f in busy_frames]
        stop_status_loop = loop_status_msg(frames, 0.15)

        # Generate the paths needed to extract and compile Nimsuggest
        temp_dir = mkdtemp()
        nimsuggest_source_dir = os.path.join(temp_dir, 'nimsuggest')
        nimlime_dir = os.path.dirname(NimLime.__file__)
        exe_output_file = os.path.join(exe_output_dir, 'nimsuggest')

        if configuration.on_windows:
            exe_output_file += '.exe'

        debug_print('temp_dir: ', temp_dir)
        debug_print('nimlime_dir: ', nimlime_dir)
        debug_print('exe_output_file: ', exe_output_file)

        # Extract the Nimsuggest source
        if configuration.is_zipped:
            # We're in a zipped package, so we need to extract the tarball
            # from our package file, then extract the tarball
            debug_print('Extracting nimsuggest tarball to temp_dir')
            ZipFile(nimlime_dir).extractall(temp_dir)
        else:
            # We're an actual directory, so we just need to copy the source
            # tree to the temp directory.
            debug_print('Copying nimsuggest source to', temp_dir)
            copytree(
                os.path.join(nimlime_dir, 'nimsuggest'),
                nimsuggest_source_dir
            )

        # Compile the nimsuggest source
        debug_print('Compiling with Nim exe: ', configuration.nim_exe)
        process, stdout, _, error = yield run_process(
            [configuration.nim_exe, 'c', '--out:' + exe_output_file,
             '-d:release',
             'nimsuggest.nim'],
            cwd=nimsuggest_source_dir, callback=this.send,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        yield stop_status_loop(get_next_method(this))

        # Handle possible errors
        if handle_process_error(error, 'Nimsuggest setup failed', 'Nim'):
            yield
        elif process.poll() != 0:
            sublime.error_message(setup_error_msg)
            debug_print('Compilation unsuccessful.')
            print(stdout)
            yield

        # Tell the user the process was successful, and remind them
        # to set the nimsuggest settings.
        sublime.status_message('Nimsuggest compiled and copied.')
        sublime.run_command('open_file', {
            'file': '${packages}/User/NimLime/NimLime.sublime-settings'
        })
        sublime.message_dialog(
            'Please make sure to set the \'nimsuggest.executable\' setting!'
        )
        start_file(exe_output_dir)
        yield


class NimGotoDefinition(NimIdeCommand, ApplicationCommand):
    """
    Goto the definition of a symbol at the cursor.
    """
    settings_selector = "nimsuggest.goto_definition"

    nimsuggest_function = staticmethod(Nimsuggest.find_definition)
    not_found_msg = "No definition found."

    @send_self
    @catch_errors
    def process_entries(self, window, view, output, entries):
        this = yield

        index = 0
        if len(entries) > 1:
            input_list = [
                ['{5}, {6}: {3}'.format(*e), e[4]] for e in entries
                ]
            index = yield window.show_quick_panel(input_list, this.send)
            if index == -1:
                yield

        # Open the entry file and go to the point
        entry = entries[index]
        target_view = window.open_file(entry[4])
        while target_view.is_loading():
            yield sublime.set_timeout(get_next_method(this), 100)

        target_view.show_at_center(
            target_view.text_point(int(entry[5]), int(entry[6]))
        )


class NimShowDefinition(NimIdeCommand, ApplicationCommand):
    """
    Show the definition of a symbol in a popup.
    """

    settings_selector = "nimsuggest.show_definition"

    nimsuggest_function = staticmethod(Nimsuggest.find_definition)
    not_found_msg = "No definition found."

    @catch_errors
    def process_entries(self, window, view, output, entries):
        popup_text = '\n'.join([e[3] for e in entries])
        popup_location = view.word(view.sel()[0])
        width = (
            view.viewport_extent()[0] -
            view.text_to_layout(popup_location.a)[0]
        )

        view.show_popup(
            popup_text, flags=2, max_width=width,
            location=popup_location.a
        )


class NimShowDefinitionInStatus(NimIdeCommand, ApplicationCommand):
    """
    Show the definition of a symbol in the status bar.
    """

    settings_selector = "nimsuggest.show_definition_in_status"

    nimsuggest_function = staticmethod(Nimsuggest.find_definition)
    not_found_msg = "No definition found."

    @catch_errors
    def process_entries(self, window, view, output, entries):
        popup_text = ''.join([e[3] for e in entries])
        sublime.status_message(popup_text)


class NimHighlightUsages(NimIdeCommand, ApplicationCommand):
    """
    Highlight uses of the symbol in the current file.
    """

    settings_selector = "nimsuggest.highlight_usages"

    nimsuggest_function = staticmethod(Nimsuggest.find_usages)
    not_found_msg = "No uses found."

    @catch_errors
    def process_entries(self, window, view, output, entries):
        pass


class NimListUsagesInFile(NimIdeCommand, ApplicationCommand):
    """
    List uses of the symbol in the current file.
    """

    settings_selector = "nimsuggest.highlight_usages_in_file"

    nimsuggest_function = staticmethod(Nimsuggest.find_usages)
    not_found_msg = "No uses found."

    @send_self
    @catch_errors
    def process_entries(self, window, view, output, entries):
        this = yield
        if len(entries) == 0:
            sublime.status_message("No definition found.")
            yield

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


class NimSuggestRenameSymbol(NimIdeCommand, ApplicationCommand):

    settings_selector = "nimsuggest.rename"

    nimsuggest_function = staticmethod(Nimsuggest.find_usages)
    not_found_msg = "Symbol not found."

    def process_entries(self, window, view, output, entries):
        # First, aggregate the entries into changes associated with a file.
        # for entry in entries:
        pass


class NimSuggestMoveSymbol(NimIdeCommand, ApplicationCommand):
    settings_selector = "nimsuggest.move"

