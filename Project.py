import sublime, sublime_plugin
import os, tempfile
from os.path import exists, basename, getmtime, join, normpath, splitext
import json
import re

class Utility:

    key = "nim-project"

    ## From https://github.com/facelessuser/FavoriteFiles/
    @staticmethod
    def get_project(win_id):
        project     = None
        reg_session = join(sublime.packages_path(), "..", "Settings", "Session.sublime_session")
        auto_save   = join(sublime.packages_path(), "..", "Settings", "Auto Save Session.sublime_session")
        session     = auto_save if exists(auto_save) else reg_session

        if not exists(session) or win_id == None:
            return project

        try:
            with open(session, 'r') as f:
                # Tabs in strings messes things up for some reason
                j = json.JSONDecoder(strict=False).decode(f.read())
                for w in j['windows']:
                    if w['window_id'] == win_id:
                        if "workspace_name" in w:
                            if sublime.platform() == "windows":
                                # Account for windows specific formatting
                                project = normpath(w["workspace_name"].lstrip("/").replace("/", ":/", 1))
                            else:
                                project = w["workspace_name"]
                            break
        except:
            pass

        # Throw out empty project names
        if project == None or re.match(".*\\.sublime-project", project) == None or not exists(project):
            project = None

        return project


    @staticmethod
    def set_nimproject(stProject, nimPath):
        if stProject is not None:
            with open(stProject, "r+") as projFile:
                data = json.JSONDecoder(strict=False).decode(projFile.read())
                data["settings"][Utility.key] = nimPath.replace("\\", "/")

                projFile.seek(0)
                projFile.write(
                    json.dumps(data, indent=4)
                )
                projFile.truncate()


    @staticmethod
    def get_nimproject(window):
        stProject = Utility.get_project(window.id())

        if stProject is not None:
            with open(stProject, 'r') as projFile:
                data = json.JSONDecoder(strict=False).decode(projFile.read())
                try:
                    path = data["settings"][Utility.key]

                    # Get full path
                    directory = os.path.dirname(stProject)
                    path      = path.replace("/", os.sep)
                    return os.path.join(directory, path)
                except: pass


class SetProjectCommand(sublime_plugin.WindowCommand):

    def run(self):
        # Retrieve path of project
        stProject = Utility.get_project(self.window.id())

        if stProject is not None:

            activeView   = self.window.active_view()
            filename     = activeView.file_name()

            try:
                directory = os.path.dirname(stProject)
                relpath   = os.path.relpath(filename, directory)

                # Set input file
                name, ext = os.path.splitext(relpath)

                if ext.lower() == ".nim":
                    Utility.set_nimproject(stProject, relpath)

            except:
                raise #pass
