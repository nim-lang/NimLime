import sublime

from threading import Thread
from sublime_plugin import ApplicationCommand
from utils.misc import (
    send_self, loop_status_msg, busy_frames, format_tag, get_next_method,
    get_output_view, write_to_view, show_view, run_process, escape_shell)
from .utils.mixins import NimLimeMixin


def debug(string):
    if False:
        print(string)


# Settings handlers
nimble_executable = None


# Load settings
def load():
    global nimble_executable
    nimble_executable = settings.get('nimble.executable', 'nimble')


settings = sublime.load_settings('NimLime.sublime-settings')
settings.add_on_change('nimble.executable', load)
load()


class NimbleMixin(NimLimeMixin):
    def load_settings(self):
        get = self.get_setting
        self.enabled = get('nimble.{0}.enabled', True)
        self.load_output_settings()

    def load_output_settings(self):
        get = self.get_setting
        self.send_output = get("nimble.{0}.output.send", True)
        self.clear_output = get("nimble.{0}.output.clear", True)
        self.show_output = get("nimble.{0}.output.show", True)
        self.output_method = get("nimble.{0}.output.method", "grouped")
        self.output_tag = get("nimble.{0}.output.tag", 'nimlime')
        self.output_name = get("nimble.{0}.output.name", 'nimlime')

    def output_content(self, output, window):
        if self.send_output:
            formatted_tag = format_tag(self.output_tag, window)
            output_window, output_view = get_output_view(
                formatted_tag,
                self.output_method,
                self.output_name,
                self.show_output,
                window
            )
            write_to_view(
                output_view, output,
                self.clear_output
            )


class NimbleUpdateCommand(NimbleMixin, ApplicationCommand):
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
        output, return_code = yield Thread(
            target=run_nimble,
            args=('-y update', this.send)
        ).start()

        # Set the status to show we've finished
        yield stop_status_loop(get_next_method(this))

        # Show output
        self.output_content(output, window)

        if return_code == 0:
            sublime.status_message("Nimble Package List Updated")
        else:
            sublime.status_message('Updating Nimble Package List Failed')

        yield


class NimbleListCommand(NimbleMixin, ApplicationCommand):
    """
    List Nimble Packages
    """
    settings_selector = 'list'

    def load_settings(self):
        get = self.get_setting
        self.send_to_quickpanel = get('nimble.{0}.quickpanel.send', True)
        self.enabled = get('nimble.{0}.enabled', True)
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

        # Show output
        self.output_content(output, window)

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

        if returncode == 0:
            sublime.status_message("Listing Nimble Packages")
        else:
            sublime.status_message('Nimble Package List Retrieval Failed')
        yield


class NimbleSearchCommand(NimbleMixin, ApplicationCommand):
    """
    Search Nimble Packages
    """
    settings_selector = "search"

    def load_settings(self):
        get = self.get_setting
        self.send_to_quickpanel = get('nimble.{0}.quickpanel.send', True)
        self.enabled = get('nimble.{0}.enabled', True)
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
            frames = ['Searching package list' + f for f in busy_frames]
            stop_status_loop = loop_status_msg(frames, 0.15)

            # Run the main command
            output, return_code = yield Thread(
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
            self.output_content(output, window)

            if return_code == 0:
                sublime.status_message("Listing Nimble Packages")
            else:
                sublime.status_message('Nimble Package List Retrieval Failed')
            yield

        callback()


class NimbleInstallCommand(NimbleMixin, ApplicationCommand):
    """
    Search Nimble Packages
    """
    settings_selector = "install"

    def load_settings(self):
        get = self.get_setting
        self.preemptive_search = get('nimble.preemptive_search', True)
        self.enabled = get('nimble.{0}.enabled', True)
        self.load_output_settings()

    def run(self):
        window = sublime.active_window()

        @send_self
        def callback():
            this = yield

            if self.preemptive_search:
                # Get user input
                search_term = yield window.show_input_panel(
                    "Package to install?", '', this.send, None, None
                )

                loading_notice = 'Searching package list'
                process_args = (
                    '-y search ' + escape_shell(search_term),
                    this.send
                )
            else:
                loading_notice = 'Loading package list'
                process_args = ('-y list ', this.send)

            # Setup the loading notice
            frames = [loading_notice + f for f in busy_frames]
            stop_status_loop = loop_status_msg(frames, 0.15)

            # Run the search/list command
            output, return_code = yield Thread(
                target=run_nimble,
                args=process_args
            ).start()

            # Set the status to show we've finished searching
            yield stop_status_loop(get_next_method(this))

            if return_code != 0:
                sublime.status_message("Nimble Package Load Failed")
            else:
                items = []
                packages = parse_package_descriptions(output)

                if len(packages) == 0:
                    sublime.status_message("No Matching Packages Found")
                else:
                    for package in packages:
                        items.append([
                            package['name'],
                            package.get('description', ''),
                            package.get('url', '')
                        ])

                    selection = yield window.show_quick_panel(items, this.send)

                    if selection != -1:
                        target_name = items[selection][0]
                        # Setup the loading notice
                        loading_notice = "Installing package"
                        frames = [loading_notice + f for f in busy_frames]
                        stop_status_loop = loop_status_msg(frames, 0.15)

                        # Run the install command
                        output, return_code = yield Thread(
                            target=run_nimble,
                            args=(
                                '-y install ' + escape_shell(target_name),
                                this.send
                            )
                        ).start()

                        yield stop_status_loop(get_next_method(this))

                        self.output_content(output, window)
                        if return_code == 0:
                            sublime.status_message("Installed Nimble Package")
                        else:
                            sublime.status_message(
                                'Nimble Package Installation Failed'
                            )
            yield

        callback()


class NimbleUninstallCommand(NimbleMixin, ApplicationCommand):
    """
    Search Nimble Packages
    """
    settings_selector = "uninstall"

    def run(self):
        window = sublime.active_window()

        @send_self
        def callback():
            this = yield

            # Setup the loading notice
            frames = ['Loading package list' + f for f in busy_frames]
            stop_status_loop = loop_status_msg(frames, 0.15)

            # Run the search/list command
            output, return_code = yield Thread(
                target=run_nimble,
                args=('-y list -i', this.send)
            ).start()

            # Set the status to show we've finished searching
            yield stop_status_loop(get_next_method(this))

            if return_code != 0:
                sublime.status_message(
                    "Nimble Installed Package Listing Failed")
            else:
                items = []
                packages = parse_package_descriptions(output)

                if len(packages) == 0:
                    sublime.status_message("No Installed Packages Found")
                else:
                    for package in packages:
                        items.append([
                            package['name'],
                            package.get('description', ''),
                            package.get('url', '')
                        ])

                    selection = yield window.show_quick_panel(items, this.send)

                    if selection != -1:
                        target_name = items[selection][0]
                        # Setup the loading notice
                        loading_notice = "Uninstalling package"
                        frames = [loading_notice + f for f in busy_frames]
                        stop_status_loop = loop_status_msg(frames, 0.15)

                        # Run the install command
                        output, return_code = yield Thread(
                            target=run_nimble,
                            args=(
                                '-y uninstall ' + escape_shell(target_name),
                                this.send
                            )
                        ).start()

                        yield stop_status_loop(get_next_method(this))

                        self.output_content(output, window)
                        if return_code == 0:
                            sublime.status_message(
                                "Uninstalled Nimble Package")
                        else:
                            sublime.status_message(
                                'Nimble Package Uninstallation Failed'
                            )
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
