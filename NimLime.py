# coding=utf-8
"""
Stub file for loading the NimLime plugin.
See __init__.py for the actual code.
"""
import os
import sys

root_dir = os.path.dirname(os.path.abspath(__file__))
if sys.version_info < (3, 0):
    execfile('__init__.py')
