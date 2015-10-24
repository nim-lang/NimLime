import sublime
import os
import sys
import traceback
from time import strftime
from NimLime import root_dir, when_settings_load
from inspect import isgeneratorfunction
from .utils.misc import exec_

error_msg = """\
The NimLime plugin has encountered an error. Please go to 
https://github.com/Varriount/NimLime and create a new issue containing the
contents of the logging file at:\\n\\n
'{0}'.\\n\\n
Though this error message is only displayed once per session of
Sublime Text, further errors will be logged to the logging file and indicated
in the status bar.\\n
To completely suppress this error message in the future, change the
'notify_and_log_errors' setting in NimLime's settings file to 'False'.
""".replace('\\n\n', '\\n').replace('\n', ' ').replace('\\n', '\n')

critical_error_msg = """\
Warning: The NimLime plugin's error handling mechanism is unable to log errors
to:
\\n\\n'{0}'.\\n\\n
Please make sure either that the directory containing the
NimLime plugin is writeable, or that the 'logging_path' setting in
NimLime's settings file is set to a writeable directory.\\n
""".replace('\\n\n', '\\n').replace('\n', ' ').replace('\\n', '\n')


default_logfile_path = os.path.join(root_dir, 'NimLime-Log.txt')
notified_user = False
logfile_path = default_logfile_path
enabled = True


def load():
    global notified_user, enabled, logfile_path
    notified_user = False
    enabled = settings.get('notify_and_log_errors', True)
    logfile_path = settings.get('logfile_path') or default_logfile_path

    try:
        open(logfile_path, 'a+').close()
    except:
        notified_user = True
        sublime.error_message(critical_error_msg.format(get_logfile_path()))

when_settings_load(load)


generator_error_handler_impl = """
        def error_handler(*args, **kwargs):
            # Optimize check away?
            if enabled:
                try:
                    yield from function(*args, **kwargs)
                except:
                    handle_error()
            else:
                yield from function(*args, **kwargs)
"""

other_error_handler_impl = """
        function()
"""

error_wrapper_impl = """
def catch_errors(function):
    if isgeneratorfunction(function):
{0}
    else:
        def error_handler(*args, **kwargs):
            # Optimize check away?
            if enabled:
                try:
                    return function(*args, **kwargs)
                except:
                    handle_error()
    return error_handler
"""


if sys.version_info >= (3, 0):
    exec_(error_wrapper_impl.format(generator_error_handler_impl))
else:
    exec_(error_wrapper_impl.format(other_error_handler_impl))

def handle_error():
    global notified_user, error_msg, critical_error_msg
    try:
        with open(logfile_path, 'a+') as log_file:
            log_file.write(strftime("\n\n%Y-%m-%d %H:%M:%S\n"))
            traceback.print_exc(None, log_file)
        message = error_msg
    except:
        message = critical_error_msg

    if not notified_user:
        sublime.error_message(message.format(logfile_path))
        notified_user = True
        
    traceback.print_exc()
    sublime.status_message("NimLime has encountered an error.")