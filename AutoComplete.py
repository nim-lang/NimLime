import sublime, sublime_plugin
import os, subprocess, tempfile
import re

try: # Python 3
    from NimLime.Project import Utility
except ImportError: # Python 2:
    from Project import Utility

settings = {}
do_suggestions = False # Whether to provide suggestions
provide_immediate_completions = False # Whether to provide completions immediatly

def update_settings():
    global do_suggestions
    global had_suggestions
    global last_suggestion_pos
    global give_suggestions
    global provide_immediate_completions

    do_suggestions = settings.get("enable_nim_completions")
    if do_suggestions == None:
        do_suggestions = False
    provide_immediate_completions = settings.get("provide_immediate_nim_completions")
    if provide_immediate_completions == None:
        provide_immediate_completions = False

    last_suggestion_pos = ""
    had_suggestions = False
    give_suggestions = False

# settings regarding auto complete
last_suggestion_pos = ""
had_suggestions = False
give_suggestions = False

def plugin_loaded():
    # Load all settings relevant for autocomplete
    global settings
    settings = sublime.load_settings("nim.sublime-settings")
    update_settings()
    settings.add_on_change("enable_nim_completions", update_settings)
    settings.add_on_change("provide_immediate_nim_completions", update_settings)

# Hack to lazily initialize ST2 settings
if int(sublime.version()) < 3000:
    sublime.set_timeout(plugin_loaded, 1000)

def position_str(filename, line, col):
    return "{0}:{1}:{2}".format(filename, line, col)

class SuggestItem:

    def prettify_signature(self, currentModule):
        if self.symType == "skProc" or self.symType == "skMethod":
            fn_name = ""
            if self.modName == currentModule:
                fn_name = self.name
            else:
                fn_name = self.qualName

            self.signature = self.signature.replace("proc", fn_name)

class NimUpdateCompletions(sublime_plugin.TextCommand):

    def run(self, edit):
        if had_suggestions: # Only run when there were already suggestions for this position
            return

        global give_suggestions
        give_suggestions = True
        self.view.window().run_command("hide_auto_complete")
        reload = lambda: self.view.window().run_command("auto_complete");
        sublime.set_timeout(reload, 0)

class NimCompleter(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):
        filename = view.file_name()
        if filename == None or not filename.endswith(".nim") or not do_suggestions:
            return []

        projFile = Utility.get_nimproject(view.window())
        if projFile is None:
            projFile = filename
        modfilename = os.path.basename(filename)
        currentModule = modfilename[:-4]

        window = sublime.active_window()
        results = []

        # Extract the cursor position
        pos = view.rowcol(view.sel()[0].begin())
        line = pos[0] + 1
        col  = pos[1]

        suggestion_pos = position_str(filename, line, col)
        global had_suggestions
        global give_suggestions
        global last_suggestion_pos

        #print(suggestion_pos)
        #print(last_suggestion_pos)
        #print("had: " + str(had_suggestions))
        #print("give: " + str(give_suggestions))

        if (not give_suggestions and suggestion_pos != last_suggestion_pos): # Reset logic
            had_suggestions = False
            give_suggestions = False

        provide_suggestions = provide_immediate_completions or give_suggestions

        if not provide_suggestions:
            return []

        last_suggestion_pos = suggestion_pos
        had_suggestions = True
        give_suggestions = False

        dirtyFileName = ""
        dirtyFile = None
        compiler = settings.get("nim_compiler_executable")
        if compiler == None or compiler == "": return []
        pargs = compiler + " --verbosity:0 idetools "

        if view.is_dirty():
            #Generate dirty file
            size = view.size()
            dirtyFile = tempfile.NamedTemporaryFile(suffix=".nim", delete=False)
            dirtyFileName = dirtyFile.name
            dirtyFile.file.write(
                view.substr(sublime.Region(0, size)).encode("UTF-8")
            )
            dirtyFile.file.close()
            pargs = pargs + "--trackDirty:" + dirtyFileName + ","
        else:
            pargs = pargs + "--track:"

        pargs = pargs + filename \
         + "," + str(line) + "," + str(col) \
         + " --suggest " + projFile

        print(pargs)

        handle = os.popen(pargs)
        line = " "
        while line:
            line = handle.readline()

            print(line)
            parts = line.split("\t")
            partlen = len(parts)

            if partlen != 8 or (parts[0] != "sug" and parts[0] != "con"):
                continue

            item = SuggestItem()
            item.symType = parts[1]
            item.qualName = parts[2]
            item.signature = parts[3]
            item.file = parts[4]
            item.line = int(parts[5])
            item.col = int(parts[6])
            item.docs = parts[7]
            dots = item.qualName.split(".")
            if len(dots) == 2:
              item.name = dots[1]
              item.modName = dots[0]
            else:
              item.modName = currentModule
              item.name = item.qualName

            item.prettify_signature(currentModule)

            completion = ""
            hint = ""

            if item.modName == currentModule:
                completion = item.name
                hint = item.name + "\t" + item.signature
            else:
                if prefix == "":
                    completion = item.name
                    hint = item.name + "\t" + item.signature
                else:
                    completion = item.qualName
                    hint = item.qualName + "\t" + item.signature

            results.append((hint, completion))

        # Close the idetools connection
        handle.close()

        # Delete the dirty file
        if dirtyFile != None:
            dirtyFile.close()
            try:
                os.unlink(dirtyFile.name)
            except OSError:
                pass
        # get results from each tab
        return results # sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS