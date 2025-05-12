Nim
===

The official Nim Programming Language plugin for Sublime Text.

Features
--------

* Syntax highlighting.
* Snippets.
* Automatic continuation of doc comments.

Installation
------------

1. Run `Package Control: Install Package` from the command palette.
2. Choose `Nim`.

It is also recommended to install [LSP-nimlangserver](https://packagecontrol.io/packages/LSP-nimlangserver)
to enjoy IDE-like features.

Settings
--------

See Preferences -> Package Settings -> Nim

Indentation Settings
--------------------

Nim requires indentation using spaces. Sublime Text defaults to using tabs for indentation, which can result in issues when working with Nim code.

To avoid indentation errors, configure Sublime Text to use spaces instead of tabs when editing Nim files:
1. Open a .nim file in Sublime Text.
2. Go to `Preferences -> Settings - Syntax Specific`.
3. In the right-hand panel (`Nim.sublime-settings`), add the following:
```json
{
	"translate_tabs_to_spaces": true,
	"tab_size": 2
}
```

Contributing
------------

Pull requests are welcome! See DEVELOPMENT.md for an overview of Nim's design.

Clone the repository in your Sublime package directory.

Install the [PackageDev](https://github.com/SublimeText/PackageDev).

Modify the `.YAML-tmLanguage` files and regenerate the `.tmLanguage` files
by summoning the command palette and selecting the `Convert (YAML, JSON, PLIST) to...`
command. Don't modify the `.tmLanguage` files, they will be overwritten!
