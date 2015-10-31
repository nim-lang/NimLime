import sublime

from sublime_plugin import EventListener
from nimlime_core.utils.mixins import NimLimeMixin


COMMENT_SCOPE = "comment.line.number-sign.doc-comment"
EMPTY_COMMENT_SUFFIX = ".empty"


class CommentListener(EventListener, NimLimeMixin):
    """
    Continues Document Comment lines.
    """
    active = True
    already_running = True
    settings_selector = 'doccontinue'

    def load_settings(self):
        super(CommentListener, self).load_settings()
        get = self.get_setting

        self.autostop = get('{0}.autostop', True)

    def on_activated(self, view):
        nim_syntax = view.settings().get('syntax', None)
        if self.enabled and not self.active:
            if nim_syntax is not None and "nim" in nim_syntax.lower():
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
            if command == "insert" and args["characters"] == '\n':
                pass
            elif command != "paste":
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

            # Stage 4 Checks (Optional)
            # Checks if the previous line has an empty doc-comment.
            # If so, and if the autostop settings are on, don't add anything
            if self.autostop and view_scope.find(EMPTY_COMMENT_SUFFIX, 36) > 0:
                continue

            # Text Modification Stage
            # Simply insert a doc-comment into the current line.
            view.run_command('insert', {'characters': '## '})
            self.already_running = False
