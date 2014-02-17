import sublime, sublime_plugin
import os, tempfile

try:  # Python 3
    from NimLime.Nimrod import Idetools
except ImportError:  # Python 2:
    from Nimrod import Idetools

# Resources
# http://sublimetext.info/docs/en/extensibility/plugins.html
# http://www.sublimetext.com/docs/2/api_reference.html#sublime.View
# http://net.tutsplus.com/tutorials/python-tutorials/how-to-create-a-sublime-text-2-plugin/
# http://www.sublimetext.com/docs/plugin-examples


class LookupCommand(sublime_plugin.TextCommand):

    def lookup(self, filename, line, col):
        result = ""
        dirtyFileName = ""

        if self.view.is_dirty():
            # Generate temp file
            size = self.view.size()

            with tempfile.NamedTemporaryFile(suffix=".nim", delete=True) as dirtyFile:
                dirtyFileName = dirtyFile.name
                dirtyFile.file.write(
                    self.view.substr(sublime.Region(0, size)).encode("UTF-8")
                )
                dirtyFile.file.close()

                result = Idetools.idetool(self.view.window(), "--def", filename, line, col, dirtyFile.name)
                dirtyFile.close();

        else:
            result = Idetools.idetool(
                self.view.window(), "--def", filename, line, col)

        # Parse the result
        value = Idetools.parse(result)

        if value is not None:
            lookupFile = filename if (value[2] == dirtyFileName) else value[2]
            self.open_definition(self.view.window(),
                lookupFile, int(value[3]), int(value[4]) + 1)
        else:
            sublime.status_message("No definition found")

    def open_definition(self, window, filename, line, col):
        arg   = filename + ":" + str(line) + ":" + str(col)
        flags = sublime.ENCODED_POSITION

        #TODO - If this is NOT in the same project, mark transient
        # flags |= sublime.TRANSIENT

        window.open_file(arg, flags)

    def run(self, edit):
        filename = self.view.file_name()
        sels = self.view.sel()

        if filename == None or not filename.endswith(".nim"):
            return

        for sel in sels:
            pos = self.view.rowcol(sel.begin())
            line = pos[0] + 1
            col = pos[1]

            self.lookup(filename, line, col)
