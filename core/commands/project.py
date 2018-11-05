# coding=utf-8
"""
User commands for setting the Nim project file.
"""
import os

from sublime_plugin import WindowCommand

from NimLime.core.utils.error_handler import catch_errors
from NimLime.core.utils.mixins import NimLimeMixin
from NimLime.core.utils.project import _get_project_file, set_nim_project


class SetProjectCommand(NimLimeMixin, WindowCommand):
    """Sets the main Nim file for the current Sublime Text project."""

    enabled = True
    settings_selector = 'project'

    def __init__(self, *args, **kwargs):
        NimLimeMixin.__init__(self)
        WindowCommand.__init__(self, *args, **kwargs)

    @catch_errors
    def run(self):
        # Retrieve path of project
        st_project = _get_project_file(self.window.id())

        if st_project is not None:
            active_view = self.window.active_view()
            filename = active_view.file_name()

            directory = os.path.dirname(st_project)
            relative_path = os.path.relpath(filename, directory)

            # Set input file
            name, extension = os.path.splitext(relative_path)
            if extension.lower() == '.nim':
                set_nim_project(st_project, relative_path)
