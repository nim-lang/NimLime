import sublime


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
