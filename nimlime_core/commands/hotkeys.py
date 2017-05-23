# coding=utf-8
"""
Hotkey wiring for NimLime
"""
from sublime_plugin import EventListener
import sublime
from nimlime_core import settings


sync_list = {}


def gen_sync_settings(key, default):
    print('f')
    global sync_list
    
    def sync_settings():
        print('e', key)
        v = sublime.active_window().active_view()
        v.settings().set(key, settings.get(key, default))
        
    sync_list[key] = sync_settings
    settings.run_on_load_and_change(key, sync_settings)  


gen_sync_settings("doccontinue.enabled", True)
gen_sync_settings("doccontinue.autostop", True)
    

class HotkeySyncer(EventListener):
    def sync(self):
        print('d')
        global sync_list
        for callback in sync_list.values():
            callback()
            
    def on_new(self, view):
        print('c')
        self.sync()

    def on_clone(self, view):
        print('b')
        self.sync()

    def on_load(self, view):
        print('a')
        self.sync()
