NimLime
=======

Super Nim Plugin for Sublime Text 2/3

Features
--------

* Syntax highlighting
* Jump to definition
* Auto-Completion
* Error checking and highlighting
* Babel package manager integration

Installation
------------

Clone the repository in your Sublime package directory

Settings
--------

See Preferences -> PackageSettings -> NimLime

Autocompletion works per default in an on-demand mode.
This means `ctrl+space` has to be pressed again to fetch Nim compiler completions.
It can also be set into an immediate mode.

If auto-completions don't work copy the `nim_update_completions` block from the NimLime
default key bindings file to the user key bindings file.

Checking the current file automatically on-save can be enabled through the setting `check_nim_on_save`.

The path to the compiler can be configured through the setting `nim_compiler_executable`.
Per default it is set to `nim`, which means that the compiler must be in your `PATH` for the plugin to work.