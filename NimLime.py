import os.path

debug = True
target_directory = os.path.dirname(__file__)

try:
    # Try using the sys_path mechanism provided by package control
    from package_control import sys_path
    sys_path.add(target_directory)
except ImportError:
    import sys
    if debug:
        print("Warning, couldn't import package_control.sys_path")
    sys.path.append(target_directory)

from nimlime_core import *