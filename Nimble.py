import sublime
import subprocess
from sublime_plugin import ApplicationCommand
from utils import (
    FlagObject, send_self, loop_status_msg, busy_frames, format_tag,
    get_output_view, write_to_view, show_view)
from threading import Thread
from time import sleep

# Resources
# http://docs.sublimetext.info/en/latest/reference/command_palette.html
# https://github.com/wbond/sublime_package_control/blob/6a8b91ca58d66cb495b383d9572bb801316bcec5/package_control/commands/install_package_command.py


def debug(string):
    if False:
        print(string)


# Settings handlers
settings = None

nimble_executable = None

# Nimble install command settings
nimble_install_enabled = None
nimble_install_mode = None
nimble_install_confirmation = None
nimble_install_output_send = None
nimble_install_output_clear = None
nimble_install_output_open = None

# Nimble update command settings
nimble_update_enabled = None
nimble_update_output_send = None
nimble_update_output_clear = None
nimble_update_output_show = None
nimble_update_output_method = None
nimble_update_output_tag = None

# Nimble list command settings
nimble_list_enabled = None
nimble_list_output_send = None
nimble_list_output_clear = None
nimble_list_output_show = None
nimble_list_output_method = None
nimble_list_output_tag = None
nimble_list_quickpanel_send = None

# Nimble search command settings
nimble_search_enabled = None
nimble_search_output_send = None
nimble_search_output_clear = None
nimble_search_output_show = None
nimble_search_output_method = None
nimble_search_output_tag = None
nimble_search_quickpanel_send = None

# Nimble update command settings
nimble_uninstall_enabled = None
nimble_uninstall_output_send = None
nimble_uninstall_output_clear = None
nimble_uninstall_output_show = None
nimble_uninstall_output_method = None
nimble_uninstall_output_tag = None


def update_settings():
    """ Update the currently loaded settings.
    Runs as a callback when settings are modified, and manually on startup.
    All settings variables should be initialized/modified here
    """
    debug('Entered update_settings')

    def load_key(key):
        globals()[key.replace('.', '_')] = settings.get(key)

    # Settings for checking a file on saving it
    load_key('nimble.executable')

    load_key("nimble.update.enabled")
    load_key("nimble.update.output.send")
    load_key("nimble.update.output.clear")
    load_key("nimble.update.output.show")
    load_key("nimble.update.output.method")
    load_key("nimble.update.output.tag")

    load_key("nimble.list.enabled")
    load_key("nimble.list.output.send")
    load_key("nimble.list.output.clear")
    load_key("nimble.list.output.show")
    load_key("nimble.list.output.method")
    load_key("nimble.list.output.tag")
    load_key("nimble.list.quickpanel.send")

    load_key("nimble.search.enabled")
    load_key("nimble.search.output.send")
    load_key("nimble.search.output.clear")
    load_key("nimble.search.output.show")
    load_key("nimble.search.output.method")
    load_key("nimble.search.output.tag")
    load_key("nimble.search.quickpanel.send")

    load_key("nimble.uninstall.enabled")
    load_key("nimble.uninstall.output.send")
    load_key("nimble.uninstall.output.clear")
    load_key("nimble.uninstall.output.show")
    load_key("nimble.uninstall.output.method")
    load_key("nimble.uninstall.output.tag")

    debug('Exiting update_settings')


def load_settings():
    """ Load initial settings object, and manually run update_settings """
    global settings
    debug('Entered load_settings')
    settings = sublime.load_settings('NimLime.sublime-settings')
    settings.add_on_change('reload', update_settings)
    update_settings()
    debug('Exiting load_settings')


# Hack to lazily initialize ST2 settings
if int(sublime.version()) < 3000:
    sublime.set_timeout(load_settings, 1000)


def run_nimble(cmd, callback=None):
    # TODO - if nimble does not exist, display error
    sleep(5)
    nimble_process = subprocess.Popen(
        nimble_executable + ' ' + cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        bufsize=0
    )

    output = nimble_process.communicate()[0].decode('UTF-8')
    returncode = nimble_process.returncode
    if callback is not None:
        sublime.set_timeout(lambda: callback((output, returncode)), 0)
    else:
        return output


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


class NimbleUpdateCommand(ApplicationCommand):

    """
    Update the Nimble package list
    """

    def run(self):
        window = sublime.active_window()

        @send_self
        def callback():
            this = yield

            # Setup the loading notice
            flag = FlagObject()
            frames = ['Updating package list' + f for f in busy_frames]
            loop_status_msg(frames, 0.15, flag)

            # Run the main command
            output, returncode = yield Thread(
                target=run_nimble,
                args=('update -y', this.send)
            ).start()

            # Set the status to show we've finished
            yield setattr(flag, 'break_status_loop', this.next)

            # Show output
            if nimble_update_output_send:
                formatted_tag = format_tag(nimble_update_output_tag, window)
                output_view = get_output_view(
                    formatted_tag,
                    nimble_update_output_method,
                    window
                )
                write_to_view(
                    output_view, output,
                    nimble_update_output_clear
                )
                if nimble_update_output_show:
                    is_console = nimble_update_output_method == 'console'
                    show_view(output_view, is_console)

            if returncode == 0:
                sublime.status_message("Nimble Package List Updated")
            else:
                sublime.status_message('Updating Nimble Package List Failed')
            yield

        callback()

    def is_enabled(self):
        return True

    def is_visible(self):
        return nimble_update_enabled

    def description(self):
        return self.__doc__


class NimbleListCommand(ApplicationCommand):

    """
    List Nimble Packages
    """

    def run(self):
        window = sublime.active_window()

        @send_self
        def callback():
            this = yield

            # Setup the loading notice
            flag = FlagObject()
            frames = ['Retrieving package list: ' + f for f in busy_frames]
            loop_status_msg(frames, 0.15, flag)

            # Run the main command
            output, returncode = yield Thread(
                target=run_nimble,
                args=('list -y', this.send)
            ).start()

            # Set the status to show we've finished
            yield setattr(flag, 'break_status_loop', this.next)

            if nimble_list_quickpanel_send:
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
            if nimble_list_output_send:
                formatted_tag = format_tag(nimble_list_output_tag, window)
                output_view = get_output_view(
                    formatted_tag,
                    nimble_list_output_method,
                    window
                )
                write_to_view(
                    output_view, output,
                    nimble_list_output_clear
                )
                if nimble_update_output_show:
                    is_console = nimble_list_output_method == 'console'
                    show_view(output_view, is_console)

            if returncode == 0:
                sublime.status_message("Listing Nimble Packages")
            else:
                sublime.status_message('Nimble Package List Retrieval Failed')
            yield

        callback()

    def is_enabled(self):
        return True

    def is_visible(self):
        return nimble_list_enabled

    def description(self):
        return self.__doc__


class NimbleSearchCommand(ApplicationCommand):

    """
    Search Nimble Packages
    """

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
            flag = FlagObject()
            frames = ['Searching package list... ' + f for f in busy_frames]
            loop_status_msg(frames, 0.15, flag)

            # Run the main command
            output, returncode = yield Thread(
                target=run_nimble,
                args=('search -y ' + search_term, this.send)
            ).start()

            # Set the status to show we've finished
            yield setattr(flag, 'break_status_loop', this.next)

            # List output
            if nimble_search_quickpanel_send:
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
            if nimble_search_output_send:
                formatted_tag = format_tag(nimble_search_output_tag, window)
                output_view = get_output_view(
                    formatted_tag,
                    nimble_search_output_method,
                    window
                )
                write_to_view(
                    output_view, output,
                    nimble_search_output_clear
                )
                if nimble_update_output_show:
                    is_console = nimble_search_output_method == 'console'
                    show_view(output_view, is_console)

            if returncode == 0:
                sublime.status_message("Listing Nimble Packages")
            else:
                sublime.status_message('Nimble Package List Retrieval Failed')
            yield

        callback()

    def is_enabled(self):
        return True

    def is_visible(self):
        return nimble_search_enabled

    def description(self):
        return self.__doc__


class NimbleUninstallCommand(ApplicationCommand):

    """
    Uninstall a Nimble package.
    """

    def run(self):
        window = sublime.active_window()

        @send_self
        def callback():
            this = yield

            # Setup the loading notice
            flag = FlagObject()
            frames = ['Uninstalling package: ' + f for f in busy_frames]
            loop_status_msg(frames, 0.15, flag)

            # Run the main command
            output, returncode = yield Thread(
                target=run_nimble,
                args=('uninstall -y', this.send)
            ).start()

            # Set the status to show we've finished
            yield setattr(flag, 'break_status_loop', this.next)

            # Show output
            if nimble_search_output_send:
                formatted_tag = format_tag(nimble_search_output_tag, window)
                output_view = get_output_view(
                    formatted_tag,
                    nimble_search_output_method,
                    window
                )
                write_to_view(
                    output_view, output,
                    nimble_search_output_clear
                )
                if nimble_search_output_show:
                    is_console = nimble_search_output_method == 'console'
                    show_view(output_view, is_console)
            if returncode == 0:
                sublime.status_message("Nimble Package Uninstalled")
            else:
                sublime.status_message('Nimble Package Uninstallation Failed')
            yield

        callback()

    def is_enabled(self):
        return True

    def is_visible(self):
        return nimble_uninstall_enabled

    def description(self):
        return self.__doc__
