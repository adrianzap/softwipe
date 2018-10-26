"""
This module contains string constants.
"""


COMPILER_WARNING_FLAGS = '-Weverything'
SET_CMAKE_CXX_FLAGS_COMPILER_WARNINGS = 'set(CMAKE_CXX_FLAGS "' + COMPILER_WARNING_FLAGS + ' ${CMAKE_CXX_FLAGS}")'
SET_CMAKE_C_FLAGS_COMPILER_WARNINGS = 'set(CMAKE_C_FLAGS "' + COMPILER_WARNING_FLAGS + ' ${CMAKE_C_FLAGS}")'


_dashes = ' --- '
_running = 'Running: '
_header = _dashes + _running + '{}' + _dashes
RUN_COMPILER_HEADER = _header.format('COMPILER')
RUN_ASSERTION_CHECK_HEADER = _header.format('ASSERTION CHECK')
RUN_CPPCHECK_HEADER = _header.format('CPPCHECK')
RUN_SPLINT_HEADER = _header.format('SPLINT')
RUN_CLANG_TIDY_HEADER = _header.format('CLANG-TIDY')
RUN_LIZARD_HEADER = _header.format('LIZARD')
RUN_KWSTYLE_HEADER = _header.format('KWSTYLE')


OS_MACOS = 'Darwin'
OS_WINDOWS = 'Windows'
OS_BEGINNING_OF_CYGWIN_NAME = 'CYGWIN_NT'  # The Windows OS number is appended to this name (e.g. for Win7 it is:
                                           # 'CYGWIN_NT-6.1')
OS_LINUX = 'Linux'
OS_UBUNTU = 'Ubuntu'
OS_DEBIAN = 'debian'
OS_FEDORA = 'Fedora'
OS_RHEL = 'Red Hat Enterprise Linux Server'


_softwipe = 'softwipe_'

RATE_COUNT_TOTAL = '{} ({}/{})'

RESULTS_FILENAME_COMPILER = _softwipe + 'compilation_warnings.txt'
RESULTS_FILENAME_ASSERTION_CHECK = _softwipe + 'assertion_check.txt'
RESULTS_FILENAME_CPPCHECK = _softwipe + 'cppcheck_results.txt'
RESULTS_FILENAME_SPLINT = _softwipe + 'splint_results.txt'
RESULTS_FILENAME_CLANG_TIDY = _softwipe + 'clang_tidy_results.txt'
RESULTS_FILENAME_LIZARD = _softwipe + 'lizard_results.txt'
RESULTS_FILENAME_KWSTYLE = _softwipe + 'kwstyle_results.txt'

RESULT_COMPILER_WARNING_RATE = 'Compiler warning rate: ' + RATE_COUNT_TOTAL
RESULT_ASSERTION_RATE = 'Assertion rate: ' + RATE_COUNT_TOTAL
RESULT_ASSERTION_RATE_DETAILED = 'Found {count} assertions in {loc} lines of pure' \
                              ' code (i.e. excluding blank lines and comment lines).' + '\n' \
                              'That\'s an assertion rate of {rate}, or {percentage}%.'
RESULT_CPPCHECK_WARNING_RATE = 'Cppcheck warning rate: ' + RATE_COUNT_TOTAL
RESULT_CLANG_TIDY_WARNING_RATE = 'Clang-tidy warning rate: ' + RATE_COUNT_TOTAL
RESULT_KWSTYLE_WARNING_RATE = 'KWStyle warning rate: ' + RATE_COUNT_TOTAL


SOFTWIPE_BUILD_DIR_NAME = _softwipe + 'build'

                                                                                #
COMMAND_FILE_HELP = """        --- Command file help ---

The command file (provided via -f option) is a file that contains:
 -for make-based projects: commands that are used to build the program
 -for compiler-based projects: compiler options

    ==== Make-based projects ====
The command file contains all commands that must be executed to correctly build
the project. The commands must be written into the file line by line.
 Example command file 1 (1 line):
make client
 Example command file 2 (4 lines):
cd builddir/
./configure
make all
make install
 If you use "cd" in your commands, do NOT escape paths or enclose them in
quotation marks!
 If no command file is given for a make-based project, it will be assumed that
one simple call of "make" works for compilation.

    ==== Compiler-based projects ====
The command file contains all options that must be passed to the compiler to
correctly build the project. The file should only contain one line.
 Note that these are just the options; targets (i.e. the files that should be
compiled) should be specified via the -l option. This is done so that the user
does not have to use a command file if no particular important options are
required for compilation.
 Example command file:
-std=c++14 -save-stats
 If no command file is given for a compiler-based project, it will be assumed
that simply compiling the targets using clang/clang++ works."""
                                                                                #
