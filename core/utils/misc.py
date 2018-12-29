# coding=utf-8
"""Misc. functions that don't really fit anywhere else."""
import os
import platform
import re
import subprocess
import sys
from functools import wraps
from threading import Thread
from weakref import proxy

import sublime


def format_msg(message):
    r"""
    Used to format user messages.

    Replaces newline characters with spaces, '\\n' with newlines, etc.
    """
    message = re.sub('\\\\n\n *', '\\\\n', message)
    message = re.sub('\n\s*', ' ', message)
    message = message.replace('\\n', '\n')
    return message.strip()


def get_next_method(generator_instance):
    """Function that retrieves the 'next' method from a generator instance."""
    if sys.version_info > (3, 0):
        return generator_instance.__next__
    else:
        return generator_instance.next


def send_self(use_proxy):
    """
    A decorator which sends a generator a reference to itself.

    The first yield statement will emit the reference.
    Useful for creating generators that can leverage callback-based functions
    in a linear style, by passing their 'send' method as callbacks.

    Note that by default, the generator instance reference sent is a weakly
    referenced proxy. To override this behavior, pass `False` or
    `use_proxy=False` as the first argument to the decorator.

    Args:
        use_proxy (bool): Whether to use a weakly referenced proxy(default is
                          True)
    """
    _use_proxy = True

    # We either directly call this, or return it, to be called by python's
    # decorator mechanism.
    def _send_self(func):
        @wraps(func)
        def _send_self_wrapper(*args, **kwargs):
            generator = func(*args, **kwargs)
            generator.send(None)
            if _use_proxy:
                generator.send(proxy(generator))
            else:
                generator.send(generator)
            return generator

        return _send_self_wrapper

    # If the argument is a callable, we've been used without being directly
    # passed an argument by the user, and thus should call _send_self directly
    if callable(use_proxy):
        # No arguments, this is the decorator
        return _send_self(use_proxy)
    else:
        # Someone has used @send_self(bool), and thus we need to return
        # _send_self to be called indirectly.
        _use_proxy = use_proxy
        return _send_self


busy_frames = ['.', '..', '...']


def loop_status_msg(frames, speed, view=None, key=''):
    """
    Display an "animated" status message.

    Create and run a generator which continually sets the status
    text to a series of strings. Return a function which, when called,
    stops the generator.
    Useful for creating 'animations' in the status bar.

    Parameters:
        frames (): A sequence of strings displayed in order on the status bar
        speed (): Delay between frame shifts, in seconds
        view (): View to set the status on. If not provided, then
                sublime.status_message is used.
        key (): Key used when setting the status on a view. Ignored if no
               view is given.

    To stop the loop, the returned function must be called with no arguments,
    or a single argument for which `bool(arg) == true`. As a special condition,
    if the first argument is a callable for which `bool(arg) == True`, then
    the argument will be invoked after the last animation loop has finished.
    If for the the given argument, `bool(arg) == False`, nothing will
    happen.
    """
    flag = _FlagObject()
    flag.flag = False

    @send_self
    def _loop_status_generator():
        self = yield

        # Get the correct status function
        if view is None:
            set_status = sublime.status_message
        else:
            set_status = lambda f: view.set_status(key, f)

        # Main loop
        while not flag.flag:
            for frame in frames:
                set_status(frame)
                yield sublime.set_timeout(
                    get_next_method(self),
                    int(speed * 1000)
                )
        if callable(flag.flag):
            flag.flag()
        yield

    def _stop_status_loop(callback=True):
        flag.flag = callback

    sublime.set_timeout(_loop_status_generator, 0)
    return _stop_status_loop


class _FlagObject(object):
    """Used with loop_status_msg to signal when a status message loop should end."""
    def __init__(self):
        self.flag = False


def view_has_nim_syntax(view=None):
    """
    Tests whether the given view (or the active view) currently has 'Nim' as
    the selected syntax.

    Args:
        view ():
    """
    if view is None:
        view = sublime.active_window().active_view()
    return 'nim' in view.settings().get('syntax', '').lower()


def trim_region(view, region):
    """
    Trim a region of whitespace.
    :type region: sublime.Region
    :type view: sublime.View
    :rtype: sublime.Region
    """
    text = view.substr(region)
    start = region.a + ((len(text) - 1) - (len(text.strip()) - 1))
    end = region.b - ((len(text) - 1) - (len(text.rstrip()) - 1))
    return sublime.Region(start, end)


def escape_shell(s):
    """
    Escape a string so that it is a shell string.
    :type s: str
    :rtype: str
    """
    '\'' + s.replace('\'', "'\"'\"'") + "'"
    return s


if sys.version_info >= (3, 0):
    ExeNotFound = FileNotFoundError
else:
    ExeNotFound = IOError


def display_process_error(error, action, exe_name):
    """
    Display an error passed to a callback from run_process.
    :type error: Exception
    :type action: str
    :type exe_name: str
    """
    message = ''
    if isinstance(error, ExeNotFound):
        message = '{0}: {1} executable could not be found.'
    elif error is not None:
        message = '{0}: Unable to start {1} executable.'

    # print(message.format(action, exe_name))
    sublime.status_message(message.format(action, exe_name))


def run_process(cmd, callback=None, timeout=0, *args, **kwargs):
    """
    Run the given process in another thread. The callback, if given, will be
    passed the process and its output when the process finishes.

    :type cmd: list[str]|tuple
    :type callback: (tuple) -> None
    :type timeout: int|float
    :type args: Any
    :type kwargs: Any
    :rtype: Thread
    """
    # Ensures that the subprocess doesn't create a Window
    if platform.system() == 'Windows':
        kwargs = kwargs.copy() 
        kwargs['creationflags'] = 0x08000000

    # Open the process
    process = subprocess.Popen(
        cmd,
        universal_newlines=True,
        *args, **kwargs
    )

    # Run the watchdog, if required
    if timeout:
        def _kill_process():
            if process.poll() is None:
                process.kill()

        sublime.set_timeout(_kill_process, int(timeout * 1000))

    # Collect the output and return
    def collecter():
        error = stdout = stderr = None
        try:
            stdout, stderr = process.communicate()
        except Exception as e:
            error = e

        return process, stdout, stderr, error

    result = run_in_thread(collecter, callback)


def run_in_thread(function, callback, *args, **kwargs):
    """
    Run the given function in a thread, calling the callback when the function
    completes.

    :type function: Any
    :type callback: Any
    :type args: Any
    :type kwargs: Any
    :rtype: Thread
    """

    def _run_in_thread_inner():
        result = function(*args, **kwargs)
        sublime.set_timeout(lambda: callback(result))

    t = Thread(target=_run_in_thread_inner)
    t.daemon = False
    t.start()
    return t


def samefile(path_one, path_two):
    """
    Cross-version samefile function
    :type path_one: str
    :type path_two: str
    :rtype: bool
    """
    stat_one = os.stat(path_one)
    stat_two = os.stat(path_two)
    return (
        stat_one.st_ino == stat_two.st_ino and
        stat_one.st_dev == stat_two.st_dev
    )


def start_file(path):
    """
    'start' a file or path, using the appropriate system handler.
    :type path: str
    :rtype: None
    """
    if platform.system() == 'Windows':
        os.startfile(path)
    elif platform.system() == 'Darwin':
        subprocess.Popen(['open', path])
    else:
        subprocess.Popen(['xdg-open', path])


def exec_(code, global_dict=None, local_dict=None):
    """
    Cross-version exec function.
    :type code: str
    :type global_dict: dict[str, Any]
    :type local_dict: dict[str, Any]
    """
    frame = sys._getframe(1)
    gd = global_dict
    ld = local_dict
    if global_dict is None:
        gd = frame.f_globals
    if local_dict is None:
        ld = frame.f_globals

    if sys.version_info > (3, 0):
        exec(code, gd, ld)
    else:
        exec('exec code in gd, ld')
