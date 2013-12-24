import sublime, sublime_plugin
import os, tempfile
from Nimrod import Idetools

##Resources
# http://sublimetext.info/docs/en/extensibility/plugins.html
# http://www.sublimetext.com/docs/2/api_reference.html#sublime.View
# http://net.tutsplus.com/tutorials/python-tutorials/how-to-create-a-sublime-text-2-plugin/
# http://www.sublimetext.com/docs/plugin-examples

class LookupCommand(sublime_plugin.TextCommand):

    def lookup(self, filename, line, col):
        result = ""
        if self.view.is_dirty():
            #Generate temp file
            size = self.view.size()

            with tempfile.NamedTemporaryFile(suffix=".nim", bufsize=size, delete=False) as dirtyFile:
                dirtyFile.file.write(
                    self.view.substr(sublime.Region(0, size))
                )
                dirtyFile.file.close()

                result = Idetools.idetool(self.view.window(), "--def", filename, line, col, dirtyFile.name)
                os.remove(dirtyFile.name)

        else:
            result = Idetools.idetool(self.view.window(), "--def", filename, line, col)

        #Parse the result
        value = Idetools.parse(result)

        if value is not None:
            Idetools.open_definition(self.view.window(),
                value[2], value[3], value[4])
        else:
            sublime.status_message("No definition found")

    def run(self, edit):
        filename = self.view.file_name()
        sels     = self.view.sel()

        for sel in sels:
            pos  = self.view.rowcol(sel.begin())
            line = pos[0] + 1
            col  = pos[1]

            self.lookup(filename, line, col)