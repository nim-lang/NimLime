import os.path
import re
import subprocess
import sublime
from sublime_plugin import TextCommand, WindowCommand
from threading import Thread
# from time import sleep

# Constants
# TODO - Shift some of these to user settings
# TODO - Show input errors through status bar
# TODO - Optionally warn if the file doesn't end in '.nim'
error_regex_template = r"{0}\((\d+),\s*(\d+)\)\s*(\w*):\s*(.*)"
message_template = "({0}, {1}) {2}: {3}"
error_msg_format = '({0},{1}): {2}: {3}'.format
DEBUG = False
POLL_INTERVAL = 1
ERROR_REGION_TAG = "NimCheckError"
WARN_REGION_TAG = "NimCheckWarn"
ERROR_REGION_MARK = "dot"
ERROR_REGION_STYLE = sublime.DRAW_OUTLINED


def debug(string):
    if DEBUG:
        print(string)


class NimClearErrors(TextCommand):

    def run(self, edit):
        self.view.erase_regions(ERROR_REGION_TAG)
        self.view.erase_regions(WARN_REGION_TAG)

    def is_enabled(self):
        nim_syntax = self.view.settings().get('syntax', "")
        return ("nimrod" in nim_syntax.lower())

    def is_visible(self):
        return self.is_enabled()


class NimCheckCurrentView(TextCommand):

    def run(self, edit):
        """
        Runs the text in the currentview through nimrod's `check` tool,
        highlighting and displaying the errors within the view's text buffer
        and the quick panel.
        """
        view = self.view
        # Save view text
        debug("Checking if the view is dirty")
        if view.is_dirty():
            debug("View is dirty - Saving")
            view.run_command('save')
        run_thread = Thread(
            target=run_nimcheck,
            args=(view.file_name(), self.display_errors)
        )
        run_thread.start()

    def display_errors(self, error_list):
        view = self.view
        warn_region_list = []
        error_region_list = []
        message_list = []
        point_list = []
        for row, column, kind, message in error_list:
            # Prepare the error region for display
            error_point = view.text_point(row, column)
            error_region = trim_region(view, view.line(error_point))
            if kind == "Error":
                error_region_list.append(error_region)
            else:
                warn_region_list.append(error_region)

            # Prepare the error message for the quickbox
            quick_message = [
                message_template.format(row, column, kind, message),
                view.substr(error_region)
            ]
            message_list.append(quick_message)
            point_list.append(error_point)

        view.add_regions(
            ERROR_REGION_TAG,
            error_region_list,
            "invalid.illegal",
            ERROR_REGION_MARK,
            ERROR_REGION_STYLE
        )
        view.add_regions(
            WARN_REGION_TAG,
            warn_region_list,
            "invalid.deprecated",
            ERROR_REGION_MARK,
            ERROR_REGION_STYLE
        )
        callback = lambda choice: goto_error(view, point_list, choice)
        sublime.active_window().show_quick_panel(message_list, callback)

    def is_enabled(self):
        nim_syntax = self.view.settings().get('syntax', "")
        return ("nimrod" in nim_syntax.lower())

    def is_visible(self):
        return self.is_enabled()


class NimCheckFile(WindowCommand):

    def run(self):
        """
        Prompts the user to select a file, runs the file through nimrod's
        'check' tool, and outputs the errors in a new view.
        """
        # Retrieve user input
        self.window.show_input_panel(
            "File to check?",
            "",
            self.check_external_file,
            None,
            None
        )

    def check_external_file(self, path):
        if os.path.isfile(path):
            run_nimcheck(path, self.display_errors)

    def display_errors(self, error_list):
        # Open or retrieve display view
        output_view = None
        for view in self.window.views():
            if view.settings().get("nimcheck_error_output", False):
                output_view = view
                break
        else:
            output_view = self.window.new_file()
            output_view.set_name("NimCheck Output")
            output_view.set_scratch(True)
            output_view.settings().set("nimcheck_error_output", True)

        # Write errors to view
        output_view.set_read_only(False)
        output = '\n'.join(
            [error_msg_format(*error) for error in error_list]
        )

        edit = output_view.begin_edit()
        output_view.insert(edit, 0, output)
        output_view.end_edit(edit)
        output_view.set_read_only(False)


def goto_error(view, point_list, choice):
    """
    Goto the line in 'view' specified by the entry in 'point_list' with the
    index 'choice'.
    Used by the show_quick_panel procedure in poll_nimcheck
    """
    if choice != -1:
        chosen_point = point_list[choice]
        view.show(chosen_point)


def trim_region(view, region):
    """
    Trim a region of whitespace.
    """
    text = view.substr(region)
    start = region.a + ((len(text) - 1) - (len(text.strip()) - 1))
    end = region.b - ((len(text) - 1) - (len(text.rstrip()) - 1))
    return sublime.Region(start, end)


def run_nimcheck(file_path, output_callback):
    """
    Runs 'nimrod check' on the file specified by 'file_path', and returns
    a list of errors found to the output_callback.
    It's highly advised to run this in a thread!
    """
    debug("Running nim_check command")

    # Prepare the regex's
    file_name = re.escape(os.path.split(file_path)[1])
    error_regex = re.compile(
        error_regex_template.format(file_name),
        flags=re.MULTILINE | re.IGNORECASE
    )
    debug("Escaped file name: " + file_name)
    debug("Error Regex: " + error_regex.pattern)

    # Run nimrod check
    debug("Running 'nimrod check' process")
    nimcheck_process = subprocess.Popen(
        "nimrod check \"{0}\"".format(file_path),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        bufsize=0
    )

    # Setup and start the polling procedure
    output_buffer = ""
    while True:
        debug("Polling 'nimrod check'...")

        # Gather any process output (to avoid pipe overflow)
        output_buffer += nimcheck_process.stdout.read().decode("UTF-8")

        # Poll the process's state
        nimcheck_process.poll()
        if nimcheck_process.returncode is not None:
            debug("'nimrod check' is done.")
            debug("Return code: " + str(nimcheck_process.returncode))

            # Retrieve and convert the matches
            error_list = []
            for match in error_regex.finditer(output_buffer):
                line = int(match.group(1)) - 1
                column = int(match.group(2)) - 1
                kind = match.group(3)
                message = match.group(4)
                error_list.append((line, column, kind, message))

            # Run the callback
            callback = lambda: output_callback(error_list)
            sublime.set_timeout(callback, 0)
            break
    #     sleep(POLL_INTERVAL)
    # sleep(POLL_INTERVAL)
