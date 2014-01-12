import os
import os.path
import re
import subprocess
import sublime
from sublime_plugin import TextCommand


error_regex_template = r"{0}\((\d+),\s*(\d+)\)(.*)"
DEBUG = True


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


class NimCheck(TextCommand):

    def run(self, edit):
        """
        Runs the text in the view through nimrod's `check` tool, and output's a
        list of error points and messages.
        """
        view = self.view

        # Prepare the regex's
        file_name = re.escape(os.path.split(view.file_name())[1])
        error_regex = re.compile(
            error_regex_template.format(file_name),
            flags=re.MULTILINE | re.IGNORECASE
        )
        debug("Escaped file name: " + file_name)
        debug("Error Regex: " + error_regex_template.format(file_name))

        # Save view text
        debug("Checking if the view is dirty")
        if view.is_dirty():
            debug("View is dirty - Saving")
            view.run_command('save')

        # Run nimrod check
        debug("Running the 'nimrod check'...")
        process = subprocess.Popen(
            ["C:\\64\\nimrod\\bin\\nimrod.exe", "check", view.file_name()],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            bufsize=0
        )

        # Polling routing does the rest of the work, to avoid blocking
        def poll_nimcheck(output_buffer):
            debug("Running polling routine")

            # Gather any process output (to avoid pipe overflow)
            output_buffer += process.stdout.read()

            # Poll the process's state
            process.poll()
            if process.returncode is not None:
                debug("Process is done.")
                debug(output_buffer)

                # Go through the matches
                regs = []
                for match in error_regex.finditer(output_buffer):
                    err_lineno = int(match.group(1)) - 1
                    err_colno = int(match.group(2)) - 1
                    err_message = match.group(3)

                    # Display the error region
                    err_point = view.text_point(err_lineno, err_colno)
                    err_region = view.line(err_point)
                    err_region = trim_region(view, err_region)
                    regs.append(err_region)
                view.add_regions(
                    "NimCheck", regs, "invalid.depracated", "dot", sublime.DRAW_OUTLINED)

                # Display the errors in the popup box

            else:
                sublime.set_timeout(lambda: poll_nimcheck(output_buffer), 5)
        sublime.set_timeout(lambda: poll_nimcheck(""), 5)
        # Get output
        # Parse output
        # Display Output
