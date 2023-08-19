NimLime
=======

Nim Programming Language plugin for Sublime Text

Features
--------

* Syntax highlighting.
* Snippets.
* Automatic continuation of doc comments.

Installation
------------

### Latest/Unstable

Note that the latest version comes directly from the repository, and thus may be broken at any time!
Thus, it is only recommended for those who wish to either help develop NimLime, or can work around bugs.

* Summon the command palette and select `Package Control: Add repository`
* Enter the project's URL (https://github.com/nim-lang/NimLime)
* Install `NimLime` through Package Control

### Stable

* Install `NimLime` through Package Control (this version is usually older than the one here)


Settings
--------

See Preferences -> Package Settings -> NimLime

Contributing
------------

Pull requests are welcome! See DEVELOPMENT.md for an overview of NimLime's design.

Clone the repository in your Sublime package directory.

Install the [PackageDev](https://github.com/SublimeText/PackageDev).

Modify the `.YAML-tmLanguage` files and regenerate the `.tmLanguage` files
by summoning the command palette and selecting the `Convert (YAML, JSON, PLIST) to...`
command. Don't modify the `.tmLanguage` files, they will be overwritten!
