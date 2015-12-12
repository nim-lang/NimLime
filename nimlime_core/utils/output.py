# coding=utf-8
"""
Functions providing a uniform way to write command/process output to a Sublime
Text view.
"""
import sublime


def get_output_view(tag, strategy, name, switch_to, fallback_window):
    """
    Retrieves an output using the given strategy, window, and views.

    Args:
        fallback_window ():
        switch_to ():
        name ():
        strategy ():
        tag ():
    """
    window_list = sublime.windows()

    # Console Strategy
    if strategy == 'console':
        view = fallback_window.active_view()
        view.settings().set('output_tag', tag)
        show_view(fallback_window, view, True)
        return fallback_window, fallback_window.get_output_panel(tag)

    # Grouped strategy
    elif strategy == 'grouped':
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


def show_view(window, view, is_console):
    # Workaround for ST2 bug

    if is_console:
        tag = view.settings().get('output_tag')
        window.run_command("show_panel", {"panel": "output." + tag})
    else:
        window.focus_view(view)


def format_tag(tag, window, view):
    return tag.format(
            view_id=view.id(),
            buffer_id=view.id(),
            file_name=view.file_name(),
            view_name=view.name(),
            window_id=window.id()
    )
