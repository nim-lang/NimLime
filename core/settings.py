import weakref
from inspect import ismethod

import sublime

_settings = None
_subscribers = []
_plugin_loaded = False


def plugin_loaded():
    global _settings, _plugin_loaded
    # print('Loaded')
    _plugin_loaded = True
    _settings = sublime.load_settings('NimLime.sublime-settings')
    _settings.add_on_change(__name__, _notify_subscribers)
    _notify_subscribers()


class MethodProxy(object):
    __slots__ = ['_object_ref', '_method_ref']

    def __init__(self, method):
        self._object_ref = weakref.ref(
            method.__self__,
            _cleanup_subscribers
        )
        self._method_ref = weakref.ref(
            method.__func__,
            _cleanup_subscribers
        )

    def __call__(self):
        object_deref = self._object_ref()
        method_deref = self._method_ref()

        if object_deref is None or method_deref is None:
            return
        else:
            return method_deref(object_deref)

    def is_valid(self):
        return (
            self._object_ref() is not None and
            self._method_ref() is not None
        )


def _notify_subscribers():
    global _subscribers
    # print('Notifying subscribers')
    for subscriber in _subscribers:
        if isinstance(subscriber, MethodProxy):
            subscriber()
        else:
            real_subscriber = subscriber()
            if real_subscriber is not None:
                real_subscriber()

    _cleanup_subscribers()


def _cleanup_subscribers(subscriber_wr=None):
    global _subscribers
    i = len(_subscribers) - 1
    while i >= 0:
        subscriber = _subscribers[i]
        pop_subscriber = False
        if isinstance(subscriber, MethodProxy):
            pop_subscriber = not subscriber.is_valid()
        else:
            pop_subscriber = (subscriber() is None)

        if pop_subscriber:
            _subscribers.pop(i)
            i -= 1
        i -= 1


def get(name, default):
    global _settings
    # import traceback;traceback.print_stack()
    if _settings is None:
        # print("Retrieving dummy value from setting", name)
        return default
    else:
        # print("Retrieving value (default {}) from {}: {}".format(default, name, _settings.get(name, default)))
        return _settings.get(name, default)


def notify_on_change(callback):
    global _subscribers
    if ismethod(callback):
        _subscribers.append(MethodProxy(callback))
    else:
        _subscribers.append(weakref.ref(callback))
