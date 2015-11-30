# Mixins used to give common functionality to NimLime commands.
from nimlime_core import settings
from nimlime_core.utils.output import (
    get_output_view, write_to_view, show_view, format_tag
)


class NimLimeMixin(object):
    setting_entries = (
        ('enabled', '{0}.enabled', True),
    )

    def __init__(self, *args, **kwargs):
        self.enabled = True
        if hasattr(self, 'load_settings'):
            self.reload_settings()

    def reload_settings(self):
        self.load_settings()
        settings.run_on_load_and_change('reload', self.load_settings)

    def get_setting(self, key, default):
        formatted_key = key.format(self.settings_selector)
        result = settings.get(formatted_key, default)
        return result

    def load_settings(self):
        def is_setting_entry(entry):
            return (
                len(entry) == 3 and
                isinstance(entry[0], str) and
                isinstance(entry[1], str)
            )

        def load_entry(entry):
            if is_setting_entry(entry):
                setattr(self, entry[0], self.get_setting(entry[1], entry[2]))
            else:
                for sub_entry in entry:
                    self.load_entry(sub_entry)

        load_entry(self.setting_entries)

    def is_enabled(self, *args, **kwargs):
        return self.enabled

    def is_visible(self):
        return self.is_enabled()

    def description(self, *args, **kwargs):
        return self.__doc__


class NimLimeOutputMixin(NimLimeMixin):
    setting_entries = (
        NimLimeMixin.setting_entries,
        ('clear_output', '{0}.output.clear', True),
        ('output_method', '{0}.output.method', 'grouped'),
        ('send_output', '{0}.output.send', True),
        ('show_output', '{0}.output.show', True),
        ('output_tag', '{0}.output.tag', 'nimlime'),
        ('raw_output', '{0}.output.raw', True),
        ('output_name', '{0}.output.name', 'nimlime'),
    )

    def write_to_output(self, content, source_window, source_view):
        tag = format_tag(self.output_tag, source_window, source_view)
        output_window, output_view = get_output_view(
            tag, self.output_method, self.output_name, self.show_output,
            source_window
        )

        write_to_view(output_view, content, self.clear_output)

        if self.show_output:
            output_view.settings().set('output_tag', tag)
            is_console = (self.output_method == 'console')
            show_view(output_window, output_view, is_console)
