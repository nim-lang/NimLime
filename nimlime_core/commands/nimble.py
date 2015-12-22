# coding=utf-8
"""
Commands to expose Nimble to the user.
"""
from threading import Thread

import subprocess

import sublime
from sublime_plugin import ApplicationCommand
from nimlime_core import configuration
from nimlime_core.utils.mixins import NimLimeOutputMixin
from nimlime_core.utils.error_handler import catch_errors
from nimlime_core.utils.misc import (
    send_self, loop_status_msg, busy_frames, get_next_method,
    run_process, escape_shell
)

class NimbleMixin(NimLimeOutputMixin):
    requires_nimble = True
    setting_entries = (
        NimLimeOutputMixin.setting_entries,
        ('timeout', '{0}.timeout', 60)
    )


class NimbleUpdateCommand(NimbleMixin, ApplicationCommand):
    """
    Update the Nimble package list
    """
    settings_selector = 'nimble.update'

    @send_self
    @catch_errors
    def run(self):
        this = yield
        window = sublime.active_window()
        view = window.active_view()

        # Setup the loading notice
        frames = ['Updating Nimble package list' + f for f in busy_frames]
        stop_status_loop = loop_status_msg(frames, 0.15)

        # Run the main command
        process, output, errors = yield run_nimble(
            (configuration.nimble_executable, '-y', 'update'),
            this.send, self.timeout
        )
        return_code = process.poll()

        # Set the status to show we've finished
        yield stop_status_loop(get_next_method(this))

        # Write output
        self.write_to_output(output, window, view)

        if return_code == 0:
            sublime.status_message("Nimble Package List Updated")
        else:
            sublime.status_message('Updating Nimble Package List Failed')

        yield


class NimbleListCommand(NimbleMixin, ApplicationCommand):
    """
    List Nimble Packages
    """
    settings_selector = 'nimble.list'
    setting_entries = (
        NimbleMixin.setting_entries,
        ('send_to_quickpanel', '{0}.quickpanel.send', True)
    )
    nimble_args = [None, '-y', 'list']

    @send_self
    @catch_errors
    def run(self):
        this = yield
        window = sublime.active_window()
        view = window.active_view()

        # Setup the loading notice
        frames = ['Retrieving Nimble package list' + f for f in busy_frames]
        stop_status_loop = loop_status_msg(frames, 0.15)

        # Run the main command
        process, output, errors = yield run_nimble(
            (configuration.nimble_executable, '-y', 'list'),
            this.send, self.timeout
        )
        return_code = process.poll()

        # Set the status to show we've finished
        yield stop_status_loop(get_next_method(this))

        # Show output
        self.write_to_output(output, window, view)

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

        if return_code == 0:
            sublime.status_message('Listing Nimble Packages')
        else:
            sublime.status_message('Nimble Package List Retrieval Failed')
        yield


class NimbleSearchCommand(NimLimeOutputMixin, ApplicationCommand):
    """
    Search Nimble Packages
    """
    requires_nimble = True
    settings_selector = 'nimble.search'
    setting_entries = (
        NimLimeOutputMixin.setting_entries,
        ('send_to_quickpanel', '{0}.quickpanel.send', True)
    )

    @send_self
    @catch_errors
    def run(self):
        this = yield
        window = sublime.active_window()
        view = window.active_view()

        # Get user input
        search_term = yield window.show_input_panel(
            "Package Search Term?", '', this.send, None, None
        )

        # Setup the loading notice
        frames = ['Searching package list' + f for f in busy_frames]
        stop_status_loop = loop_status_msg(frames, 0.15)

        # Run the main command
        process, output, error = yield run_nimble(
            (configuration.nimble_executable, '-y', 'search', search_term),
            this.send, self.timeout
        )
        return_code = process.poll()

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
        self.write_to_output(output, window, view)

        if return_code == 0:
            sublime.status_message("Listing Nimble Packages")
        else:
            sublime.status_message('Nimble Package List Retrieval Failed')
        yield


class NimbleInstallCommand(NimbleMixin, ApplicationCommand):
    """
    Search Nimble Packages
    """
    requires_nimble = True
    settings_selector = 'nimble.install'
    setting_entries = (
        NimbleMixin.setting_entries,
        ('preemptive_search', 'nimble.preemptive_search', True)
    )

    @send_self
    @catch_errors
    def run(self):
        this = yield
        window = sublime.active_window()
        view = window.active_view()

        if self.preemptive_search:
            # Get user input
            search_term = yield window.show_input_panel(
                "Package to install?", '', this.send, None, None
            )

            loading_notice = 'Searching package list'
            process_args = (
                configuration.nimble_executable, '-y', 'search',
                escape_shell(search_term)
            )
        else:
            loading_notice = 'Loading package list'
            process_args = (configuration.nimble_executable, '-y', 'list ')

        # Setup the loading notice
        frames = [loading_notice + f for f in busy_frames]
        stop_status_loop = loop_status_msg(frames, 0.15)

        # Run the search/list command
        process, output, errors = run_process(
            process_args, this.send, self.timeout
        )
        return_code = process.poll()

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
                    process, output, errors = run_process(
                        [configuration.nimble_executable, '-y', 'install',
                         escape_shell(target_name)], this.send, self.timeout
                    )

                    # Stop the status notice
                    yield stop_status_loop(get_next_method(this))

                    self.write_to_output(output, window, view)
                    if return_code == 0:
                        sublime.status_message("Installed Nimble Package")
                    else:
                        sublime.status_message(
                            'Nimble Package Installation Failed'
                        )
        yield


class NimbleUninstallCommand(NimLimeOutputMixin, ApplicationCommand):
    """
    Search Nimble Packages
    """
    requires_nimble = True
    settings_selector = "nimble.uninstall"

    @send_self
    @catch_errors
    def run(self):
        window = sublime.active_window()
        view = window.active_view()

        this = yield

        # Setup the loading notice
        frames = ['Loading package list' + f for f in busy_frames]
        stop_status_loop = loop_status_msg(frames, 0.15)

        # Run the search/list command
        process, output, errors = run_process(
            [configuration.nimble_executable, '-y', 'list', '-i'],
            this.send, self.timeout
        )
        return_code = process.poll()

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
                    process, output, errors = run_process(
                        [configuration.nimble_executable, '-y', 'uninstall'],
                        this.send, self.timeout
                    )
                    return_code = process.poll()

                    yield stop_status_loop(get_next_method(this))

                    self.write_to_output(output, window, view)
                    if return_code == 0:
                        sublime.status_message(
                            "Uninstalled Nimble Package")
                    else:
                        sublime.status_message(
                            'Nimble Package Uninstallation Failed'
                        )
        yield

def run_nimble(cmd, callback, timeout):
    run_process(
        cmd, callback, timeout,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

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
