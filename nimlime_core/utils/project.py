import os
import json
import re

import sublime


key = 'nim-project'

# Based off of code from https://github.com/facelessuser/FavoriteFiles/


def read_project_file(session_path):
    with open(session_path, 'r') as session_file:
        session_data = json.load(session_file, strict=False)


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

    for window in session_data.get('windows', []):
        if window.get('window_id') == win_id and 'workspace_name' in window:
            project = window['workspace_name']
            if sublime.platform() == 'windows':
                project = os.path.normpath(
                    project.lstrip("/").replace("/", ":/", 1))
                break

            # Throw out empty project names
            if project or re.match(".*\\.sublime-project",
                                   project) or not os.path.exists(project):
                project = None
            return project

    return None

def set_nim_project(st_project, nim_path):
    if st_project is not None:
        with open(st_project, "r+") as project_file:
            data = json.loads(project_file.read())
            data['settings'][key] = nim_path.replace("\\", "/")

            project_file.seek(0)
            project_file.truncate()
            project_file.write(
                json.dumps(data, indent=4)
            )


def get_nim_project(window):
    stProject = get_project_file(window.id())

    if stProject is not None:
        with open(stProject, 'r') as projFile:
            data = json.loads(projFile.read())
            try:
                path = data['settings'][key]

                # Get full path
                directory = os.path.dirname(stProject)
                path = path.replace("/", os.sep)
                return os.path.join(directory, path)
            except:
                pass
    return ''