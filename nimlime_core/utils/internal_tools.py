# coding=utf-8
"""
Internal tools for NimLime development & testing.
"""
from pprint import pformat

import sublime
from nimlime_core import configuration

try:
    from cProfile import Profile
except ImportError:
    from profile import Profile
from functools import wraps
from pstats import Stats

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

debug_on = False
if debug_on:
    sublime.message_dialog('NimLime running in debug mode.')


# Debug printer
def debug_print(*args):
    """
    Print when debugging.
    :type args: Any
    """
    if configuration.in_debug_mode:
        res = []
        for o in args:
            if isinstance(o, str):
                res.append(o)
            else:
                res.append(pformat(o))
        print(''.join(res))


# Profiling functions
profiler = Profile()
profiler_running = False


def profile_func(func):
    """
    Decorator which profiles a single function.
    Call print_profile_data to print the collected data.
    :type func: Callable
    :rtype: Callable
    """

    @wraps(func)
    def _profile_wrapper(*args, **kwargs):
        global profiler_running
        if not profiler_running:
            profiler_running = True
            try:
                profiler.enable()
                return func(*args, **kwargs)
            finally:
                profiler.disable()
                profiler_running = False

    return _profile_wrapper


def print_profile_data():
    """
    Print the collected profile data.
    """
    stream = StringIO()
    statistics = Stats(profiler, stream=stream)
    statistics.sort_stats('cumulative')
    statistics.print_stats()
    print(stream.getvalue())
