from sublime_plugin import TextCommand


class NimlimeOutputCommand(TextCommand):

    def run(self, edit_obj, action, args):
        if action == 'insert':
            self.view.insert(edit_obj, *args)
        elif action == 'erase':
            region = sublime.Region(*args)
            self.view.erase(edit_obj, region)
        elif action == 'replace':
            region = sublime.Region(args[0], args[1])
            self.view.replace(edit_obj, region, args[2])
        else:
            raise Exception("Bad edit action")