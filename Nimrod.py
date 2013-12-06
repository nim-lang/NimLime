import sublime, sublime_plugin
import re, os, subprocess


class Idetools:

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
        m = Idetools.pattern.match(result)

        if m is not None:
            cmd = m.group("cmd")

            if cmd == "def":
                return (m.group("symbol"), m.group("type"),
                 m.group("path"), m.group("line"), 
                 m.group("col"), m.group("description"))

        else: None

        return None