# coding=utf-8
"""
Commands and code to expose nimsuggest functionality to the user.
"""
import os
import shutil
import subprocess
import tarfile
import traceback
from shutil import copytree
from tempfile import mkdtemp
from zipfile import ZipFile

import NimLime
import sublime
from nimlime_core import configuration
from nimlime_core.utils.error_handler import catch_errors
from nimlime_core.utils.internal_tools import debug_print
from nimlime_core.utils.misc import (send_self, get_next_method, samefile,
                                     run_process, busy_frames, format_msg,
                                     loop_status_msg, start_file)
from nimlime_core.utils.mixins import (NimLimeOutputMixin, IdetoolMixin,
                                       NimLimeMixin)
from sublime_plugin import ApplicationCommand


class NimIdeCommand(NimLimeOutputMixin, IdetoolMixin, ApplicationCommand):
    requires_nimsuggest = True
    requires_nim_syntax = True
    st2_compatible = False


setup_error_msg = format_msg("""
Nimsuggest doesn't appear to have been setup correctly.\\n
Please look at the output of the debug console (ctrl+`) for more information.
""")


class NimCompileInternalNimsuggest(NimLimeMixin, ApplicationCommand):
    """
    Compile the version of Nimsuggest bundled with NimLime.
    """
    requires_nim = True
    st2_compatible = False

    @send_self
    @catch_errors
    def run(self):
        this = yield
        window = sublime.active_window()

        # Retrieve and check the destination path for the Nimsuggest executable
        exe_dir = yield window.show_input_panel(
            'Path to copy nimsuggest to? (Blank for home directory)', '',
            this.send, None, None
        )

        exe_dir = exe_dir or os.path.expanduser('~')
        debug_print('exe_dir: ', exe_dir)

        if not (os.path.exists(exe_dir) or not os.path.isdir(exe_dir)):
            sublime.error_message('Invalid path for nimsuggest executable.')
            yield

        # Signal that we are compiling Nimsuggest
        frames = ['Compiling Internal Nimsuggest' + f for f in busy_frames]
        stop_status_loop = loop_status_msg(frames, 0.15)

        temp_dir = mkdtemp()

        nimlime_dir = os.path.dirname(NimLime.__file__)
        nimsuggest_tmp_exe = os.path.join(temp_dir, 'nimsuggest', 'nimsuggest')

        if configuration.on_windows:
            nimsuggest_tmp_exe += '.exe'

        debug_print('temp_dir: ', temp_dir)
        debug_print('nimlime_dir: ', nimlime_dir)
        debug_print('nimsuggest_tmp_exe: ', nimsuggest_tmp_exe)

        if configuration.is_zipped:
            # We're in a zipped package, so we need to extract the tarball
            # from our package file, then extract the tarball
            debug_print('Extracting nimsuggest tarball to temp_dir')

            package_file = ZipFile(nimlime_dir)
            package_file.extract('nimsuggest.tar.gz', temp_dir)
            tarfile.open(
                os.path.join(temp_dir, 'nimsuggest.tar.gz')
            ).extractall(temp_dir)
        else:
            # We're an actual directory, so we just need to copy the source
            # tree to the temp directory.
            debug_print('Copying nimsuggest source to', temp_dir)

            copytree(
                os.path.join(nimlime_dir, 'nimsuggest'),
                os.path.join(temp_dir, 'nimsuggest')
            )

        # Now that the nimsuggest source has been extracted to a temporary
        # directory, compile it.
        data = yield run_process(
            [configuration.nim_executable, 'c', '-d:release', 'nimsuggest.nim'],
            cwd=os.path.join(temp_dir, 'nimsuggest'),
            callback=this.send,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )

        debug_print('Compiling with Nim exe: ', configuration.nim_executable)

        yield stop_status_loop(get_next_method(this))

        # Now check if the compilation was successful
        if data[0].poll() != 0:
            # If not, print the output and show the user an error message.
            debug_print('Compilation unsuccessful.')
            print(data[1])
            sublime.error_message(setup_error_msg)
        else:
            try:
                # Copy the executable to the destination directory.
                debug_print('Copying from: ', nimsuggest_tmp_exe)
                debug_print('Copying to: ', exe_dir)

                shutil.copy(nimsuggest_tmp_exe, exe_dir)

                # Tell the user the process was successful, and remind them
                # to set the nimsuggest settings.
                sublime.status_message('Nimsuggest compiled and copied.')
                sublime.run_command('open_file', {
                    "file": "${packages}/User/NimLime/NimLime.sublime-settings"
                })
                sublime.message_dialog(
                    "Please make sure to set the 'nimsuggest.exe' setting!"
                )
                start_file(exe_dir)
            except Exception:
                # There was an error in the copying process
                debug_print('Copy unsuccessful.')
                traceback.print_exc()
                sublime.error_message(setup_error_msg)
        yield


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
                'NimLime: No definition found in project files.'
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
        global flags
        this = yield
        window = sublime.active_window()
        view = window.active_view()
        nimsuggest = self.get_nimsuggest_instance(view.file_name())
        ide_params = self.get_ide_parameters(window, view)
        nim_file, dirty_file, line, column = ide_params

        data = yield nimsuggest.find_definition(
            nim_file, dirty_file, line, column, this.send
        )

        # Get the file and open it.
        def printer(n, ret=None):
            def _printer(*args, **kwargs):
                print(n)
                print("Positional args: ", repr(args))
                print("Keyword args: ", repr(kwargs))
                print()
                return ret

            return _printer

        if len(data[1]) > 0:
            output, entries = data
            yield view.show_popup(entries[0][3], flags=2,
                                  on_hide=printer('a'),
                                  on_navigate=printer('b')
                                  )

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
            sublime.status_message('NimLime: No definition found in project '
                                   'files.')

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
        data = yield nimsuggest.get_suggestions(
            nim_file, dirty_file, line, column, this.send
        )
        output, entries = data
        print("This:", repr(data))
        yield view.show_popup_menu([e[2] for e in entries], this.send)
        yield

# class NimOutputInvokation(NimIdeCommand):
