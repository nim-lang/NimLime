from sublime_plugin import EventListener

# TODO
# Add double line erasure option
# Add setting loading
# Fix commont/doComment distinction

COMMENT_SCOPE = "comment.line.number-sign.nimrod"
DEBUG = False


def debug(string):
    if DEBUG:
        print(string)


class CommentListener(EventListener):

    """
    Continues docComment lines.
    """

    def __init__(self):
        debug("CommentListener active.")
        self.active = True

    def on_activated(self, view):
        nim_syntax = view.settings().get('syntax', None)
        if not self.active:
            if nim_syntax is not None and "nimrod" in nim_syntax:
                self.active = True

    def on_deactivated(self, view):
        self.active = False

    def on_modified(self, view):
        if not self.active:
            return
        rowcol_set = [view.rowcol(s.a) for s in view.sel() if s.empty()]

        for row, col in rowcol_set:

            # Stage 2
            command, args, repeats = view.command_history(0, False)
            if (command == "insert" and args["characters"] == '\n'):
                debug("Stage 2 success - A")
            elif (command == "paste"):
                debug("Stage 2 success - B")
            else:
                debug("Stage 2 failure")
                return

            command, args, repeats = view.command_history(1, False)
            if command == "continueComment":
                return

            # Stage 3
            current_line = view.line(view.text_point(row, col))
            if view.substr(current_line).isspace():
                debug("Stage 3 success")
            else:
                debug("Stage 3 failure")
                return

            # Stage 1
            last_line = view.line(view.text_point(row - 1, 0))
            debug(view.scope_name(last_line.b))
            if COMMENT_SCOPE in view.scope_name(last_line.b):
                debug("Stage 1 success")
            else:
                debug("Stage 1 failure")
                return
            insertion_edit = view.begin_edit("continueComment")
            view.insert(insertion_edit, view.text_point(row, col), "## ")
            view.end_edit(insertion_edit)
