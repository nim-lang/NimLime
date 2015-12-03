import os
import subprocess
import socket


def create_server_socket(host, port=0):
    def create_server_socket_from_info(*addrinfo_params):
        try:
            address_matches = socket.getaddrinfo(*addrinfo_params)
        except socket.gaierror:
            return None

        for info in address_matches:
            af, socktype, proto, canonname, sa = info
            try:
                result = socket.socket(af, socktype, proto)
                result.bind(sa)
                # result.setblocking(0)
                result.listen(5)
                return result
            except socket.error as msg:
                pass

    # Try IPv4, then IPv6
    result = create_server_socket_from_info(
        host, port, socket.AF_INET,
        socket.SOCK_STREAM, 0, socket.AI_PASSIVE
    )
    if result is None:
        result = create_server_socket_from_info(
            host, port, socket.AF_INET6,
            socket.SOCK_STREAM, 0, socket.AI_PASSIVE
        )

    return result


double_newline_byte = '\r\n\r\n'.encode('utf-8')


class IdeTool(object):
    """
    Used to retrieve suggestions, completions, and other IDE-like information
    using a pool of nimsuggest instances.
    """

    def __init__(self, executable, limit):
        # Establish a server socket and get the information needed to connect
        # nimsuggest instances to this process.
        self.server_socket = create_server_socket("")
        host, port = self.server_socket.getsockname()

        # Information needed to start a nimsuggest process
        self.executable = executable
        self.process_args = [
            'nimsuggest', 'tcp', '--client',
            '--address:' + host, '--port:' + str(port),
            None  # This gets mutated during add_project_file
        ]

        # Mapping of project files to nimsuggest instances and their sockets
        self.nimsuggest_instances = {}

        # Mapping of current outstanding requests

        # General settings
        self.process_limit = limit

    def __del__(self):
        # Kill each process, then try closing each socket.
        for process, connection in self.nimsuggest_instances.values():
            process.kill()
            try:
                connection.shutdown(socket.SHUT_RDWR)
                connection.close()
            except socket.error:
                pass

    def add_project_file(self, project_file):
        canonical_project = os.path.normcase(os.path.normpath(project_file))
        if canonical_project in self.nimsuggest_instances:
            return
        self.process_args[-1] = canonical_project
        process = subprocess.Popen(
            executable=self.executable,
            args=self.process_args,
        )
        connection, _ = self.server_socket.accept()
        self.nimsuggest_instances[canonical_project] = (process, connection)

    def remove_project_file(self, project_file):
        old_data = self.nimsuggest_instances.get(project_file, None)
        if old_data is not None:
            del(self.nimsuggest_instances[project_file])
            old_process, old_connection, old_address = old_data
            if old_process.poll() is None:
                old_process.kill()
            try:
                old_connection.close()
            except socket.error:
                pass

    def run_command(self, project, command, nim_file, dirty_file, line, column):
        # Normalize the file and project paths, then grab the appropriate
        # process and socket objects.
        canonical_project = os.path.normcase(os.path.normpath(project))
        process, connection = self.nimsuggest_instances[canonical_project]

        # Send the formatted command down the socket
        if dirty_file:
            formatted_command = '{0}\t"{1}";{2}:{3}:{4}\r\n'.format(
                command, nim_file, dirty_file, line, column
            ).encode('utf-8')
        else:
            formatted_command = '{0}\t"{1}":{2}:{3}\r\n'.format(
                command, nim_file, line, column
            ).encode('utf-8')

        try:
            connection.send(formatted_command)

            # Repeatedly read socket data into a bytearray buffer,
            # Looking for a double newline (\r\n\r\n) as the end mark.
            result = bytearray()
            while True:
                result += connection.recv(1)  # Optimize?
                newline_found = result.find(
                    double_newline_byte,
                    len(result) - len(double_newline_byte))
                if newline_found != -1:
                    break
        except socket.error:
            return None

        return result

def main():
    koch_source = "C:\\xCommon\\Nim\\koch.nim"
    i = IdeTool("C:\\x64\\Nimsuggest\\Nimsuggest.exe", 0)
    i.add_project_file(koch_source)
    print(i.run_command(koch_source, 'chk', koch_source, "", 0, 0))


if __name__ == "__main__":
    main()