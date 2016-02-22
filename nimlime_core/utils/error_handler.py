# coding=utf-8
"""
This module contains code for handling generic uncaught exceptions at the
function level, and notifying the user of them.

The 'catch_errors' function is meant to be used as a decorator to catch
exceptions and errors thrown by code. It handles uncaught exceptions by
notifying the user through an error message box or a status message, and then
logging the exception to a log file.

The 'catch_errors' function should *not* be used for an automatically running
function, as repeated writing to the log file may result in degraded
performance and an annoyed user.

NOTE: The 'catch_errors' mechanism relies on the availability of
'yield from', which is only available on Python 3.3+ (or Sublime Text 3).
Since most of the commands are generators due to using 'send_self', this
makes the error handling mechanism rather less effective on ST2.
"""

import os
import sys
import tempfile
import traceback
from time import strftime

import sublime
from nimlime_core import settings
from nimlime_core.utils.misc import exec_, format_msg

error_msg = format_msg("""\
The NimLime plugin has encountered an error. Please go to 
https://github.com/Varriount/NimLime and create a new issue containing the
contents of the logging file at:\\n\\n
'{0}'.\\n\\n
Though this error message is only displayed once per session of
Sublime Text, further errors will be logged to the logging file and indicated
in the status bar.\\n
To completely suppress this error message in the future, change the
'error_handler.enabled' setting in NimLime's settings file to 'False'.
""")

critical_error_msg = format_msg("""\
Warning: The NimLime plugin's error handling mechanism is unable to log errors
to:
\\n\\n'{0}'.\\n\\n
Please make sure either that the directory containing the
NimLime plugin is writeable, or that the 'error_handler.logpath' setting in
NimLime's settings file is set to a writeable directory.\\n
To completely suppress this error message in the future, change the
'error_handler.enabled' setting in NimLime's settings file to 'False'.
""")

default_logfile_path = tempfile.gettempdir()

enabled = True
logfile_path = default_logfile_path
notified_user = False


def _load():
    global notified_user, enabled, logfile_path
    notified_user = False
    enabled = settings.get('error_handler.enabled', True)
    if not enabled:
        return

    logfile_path = settings.get('error_handler.logfile_path')
    logfile_path = logfile_path or default_logfile_path

    logfile_path = os.path.join(logfile_path, 'NimLime-Log.txt')
    try:
        open(logfile_path, 'a+').close()
    except Exception:
        notified_user = True
        sublime.error_message(critical_error_msg.format(logfile_path))


settings.run_on_load_and_change('error_handler.logfile_path', _load)

# These are needed because 'yield from' was only introduced in Python 3.3
# Trying to use 'yield from' in Python 2.6 causes a syntax error, which can't
# be handled - thus, exec must be used.
generator_error_handler_impl = """
        def error_handler(*args, **kwargs):
            # Optimize check away?
            if enabled:
                try:
                    yield from function(*args, **kwargs)
                except Exception:
                    print_stack()
                    _handle_error()
                    raise
            else:
                yield from function(*args, **kwargs)
"""

other_error_handler_impl = """
        error_handler = function
"""
catch_errors = None
error_wrapper_impl = """
from inspect import isgeneratorfunction
from traceback import print_stack
def catch_errors(function):
    if isgeneratorfunction(function):
{0}
    else:
        def error_handler(*args, **kwargs):
            # Optimize check away?
            if enabled:
                try:
                    return function(*args, **kwargs)
                except Exception:
                    _handle_error()
                    raise
    return error_handler
"""

if sys.version_info >= (3, 0):
    exec_(error_wrapper_impl.format(generator_error_handler_impl))
else:
    exec_(error_wrapper_impl.format(other_error_handler_impl))


def _handle_error():
    global notified_user, error_msg, critical_error_msg
    try:
        with open(logfile_path, 'a+') as logfile:
            logfile.write(strftime("\n\n%Y-%m-%d: %H:%M:%S\n"))
            logfile.write("[Stack frames]\n")
            for thread_id, stack_frame in sys._current_frames().items():
                logfile.write("[Thread {0}]\n".format(thread_id))
                traceback.print_stack(stack_frame, file=logfile)
            logfile.write("Main ")
            traceback.print_exc(file=logfile)
        message = error_msg
    except Exception:
        print("\nError handler exception:")
        traceback.print_exc()
        message = critical_error_msg

    if not notified_user:
        sublime.error_message(message.format(logfile_path))
        notified_user = True
    sublime.status_message("NimLime has encountered an error.")
