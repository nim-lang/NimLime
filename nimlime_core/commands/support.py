# coding=utf-8
"""
Support commands for NimLime.
These commands are for configuring and getting information about the NimLime
plugin itself.
"""
import webbrowser

from sublime_plugin import ApplicationCommand


class NimLimeOpenSupport(ApplicationCommand):
    "Open NimLime's Support Page"
    def run(self):
        webbrowser.open("https://github.com/Varriount/NimLime/issues", 2)