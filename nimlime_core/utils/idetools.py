# coding=utf-8
"""
Module containing Nimsuggest process interface code.
"""
import os
import re
import subprocess
import sys
from threading import Thread

import sublime
from nimlime_core import configuration

try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x

ON_POSIX = 'posix' in sys.builtin_module_names
DOUBLE_NEWLINE_BYTE = '\r\n\r\n'.encode()
ANSWER_REGEX = r"""
(?P<answer_type>[^\t]*)\t
(?P<symbol_type>[^\t]*)\t
(?P<name>[^\t]*)\t
(?P<declaration>[^\t]*)\t
(?P<file_path>[^\t]*)\t
(?P<line>[^\t]*)\t
(?P<column>[^\t]*)\t
(?P<docstring>[^\t]*)\t
.*\n?
"""


def _nimsuggest_handler(process, input_queue):
    while True:
        input_data, callback = input_queue.get()
        process.stdin.write(input_data)

        raw_output = bytearray()
        while True:
            output_char = process.stdout.read(1)
            if not output_char:
                # Subprocess is dead
                return

            raw_output.append(output_char)
            newline_found = raw_output.find(
                    DOUBLE_NEWLINE_BYTE,
                    len(raw_output) - len(DOUBLE_NEWLINE_BYTE)
            )
            if newline_found != -1:
                break

        # Parse the data
        output = raw_output.decode('utf-8')
        entries = re.findall(ANSWER_REGEX, output, re.X)

        # Run the callback
        input_queue.task_done()
        sublime.set_timeout(0, lambda: callback(entries))


class Nimsuggest(object):
    """
    Used to retrieve suggestions, completions, and other IDE-like information
    using a pool of nimsuggest instances.
    """

    def __init__(self, project_file):
        """
        Create a Nimsuggest instance using the given project file path.
        :type project_file: string
        """

        # Nimsuggest process
        self.input_queue = None
        self.nimsuggest_process = None
        self.nimsuggest_handler = None

        # Information needed to start a nimsuggest process
        self.process_args = ('nimsuggest', 'stdin', project_file)
        self.environment = os.environ.copy()
        self.environment['PATH'] = "{0};{1}".format(
                os.path.dirname(configuration.nimsuggest_executable),
                self.environment['PATH']
        )

    def start_nimsuggest(self):
        """
        Start the internal nimsuggest process
        """
        # Create input/output queues
        self.input_queue = Queue()

        # Create process
        self.nimsuggest_process = subprocess.Popen(
                executable=configuration.nimsuggest_executable,
                args=self.process_args,
                env=self.environment,
                creationflags=0x08000000,
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE
        )

        # Start handler
        self.nimsuggest_handler = Thread(
                target=_nimsuggest_handler,
                args=(
                self.input_queue, self.output_queue, self.nimsuggest_process)
        )
        self.nimsuggest_handler.daemon = True  # thread dies with the program
        self.nimsuggest_handler.start()

    def stop_nimsuggest(self):
        """
        Stop the internal nimsuggest process.
        """
        # First, kill the subprocess
        if self.nimsuggest_process.poll() is None:
            self.nimsuggest_process.kill()

        # Next, clear the thread
        self.nimsuggest_handler = None

    def run_command(self, command, nim_file, dirty_file, line, column, cb):
        # First, check that the process and thread are active
        alive = (
            self.nimsuggest_handler.is_alive() and
            self.nimsuggest_process.poll is None
        )
        if not alive:
            self.stop_nimsuggest()
            self.start_nimsuggest()

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

    def find_d_usages(self, nim_file, dirty_file, line, column, cb):
        self.run_command('dus', nim_file, dirty_file, line, column, cb)

    def get_suggestions(self, nim_file, dirty_file, line, column, cb):
        self.run_command('sug', nim_file, dirty_file, line, column, cb)

    def get_outline(self, nim_file, dirty_file, line, column, cb):
        self.run_command('outline', nim_file, dirty_file, line, column, cb)
