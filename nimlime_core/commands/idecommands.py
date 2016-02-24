# coding=utf-8
"""
Commands and code to expose nimsuggest functionality to the user.
"""
import os
import subprocess
import tarfile
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
                                     loop_status_msg, start_file,
                                     handle_process_error)
from nimlime_core.utils.mixins import (NimLimeOutputMixin, IdetoolMixin,
                                       NimLimeMixin)
from sublime_plugin import ApplicationCommand


class NimIdeCommand(NimLimeOutputMixin, IdetoolMixin, ApplicationCommand):
    """A Nimsuggest command."""
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
            ZipFile(nimlime_dir).extract('nimsuggest.tar.gz', temp_dir)
            tarfile.open(
                os.path.join(temp_dir, 'nimsuggest.tar.gz')
            ).extractall(temp_dir)
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

    @send_self
    @catch_errors
    def run(self):
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
                print('Positional args: ', repr(args))
                print('Keyword args: ', repr(kwargs))
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
    """
    Find usages of a symbol in the current file.
    """
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
    """Get suggestions"""
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
        print('This:', repr(data))
        yield view.show_popup_menu([e[2] for e in entries], this.send)
        yield

# class NimOutputInvocation(NimIdeCommand):
