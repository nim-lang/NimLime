from weakref import proxy, WeakKeyDictionary
import sublime

busy_frames = ['.', '..', '...']
output_handle_mappings = WeakKeyDictionary()


def send_self(arg):
    """ A decorator which sends a generator a reference to itself via the first
    'yield' used.
    Useful for creating generators that can leverage callback-based functions
    in a linear style, by passing their 'send' or 'next' methods as callbacks.

    Note that by default, the generator reference sent is a weak reference.
    To override this behavior, pass 'True' as the first argument to the
    decorator.
    """
    use_proxy = True

    # We either directly call this, or return it, to be called by python's
    # decorator mechanism.
    def _send_self(func):
        def send_self_wrapper(*args, **kwargs):
            generator = func(*args, **kwargs)
            generator.send(None)
            if use_proxy:
                generator.send(proxy(generator))
            else:
                generator.send(generator)
        return send_self_wrapper

    # If the argument is a callable, we've been used without being directly
    # passed an arguement by the user, and thus should call _send_self directly
    if callable(arg):
        # No arguments, this is the decorator
        return _send_self(arg)
    else:
        # Someone has used @send_self(True), and thus we need to return
        # _send_self to be called indirectly.
        use_proxy = False
        return _send_self


class FlagObject(object):

    """
    Used with loop_status_msg to signal when a status message loop should end.
    """
    break_status_loop = False

    def __init__(self):
        self.break_status_loop = False


def loop_status_msg(frames, speed, flag_obj, view=None, key=''):
    """ Creates a generator which continually sets the status text to a series
    of strings.
    Useful for creating 'animations' in the status bar.

    If a view is given, sets the status for that view only (along with an
    optional key). To stop the loop, the given flag object must have it's
    'break_status_loop' attribute set to a truthy value.
    """
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
        while not flag_obj.break_status_loop:
            for frame in frames:
                set_status(frame)
                yield set_timeout(self.next, int(speed * 1000))
        if callable(flag_obj.break_status_loop):
            flag_obj.break_status_loop()
        yield

    sublime.set_timeout(loop_status_generator, 0)


def get_output_view(tag, strategy, window, views=None):
    """
    Retrieves an output using the given strategy, window, and views.
    """
    if views is None:
        views = all_views()

    # Console Strategy
    if strategy == 'console':
        return window.get_output_panel(tag)

    # Grouped strategy
    if strategy == 'grouped':
        for view in views:
            if view.settings().get('output_tag', False) is not False:
                return view

    if (strategy == 'separate') or (strategy == 'grouped'):
        result = window.new_file()
        result.set_name(tag + " Output")
        result.set_scratch(True)
        result.settings().set('output_tag', tag)
        return result


def write_output_view(view, content, clear):
    """
    Writes to an output view.
    """
    edit = view.begin_edit()
    if clear or view.size() == 0:
        view.erase(edit, sublime.Region(0, view.size()))
    else:
        view.insert(edit, view.size(), "\n\n")
    view.insert(edit, view.size(), content)
    view.end_edit(edit)


def show_output_view(view, is_console=False):
    """
    Shows an output view.
    """
    window = view.window()
    if is_console:
        tag = view.settings().get('output_tag')
        window.run_command("show_panel", {"panel": "output." + tag})
    else:
        window.focus_view(view)


def view_has_nim_syntax(view=None):
    """
    Tests whether the given view (or the active view) currently has 'Nim' as
    the selected syntax.
    """
    if view is None:
        view = sublime.active_window().active_view()
    return 'nim' in view.settings().get('syntax', '').lower()


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


def all_views():
    for window in sublime.windows():
        for view in window.views():
            yield view


def trim_region(view, region):
    """
    Trim a region of whitespace.
    """
    text = view.substr(region)
    start = region.a + ((len(text) - 1) - (len(text.strip()) - 1))
    end = region.b - ((len(text) - 1) - (len(text.rstrip()) - 1))
    return sublime.Region(start, end)
