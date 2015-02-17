from sublime_plugin import EventListener
import sublime

# TODO - Features
# Add double line erasure option

# TODO - Optimizations
# Reduce rowcol/textpoint conversions
# Add and use scope selectors for checking?
#  - To check that previous line is empty
#  - To check that current line is an empty line after a doc-comment

COMMENT_SCOPE = "comment.line.number-sign.doc-comment.nim"
RECURSION_LEVEL = 0


def debug(string):
    if False:
        print(string)

settings = None
doccontinue_enabled = None


def update_settings():
    """ Update the currently loaded settings.
    Runs as a callback when settings are modified, and manually on startup.
    All settings variables should be initialized/modified here
    """
    debug('Entered update_settings')

    def load_key(key):
        globals()[key.replace('.', '_')] = settings.get(key)

    # Settings for checking a file on saving it
    load_key('doccontinue.enabled')
    debug('Exiting update_settings')


def load_settings():
    """ Load initial settings object, and manually run update_settings """
    global settings
    debug('Entered load_settings')
    settings = sublime.load_settings('NimLime.sublime-settings')
    settings.clear_on_change('reload')
    settings.add_on_change('reload', update_settings)
    update_settings()
    debug('Exiting load_settings')


# Hack to lazily initialize ST2 settings
if int(sublime.version()) < 3000:
    sublime.set_timeout(load_settings, 1000)


class CommentListener(EventListener):

    """
    Continues docComment lines.
    """
    active = True
    already_running = True

    def on_activated(self, view):
        debug('Entered CommentListener.on_activated')
        nim_syntax = view.settings().get('syntax', None)
        if doccontinue_enabled and not self.active:
            if nim_syntax is not None and "nim" in nim_syntax:
                self.active = True

    def on_deactivated(self, view):
        debug('Entered CommentListener.on_deactivated')
        self.active = False

    def on_modified(self, view):
        # Pre-process stage
        if not self.active:
            debug("Pre-process failure - Inactive")
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
                debug("Stage 1 success - A")
                pass
            elif (command == "paste"):
                debug("Stage 1 success - B")
                pass
            else:
                debug("Stage 1 failure - 1")
                self.already_running = False
                return

            # Used to determine if the user is undoing the insertion.
            command, args, repeats = view.command_history(1, False)
            if command == "continueComment":
                debug("Stage 1 failure - 2")
                self.already_running = False
                return

            current_point = view.text_point(row, col)
            current_line = view.line(current_point)
            if (col == 0) or (view.substr(current_line).isspace()):
                debug("Stage 2 success")
                pass
            else:
                debug("Stage 2 failure")
                self.already_running = False
                return

            # Stage 3 Checks
            # Checks that the previous line had a doc-comment.
            last_line = view.line(view.text_point(row - 1, 0))
            debug(view.scope_name(last_line.b))
            if COMMENT_SCOPE in view.scope_name(last_line.b):
                debug("Stage 3 success")
                pass
            else:
                debug("Stage 3 failure")
                self.already_running = False
                return

            # Stage 4 Checks (Optional)
            # Checks if the previous line has an empty doc-comment.
            # view.substr(current_line)

            # Text Modification Stage
            # Simply insert a doc-comment into the current line.
            insertion_edit = view.begin_edit("continueComment")
            view.insert(insertion_edit, current_point, "## ")
            view.end_edit(insertion_edit)
            self.already_running = False
