import os

from sublime_plugin import WindowCommand
from .utils.error_handler import catch_errors
from .utils.project import get_project_file, set_nim_project
from .utils.mixins import NimLimeMixin


class SetProjectCommand(NimLimeMixin, WindowCommand):

    """ Sets the main Nim file for the current Sublime Text project. """
    enabled = True
    settings_selector = 'project'

    @catch_errors
    def run(self):
        # Retrieve path of project
        st_project = get_project_file(self.window.id())

        if st_project is not None:
            active_view = self.window.active_view()
            filename = active_view.file_name()

            try:
                directory = os.path.dirname(st_project)
                relative_path = os.path.relpath(filename, directory)

                # Set input file
                name, extension = os.path.splitext(relative_path)
                if extension.lower() == ".nim":
                    set_nim_project(st_project, relative_path)

            except:
                pass
