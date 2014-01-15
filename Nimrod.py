import sublime
import sublime_plugin
import re
import subprocess
import os
from Project import Utility


class Idetools:

    service = None

    # Fields
    pattern = re.compile(
        '^(?P<cmd>\S+)\s(?P<ast>\S+)\s' +
        '(?P<symbol>\S+)( (?P<instance>\S+))?\s' +
        '(?P<type>[^\t]+)\s(?P<path>[^\t]+)\s' +
        '(?P<line>\d+)\s(?P<col>\d+)\s' +
        '(?P<description>\".+\")?')

    # Methods
    @staticmethod
    def ensure_service(proj=""):
        # If service is running, do nothing
        if Idetools.service is not None and not Idetools.service.poll():
            return

        Idetools.service = subprocess.Popen(
            "nimrod --verbosity:0 serve " +
            "--server.type:stdin " + proj,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True)

        print("Nimrod CaaS now running")

    @staticmethod
    def idetool(win, cmd, filename, line, col, dirtyFile="", extra=""):

        trackType = " --track:"
        filePath = filename
        projFile = Utility.get_nimproject(win)

        if projFile is None:
            projFile = filename

        workingDir = os.path.dirname(projFile)

        if dirtyFile != "":
            trackType = " --trackDirty:"
            filePath = dirtyFile + "," + filePath

        if False:  # TODO - use this when it's not broken in nimrod
            # Ensure IDE Tools service is running
            Idetools.ensure_service()

            # Call the service
            args = "idetools" \
                + trackType \
                + "\"" + filePath + "," + str(line) + "," + str(col) + "\" " \
                + cmd + extra

            print(args)
            return Idetools.service.communicate(args + "\r\n")

        else:
            args = "nimrod --verbosity:0 idetools " \
                + cmd + trackType \
                + "\"" + filePath + "," + str(line) + "," + str(col) \
                + "\" \"" + projFile + "\"" + extra
            print(args)

            output = subprocess.Popen(args,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      shell=True,
                                      cwd=workingDir)

            result = ""
            for result in output.stdout:
                pass

            # print(output.stderr.read())

            output.wait()

        return result

    @staticmethod
    def open_definition(win, filename, line, col):
        arg = filename + ":" + str(line) + ":" + str(col)
        flags = sublime.ENCODED_POSITION

        # TODO - If this is NOT in the same project, mark transient
        # flags |= sublime.TRANSIENT

        win.open_file(arg, flags)

    @staticmethod
    def parse(result):
        m = Idetools.pattern.match(result)

        if m is not None:
            cmd = m.group("cmd")

            if cmd == "def":
                return (m.group("symbol"), m.group("type"),
                        m.group("path"), m.group("line"),
                        m.group("col"), m.group("description"))

        else:
            None

        return None
