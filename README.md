NimLime
=======

Super Nimrod Plugin for Sublime Text 2/3

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

Autocompletion is per default in an on-demand mode.  
This means `ctrl+space` has to be pressed again to fetch Nimrod compiler completions.
It can also be set into an immediate mode.

If auto-completions don't work copy the `nimrod_update_completions` block from the NimLime
default key bindings file to the user key bindings file.
