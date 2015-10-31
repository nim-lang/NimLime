import os
import json
import re

import sublime


# Based off of code from https://github.com/facelessuser/FavoriteFiles/
def get_project_file(win_id):
    session_data = None

    # Construct the base settings paths
    auto_save_session_path = os.path.join(
        sublime.packages_path(),
        '..',
        'Settings',
        'Auto Save Session.sublime_session'
    )
    regular_session_path = os.path.join(
        sublime.packages_path(),
        "..",
        'Settings',
        'Session.sublime_session'
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
        return None

    # Find the window data corresponding with the given ID
    project = find_project_in_data(session_data, win_id) or ""

    # Throw out empty project names
    if re.match(".*\\.sublime-project", project) or os.path.exists(project):
        return project

    return None


def find_project_in_data(session_data, win_id):
    # Iterates through the given session data, searching for the window
    # with the given ID, and returning the project path associated with the
    # window.
    for window in session_data.get('windows', ()):
        if window.get('window_id') == win_id and 'workspace_name' in window:
            project = window['workspace_name']
            if sublime.platform() == 'windows':
                project = os.path.normpath(
                    project.lstrip("/").replace("/", ":/", 1)
                )
            return project

    return None


def set_nim_project(st_project, nim_path):
    if st_project is not None:
        with open(st_project, "r+") as project_file:
            data = json.loads(project_file.read())
            data['settings']['nim-project'] = nim_path.replace("\\", "/")

            project_file.seek(0)
            project_file.truncate()
            project_file.write(
                json.dumps(data, indent=4)
            )


def get_nim_project(window):
    st_project = get_project_file(window.id())

    if st_project is not None:
        with open(st_project, 'r') as projFile:
            data = json.loads(projFile.read())
            try:
                path = data['settings']['nim-project']

                # Get full path
                directory = os.path.dirname(st_project)
                path = path.replace("/", os.sep)
                return os.path.join(directory, path)
            except:
                pass
    return ''
