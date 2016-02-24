# coding=utf-8
"""
Functions for retrieving and saving the Nim project file path in a Sublime Text
project.
"""
import json
import os
import platform
import re

import sublime


# Based off of code from https://github.com/facelessuser/FavoriteFiles/
def _get_project_file(win_id):
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
        '..',
        'Settings',
        'Session.sublime_session'
    )

    # Try loading the session data from one of the files
    for session_path in (auto_save_session_path, regular_session_path):
        try:
            with open(session_path) as session_file:
                session_data = json.load(session_file, strict=False)
            break
        except (IOError, ValueError):
            continue
    if session_data is None:
        return None

    # Find the window data corresponding with the given ID
    project = _find_project_in_data(session_data, win_id) or ''

    # Throw out empty project names
    if re.match('.*\\.sublime-project', project) or os.path.exists(project):
        return project

    return None


def _find_project_in_data(session_data, win_id):
    # Iterates through the given session data, searching for the window
    # with the given ID, and returning the project path associated with the
    # window.
    for window in session_data.get('windows', ()):
        if window.get('window_id') == win_id and 'workspace_name' in window:
            project = window['workspace_name']
            if platform.system() == 'Windows':
                project = os.path.normpath(
                    project.lstrip('/').replace('/', ':/', 1)
                )
            return project

    return None


def set_nim_project(st_project, nim_path):
    """
    Associate a nim project file with the current sublime project.
    :type st_project: str
    :type nim_path: str
    """
    if st_project is not None:
        with open(st_project, 'r+') as project_file:
            data = json.loads(project_file.read())
            data['settings']['nim-project'] = nim_path.replace('\\', '/')

            project_file.seek(0)
            project_file.truncate()
            project_file.write(
                json.dumps(data, indent=4)
            )


def get_nim_project(window, view):
    """
    Given a window and view, return the Nim project associated with it.
    :type window: sublime.Window
    :type view: sublime.View
    :rtype: str
    """
    st_project = _get_project_file(window.id())
    result = view.file_name()

    if st_project is not None:
        with open(st_project) as project_file:
            data = json.loads(project_file.read())
            try:
                path = data['settings']['nim-project']

                # Get full path
                directory = os.path.dirname(st_project)
                path = path.replace('/', os.sep)
                result = os.path.join(directory, path)
            except IOError:
                pass
    return result
