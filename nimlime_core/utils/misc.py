from weakref import proxy, WeakKeyDictionary
from sys import version_info
from functools import wraps
import subprocess

import sublime


busy_frames = ['.', '..', '...']
output_handle_mappings = WeakKeyDictionary()


def debug(string):
    if False:
        print(string)


def get_next_method(generator_instance):
    if version_info[0] >= 3:
        return generator_instance.__next__
    else:
        return generator_instance.next


def send_self(use_proxy):
    """ A decorator which sends a generator a reference to itself via the first
    'yield' used.
    Useful for creating generators that can leverage callback-based functions
    in a linear style, by passing their 'send' method as callbacks.

    Note that by default, the generator instance reference sent is a weakly
    referenced proxy. To override this behavior, pass `False` or
    `use_proxy=False` as the first argument to the decorator.
    """
    _use_proxy = True

    # We either directly call this, or return it, to be called by python's
    # decorator mechanism.
    def _send_self(func):
        @wraps(func)
        def send_self_wrapper(*args, **kwargs):
            generator = func(*args, **kwargs)
            generator.send(None)
            if _use_proxy:
                generator.send(proxy(generator))
            else:
                generator.send(generator)

        return send_self_wrapper

    # If the argument is a callable, we've been used without being directly
    # passed an arguement by the user, and thus should call _send_self directly
    if callable(use_proxy):
        # No arguments, this is the decorator
        return _send_self(use_proxy)
    else:
        # Someone has used @send_self(bool), and thus we need to return
        # _send_self to be called indirectly.
        _use_proxy = use_proxy
        return _send_self


def loop_status_msg(frames, speed, view=None, key=''):
    """ Creates and runs a generator which continually sets the status
    text to a series of strings. Returns a function which, when called,
    stops the generator.
    Useful for creating 'animations' in the status bar.

    Parameters:
        `frames`: A sequence of strings displayed in order on the status bar
        `speed`: Delay between frame shifts, in seconds
        `view`: View to set the status on. If not provided, then
                sublime.status_message is used.
        `key`: Key used when setting the status on a view. Ignored if no
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
    def loop_status_generator():
        self = yield

        # Get the correct status function
        set_timeout = sublime.set_timeout
        if view is None:
            set_status = sublime.status_message
        else:
            set_status = lambda f: view.set_status(key, f)

        # Main loop
        while not flag.flag:
            for frame in frames:
                set_status(frame)
                yield set_timeout(get_next_method(self), int(speed * 1000))
        if callable(flag.flag):
            flag.flag()
        yield

    def stop_status_loop(callback=True):
        flag.flag = callback

    sublime.set_timeout(loop_status_generator, 0)
    return stop_status_loop


class _FlagObject(object):

    """
    Used with loop_status_msg to signal when a status message loop should end.
    """
    __slots__ = ['flag']

    def __init__(self):
        self.flag = False


def get_output_view(tag, strategy, name, switch_to, fallback_window):
    """
    Retrieves an output using the given strategy, window, and views.
    """
    window_list = sublime.windows()

    # Console Strategy
    if strategy == 'console':
        view = fallback_window.active_view()
        view.settings().set('output_tag', tag)
        show_view(fallback_window, view, True)
        return fallback_window, fallback_window.get_output_panel(tag)

    # Grouped strategy
    if strategy == 'grouped':
        for window in window_list:
            view_list = window.views()
            for view in view_list:
                if view.settings().get('output_tag') == tag:
                    if switch_to:
                        show_view(window, view, False)
                    return window, view

    if (strategy == 'separate') or (strategy == 'grouped'):
        w = sublime.active_window()
        v = w.active_view()

        result = fallback_window.new_file()
        result.set_name(name)
        result.set_scratch(True)
        result.settings().set('output_tag', tag)
        if switch_to:
            show_view(fallback_window, result, False)
        else:
            show_view(w, v, False)
        return fallback_window, result


def write_to_view(view, content, clear):
    """
    Writes to a view.
    """
    edit = view.begin_edit()
    if clear or view.size() == 0:
        view.erase(edit, sublime.Region(0, view.size()))
    else:
        view.insert(edit, view.size(), "\n\n")
    view.insert(edit, view.size(), content)
    view.end_edit(edit)


def show_view(window, view, is_console):
    """
    Shows an output view.
    """

    # Workaround for ST2 bug

    if is_console:
        tag = view.settings().get('output_tag')
        window.run_command("show_panel", {"panel": "output." + tag})
    else:
        window.focus_view(view)


def format_tag(tag, window=None, view=None):
    view_id = ''
    buffer_id = ''
    file_name = ''
    view_name = ''
    window_id = ''

    if view is not None:
        view_id = view.id()
        buffer_id = view.id()
        file_name = view.file_name()
        view_name = view.name()

    if window is not None:
        window_id = window.id()

    return tag.format(
        view_id=view_id,
        buffer_id=buffer_id,
        file_name=file_name,
        view_name=view_name,
        window_id=window_id
    )


def view_has_nim_syntax(view=None):
    """
    Tests whether the given view (or the active view) currently has 'Nim' as
    the selected syntax.
    """
    if view is None:
        view = sublime.active_window().active_view()
    return 'nim' in view.settings().get('syntax', '').lower()


def trim_region(view, region):
    """
    Trim a region of whitespace.
    """
    text = view.substr(region)
    start = region.a + ((len(text) - 1) - (len(text.strip()) - 1))
    end = region.b - ((len(text) - 1) - (len(text.rstrip()) - 1))
    return sublime.Region(start, end)


def escape_shell(s):
    "'" + s.replace("'", "'\"'\"'") + "'"
    return s


def run_process(cmd, callback=None):
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        bufsize=0
    )

    output = process.communicate()[0].decode('UTF-8')
    returncode = process.returncode

    if callback is not None:
        sublime.set_timeout(lambda: callback((output, returncode)), 0)
    else:
        return output


