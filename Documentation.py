import sublime_plugin
import os
import json

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))


class ListModulesCommand(sublime_plugin.WindowCommand):

    """
    Display list of all modules and their descriptions
    """
    path = "/Documentation/modules/module_index.json"

    def on_item(self, picked):
        # TODO - Open the file at that point
        pass

    def on_done(self, picked):
        if picked < 0:
            return

        item = self.items[picked]
        module = item[0]
        mod_path = PACKAGE_DIR + "/Documentation/modules/" + module + ".json"

        mod_items = []
        with open(mod_path) as json_data:
            data = json.load(json_data)

            for obj in data:
                row = []
                if obj.get("name"):
                    row.append(obj["name"])
                    mod_items.append(row)

                if obj.get("code"):
                    row.append(obj["code"][0:100])

                if obj.get("description"):
                    row.append(obj["description"][0:100])

        self.window.show_quick_panel(mod_items, self.on_item)

    def run(self):
        self.items = []

        # Parse items
        with open(PACKAGE_DIR + ListModulesCommand.path) as json_data:
            data = json.load(json_data)

            for obj in data:
                row = [obj["module"]]
                if obj.get("description"):
                    row.append(obj["description"][0:100])

                self.items.append(row)

            self.window.show_quick_panel(self.items, self.on_done)


class ListAllCommand(sublime_plugin.WindowCommand):

    """
    Display index of all procs/modules/methods/etc in std lib
    """
    path = PACKAGE_DIR + "/Documentation/modules/proc_index.json"

    def on_done(self, picked):
        # TODO - Open file at that point
        pass

    def run(self):
        items = []

        with open(ListAllCommand.path) as json_data:
            data = json.load(json_data)

            for obj in data:
                row = [
                    obj["name"],
                    "import " + obj["module"],
                    obj["code"][0:100]
                ]

                if obj.get("desc"):
                    row.append(obj["desc"][0:100])

                items.append(row)

        self.window.show_quick_panel(
            sorted(items, key=lambda i: i[0]),
            self.on_done
        )
