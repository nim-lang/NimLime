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

if sys.version_info < (3, 0):
    from Queue import Queue
else:
    from queue import Queue  # python 3.x

DOUBLE_NEWLINE_BYTE = (os.linesep * 2).encode()
NEWLINE_BYTE = os.linesep.encode()
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


def check_process(process, args, failure_count):
    """
    Check if the process is alive, if it isn't, restart it.
    :type process: subprocess.Popen|None
    :type args:
    :type failure_count:
    :rtype:
    """
    if process is None or process.poll() is not None:
        process = subprocess.Popen(**args)
    return process, failure_count


def _nimsuggest_handler(input_queue, process_args):
    process, fail_count = check_process(None, process_args, -1)
    input_queue.nimsuggest_process = process

    while input_queue.nim_running:
        process, fail_count = check_process(process, process_args, fail_count)
        input_queue.nimsuggest_process = process
        if fail_count > 10:
            break

        input_data, callback = input_queue.get()
        process.stdin.write(input_data)
        process.stdin.flush()

        # Assigned to later
        entries = None

        raw_output = bytearray()
        while True:
            process.stdout.flush()
            output_char = process.stdout.read(1)
            if output_char == b'':
                wrapped_callback = lambda: callback((raw_output, None))
                break

            raw_output.extend(output_char)
            newline_found = raw_output.find(
                DOUBLE_NEWLINE_BYTE,
                len(raw_output) - len(DOUBLE_NEWLINE_BYTE)
            )
            if newline_found != -1:
                wrapped_callback = lambda: callback((raw_output, entries))
                break

        # Parse the data
        output = raw_output.decode('utf-8')
        entries = re.findall(ANSWER_REGEX, output, re.X)
        if len(entries) == 0:
            print('No entries found. Output:')
            print(output)

        # Run the callback
        input_queue.task_done()
        sublime.set_timeout(wrapped_callback, 0)

    # Cleanup
    if process.poll() is None:
        process.kill()


class Nimsuggest(object):
    """
    Used to retrieve suggestions, completions, and other IDE-like information
    using a pool of nimsuggest instances.
    """

    def __init__(self, project_file):
        """
        Create a Nimsuggest instance using the given project file path.
        :type project_file: str
        """

        # Nimsuggest process handlers
        self.input_queue = None
        self.nimsuggest_handler = None

        # Information needed to start a nimsuggest process
        self.environment = os.environ.copy()
        self.environment['PATH'] = '{0};{1}'.format(
            os.path.dirname(configuration.nim_exe),
            self.environment['PATH']
        )

        self.process_args = dict(
            executable=configuration.nimsuggest_exe,
            args=['nimsuggest', 'stdin', '--interactive:false', project_file],
            env=self.environment,
            universal_newlines=False,
            creationflags=(configuration.on_windows and 0x08000000) or None,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

    def start_nimsuggest(self):
        """
        Start the internal nimsuggest process
        """
        # Create input/output queues
        self.input_queue = Queue()
        self.input_queue.nim_running = True

        # Start request handler
        self.nimsuggest_handler = Thread(
            target=_nimsuggest_handler,
            args=(self.input_queue, self.process_args)
        )

        self.nimsuggest_handler.daemon = True  # thread dies with the program
        self.nimsuggest_handler.start()

    def stop_nimsuggest(self):
        """
        Stop the internal nimsuggest process.
        """
        # We use the input_queue to signal to the handler thread to cleanup.
        if self.input_queue is not None:
            self.input_queue.nim_running = False
        self.nimsuggest_handler = None

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
        alive = (
            self.nimsuggest_handler is not None and
            self.input_queue.nimsuggest_process is not None and
            self.nimsuggest_handler.is_alive() and
            self.input_queue.nimsuggest_process.poll() is None
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
