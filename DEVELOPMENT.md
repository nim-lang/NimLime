NimLime Architecture Overview
=============================
The following is a general overview of the NimLime plugin's design and the
considerations that should be made when adding or extending functionality.


Directory Structure
-------------------
- **/**  
  Root directory.  
  Contains various sublime text plugin files that can't be moved elsewhere,
  meta files (such as this one), and the base plugin script loaded by
  Sublime Text, 'NimLime.py'.

- **/nimlime_core**  
  Main module.  
  Contains the module initialization code, as well as common code used
  by both command and support modules.

- **/nimlime_core/utils**  
  Support and utility module.  
  Contains support code used across multiple command files.

- **/nimlime_core/commands**  
  'Plugin' module.  
  Contains the commands and event listeners that implementing NimLime's
  features.  
  *Note*: The python files in this directory are specially loaded by the
  module's ``__init__.py`` so that all commands and event listeners are
  exported automatically. This allows ``NimLime.py`` to import and export
  *just* the commands to be exposed to Sublime Text's plugin system, without
  causing namespace pollution.

- **/Syntaxes**  
  Sublime text syntax directory.  
  Contains the Sublime Text syntax files used by NimLime.

- **/Support**  
  Main Sublime Text data directory.  
  Contains menu, preferences, and other data files used by Sublime Text's
  plugin system.


NimLime Commands
----------------
NimLime commands follow a certain augmented architecture which helps them act
in a consistant manner and makes developing them less painful.  
First, most commands use a mixin from ``/nimlime_core/utils/mixins.py``. The
mixins implement two important functionalities: setting loading and textual
output. Refer to the documentation in that module for more information.
