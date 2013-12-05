import sublime, sublime_plugin
import os, subprocess
import re

##Resources
# http://sublimetext.info/docs/en/extensibility/plugins.html
# http://www.sublimetext.com/docs/2/api_reference.html#sublime.View
# http://net.tutsplus.com/tutorials/python-tutorials/how-to-create-a-sublime-text-2-plugin/
# http://www.sublimetext.com/docs/plugin-examples

class Nimrod:

    ## Fields
    pattern = re.compile(
        '^(?P<cmd>\S+)\s(?P<ast>\S+)\s' + 
        '(?P<symbol>\S+)( (?P<instance>\S+))?\s' +
        '(?P<type>[^\t]+)\s(?P<path>[^\t]+)\s' + 
        '(?P<line>\d+)\s(?P<col>\d+)\s' +
        '(?P<description>\".+\")?')

    ## Methods
    @staticmethod
    def idetool(cmd, filename, line, col, extra = ""):
        args = "nimrod --verbosity:0 idetools " \
             + cmd + " --track:" \
             + filename + "," + str(line) + "," + str(col) \
             + " " + filename + extra

        result = ""
        for result in os.popen(args): pass
        return result

    @staticmethod
    def open_definition(win, filename, line, col):
        arg   = filename + ":" + str(line) + ":" + str(col)
        flags = sublime.ENCODED_POSITION

        #TODO - If this is NOT in the same project, mark transient
        # flags |= sublime.TRANSIENT

        win.open_file(arg, flags)

    @staticmethod
    def parse(result):
        print(result)
        m = Nimrod.pattern.match(result)

        if m is not None:
            cmd = m.group("cmd")

            if cmd == "def":
                return (m.group("symbol"), m.group("type"),
                 m.group("path"), m.group("line"), 
                 m.group("col"), m.group("description"))

        else: None

        return None


class LookupCommand(sublime_plugin.TextCommand):

    def lookup(self, filename, line, col):
        result = Nimrod.idetool("--def", filename, line, col)

        #Parse the result
        value = Nimrod.parse(result)

        if value is not None:
            Nimrod.open_definition(self.view.window(), 
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