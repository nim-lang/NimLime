# coding=utf-8
"""
Module containing Nimsuggest process interface code.
"""
import os
import re
import subprocess
import sys
from threading import Thread, Lock
from collections import namedtuple

import sublime
from nimlime_core import configuration
from nimlime_core.utils.internal_tools import debug_print


if sys.version_info < (3, 0):
    from Queue import Queue, Empty
else:
    from queue import Queue  # python 3.x


TAB_BYTE = '\t'.encode()
DOUBLE_NEWLINE_BYTE = (os.linesep*2).encode()
NEWLINE_BYTE = os.linesep.encode()
EXIT_REQUEST = object()
ANSWER_REGEX = r"""
(?P<answer_type>[^\t]*)\t
(?P<symbol_type>[^\t]*)\t
(?P<name>[^\t]*)\t
(?P<declaration>[^\t]*)\t
(?P<file_path>[^\t]*)\t
(?P<line>[^\t]*)\t
(?P<column>[^\t]*)\t
(?P<docstring>[^\t]*)\n?
"""
NimsuggestEntry = namedtuple(
    "NimsuggestEntry",
    (
        'answer_type', 'symbol_type', 'name',
        'declaration', 'file_path', 'line',
        'column', 'docstring'
    )
)


class Nimsuggest(object):
    """
    Used to retrieve suggestions, completions, and other IDE-like information
    for a Nim project.
    """

    def __init__(self, project_file, max_failures):
        """
        Create a Nimsuggest instance using the given project file path.
        :type project_file: str
        """
        self.max_failures = max_failures
        self.current_failures = -1
        self.running = False

        # Nimsuggest process handlers
        self.input_queue = Queue()
        self.state_transition_lock = Lock()  # Used for shutdown of server
        # thread.
        self.server_thread = None

        # Information needed to start a nimsuggest process
        self.environment = os.environ
        if os.path.isfile(configuration.nim_exe):
            self.environment = os.environ.copy()
            self.environment['PATH'] = '{0};{1}'.format(
                os.path.dirname(configuration.nim_exe),
                self.environment['PATH']
            )

        self.process_args = dict(
            args=[configuration.nimsuggest_exe,
                  '--nimpath:"C:\\x64\\Nim\\"',
                  'stdin', '--interactive:false',
                  project_file],
            env=self.environment,
            universal_newlines=False,
            creationflags=(configuration.on_windows and 0x08000000) or None,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

    def start(self):
        """
        Start the internal nimsuggest process
        """
        if self.running:
            raise Exception("Nimsuggest instance already running.")
        self.server_thread = Thread(target=self.run)
        self.server_thread.daemon = True
        self.server_thread.start()

    def stop(self):
        """
        Stop the internal nimsuggest process.
        """
        # We use the input_queue to signal to the handler thread to cleanup.
        if not self.running:
            raise Exception("Nimsuggest instance already stopped.")
        self.input_queue.put(EXIT_REQUEST)

    def check_process(self, process):
        result = process
        if process is None or process.poll() is not None:
            try:
                result = subprocess.Popen(**self.process_args)
                self.current_failures += 1
            except OSError:
                self.current_failures = self.max_failures
                result = None
        return result

    def run(self):
        self.running = True
        self.current_failures = -1
        process = self.check_process(None)

        if self.current_failures >= self.max_failures:
            self.running = False
            sublime.set_timeout(
                lambda: sublime.status_message(
                    "Error: Nimsuggest process couldn't be started."
                ), 0
            )
            self.input_queue = Queue()

        while self.running:
            # Retrieve the next request and send it to the process.
            request = self.input_queue.get()
            debug_print("Got request", request)
            if request is EXIT_REQUEST:
                break

            # Check up on the process
            process = self.check_process(process)
            if self.current_failures >= self.max_failures:
                sublime.set_timeout(
                    lambda: sublime.status_message(
                        "Nimsuggest process failure limit reached."
                    )
                )
                break

            input_data, callback = request
            process.stdin.write(input_data)
            process.stdin.flush()

            # Get output from Nimsuggest.
            incomplete_data = False
            raw_output = bytearray()
            while True:
                # Get the next byte
                process.stdout.flush()
                output_char = process.stdout.read(1)

                # The process returns nothing if it has exited
                if output_char == b'':
                    incomplete_data = True
                    break

                raw_output.extend(output_char)
                newline_found = raw_output.find(
                    DOUBLE_NEWLINE_BYTE,
                    len(raw_output) - len(DOUBLE_NEWLINE_BYTE)
                )
                if newline_found != -1:
                    break

            # Parse the data
            entries = None
            output = raw_output.decode('utf-8')
            if not incomplete_data:
                entries = re.findall(ANSWER_REGEX, output, re.X)
                if len(entries) == 0:
                    print('No entries found. Output:')
                    print(output)
            else:
                debug_print("Nimsuggest process pipe was closed.")
                print(output)

            # Run the callback
            self.input_queue.task_done()
            debug_print("Finished request, ", len(entries), " entries found.")
            sublime.set_timeout(lambda: callback((raw_output, entries)), 0)

        # Cleanup
        with self.state_transition_lock:
            while True:
                try:
                    callback = self.input_queue.get_nowait()
                    sublime.set_timeout(lambda: callback('', None), 0)
                    self.input_queue.task_done()
                except Empty:
                    break

            if process is not None and process.poll() is None:
                process.kill()

            self.running = False

    def run_command(self, command, nim_file, dirty_file, line, column, cb):
        # First, check that the process and thread are active
        """
        Run the given nimsuggest command.
        :type command: str
        :type nim_file: str
        :type dirty_file: str
        :type line: int
        :type column: int
        :type cb: (str, list[Any]) -> None
        """
        with self.state_transition_lock:
            if not self.running:
                self.start()

            # Next, prepare the command
            if dirty_file:
                formatted_command = '{0}\t"{1}";"{2}":{3}:{4}\r\n'.format(
                    command, nim_file, dirty_file, line, column
                ).encode('utf-8')
            else:
                formatted_command = '{0}\t"{1}":{2}:{3}\r\n'.format(
                    command, nim_file, line, column
                ).encode('utf-8')
            self.input_queue.put((formatted_command, cb))

    def __del__(self):
        pass

    def find_definition(self, nim_file, dirty_file, line, column, cb):
        self.run_command('def', nim_file, dirty_file, line, column, cb)

    def find_usages(self, nim_file, dirty_file, line, column, cb):
        self.run_command('use', nim_file, dirty_file, line, column, cb)

    def find_dot_usages(self, nim_file, dirty_file, line, column, cb):
        self.run_command('dus', nim_file, dirty_file, line, column, cb)

    def get_suggestions(self, nim_file, dirty_file, line, column, cb):
        self.run_command('sug', nim_file, dirty_file, line, column, cb)

    def get_context(self, nim_file, dirty_file, line, column, cb):
        self.run_command('context', nim_file, dirty_file, line, column, cb)

    def get_highlights(self, nim_file, dirty_file, line, column, cb):
        self.run_command('highlight', nim_file, dirty_file, line, column, cb)

    def get_outline(self, nim_file, dirty_file, line, column, cb):
        self.run_command('outline', nim_file, dirty_file, line, column, cb)
