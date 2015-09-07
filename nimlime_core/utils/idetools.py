import re
import subprocess
import socket
import sys
from time import sleep

from .project import get_project_file
import sublime


class Idetools:
    # Fields
    service = None
    running = False
    outThread = None

    pattern = re.compile(
        '^(?P<cmd>\S+)\s(?P<ast>\S+)\s' +
        '(?P<symbol>\S+)( (?P<instance>\S+))?\s' +
        '(?P<type>[^\t]+)\s(?P<path>[^\t]+)\s' +
        '(?P<line>\d+)\s(?P<col>\d+)\s' +
        '(?P<description>\".+\")?')

    # Methods
    @staticmethod
    def print_output(out):
        try:
            for line in iter(out.readline, b''):
                print(line.rstrip())
        except: pass

    @staticmethod
    def linesplit(socket):
        buffer = None

        if sys.version_info < (3, 0):
            buffer = socket.recv(4096)
        else:
            buffer = socket.recv(4096).decode('UTF-8')

        buffering = buffer is not None
        while buffering:
            if "\n" in buffer:
                (line, buffer) = buffer.split("\n", 1)
                yield line + "\n"
            else:
                more = socket.recv(4096)
                if not more:
                    buffering = False
                else:
                    buffer += more.decode('UTF-8')
        if buffer:
            yield buffer

    @staticmethod
    def opensock():
        sock = socket.create_connection(("localhost", 8088), 3)
        sock.settimeout(2.0)
        return sock

    @staticmethod
    def sendrecv(args, getresp=True):
        sock = None
        try:
            sock = Idetools.opensock()

            if sys.version_info < (3, 0):
                sock.send(args + "\r\n")
            else:
                sock.send(bytes(args + "\r\n", 'UTF-8'))

            if getresp:
                for line in Idetools.linesplit(sock):
                    return line
                return ""
        except:
            return ""
        finally:
            if sock is not None:
                sock.close()

    @staticmethod
    def ensure_socket(secs=5, wait=.2):
        while True:
            sock = None
            try:
                sock = Idetools.opensock()
                return True
            except:
                secs -= wait
                if secs <= 0:
                    print('nimsuggest failed to respond')
                    Idetools.service = None
                    return False
                sleep(wait)
            finally:
                if sock is not None:
                    sock.close()

    @staticmethod
    def ensure_service(proj=""):
        # Ensure there is a listening socket
        if Idetools.ensure_socket(secs=0):
            return

        # If server is running, do nothing
        if Idetools.service is not None and Idetools.service.poll() is None:
            return

        # Start the server
        proc = subprocess.Popen(
            'nimsuggest --port:8088 "' + proj + '"',
            bufsize=0,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            shell=True)

        Idetools.service = proc
        # Idetools.outThread = Thread(
        #     target=Idetools.print_output,
        #     args=(proc.stdout,))

        # Idetools.outThread.daemon = True
        # Idetools.outThread.start()

        # Ensure the socket is available
        Idetools.ensure_socket()

        print('nimsuggest running on "' + proj + '"')

    @staticmethod
    def idetool(win, cmd, filename, line, col, dirtyFile=""):
        filePath = filename
        projFile = get_project_file(win)

        if projFile is None:
            projFile = filename

        if dirtyFile != "":
            filePath = filePath + '";"' + dirtyFile

        # Ensure IDE Tools server is running
        Idetools.ensure_service(projFile)

        # Call the server
        args = 'def "' + filePath + '":' + str(line) + ":" + str(col)
        print(args)

        # Write to service & read result
        result = Idetools.sendrecv(args)
        if result is not None:
            return result

    @staticmethod
    def parse(result):
        m = Idetools.pattern.match(result)
        if m is not None:
            cmd = m.group("cmd")

            if cmd == "def":
                return (m.group("symbol"), m.group("type"),
                        m.group("path"), m.group("line"),
                        m.group("col"), m.group("description"))

        return None


    @staticmethod
    def show_tooltip(view, value):
        (func, typ, desc) = (value[0], value[1], value[5])

        if desc is None:
            desc = ""
        else:
            desc = desc.strip('"')

        view.show_popup(
            '<b>%s</b>'
            '<div style="color: #666"><i>%s</i></div>'
            '<div>%s</div>' %
            (func, typ, desc))

    @staticmethod
    def open_definition(window, filename, line, col):
        arg = filename + ":" + str(line) + ":" + str(col)
        flags = sublime.ENCODED_POSITION

        # TODO - If this is NOT in the same project, mark transient
        # flags |= sublime.TRANSIENT
        window.open_file(arg, flags)

    @staticmethod
    def lookup(command, goto, filename, line, col):
        result = ""
        dirty_file_name = ""

        if command.view.is_dirty():
            # Generate temp file
            size = command.view.size()

            with NamedTemporaryFile(suffix=".nim", delete=False) as dirty_file:
                dirty_file_name = dirty_file.name
                dirty_file.file.write(
                    command.view.substr(Region(0, size)).encode("UTF-8")
                )
                dirty_file.file.close()

                result = Idetools.idetool(
                    command.view.window(),
                    "--def",
                    filename,
                    line,
                    col,
                    dirty_file.name
                )
                dirty_file.close()

            try:
                os.unlink(dirty_file.name)
            except OSError:
                pass
        else:
            result = Idetools.idetool(
                command.view.window(), "--def", filename, line, col)

        # Parse the result
        value = Idetools.parse(result)

        if value is not None:
            if value[2] == dirty_file_name:
                lookup_file = filename
            else:
                lookup_file = value[2]


            if goto:
                Idetools.open_definition(
                    command.view.window(),
                    lookup_file,
                    int(value[3]),
                    int(value[4]) + 1
                )
            else:
                Idetools.show_tooltip(command.view, value)
        else:

            sublime.status_message("No definition found")