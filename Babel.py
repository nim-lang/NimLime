import sublime
import sublime_plugin
import subprocess
import threading
import functools

# Resources
# http://docs.sublimetext.info/en/latest/reference/command_palette.html
# https://github.com/wbond/sublime_package_control/blob/6a8b91ca58d66cb495b383d9572bb801316bcec5/package_control/commands/install_package_command.py


def run_babel(cmd):
    # TODO - in babel does not exist, display error
    output = subprocess.Popen("babel " + cmd,
                              stdout=subprocess.PIPE,
                              shell=True)
    return output.stdout


class Package(object):
    pass


class BabelListCommand(sublime_plugin.WindowCommand):

    """
    Present a list of available babel packages and allow
    the user to pick a package to install.
    """

    def list(self):
        items = run_babel("list")
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

        self.window.run_command("babel_install", {'name': item[0]})

    def run(self):
        # Display list of packages to install
        self.items = []

        for item in self.list():
            self.items.append([
                item.name,
                item.description
            ])

        self.window.show_quick_panel(self.items, self.on_done)


class BabelUpdateCommand(sublime_plugin.WindowCommand):

    """
    Update the Babel package list
    """

    @staticmethod
    def update():
        run_babel("update")

        def show_status():
            sublime.status_message("Babel package list updated")

        sublime.set_timeout(show_status, 10)

    def run(self):
        sublime.status_message("Updating Babel package list...")
        threading.Thread(
            target=functools.partial(BabelUpdateCommand.update)
        ).start()


class BabelInstallThread(threading.Thread):

    def __init__(self, pkgName=""):
        self.pkgName = pkgName
        threading.Thread.__init__(self)

    def run(self):
        run_babel("install -y " + self.pkgName)
        msg = self.pkgName + " installed."

        def show_status():
            sublime.status_message(msg)

        sublime.set_timeout(show_status, 10)


class BabelInstallCommand(sublime_plugin.WindowCommand):

    """
    Install the specified babel package
    """

    def run(self, name):
        BabelInstallThread(name).start()
