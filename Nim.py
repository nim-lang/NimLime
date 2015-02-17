import sublime
import sublime_plugin
import sys
import re
import subprocess
import socket
from time import sleep
from threading import Thread
import os

auto_reload = False

st_version = 2
if int(sublime.version()) > 3000:
    st_version = 3

if st_version == 3:
    from NimLime.Project import Utility
else:
    from Project import Utility

class Idetools:

    # Fields
    service   = None
    running   = False
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
        for line in iter(out.readline, b''):
            print(line.rstrip())

    @staticmethod
    def linesplit(socket):
        buffer = None

        if st_version == 2:
            buffer = socket.recv(4096)
        else:
            buffer = socket.recv(4096).decode('UTF-8')

        buffering = True
        while buffering:
            if "\n" in buffer:
                (line, buffer) = buffer.split("\n", 1)
                yield line + "\n"
            else:
                more = socket.recv(4096)
                if not more:
                    buffering = False
                else:
                    buffer += more
        if buffer:
            yield buffer

    @staticmethod
    def opensock():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", 8088))
        return s

    @staticmethod
    def sendrecv(args, getresp = True):
        sock = None
        try:
            sock = Idetools.opensock()

            if st_version == 2:
                sock.send(args + "\r\n")
            else:
                sock.send(bytes(args + "\r\n", 'UTF-8'))

            if getresp:
                for line in Idetools.linesplit(sock):
                    print(line)
                    return line
                return ""
        except Exception as e:
            print(e)
        finally:
            if sock is not None:
                sock.close()

    @staticmethod
    def ensure_socket(secs=2, wait=.2):
        while True:
            sock = None
            try:
                sock = Idetools.opensock()
                sock.close()
                return True
            except:
                secs -= wait
                if secs <= 0:
                    print('nimsuggest failed to respond')
                    Idetools.service = None
                    return False
                sleep(wait)
                sock = None

    @staticmethod
    def ensure_service(proj = ""):
        # Ensure there is a listening socket
        if Idetools.ensure_socket(secs = 0):
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

        Idetools.service   = proc
        Idetools.outThread = Thread(
            target=Idetools.print_output,
            args=(proc.stdout,))

        Idetools.outThread.daemon = True
        Idetools.outThread.start()

        # Ensure the socket is available
        Idetools.ensure_socket()

        print('nimsuggest running on "' + proj + '"')

    @staticmethod
    def idetool(win, cmd, filename, line, col, dirtyFile=""):
        filePath = filename
        projFile = Utility.get_nimproject(win)

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

if auto_reload:
    # Perform auto-reload
    reload_mods = []
    for mod in sys.modules:
        if mod[0:7] == 'NimLime' and sys.modules[mod] != None:
            reload_mods.append(mod)

    # Reload modules
    mods_load_order = [
        'Project',
        'Nim',
        'Lookup',
        'Documentation',
        'Nimble',
        'AutoComplete'
    ]

    mod_load_prefix = ''
    if st_version == 3:
        mod_load_prefix = 'NimLime.'
        from imp import reload

    for mod in mods_load_order:
        if mod in reload_mods:
            reload(sys.modules[mod])
            print("reloading " + mod)