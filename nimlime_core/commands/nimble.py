# coding=utf-8
"""
Commands to expose Nimble to the user.
"""

import subprocess

import sublime
from nimlime_core import configuration
from nimlime_core.utils.error_handler import catch_errors
from nimlime_core.utils.misc import (
    send_self, loop_status_msg, busy_frames, get_next_method,
    run_process, escape_shell,
    handle_process_error)
from nimlime_core.utils.mixins import NimLimeOutputMixin
from sublime_plugin import ApplicationCommand


class NimbleMixin(NimLimeOutputMixin):
    """
    Mixin for Nimble commands.
    """
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
        process, stdout, _, error = yield run_process(
            (configuration.nimble_exe, '-y', 'update'),
            callback=this.send, timeout=self.timeout,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        yield stop_status_loop(get_next_method(this))

        # Handle possible errors
        if handle_process_error(error, 'Nimble Update Failed', 'Nimble'):
            yield

        # Write output
        self.write_to_output(stdout, window, view)

        if process.poll() == 0:
            sublime.status_message('Nimble Package List Updated')
        else:
            sublime.status_message('Nimble Update Failed')

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

    @send_self
    @catch_errors
    def run(self):
        this = yield
        window = sublime.active_window()
        view = window.active_view()

        # Setup the loading notice
        frames = ['Retrieving Nimble Package List' + f for f in busy_frames]
        stop_status_loop = loop_status_msg(frames, 0.15)

        # Run the main command
        process, stdout, _, error = yield run_process(
            [configuration.nimble_exe, '-y', 'list'],
            callback=this.send, timeout=self.timeout,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        yield stop_status_loop(get_next_method(this))

        # Handle possible errors
        if handle_process_error(error, 'Nimble List Failed', 'Nimble'):
            yield

        # Show output
        self.write_to_output(stdout, window, view)

        if self.send_to_quickpanel:
            items = []
            packages = parse_package_descriptions(stdout)
            for package in packages:
                items.append([
                    package['name'],
                    package.get('description', ''),
                    package.get('url', '')
                ])
            window.show_quick_panel(items, None)

        if process.poll() == 0:
            sublime.status_message('Listing Nimble packages')
        else:
            sublime.status_message('Nimble Package List Retrieval Failed')
        yield


class NimbleSearchCommand(NimLimeOutputMixin, ApplicationCommand):
    """
    Search Nimble Packages
    """
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
            'Package Search Term?', '', this.send, None, None
        )

        # Setup the loading notice
        frames = ['Searching Package List' + f for f in busy_frames]
        stop_status_loop = loop_status_msg(frames, 0.15)

        # Run the main command
        process, stdout, _, error = yield run_process(
            (configuration.nimble_exe, '-y', 'search', search_term),
            callback=this.send, timeout=self.timeout,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        yield stop_status_loop(get_next_method(this))

        # Handle errors
        if handle_process_error(error, 'Nimble Search Failed', 'Nimble'):
            yield

        # List output
        if self.send_to_quickpanel:
            items = []
            packages = parse_package_descriptions(stdout)
            for package in packages:
                items.append([
                    package['name'],
                    package.get('description', ''),
                    package.get('url', '')
                ])
            window.show_quick_panel(items, None)

        # Show output
        self.write_to_output(stdout, window, view)

        if process.poll() == 0:
            sublime.status_message('Listing Nimble Packages')
        else:
            sublime.status_message('Nimble Package List Retrieval Failed')
        yield


class NimbleInstallCommand(NimbleMixin, ApplicationCommand):
    """
    Search Nimble Packages
    """
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
                'Package to install?', '', this.send, None, None
            )

            loading_notice = 'Searching Package List'
            process_args = (
                configuration.nimble_exe, '-y', 'search',
                escape_shell(search_term)
            )
        else:
            loading_notice = 'Loading Package List'
            process_args = (configuration.nimble_exe, '-y', 'list ')

        # Setup the loading notice
        frames = [loading_notice + f for f in busy_frames]
        stop_status_loop = loop_status_msg(frames, 0.15)

        # Run the search/list command
        process, stdout, _, error = yield run_process(
            process_args, callback=this.send, timeout=self.timeout
        )
        stop_status_loop(get_next_method(this))

        # Handle errors
        if handle_process_error(error, 'Loading Nimble Packages Failed',
                                'Nimble'):
            yield

        if process.poll() != 0:
            sublime.status_message('Nimble Package Load Failed')
            yield

        # Parse the package list
        items = []
        packages = parse_package_descriptions(stdout)

        if len(packages) == 0:
            sublime.status_message('No Matching Packages Found')
            yield

        # Display the list and get the selected package.
        for package in packages:
            items.append([
                package['name'],
                package.get('description', ''),
                package.get('url', '')
            ])

        selection = yield window.show_quick_panel(items, this.send)
        if selection == -1:
            yield
        target_name = items[selection][0]

        # Setup the loading notice
        frames = ['Installing Package' + f for f in busy_frames]
        stop_status_loop = loop_status_msg(frames, 0.15)

        # Run the install command
        process, stdout, _, error = yield run_process(
            [configuration.nimble_exe, '-y', 'install',
             escape_shell(target_name)], this.send, self.timeout
        )
        yield stop_status_loop(get_next_method(this))

        if handle_process_error(error, 'Nimble Package Install Failed',
                                'Nimble'):
            yield

        self.write_to_output(stdout, window, view)
        if process.poll() == 0:
            sublime.status_message('Installed Nimble Package')
        else:
            sublime.status_message('Nimble Package Installation Failed')
        yield


class NimbleUninstallCommand(NimLimeOutputMixin, ApplicationCommand):
    """
    Search Nimble Packages
    """
    settings_selector = 'nimble.uninstall'

    @send_self
    @catch_errors
    def run(self):
        this = yield
        window = sublime.active_window()
        view = window.active_view()

        # Setup the loading notice
        frames = ['Loading package list' + f for f in busy_frames]
        stop_status_loop = loop_status_msg(frames, 0.15)

        # Run the search/list command
        process, stdout, stderr, error = yield run_process(
            [configuration.nimble_exe, '-y', 'list', '-i'],
            this.send, self.timeout
        )
        yield stop_status_loop(get_next_method(this))

        # Handle errors
        if handle_process_error(error, 'Nimble Package Uninstall Failed',
                                'Nimble'):
            yield
        elif process.poll() != 0:
            sublime.status_message('Nimble Installed Package Listing Failed')
            yield

        # Parse the package descriptions
        packages = parse_package_descriptions(stdout)
        if len(packages) == 0:
            sublime.status_message('No Installed Packages Found')
            yield

        items = []
        for package in packages:
            items.append([
                package['name'],
                package.get('description', ''),
                package.get('url', '')
            ])

        # Display packages and retrieve the selection
        selection = yield window.show_quick_panel(items, this.send)
        if selection == -1:
            yield

        target_name = items[selection][0]

        # Setup the loading notice
        frames = ['Uninstalling Package' + f for f in busy_frames]
        stop_status_loop = loop_status_msg(frames, 0.15)

        # Run the install command
        process, stdout, stderr, error = yield run_process(
            [configuration.nimble_exe, '-y', 'uninstall',
             target_name],
            this.send, self.timeout
        )
        yield stop_status_loop(get_next_method(this))

        # Handle errors
        if handle_process_error(error, 'Nimble Package Uninstallation Failed',
                                'Nimble'):
            yield

        # Write output
        self.write_to_output(stdout, window, view)

        if process.poll() == 0:
            sublime.status_message('Uninstalled Nimble Package')
        else:
            sublime.status_message(
                'Nimble Package Uninstallation Failed')
        yield


def parse_package_descriptions(descriptions):
    """
    Parse package descriptions from Nimble output.
    :type descriptions: str
    :rtype: list[dict[str, str]
    """
    package_list = []
    current_package = None
    for row in descriptions.splitlines():
        if len(row) == 0 or row.isspace():
            if current_package is not None:
                package_list.append(current_package)
                current_package = None

        elif current_package is None:
            current_package = {'name': row.split(':', 1)[0]}

        else:
            info = row.split(':', 1)
            if len(info) == 2:
                current_package[info[0].strip()] = info[1].strip()

    if current_package is not None:
        package_list.append(current_package)

    return package_list
