from sublime_plugin import EventListener
from utils import NimLimeMixin
import sublime

# TODO - Features
# Add double line erasure option

# TODO - Optimizations
# Reduce rowcol/textpoint conversions
# Add and use scope selectors for checking?
#  - To check that previous line is empty
#  - To check that current line is an empty line after a doc-comment
#  - Use startswith instead of in

COMMENT_SCOPE = "comment.line.number-sign.doc-comment"
EMPTY_COMMENT_SUFFIX = ".empty"

settings = sublime.load_settings('NimLime.sublime-settings')


class CommentListener(EventListener, NimLimeMixin):

    """
    Continues docComment lines.
    """
    active = True
    already_running = True

    def load_settings(self):
        get = lambda key: settings.get(key)
        self.enabled = get('docontinue.enabled')
        self.autostop = get('docontinue.autostop')

    def on_activated(self, view):
        nim_syntax = view.settings().get('syntax', None)
        if self.enabled and not self.active:
            if nim_syntax is not None and "nim" in nim_syntax:
                self.active = True

    def on_deactivated(self, view):
        self.active = False

    def on_modified(self, view):
        # Pre-process stage
        if not self.active:
            return

        if self.already_running:
            self.already_running = False
            return

        self.already_running = True
        rowcol_set = [view.rowcol(s.a) for s in view.sel() if s.empty()]
        for row, col in rowcol_set:

            # Stage 1 Checks
            # Checks if the last history action was a newline insertion.
            command, args, repeats = view.command_history(0, False)
            if (command == "insert" and args["characters"] == '\n'):
                pass
            elif (command != "paste"):
                self.already_running = False
                continue

            # Checks if the user is undoing the insertion.
            command, args, repeats = view.command_history(1, False)
            if command == "continueComment":
                self.already_running = False
                continue

            current_point = view.text_point(row, col)
            current_line = view.line(current_point)
            if (col != 0) and not (view.substr(current_line).isspace()):
                self.already_running = False
                continue

            # Stage 3 Checks
            # Checks that the previous line had a doc-comment.
            last_line = view.line(view.text_point(row - 1, 0))
            view_scope = view.scope_name(last_line.b)
            if COMMENT_SCOPE not in view_scope:
                self.already_running = False
                continue

            print("here")
            # Stage 4 Checks (Optional)
            # Checks if the previous line has an empty doc-comment.
            # If so, and if the autostop settings are on, don't add anything
            if self.autostop and view_scope.find(EMPTY_COMMENT_SUFFIX, 36) > 0:
                continue

            # Text Modification Stage
            # Simply insert a doc-comment into the current line.
            # insertion_edit = view.begin_edit("continueComment")
            view.run_command('insert', {'characters': '## '})
            # view.end_edit(insertion_edit)
            self.already_running = False
