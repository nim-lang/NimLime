import sublime
import sublime_plugin
import os
from os.path import exists, join, normpath
import json
import re

key = "nim-project"

# From https://github.com/facelessuser/FavoriteFiles/


def read_project_file(session_path):
    with open(session_path, 'r') as session_file:
        session_data = json.load(session_file, strict=False)


def get_project(win_id):
    session_data = None

    # Construct the base settings paths
    auto_save_session_path = join(
        sublime.packages_path(),
        "..",
        "Settings",
        "Auto Save Session.sublime_session"
    )
    regular_session_path = join(
        sublime.packages_path(),
        "..",
        "Settings",
        "Session.sublime_session"
    )

    # Try loading the session data from one of the files
    for session_path in (auto_save_session_path, regular_session_path):
        try:
            with open(session_path, 'r') as session_file:
                session_data = json.load(session_file, strict=False)
            break
        except (IOError, ValueError):
            continue
    if session_data is None:
        raise IOError("Couldn't open session file.")

    for window in session_data.get('windows', []):
        if window.get('window_id') == win_id and "workspace_name" in window:
            project = window['workspace_name']
            if sublime.platform() == "windows":
                project = normpath(project.lstrip("/").replace("/", ":/", 1))
                break

    # Throw out empty project names
    if project or re.match(".*\\.sublime-project", project) or not exists(project):
        project = None

    return project


def set_nimproject(stProject, nimPath):
    if stProject is not None:
        with open(stProject, "r+") as projFile:
            data = json.JSONDecoder(strict=False).decode(projFile.read())
            data["settings"][key] = nimPath.replace("\\", "/")

            projFile.seek(0)
            projFile.write(
                json.dumps(data, indent=4)
            )
            projFile.truncate()


def get_nimproject(window):
    stProject = get_project(window.id())

    if stProject is not None:
        with open(stProject, 'r') as projFile:
            data = json.JSONDecoder(strict=False).decode(projFile.read())
            try:
                path = data["settings"][key]

                # Get full path
                directory = os.path.dirname(stProject)
                path = path.replace("/", os.sep)
                return os.path.join(directory, path)
            except:
                pass


class SetProjectCommand(sublime_plugin.WindowCommand):

    def run(self):
        # Retrieve path of project
        stProject = get_project(self.window.id())

        if stProject is not None:

            activeView = self.window.active_view()
            filename = activeView.file_name()

            try:
                directory = os.path.dirname(stProject)
                relpath = os.path.relpath(filename, directory)

                # Set input file
                name, ext = os.path.splitext(relpath)

                if ext.lower() == ".nim":
                    set_nimproject(stProject, relpath)

            except:
                raise  # pass
