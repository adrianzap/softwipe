"""
This module contains string constants.
"""


COMPILER_WARNING_FLAGS = '-Weverything -Wno-padded -Wno-c++98-compat -Wno-c++98-compat-pedantic -Wno-c99-compat ' \
                         '-Wno-c++11-extensions -Wno-newline-eof -Wno-source-uses-openmp'
COMPILER_SANITIZER_FLAGS = '-g -fno-omit-frame-pointer -fsanitize=address -fsanitize-recover=address ' \
                           '-fsanitize=undefined'
COMPILE_FLAGS = COMPILER_WARNING_FLAGS + ' ' + COMPILER_SANITIZER_FLAGS
SET_CFLAGS = 'CFLAGS="{}"'.format(COMPILE_FLAGS)
SET_CXXFLAGS = 'CXXFLAGS="{}"'.format(COMPILE_FLAGS)
SET_CPPFLAGS = 'CPPFLAGS="{}"'.format(COMPILE_FLAGS)
SET_LDFLAGS = 'LDFLAGS="{}"'.format(COMPILE_FLAGS)

SET_CC = 'CC="clang"'
SET_CXX = 'CXX="clang++"'

SET_ALL_MAKE_FLAGS = SET_CC + ' ' + SET_CXX + ' ' + SET_CFLAGS + ' ' + SET_CXXFLAGS + ' ' + SET_CPPFLAGS + ' ' + \
                     SET_LDFLAGS


NO_MAKE_CLEAN_TARGET_FOUND = 'Seems like there is no "make clean" target :( Please make sure the build directory is ' \
                             'clean such that I can compile from scratch, else I might not find all warnings.\n' \
                             'If you do have a "make clean" target, please make sure you\'re using "rm -f" to ' \
                             'prevent rm from  crashing if a file doesn\'t exist.'


COMPILATION_CRASHED = 'Compilation crashed with error code {}!\n{}'


CLANG_TIDY_CHECKS_C = '-*,bugprone-*,clang-analyzer-*,misc-*,modernize-*,mpi-*,performance-*,readability-*,' \
                      '-readability-non-const-parameter'
CLANG_TIDY_CHECKS_CPP = CLANG_TIDY_CHECKS_C + ',boost-*,cppcoreguidelines-*'


_dashes = ' --- '
_running = 'Running: '
_header = _dashes + _running + '{}' + _dashes
RUN_COMPILER_HEADER = _header.format('COMPILER')
RUN_EXECUTION_WITH_SANITIZERS_HEADER = _dashes + 'EXECUTING the program with clang sanitizers' + _dashes
RUN_ASSERTION_CHECK_HEADER = _header.format('ASSERTION CHECK')
RUN_CPPCHECK_HEADER = _header.format('CPPCHECK')
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

SOFTWIPE_BUILD_DIR_NAME = _softwipe + 'build'
SOFTWIPE_COMPILED_EXE_NAME = _softwipe + 'compiled_exe.out'

RESULTS_FILENAME_COMPILER_MUST_BE_FIXED = _softwipe + 'compilation_warnings_must_be_fixed.txt'
RESULTS_FILENAME_COMPILER_SHOULD_BE_FIXED = _softwipe + 'compilation_warnings_should_be_fixed.txt'
RESULTS_FILENAME_COMPILER_COULD_BE_FIXED = _softwipe + 'compilation_warnings_could_be_fixed.txt'
RESULTS_FILENAME_SANITIZERS = _softwipe + 'sanitizer_output.txt'
RESULTS_FILENAME_ASSERTION_CHECK = _softwipe + 'assertion_check.txt'
RESULTS_FILENAME_CPPCHECK = _softwipe + 'cppcheck_results.txt'
RESULTS_FILENAME_CLANG_TIDY = _softwipe + 'clang_tidy_results.txt'
RESULTS_FILENAME_LIZARD = _softwipe + 'lizard_results.txt'
RESULTS_FILENAME_KWSTYLE = _softwipe + 'kwstyle_results.txt'

RATE_COUNT_TOTAL = '{} ({}/{})'

RESULT_WEIGHTED_COMPILER_WARNING_RATE = 'Weighted compiler warning rate: ' + RATE_COUNT_TOTAL
RESULT_ASAN_ERROR_RATE = 'AddressSanitizer error rate: ' + RATE_COUNT_TOTAL
RESULT_UBSAN_ERROR_RATE = 'UndefinedBehaviorSanitizer error rate: ' + RATE_COUNT_TOTAL
RESULT_ASSERTION_RATE = 'Assertion rate: ' + RATE_COUNT_TOTAL
RESULT_ASSERTION_RATE_DETAILED = 'Found {count} assertions in {loc} lines of pure' \
                              ' code (i.e. excluding blank lines and comment lines).' + '\n' \
                              'That\'s an assertion rate of {rate}, or {percentage}%.'
RESULT_WEIGHTED_CPPCHECK_WARNING_RATE = 'Total weighted Cppcheck warning rate: ' + RATE_COUNT_TOTAL
RESULT_WEIGHTED_CLANG_TIDY_WARNING_RATE = 'Weighted Clang-tidy warning rate: ' + RATE_COUNT_TOTAL
RESULT_KWSTYLE_WARNING_RATE = 'KWStyle warning rate: ' + RATE_COUNT_TOTAL


DETAILLED_RESULTS_WRITTEN_INTO = 'Detailled results have been written into {}'
LINES_OF_PURE_CODE_ARE = 'Lines of pure code (excluding blank and comment lines): {}'


FAILED_TO_FIND_TOOLS = 'Failed to find the following tools:'
MAKE_SURE_TOOLS_ARE_INSTALLED = 'Make sure all tools are installed on your system and accessible. Either put their ' \
                                'location into your PATH or provide a full path to each tool as its exe_name in ' \
                                'tools_info.py.'

USER_IS_ROOT_WARNING = 'You are running as root! This will cause my output files to be inaccessible without root ' \
                       'privileges (so I cannot overwrite them without root privileges anymore). Please only ' \
                       'continue as root if necessary.\n' \
                       'Do you want to continue as root? (Y/n)'


USER_DID_NOT_SPECIFY_EXECUTE_FILE_USING_AOUT_NOW = 'Warning! You did not specify an executefile. I\'m trying to run ' \
                                                   'your program using "a.out" or "' + SOFTWIPE_COMPILED_EXE_NAME + \
                                                   '" now. In most cases, this will not ' \
                                                   'work properly, and you should specify an executefile.\n' \
                                                   'For more information, please run: softwipe.py --executefilehelp'

EXECUTION_FILE_NOT_FOUND = 'I could not find the executable "{}".\n' \
                           'If you haven\'t specified an executefile, please do so. If you did specify an ' \
                           'executefile, please make sure it is correct.'

                                                                                #
EXECUTE_FILE_HELP = """        --- Execute file help ---

The execute file (provided via -e option) is a file that contains a command line
that executes your program. It should only contain one single line containing
exactly the command line you would use for executing it.
For example, if your program compiles the executable "foobar" and requires two
arguments "-x" and "-y", your file should contain a line like this:
  foobar -x baz -y qux
If your file contains more than one line, any line beyond the first will be
ignored.
If you omit the execute file, I will try calling "a.out" or
\"""" + SOFTWIPE_COMPILED_EXE_NAME + """\" (which will most likely not work :))
"""
                                                                                #
COMMAND_FILE_HELP = """        --- Command file help ---

The command file (provided via -f option) is a file that contains:
 -for make-based projects: commands that are used to build the program
 -for compiler-based projects: compiler options
Note that you can also specify a command file for CMake-based programs, if an
additional argument needs to be given to the "make" call for correctly
compiling your program.

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
that simply compiling the targets using clang/clang++ works.
"""
                                                                                #
