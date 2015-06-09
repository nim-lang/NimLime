import sublime

if int(sublime.version()) >= 3000:
    import NimLime.NimLime as lime
else:
    import NimLime as lime

add_module = lime.add_module
