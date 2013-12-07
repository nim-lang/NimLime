import sublime, sublime_plugin
import os, threading, functools

##Resources
# http://docs.sublimetext.info/en/latest/reference/command_palette.html
# https://github.com/wbond/sublime_package_control/blob/6a8b91ca58d66cb495b383d9572bb801316bcec5/package_control/commands/install_package_command.py

class Babel:

    @staticmethod
    def run(cmd):
        #TODO - in babel does not exist, display error
        return os.popen("babel " + cmd)


class Package(object): 
    pass


class BabelListCommand(sublime_plugin.WindowCommand):
    """
    Present a list of available babel packages and allow
    the user to pick a package to install.
    """

    def list(self):
        items = Babel.run("list")
        pkg   = None

        for row in items:

            if row.strip() == "":
                if pkg is not None:
                    yield pkg
                pkg = None
                continue

            #Process row name
            if pkg == None:
                #Split package and start new package
                pkg = Package()
                setattr(pkg, "name", row.split(":", 1)[0].strip())

            #Parse property
            else:
                info = row.split(":", 1)
                setattr(pkg, info[0].strip(), info[1].strip())

    def on_done(self, picked):
        item = self.items[picked]

        self.window.run_command("babel_install", { 'name':  item[0] })

    def run(self):
        #Display list of packages to install
        self.items = []

        for item in self.list():
            self.items.append([
                item.name,
                item.description
            ])

        self.window.show_quick_panel(self.items, self.on_done)


class BabelUpdateCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        None


class BabelInstallCommand(sublime_plugin.WindowCommand):
    """
    Install the specified babel package
    """

    @staticmethod
    def install(name):
        Babel.run("install " + name)
        msg = name + " installed."

        def show_status():
            sublime.status_message(msg)

        sublime.set_timeout(show_status, 10)

    def run(self, name):
        threading.Thread(
            target=functools.partial(BabelInstallCommand.install, name)
        ).start()


class BabelUninstallCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        None