# coding=utf-8
"""
Pseudo-root for the NimLime plugin.
This adds the actual NimLime root to the python module path list.
"""
import os

root_dir = os.path.dirname(os.path.abspath(__file__))

try:
    # Try using the sys_path mechanism provided by package control
    from package_control import sys_path

    sys_path.add(root_dir)
except ImportError:
    import sys

    sys_path = sys.path
    print("NimLime: Warning, couldn't import package_control.sys_path")
    sys.path.append(root_dir)

from nimlime_core.commands import *
