import sublime


settings = sublime.load_settings('NimLime.sublime-settings')
load_callbacks = []
when_settings_load = load_callbacks.append

def load():
	global settings, load_callbacks
	s = sublime.load_settings('NimLime.sublime-settings')
	if settings.get('has_loaded', True) is None:
		sublime.set_timeout(load, 1000)
	else:
		for callback in load_callbacks:
			callback()
		when_settings_load = lambda c: c()
		load_callbacks = None

load()


from .autocomplete import *
from .doccontinue import *
from .documentation import *
from .gotodef import *
from .lookup import *
from .nimble import *
from .nimcheck import *
from .project import *