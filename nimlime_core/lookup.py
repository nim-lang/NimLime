from tempfile import NamedTemporaryFile

from sublime_plugin import TextCommand
from .utils.mixins import NimLimeMixin
from .utils.idetools import Idetools

# Resources
# http://sublimetext.info/docs/en/extensibility/plugins.html
# http://www.sublimetext.com/docs/2/api_reference.html#sublime.View
# http://net.tutsplus.com/tutorials/python-tutorials/how-to-create-a-sublime-text-2-plugin/
# http://www.sublimetext.com/docs/plugin-examples


class LookupCommand(NimLimeMixin, TextCommand):

    def run(self, edit):
        filename = self.view.file_name()
        sels = self.view.sel()

        if filename is None or not filename.endswith(".nim"):
            return

        for sel in sels:
            pos = self.view.rowcol(sel.begin())
            line = pos[0] + 1
            col = pos[1]

            Idetools.lookup(self, False, filename, line, col)
