# coding=utf-8
"""
Commands and code to expose nimsuggest functionality to the user.
"""
import os
from os import fdopen
from pprint import pprint
from tempfile import mkstemp

import sublime
from nimlime_core.utils.error_handler import catch_errors
from nimlime_core.utils.idetools import Nimsuggest
from nimlime_core.utils.misc import send_self
from nimlime_core.utils.mixins import NimLimeOutputMixin, NimLimeMixin
from sublime_plugin import ApplicationCommand

nimsuggest_instances = {}
tmp_files = {}


class NimFindDefinition(NimLimeOutputMixin, ApplicationCommand):
    settings_selector = 'idetools.find_definition'

    @send_self
    @catch_errors
    def run(self):
        this = yield
        window = sublime.active_window()
        view = window.active_view()
        nimsuggest = get_nimsuggest_instance(view.file_name())

        nim_file, dirty_file, line, column = get_ide_parameters(window, view)
        entries = yield nimsuggest.find_definition(
                nim_file, dirty_file, line, column, this.send
        )
        pprint(entries)


class NimFindUsages(NimLimeOutputMixin, ApplicationCommand):
    settings_selector = 'idetools.find_usages'

    @send_self
    @catch_errors
    def run(self):
        this = yield
        window = sublime.active_window()
        view = window.active_view()
        nimsuggest = get_nimsuggest_instance(view.file_name())

        entries = yield nimsuggest.find_definition(
                nim_file, dirty_file, line, column, this.send
        )
        pprint(entries)


class NimFindUsagesInCurrentFile(NimLimeMixin, ApplicationCommand):
    settings_selector = 'idetools.find_current_file_usages'

    @send_self
    @catch_errors
    def run(self):
        this = yield
        window = sublime.active_window()
        view = window.active_view()
        nimsuggest = get_nimsuggest_instance(view.file_name())

        entries = yield nimsuggest.find_definition(
                nim_file, dirty_file, line, column, this.send
        )
        pprint(entries)


class GetNimSuggestions(NimLimeMixin, ApplicationCommand):
    settings_selector = 'idetools.get_suggestions'

    @send_self
    @catch_errors
    def run(self):
        this = yield
        window = sublime.active_window()
        view = window.active_view()
        nimsuggest = get_nimsuggest_instance(view.file_name())

        entries = yield nimsuggest.find_definition(
                nim_file, dirty_file, line, column, this.send
        )
        pprint(entries)


def get_nimsuggest_instance(project_file):
    canonical_project = os.path.normcase(os.path.normpath(project_file))
    instance = nimsuggest_instances.get(canonical_project)
    if instance is None:
        instance = Nimsuggest(canonical_project)
        nimsuggest_instances[project_file] = instance
    return instance


def get_ide_parameters(window, view):
    nim_file = view.file_name()

    tmp_pair = tmp_files.get(nim_file, None)
    if tmp_pair is None:
        a, b = mkstemp()
        tmp_pair = (fdopen(a, 'wb', 0), b)
        tmp_files[nim_file] = tmp_pair
    handle, dirty_file = tmp_pair

    handle.truncate(0)
    handle.write(view.substr(sublime.Region(0, view.size())).encode('utf-8'))
    handle.flush()

    line, column = view.rowcol(view.sel()[0].a)
    line += 1
    column += 1

    return nim_file, dirty_file, line, column
