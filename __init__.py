import os

debug = True
root_dir = os.path.dirname(os.path.abspath(__file__))


try:
    # Try using the sys_path mechanism provided by package control
    from package_control import sys_path
    sys_path.add(root_dir)
except ImportError:
    import sys
    if debug:
        print("Warning, couldn't import package_control.sys_path")
    sys.path.append(root_dir)

from nimlime_core import *