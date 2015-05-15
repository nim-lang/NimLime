import os.path
import re
from threading import Thread

import sublime
from sublime_plugin import ApplicationCommand, EventListener
from utils import (
    view_has_nim_syntax, send_self, busy_frames, get_next_method,
    loop_status_msg, trim_region, NimLimeMixin, run_process
)





# Constants
ERROR_REGION_TAG = 'NimCheckError'
WARN_REGION_TAG = 'NimCheckWarn'
ERROR_REGION_MARK = 'dot'
ERROR_REGION_STYLE = sublime.DRAW_OUTLINED
ERROR_MSG_FORMAT = '({0},{1}): {2}: {3}'.format
MESSAGE_REGEX = re.compile(
    (r"""
        ^
        (.+)  \(          # File Name
        (\d+) \,\s        # Line Number
        (\d+) \)\s*       # Column Number
        (\w+) \s*:\s*     # Message Type
        (.+)  \n          # Message Content
        (.*   \n\s*  \^)? # Message Context
    """),
    flags=re.MULTILINE | re.IGNORECASE | re.VERBOSE
)


# Load settings
def load():
    global nim_executable
    nim_executable = settings.get('nim.executable', 'nim')


settings = sublime.load_settings('NimLime.sublime-settings')
settings.add_on_change('nim.executable', load)
nim_executable = None
load()


# Commands
class NimClearErrors(ApplicationCommand, NimLimeMixin):
    """ Clears error and warning marks generated by the Nim checker. """

    def run(self):
        current_view = sublime.active_window().active_view()
        current_view.erase_regions(ERROR_REGION_TAG)
        current_view.erase_regions(WARN_REGION_TAG)
        sublime.status_message('Cleared Nim Check Errors & Hints')

    def is_visible(self):
        view = sublime.active_window().active_view()
        return ((settings.get('check.current_file.enabled') or
                 settings.get('check.on_save.enabled')) and
                view_has_nim_syntax(view))


class NimCheckCurrentView(ApplicationCommand, NimLimeMixin):
    """ Checks the current Nim file for errors. """
    settings_selector = 'current_file'

    def load_settings(self):
        get = lambda key: settings.get(key.format(self.settings_selector))
        self.enabled = get('check.{0}.enabled')
        self.highlight_errors = get('check.{0}.highlight_errors')
        self.highlight_warnings = get('check.{0}.highlight_warnings')

        self.include_context = get('check.{0}.list.include_context')
        self.list_errors = get('check.{0}.list.show_errors')
        self.list_warnings = get('check.{0}.list.show_warnings')
        self.move_cursor = get('check.{0}.list.move_cursor')

        self.clear_output = get('check.{0}.output.clear')
        self.output_method = get('check.{0}.output.method')
        self.send_output = get('check.{0}.output.send')
        self.show_output = get('check.{0}.output.show')
        self.output_tag = get('check.{0}.output.tag')
        self.raw_output = get('check.{0}.output.raw')

    @send_self
    def run(self, show_error_list=True):
        this = yield

        frames = ["Running Nim Check" + f for f in busy_frames]
        stop_status_loop = loop_status_msg(frames, 0.15)

        window = sublime.active_window()
        view = window.active_view()
        view_name = os.path.split(view.file_name() or view.name())[1]
        output_name = view_name + ' - Nim Check Output'

        # Save view text
        if view.is_dirty():
            view.run_command('save')

        # Run 'nim check' on the current view and retrieve the output.
        output, returncode = yield Thread(
            target=run_nimcheck,
            args=(view.file_name(), this.send)
        ).start()

        messages = parse_nimcheck_output(output)

        yield stop_status_loop(get_next_method(this))
        sublime.status_message("Nim Check Finished.")

        self.highlight_and_list_messages(messages, window, view)

        if self.send_output:
            if self.raw_output:
                content = output
            else:
                gen = (m[5] for m in messages if view_name == m[0])
                content = "\n".join(gen)
            self.write_to_output(content, window, view, output_name)
        yield

    def is_visible(self):
        return (self.enabled and view_has_nim_syntax())

    def highlight_and_list_messages(self, messages, window, view):
        view_name = os.path.split(view.file_name() or view.name())[1]

        # For listing
        if self.list_errors or self.list_warnings:
            quick_message_list = []
            point_list = []

        # For highlighting
        if self.highlight_errors:
            error_region_list = []
        if self.highlight_warnings:
            warn_region_list = []

        for file_name, row, column, kind, message, all in messages:
            if file_name != view_name:
                continue

            # For listing
            if self.list_errors or self.list_warnings:
                point = view.text_point(row, column)
                point_list.append(point)

            # For highlighting
            message_point = view.text_point(row, column)
            message_region = trim_region(view, view.line(message_point))

            if kind == "Error":
                # For listing
                if self.list_errors:
                    if self.include_context:
                        quick_message_list.append(all.split('\n'))
                    else:
                        quick_message_list.append(all.split('\n')[0])

                # For highlighting
                if self.highlight_errors:
                    error_region_list.append(message_region)

            else:
                # For listing
                if self.list_warnings:
                    if self.include_context:
                        quick_message_list.append(all.split('\n'))
                    else:
                        quick_message_list.append(all.split('\n')[0])

                # For highlighting
                if self.highlight_warnings:
                    warn_region_list.append(message_region)

        if self.highlight_errors:
            view.add_regions(
                ERROR_REGION_TAG,
                error_region_list,
                'invalid.illegal',
                ERROR_REGION_MARK,
                ERROR_REGION_STYLE
            )

        if self.highlight_warnings:
            view.add_regions(
                WARN_REGION_TAG,
                warn_region_list,
                'invalid.deprecated',
                ERROR_REGION_MARK,
                ERROR_REGION_STYLE
            )

        if self.list_errors or self.list_warnings:
            def goto_error(choice):
                if choice != -1:
                    chosen_point = point_list[choice]
                    view.show(chosen_point)
                    if self.move_cursor:
                        view.sel().clear()
                        view.sel().add(sublime.Region(chosen_point))

            if self.include_context:
                window.show_quick_panel(
                    quick_message_list, goto_error, sublime.MONOSPACE_FONT
                )
            else:
                window.show_quick_panel(quick_message_list, goto_error)


class NimCheckOnSaveListener(EventListener, NimCheckCurrentView):
    settings_selector = 'on_save'

    def on_post_save(self, view):
        if self.enabled and view_has_nim_syntax(view):
            self.run()


class NimCheckFile(ApplicationCommand, NimLimeMixin):
    """ Check an external nim file """
    last_entry = ''

    def load_settings(self):
        get = lambda key: settings.get(key)
        self.enabled = get("check.current_file.enabled")
        self.remember_input = get("check.external_file.remember_input")

        self.include_context = get(
            "check.external_file.output.include_context")
        self.clear_output = get("check.external_file.output.clear")
        self.output_method = get("check.external_file.output.method")
        self.show_output = get("check.external_file.output.show")
        self.output_tag = get("check.external_file.output.tag")

    def run(self):
        window = sublime.active_window()

        @send_self
        def callback():
            this = yield

            # Retrieve user input
            initial_text = ''
            if self.remember_input:
                initial_text = self.last_entry

            path = yield window.show_input_panel(
                "File to check?", initial_text, this.send, None, None
            )
            self.last_entry = path

            # Run 'nim check' on the external file.
            if os.path.isfile(path):
                frames = ['Checking external file' + f for f in busy_frames]
                stop_status_loop = loop_status_msg(frames, 0.25)

                output, returncode = yield Thread(
                    target=run_nimcheck,
                    args=(path, this.send)
                ).start()

            else:
                sublime.error_message(
                    "File '{0}' does not exist, or isn't a file.".format(path)
                )
                yield

            error_list = parse_nimcheck_output(output)
            # Prepare output
            error_output = '\n'.join(
                [error[4] for error in error_list]
            )

            # Stop the status loop
            yield stop_status_loop(get_next_method(this))
            sublime.status_message("External file checked.")

            # Print to the output view
            fallback_view_name = path + " - Nim Check Output"
            self.write_to_output(
                error_output, window, None, fallback_view_name
            )

            yield

        callback()


# Utility functions
def run_nimcheck(file_path, callback):
    # Prepare the regex's
    run_process(
        "{0} check --verbosity:2 \"{1}\"".format(
            nim_executable, file_path
        ),
        callback
    )


def parse_nimcheck_output(output):
    # Retrieve and convert the matches
    message_list = []
    for match in MESSAGE_REGEX.finditer(output):
        all = match.group(0)
        file_name = match.group(1)
        line = int(match.group(2)) - 1
        column = int(match.group(3)) - 1
        kind = match.group(4)
        message = match.group(5)
        message_list.append((file_name, line, column, kind, message, all))

    # Sort the error list by line
    message_list.sort(key=lambda item: item[1])
    return message_list
