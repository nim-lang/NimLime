import sublime
import sublime_plugin
import subprocess
import threading
import functools

# Resources
# http://docs.sublimetext.info/en/latest/reference/command_palette.html
# https://github.com/wbond/sublime_package_control/blob/6a8b91ca58d66cb495b383d9572bb801316bcec5/package_control/commands/install_package_command.py


def run_nimble(cmd):
    # TODO - in nimble does not exist, display error
    output = subprocess.Popen("nimble " + cmd,
                              stdout=subprocess.PIPE,
                              shell=True)
    return output.stdout


class Package(object):
    pass


class NimbleListCommand(sublime_plugin.WindowCommand):

    """
    Present a list of available nimble packages and allow
    the user to pick a package to install.
    """

    def list(self):
        items = run_nimble("list")
        pkg = None

        for row in items:

            if row.strip() == "":
                if pkg is not None:
                    yield pkg
                pkg = None
                continue

            # Process row name
            if pkg is None:
                # Split package and start new package
                pkg = Package()
                setattr(pkg, "name", row.split(":", 1)[0].strip())

            # Parse property
            else:
                info = row.split(":", 1)
                if len(info) < 2:
                    continue
                setattr(pkg, info[0].strip(), info[1].strip())

    def on_done(self, picked):
        if picked < 0:  # Action was cancelled
            return

        item = self.items[picked]

        self.window.run_command("nimble_install", {'name': item[0]})

    def run(self):
        # Display list of packages to install
        self.items = []

        for item in self.list():
            self.items.append([
                item.name,
                item.description
            ])

        self.window.show_quick_panel(self.items, self.on_done)


class NimbleUpdateCommand(sublime_plugin.WindowCommand):

    """
    Update the Nimble package list
    """

    @staticmethod
    def update():
        run_nimble("update")

        def show_status():
            sublime.status_message("Nimble package list updated")

        sublime.set_timeout(show_status, 10)

    def run(self):
        sublime.status_message("Updating Nimble package list...")
        threading.Thread(
            target=functools.partial(NimbleUpdateCommand.update)
        ).start()


class NimbleInstallThread(threading.Thread):

    def __init__(self, pkgName=""):
        self.pkgName = pkgName
        threading.Thread.__init__(self)

    def run(self):
        run_nimble("install -y " + self.pkgName)
        msg = self.pkgName + " installed."

        def show_status():
            sublime.status_message(msg)

        sublime.set_timeout(show_status, 10)


class NimbleInstallCommand(sublime_plugin.WindowCommand):

    """
    Install the specified Nimble package
    """

    def run(self, name):
        NimbleInstallThread(name).start()
