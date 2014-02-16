import sublime, sublime_plugin
import os, subprocess, tempfile
import re

try:  # Python 3
    from NimrodSublime.Project import Utility
except ImportError:  # Python 2:
    from Project import Utility

##Resources
# http://sublimetext.info/docs/en/extensibility/plugins.html
# http://www.sublimetext.com/docs/2/api_reference.html#sublime.View
# http://net.tutsplus.com/tutorials/python-tutorials/how-to-create-a-sublime-text-2-plugin/
# http://www.sublimetext.com/docs/plugin-examples

import sublime_plugin, sublime

class SuggestItem:

    def prettify_signature(self, currentModule):
        if self.symType == "skProc":
            fn_name = ""
            if self.modName == currentModule:
                fn_name = self.name
            else:
                fn_name = self.qualName

            self.signature = self.signature.replace("proc", fn_name)


class NimrodCompleter(sublime_plugin.EventListener):

    def on_query_completions(self, view, prefix, locations):
        filename = view.file_name()
        if filename == None or not filename.endswith(".nim"):
            return []

        dotop = prefix == ""

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
        
        dirtyFileName = ""
        dirtyFile = None
        pargs = "nimrod --verbosity:0 idetools --suggest "

        if view.is_dirty():
            #Generate dirty file
            size = view.size()
            dirtyFile = tempfile.NamedTemporaryFile(suffix=".nim", delete=True)
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
         + " " + projFile

        print(pargs)

        handle = os.popen(pargs)
        line = " "
        while line:
            line = handle.readline()

            print(line)
            parts = line.split("\t")
            partlen = len(parts)

            if partlen != 8 or parts[0] != "sug":
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
                if dotop:
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

        # get results from each tab
        return results # sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS