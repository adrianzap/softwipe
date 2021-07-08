"""
This module contains all information concerning the tools that are used by softwipe.
"""

import collections
import enum


Tool = collections.namedtuple('Tool', ['exe_name', 'install_name', 'install_via'])
VIA = enum.Enum('VIA', 'PACKAGE_MANAGER PIP DOWNLOAD')


# The exe_names may be modified to contain a full path
class TOOLS:
    """
    A container used to separately download static analysis tools used by softwipe.
    """
    CLANG = Tool('clang', 'clang', VIA.PACKAGE_MANAGER)
    CLANGPP = Tool('clang++', 'clang', VIA.PACKAGE_MANAGER)
    CMAKE = Tool('cmake', 'cmake', VIA.PACKAGE_MANAGER)
    MAKE = Tool('make', 'make', VIA.PACKAGE_MANAGER)
    COMPILEDB = Tool('compiledb', 'compiledb', VIA.PIP)
    CPPCHECK = Tool('cppcheck', 'cppcheck', VIA.PACKAGE_MANAGER)
    CLANG_TIDY = Tool('clang-tidy', 'llvm', VIA.PACKAGE_MANAGER)
    LIZARD = Tool('lizard', 'lizard', VIA.PIP)
    KWSTYLE = Tool('KWStyle', 'KWStyle', VIA.DOWNLOAD)
    INFER = Tool('infer', 'infer', VIA.DOWNLOAD)
    # NOTINSTALLED0 = Tool('jshgjhsdhg', 'jshjlgbkjvjkshg', Via.PACKAGE_MANAGER)
    # NOTINSTALLED1 = Tool('hsdhjkhsjdhgjk', 'ahdjfhjkhdjkfhs', Via.PACKAGE_MANAGER)
    # NOTINSTALLED2 = Tool('hshjkgh', 'ksjhkjghjlsdg', Via.PIP)
