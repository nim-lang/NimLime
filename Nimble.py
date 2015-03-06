import sublime
from sublime_plugin import ApplicationCommand
from utils import (
    send_self, loop_status_msg, busy_frames, format_tag, get_next_method,
    get_output_view, write_to_view, show_view, run_process, escape_shell,
    NimLimeMixin)
from threading import Thread

# Resources
# http://docs.sublimetext.info/en/latest/reference/command_palette.html
# https://github.com/wbond/sublime_package_control/blob/6a8b91ca58d66cb495b383d9572bb801316bcec5/package_control/commands/install_package_command.py


def debug(string):
    if False:
        print(string)


# Settings handlers
nimble_executable = None


# Load settings
def load():
    global nimble_executable
    nimble_executable = settings.get('nimble.executable', 'nim')

settings = sublime.load_settings('NimLime.sublime-settings')
settings.add_on_change('nimble.executable', load)
load()


class NimbleMixin(NimLimeMixin):

    def load_settings(self):
        get = lambda key: settings.get(key.format(self.settings_selector))
        self.enabled = get('nimble.{0}.enabled')
        self.load_output_settings()

    def load_output_settings(self):
        get = lambda key: settings.get(key.format(self.settings_selector))
        self.send_output = get("nimble.{0}.output.send")
        self.clear_output = get("nimble.{0}.output.clear")
        self.show_output = get("nimble.{0}.output.show")
        self.output_method = get("nimble.{0}.output.method")
        self.output_tag = get("nimble.{0}.output.tag")
        self.raw_output = get("nimble.{0}.output.raw")


class NimbleUpdateCommand(ApplicationCommand, NimbleMixin):

    """
    Update the Nimble package list
    """
    settings_selector = 'update'

    @send_self
    def run(self):
        this = yield

        window = sublime.active_window()

        # Setup the loading notice
        frames = ['Updating Nimble package list' + f for f in busy_frames]
        stop_status_loop = loop_status_msg(frames, 0.15)

        # Run the main command
        output, returncode = yield Thread(
            target=run_nimble,
            args=('-y update', this.send)
        ).start()

        # Set the status to show we've finished

        yield stop_status_loop(get_next_method(this))

        # Show output
        if self.send_output:
            self.write_to_output(output, window, None, "Nimble Status")

        if returncode == 0:
            sublime.status_message("Nimble Package List Updated")
        else:
            sublime.status_message('Updating Nimble Package List Failed')

        yield


class NimbleListCommand(ApplicationCommand, NimbleMixin):

    """
    List Nimble Packages
    """
    settings_selector = 'list'

    def load_settings(self):
        get = lambda key: settings.get(key.format(self.settings_selector))
        self.enabled = get('nimble.{0}.enabled')
        self.send_to_quickpanel = get('nimble.{0}.list.send')
        self.load_output_settings()

    @send_self
    def run(self):
        this = yield

        window = sublime.active_window()

        # Setup the loading notice
        frames = ['Retrieving package list' + f for f in busy_frames]
        stop_status_loop = loop_status_msg(frames, 0.15)

        # Run the main command
        output, returncode = yield Thread(
            target=run_nimble,
            args=('-y list', this.send)
        ).start()

        # Set the status to show we've finished
        yield stop_status_loop(get_next_method(this))

        if self.send_to_quickpanel:
            items = []
            packages = parse_package_descriptions(output)
            for package in packages:
                items.append([
                    package['name'],
                    package.get('description', ''),
                    package.get('url', '')
                ])
            window.show_quick_panel(items, None)

        # Show output
        if self.send_output:
            formatted_tag = format_tag(self.output_tag, window)
            output_window, output_view = get_output_view(
                formatted_tag,
                self.output_method,
                "Nimble List Output",
                window
            )
            write_to_view(
                output_view, output,
                self.clear_output
            )
            if self.show_output:
                is_console = self.output_method == 'console'
                show_view(output_window, output_view, is_console)

        if returncode == 0:
            sublime.status_message("Listing Nimble Packages")
        else:
            sublime.status_message('Nimble Package List Retrieval Failed')
        yield


class NimbleSearchCommand(ApplicationCommand, NimbleMixin):

    """
    Search Nimble Packages
    """
    settings_selector = "search"

    def load_settings(self):
        get = lambda key: settings.get(key.format(self.settings_selector))
        self.enabled = get('nimble.{0}.enabled')
        self.send_to_quickpanel = get('nimble.{0}.list.send')
        self.load_output_settings()

    def run(self):
        window = sublime.active_window()

        @send_self
        def callback():
            this = yield

            # Get user input
            search_term = yield window.show_input_panel(
                "Package Search Term?", '', this.send, None, None
            )

            # Setup the loading notice
            frames = ['Searching package list... ' + f for f in busy_frames]
            stop_status_loop = loop_status_msg(frames, 0.15)

            # Run the main command
            output, returncode = yield Thread(
                target=run_nimble,
                args=('-y search ' + escape_shell(search_term), this.send)
            ).start()

            # Set the status to show we've finished
            yield stop_status_loop(get_next_method(this))

            # List output
            if self.send_to_quickpanel:
                items = []
                packages = parse_package_descriptions(output)
                for package in packages:
                    items.append([
                        package['name'],
                        package.get('description', ''),
                        package.get('url', '')
                    ])
                window.show_quick_panel(items, None)

            # Show output
            if self.send_output:
                formatted_tag = format_tag(self.output_tag, window)
                output_window, output_view = get_output_view(
                    formatted_tag,
                    self.output_method,
                    "Nimble Search Output",
                    window
                )
                write_to_view(
                    output_view, output,
                    self.clear_output
                )
                if self.show_output:
                    is_console = self.output_method == 'console'
                    show_view(output_window, output_view, is_console)

            if returncode == 0:
                sublime.status_message("Listing Nimble Packages")
            else:
                sublime.status_message('Nimble Package List Retrieval Failed')
            yield

        callback()


class NimbleUninstallCommand(ApplicationCommand):

    """
    Uninstall a Nimble package.
    """
    settings_selector = "uninstall"

    def run(self):
        window = sublime.active_window()

        @send_self
        def callback():
            this = yield

            # Setup the loading notice
            frames = ['Uninstalling package: ' + f for f in busy_frames]
            stop_status_loop = loop_status_msg(frames, 0.15)

            # Run the main command
            output, returncode = yield Thread(
                target=run_nimble,
                args=('-y uninstall', this.send)
            ).start()

            # Set the status to show we've finished
            yield stop_status_loop(get_next_method(this))

            # Show output
            if self.send_output:
                formatted_tag = format_tag(self.output_tag, window)
                output_view = get_output_view(
                    formatted_tag,
                    self.output_method,
                    window
                )
                write_to_view(
                    output_view, output,
                    self.clear_output
                )
                if self.show_output:
                    is_console = self.output_method == 'console'
                    show_view(output_view, is_console)
            if returncode == 0:
                sublime.status_message("Nimble Package Uninstalled")
            else:
                sublime.status_message('Nimble Package Uninstallation Failed')
            yield

        callback()


def run_nimble(command, callback):
    global nimble_executable
    run_process(nimble_executable + " " + command, callback)


def parse_package_descriptions(descriptions):
    package_list = []
    current_package = None
    for row in descriptions.splitlines():
        if len(row) == 0 or row.isspace():
            if current_package is not None:
                package_list.append(current_package)
                current_package = None

        elif current_package is None:
            current_package = {'name': row.split(":", 1)[0]}

        else:
            info = row.split(":", 1)
            if len(info) == 2:
                current_package[info[0].strip()] = info[1].strip()

    if current_package is not None:
        package_list.append(current_package)

    return package_list
