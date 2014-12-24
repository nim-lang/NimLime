from sublime_plugin import EventListener
import sublime

# TODO - Features
# Add double line erasure option

# TODO - Optimizations
# Inline recursion checking
# Reduce rowcol/textpoint conversions
# Add and use scope selectors for checking?
#  - To check that previous line is empty
#  - To check that current line is an empty line after a doc-comment

COMMENT_SCOPE = "comment.line.number-sign.doc-comment.nim"
RECURSION_LEVEL = 0
# DEBUG = False


# def debug(string):
#     if DEBUG:
#         print(string)


def recursion_limit(func):
    def aux_recursion_limit(*args, **kwargs):
        global RECURSION_LEVEL
        # debug("Pre-start recursion level - " + str(RECURSION_LEVEL))
        RECURSION_LEVEL += 1
        # debug("Post-start recursion level - " + str(RECURSION_LEVEL))

        if RECURSION_LEVEL <= 1:
            func(*args, **kwargs)
        # else:
            # debug("Recursion limited at level " + str(RECURSION_LEVEL))

        # debug("Pre-end recursion level - " + str(RECURSION_LEVEL))
        RECURSION_LEVEL -= 1
        # debug("Post-end recursion level - " + str(RECURSION_LEVEL))
    return aux_recursion_limit


class CommentListener(EventListener):

    """
    Continues docComment lines.
    """

    def __init__(self):
        # debug("CommentListener active.")
        def activation_change():
            nim_settings = sublime.load_settings("NimLime")
            active = nim_settings.get("enable_continuation", "true")
            if active.lower == "true":
                self.active = True
            else:
                self.active = False
        nim_settings = sublime.load_settings("NimLime")
        nim_settings.add_on_change("enable_continuation", activation_change)
        activation_change()

    def on_activated(self, view):
        nim_syntax = view.settings().get('syntax', None)
        if not self.active:
            if nim_syntax is not None and "nim" in nim_syntax:
                self.active = True

    def on_deactivated(self, view):
        self.active = False

    @recursion_limit
    def on_modified(self, view):

        # Pre-process stage
        if not self.active:
            # debug("Pre-process failure - Inactive")
            return

        rowcol_set = [view.rowcol(s.a) for s in view.sel() if s.empty()]
        for row, col in rowcol_set:
            # Stage 1 Checks
            # Checks if the last history action was a newline insertion.
            command, args, repeats = view.command_history(0, False)
            if (command == "insert" and args["characters"] == '\n'):
                # debug("Stage 1 success - A")
                pass
            elif (command == "paste"):
                # debug("Stage 1 success - B")
                pass
            else:
                # debug("Stage 1 failure - 1")
                return

            # Used to determine if the user is undoing the insertion.
            command, args, repeats = view.command_history(1, False)
            if command == "continueComment":
                # debug("Stage 1 failure - 2")
                return

            current_point = view.text_point(row, col)
            current_line = view.line(current_point)
            if (col == 0) or (view.substr(current_line).isspace()):
                # debug("Stage 2 success")
                pass
            else:
                # debug("Stage 2 failure")
                return

            # Stage 3 Checks
            # Checks that the previous line had a doc-comment.
            last_line = view.line(view.text_point(row - 1, 0))
            # debug(view.scope_name(last_line.b))
            if COMMENT_SCOPE in view.scope_name(last_line.b):
                # debug("Stage 3 success")
                pass
            else:
                # debug("Stage 3 failure")
                return

            # Stage 4 Checks (Optional)
            # Checks if the previous line has an empty doc-comment.
            # view.substr(current_line)

            # Text Modification Stage
            # Simply insert a doc-comment into the current line.
            insertion_edit = view.begin_edit("continueComment")
            view.insert(insertion_edit, current_point, "## ")
            view.end_edit(insertion_edit)
