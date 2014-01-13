import os.path
import re
import subprocess
import sublime
from sublime_plugin import TextCommand

# Constants
# TODO - Shift some of these to user settings
error_regex_template = r"{0}\((\d+),\s*(\d+)\)(.*)"
message_template = "({0}, {1}) {2}"
DEBUG = True
POLL_INTERVAL = 0
ERROR_REGION_TAG = "NimCheck"
ERROR_REGION_MARK = "dot"
ERROR_REGION_STYLE = sublime.DRAW_OUTLINED


def debug(string):
    if DEBUG:
        print(string)


def trim_region(view, region):
    """
    Trim a region of whitespace.
    """
    text = view.substr(region)
    start = region.a + ((len(text) - 1) - (len(text.strip()) - 1))
    end = region.b - ((len(text) - 1) - (len(text.rstrip()) - 1))
    return sublime.Region(start, end)


class NimCheckFile(TextCommand):

    def run(self, edit):
        """
        Runs the text in the view through nimrod's `check` tool, and output's a
        list of error points and messages.
        """
        debug("Running nim_check command")
        view = self.view

        # Prepare the regex's
        file_name = re.escape(os.path.split(view.file_name())[1])
        error_regex = re.compile(
            error_regex_template.format(file_name),
            flags=re.MULTILINE | re.IGNORECASE
        )
        debug("Escaped file name: " + file_name)
        debug("Error Regex: " + error_regex.pattern)

        # Save view text
        debug("Checking if the view is dirty")
        if view.is_dirty():
            debug("View is dirty - Saving")
            view.run_command('save')

        # Run nimrod check
        debug("Running 'nimrod check' process")
        nimcheck_process = subprocess.Popen(
            ["nimrod", "check", view.file_name()],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            bufsize=0
        )

        # Start the polling function
        poller = lambda: poll_nimcheck(
            "",
            nimcheck_process,
            view,
            error_regex
        )
        sublime.set_timeout(poller, POLL_INTERVAL)


def goto_error(view, point_list, choice):
    """
    Used by the show_quick_panel procedure in poll_nimcheck
    """
    if choice != -1:
        chosen_point = point_list[choice]
        view.show(chosen_point)


def poll_nimcheck(output_buffer, nimcheck_process, view, error_regex):
    """
    Polls a 'nimrod check' subprocess, reporting errors to the user.
    """
    debug("Polling 'nimrod check'...")

    # Gather any process output (to avoid pipe overflow)
    output_buffer += nimcheck_process.stdout.read()

    # Poll the process's state
    nimcheck_process.poll()
    if nimcheck_process.returncode is not None:
        debug("'nimrod check' is done.")
        debug(output_buffer)

        # Go through the matches
        region_list = []
        message_list = []
        point_list = []
        for match in error_regex.finditer(output_buffer):
            line = int(match.group(1)) - 1
            column = int(match.group(2)) - 1
            message = match.group(3)

            # Prepare the error region for display
            error_point = view.text_point(line, column)
            error_region = trim_region(view, view.line(error_point))
            region_list.append(error_region)

            # Prepare the error message for the quickbox
            quick_message = [
                message_template.format(line, column, message),
                view.substr(error_region)
            ]
            message_list.append(quick_message)
            point_list.append(error_point)

        view.add_regions(
            ERROR_REGION_TAG,
            region_list,
            "invalid.depracated",
            ERROR_REGION_MARK,
            ERROR_REGION_STYLE
        )
        callback = lambda choice: goto_error(view, point_list, choice)
        sublime.active_window().show_quick_panel(message_list, callback)
    else:
        # Set poll_nimcheck to be called later
        poller = lambda: poll_nimcheck(
            output_buffer,
            nimcheck_process,
            view,
            error_regex
        )
        sublime.set_timeout(poller, POLL_INTERVAL)
