#!/usr/bin/env python3
"""
The main module of softwipe. Here, command line arguments get parsed and the pipeline gets started.
"""

import argparse
import sys
import os

import strings
import compile_phase
import static_analysis_phase
import util


def print_command_file_help_and_exit():
    print(strings.COMMAND_FILE_HELP)
    sys.exit(0)


def parse_arguments():
    """
    Parse command line arguments.
    :return: The "args" Namespace that contains the command line arguments specified by the user.
    """
    # Preparser, used for the command file help. Without the preparser, one would get an error because 'programdir'
    # is a required argument but is missing. With the preparser, the help can be printed anyway.
    preparser = argparse.ArgumentParser(add_help=False)
    preparser.add_argument('--commandfilehelp', default=False, action='store_true')
    preargs, unk = preparser.parse_known_args()
    if preargs.commandfilehelp:
        print_command_file_help_and_exit()

    # Main parser
    parser = argparse.ArgumentParser(description="Check the software quality of a C/C++ program")

    parser.add_argument('programdir', help="the root directory of your target program")

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('-M', '--cmake', action='store_true', help='compile the program using cmake. This is the default '
                                                                 'option')
    mode.add_argument('-m', '--make', action='store_true', help='compile the program using make')
    mode.add_argument('-l', '--clang', nargs='+', metavar='target', help='compile the program using the clang/clang++ '
                                                                         'compiler. This option takes as arguments the'
                                                                         ' files to compile')

    c = parser.add_mutually_exclusive_group()
    c.add_argument('-c', '--cc', action='store_true', help='use C. This is the default option')
    c.add_argument('-C', '--cpp', action='store_true', help='use C++')

    parser.add_argument('-f', '--commandfile', nargs=1, help='path to a "command file" which can be used to provide '
                                                             'commands that should be executed for building a '
                                                             'make-based project or to provide compiler options for '
                                                             'building a simple compiler-based project')
    parser.add_argument('--commandfilehelp', action='store_true', help='print detailed information about how the '
                                                                       'command file works and exit')

    parser.add_argument('-x', '--exclude', nargs=1, help='a comma separated list of files and directories that should '
                                                         'be excluded from being analyzed by this program')

    args = parser.parse_args()
    return args


def compile_program(args, cpp):
    """
    Run the automatic compilation of the target project.
    :param args: The "args" Namespace as returned from parse_arguments().
    :param cpp: Whether C++ is used or not. True if C++, False if C.
    :return: The compiler warning list which contains the names of all warnings that have been generated while
    compiling.
    """
    print(strings.RUN_COMPILER_HEADER)
    program_dir_abs = os.path.abspath(args.programdir)
    command_file = args.commandfile

    if args.make:
        if command_file:
            compiler_warning_list = compile_phase.compile_program_make(program_dir_abs, cpp,
                                                                       make_command_file=command_file[0])
        else:
            compiler_warning_list = compile_phase.compile_program_make(program_dir_abs, cpp)
    elif args.clang:
        if command_file:
            compiler_warning_list = compile_phase.compile_program_clang(program_dir_abs, args.clang, cpp,
                                                                        clang_command_file=command_file[0])
        else:
            compiler_warning_list = compile_phase.compile_program_clang(program_dir_abs, args.clang, cpp)
    else:
        compiler_warning_list = compile_phase.compile_program_cmake(program_dir_abs, cpp)

    return compiler_warning_list


def static_analysis(args, cpp):
    """
    Run all the static analysis.
    :param args: The "args" Namespace as returned from parse_arguments().
    :param cpp: Whether C++ is used or not. True if C++, False if C.
    """
    program_dir_abs = os.path.abspath(args.programdir)
    exclude = args.exclude
    static_analysis_phase.run_static_analysis(program_dir_abs, cpp, exclude)


def main():
    args = parse_arguments()
    util.check_if_all_required_tools_are_installed()
    cpp = True if args.cpp else False
    compiler_warning_list = compile_program(args, cpp)
    # valgrind / gcc mem sanity check?
    static_analysis(args, cpp)


if __name__ == "__main__":
    main()
