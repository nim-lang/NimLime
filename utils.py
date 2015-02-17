from weakref import proxy
import sublime

busy_frames = [
    '[=     ]', '[ =    ]', '[  =   ]', '[   =  ]', '[    = ]',
    '[     =]', '[    = ]', '[   =  ]', '[  =   ]', '[ =    ]'
]


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


def write_to_output(window, output, tag, via_console=True, clear=False,
                    show_panel=True):
    """
    Writes a string to an output view
    """
    if via_console:
        output_view = window.get_output_panel(tag)
    else:
        for view in window.views():
            if view.settings().get(tag + "_output", False):
                output_view = view
                break
        output_view = window.new_file()
        output_view.set_name(tag + " Output")
        output_view.set_scratch(True)
        output_view.settings().set(tag + "_output", True)

    if clear:
        edit = output_view.begin_edit()
        output_view.erase(edit, sublime.Region(1, output_view.size()))
        output_view.end_edit(edit)

    edit = output_view.begin_edit()
    output_view.insert(edit, output_view.size(), "\n")
    output_view.insert(edit, output_view.size(), output)
    output_view.end_edit(edit)
    if via_console:
        window.run_command("show_panel", {"panel": "output." + tag})
    else:
        window.focus_view(output_view)
