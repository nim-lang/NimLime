Directory Structure
  /
    Root directory.
    Contains various sublime text plugin files that can't be moved elsewhere,
    meta files (such as this one), and the base plugin script loaded by
    Sublime Text, 'NimLime.py'.

  /nimlime_core
    Main module.
    Contains the module initialization code, as well as common code used
    by both command and support modules.

  /nimlime_core/utils
    Support and utility module.
    Contains support code used across multiple command files.

  /nimlime_core/commands
    'Plugin' module.
    Contains the commands and event listeners that implementing NimLime's
    features.
    *Note*: The all python files in this directory are loaded, and all command
    and event listener classes are exported automatically.

  /Syntaxes
    Sublime text syntax directory.
    Contains the Sublime Text syntax files used by NimLime.

  /Support
    Main Sublime Text data directory.
    Contains menu, preferences, and other data files used by Sublime Text's
    plugin system.

