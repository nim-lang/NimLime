from tempfile import NamedTemporaryFile
import os

import NimLime
from sublime_plugin import TextCommand
from sublime import Region
from utils.misc import NimLimeMixin
from utils.idetools import Idetools

import sublime

NimLime.add_module(__name__)

class GotodefCommand(TextCommand, NimLimeMixin):

    def run(self, edit):
        filename = self.view.file_name()
        sels = self.view.sel()

        if filename is None or not filename.endswith(".nim"):
            return

        for sel in sels:
            pos = self.view.rowcol(sel.begin())
            line = pos[0] + 1
            col = pos[1]

            Idetools.lookup(self, True, filename, line, col)