from sublime_plugin import EventListener

# TODO - Features
# Add double line erasure option
# Add setting loading

# TODO - Optimizations
# Erase debug calls
# Inline recursion checking
# Reduce rowcol/textpoint conversions
# Add and use scope selectors for checking?
#  - To check that previous line is empty
#  - To check that current line is an empty line after a doc-comment

COMMENT_SCOPE = "comment.line.number-sign.doc-comment.nimrod"
RECURSION_LEVEL = 0
DEBUG = True


def debug(string):
    if DEBUG:
        print(string)


def recursion_limit(func):
    def aux_recursion_limit(*args, **kwargs):
        global RECURSION_LEVEL
        debug("Pre-start recursion level - " + str(RECURSION_LEVEL))
        RECURSION_LEVEL += 1
        debug("Post-start recursion level - " + str(RECURSION_LEVEL))

        if RECURSION_LEVEL <= 1:
            func(*args, **kwargs)
        else:
            debug("Recursion limited at level " + str(RECURSION_LEVEL))

        debug("Pre-end recursion level - " + str(RECURSION_LEVEL))
        RECURSION_LEVEL -= 1
        debug("Post-end recursion level - " + str(RECURSION_LEVEL))
    return aux_recursion_limit


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

    @recursion_limit
    def on_modified(self, view):

        # Pre-process stage
        if not self.active:
            debug("Pre-process failure - Inactive")
            return

        rowcol_set = [view.rowcol(s.a) for s in view.sel() if s.empty()]
        for row, col in rowcol_set:
            # Stage 1 Checks
            # Checks if the last history action was a newline insertion.
            command, args, repeats = view.command_history(0, False)
            if (command == "insert" and args["characters"] == '\n'):
                debug("Stage 1 success - A")
            elif (command == "paste"):
                debug("Stage 1 success - B")
            else:
                debug("Stage 1 failure - 1")
                return

            # Used to determine if the user is undoing the insertion.
            command, args, repeats = view.command_history(1, False)
            if command == "continueComment":
                debug("Stage 1 failure - 2")
                return

            # Stage 2 Checks
            # Checks that the current line has only whitespace characters.

            current_line = view.line(view.text_point(row, col))
            if (col == 0) or (view.substr(current_line).isspace()):
                debug("Stage 2 success")
            else:
                debug("Stage 2 failure")
                return

            # Stage 3 Checks
            # Checks that the previous line had a doc-comment.
            last_line = view.line(view.text_point(row - 1, 0))
            debug(view.scope_name(last_line.b))
            if COMMENT_SCOPE in view.scope_name(last_line.b):
                debug("Stage 3 success")
            else:
                debug("Stage 3 failure")
                return

            # Stage 4 Checks (Optional)
            # Checks if the previous line has an empty doc-comment.
            # view.substr(current_line)

            # Text Modification Stage
            # Simply insert a doc-comment into the current line.
            insertion_edit = view.begin_edit("continueComment")
            view.insert(insertion_edit, view.text_point(row, col), "## ")
            view.end_edit(insertion_edit)
