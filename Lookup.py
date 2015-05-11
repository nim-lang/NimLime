from sublime_plugin import TextCommand
from sublime import Region
from utils import NimLimeMixin
from tempfile import NamedTemporaryFile
import sublime
import os

try:  # Python 3
    from NimLime.Nim import Idetools
except ImportError:  # Python 2:
    from Nim import Idetools

# Resources
# http://sublimetext.info/docs/en/extensibility/plugins.html
# http://www.sublimetext.com/docs/2/api_reference.html#sublime.View
# http://net.tutsplus.com/tutorials/python-tutorials/how-to-create-a-sublime-text-2-plugin/
# http://www.sublimetext.com/docs/plugin-examples


class LookupCommand(TextCommand, NimLimeMixin):

    def lookup(self, filename, line, col):
        result = ""
        dirty_file_name = ""

        if self.view.is_dirty():
            # Generate temp file
            size = self.view.size()

            with NamedTemporaryFile(suffix=".nim", delete=False) as dirty_file:
                dirty_file_name = dirty_file.name
                dirty_file.file.write(
                    self.view.substr(Region(0, size)).encode("UTF-8")
                )
                dirty_file.file.close()

                result = Idetools.idetool(
                    self.view.window(),
                    "--def",
                    filename,
                    line,
                    col,
                    dirty_file.name
                )
                dirty_file.close()

            try:
                os.unlink(dirty_file.name)
            except OSError:
                pass
        else:
            result = Idetools.idetool(
                self.view.window(), "--def", filename, line, col)

        # Parse the result
        value = Idetools.parse(result)

        if value is not None:
            if value[2] == dirty_file_name:
                lookup_file = filename
            else:
                lookup_file = value[2]
            self.open_definition(
                self.view.window(),
                lookup_file,
                int(value[3]),
                int(value[4]) + 1
            )
        else:
            sublime.status_message("No definition found")

    def open_definition(self, window, filename, line, col):
        arg = filename + ":" + str(line) + ":" + str(col)
        flags = sublime.ENCODED_POSITION

        # TODO - If this is NOT in the same project, mark transient
        # flags |= sublime.TRANSIENT

        window.open_file(arg, flags)

    def run(self, edit):
        filename = self.view.file_name()
        sels = self.view.sel()

        if filename is None or not filename.endswith(".nim"):
            return

        for sel in sels:
            pos = self.view.rowcol(sel.begin())
            line = pos[0] + 1
            col = pos[1]

            self.lookup(filename, line, col)
