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
import execution_phase
import util
import automatic_tool_installation
import scoring


def parse_arguments():
    """
    Parse command line arguments.
    :return: The "args" Namespace that contains the command line arguments specified by the user.
    """
    # Preparser, used for the command file & execute file help. Without the preparser, one would get an error because
    # 'programdir' is a required argument but is missing. With the preparser, the help can be printed anyway.
    preparser = argparse.ArgumentParser(add_help=False)
    preparser.add_argument('--commandfilehelp', default=False, action='store_true')
    preparser.add_argument('--executefilehelp', default=False, action='store_true')
    preargs, unk = preparser.parse_known_args()

    # Both helps can be printed at once
    if preargs.executefilehelp:
        print(strings.EXECUTE_FILE_HELP)
    if preargs.commandfilehelp:
        print(strings.COMMAND_FILE_HELP)
    if preargs.executefilehelp or preargs.commandfilehelp:  # Exit if either one or both helps have been printed
        sys.exit(0)

    # Main parser
    parser = argparse.ArgumentParser(description='Check the software quality of a C/C++ program\n\n'
                                                 'Important arguments you probably want to use:\n'
                                                 '  -c/-C to tell me whether your program is C or C++\n'
                                                 '  -M/-m/-l to tell me how to build your program\n'
                                                 '  -e to specify a file that tells me how to execute your program\n'
                                                 'Example command line for a CMake-based C++ program:\n'
                                                 './softwipe.py -CM path/to/program -e path/to/executefile\n',
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('programdir', help="the root directory of your target program")

    c = parser.add_mutually_exclusive_group()
    c.add_argument('-c', '--cc', action='store_true', help='use C. This is the default option')
    c.add_argument('-C', '--cpp', action='store_true', help='use C++')

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('-M', '--cmake', action='store_true', help='compile the program using cmake. This is the default '
                                                                 'option')
    mode.add_argument('-m', '--make', action='store_true', help='compile the program using make. Note that this '
                                                                'option requires a "standard" style makefile that '
                                                                'uses common variables like ${CC}, ${CFLAGS}, '
                                                                '${LDFLAGS} etc. to work properly')
    mode.add_argument('-l', '--clang', nargs='+', metavar='target', help='compile the program using the clang/clang++ '
                                                                         'compiler. This option takes as arguments the'
                                                                         ' files to compile')

    parser.add_argument('-e', '--executefile', nargs=1, help='path to an "execute file" which contains a command line '
                                                             'that executes your program')
    parser.add_argument('--executefilehelp', action='store_true', help='print detailled information about how the '
                                                                       'execute file works and exit')

    parser.add_argument('-f', '--commandfile', nargs=1, help='path to a "command file" which can be used to provide '
                                                             'commands that should be executed for building a '
                                                             'make-based project or to provide compiler options for '
                                                             'building a simple compiler-based project')
    parser.add_argument('--commandfilehelp', action='store_true', help='print detailed information about how the '
                                                                       'command file works and exit')

    parser.add_argument('-x', '--exclude', nargs=1, help='a comma separated list of files and directories that should '
                                                         'be excluded from being analyzed by this program')

    parser.add_argument('-p', '--path', nargs=1, help='a comma separated list of paths that should be added to the '
                                                      'PATH environment variable. Use this if you have a dependency '
                                                      'installed but not accessible via your default PATH')

    parser.add_argument('--no-execution', action='store_true', help='Do not execute your program. This skips the '
                                                                    'clang sanitizer check')

    args = parser.parse_args()
    return args


def add_to_path_variable(paths):
    """
    Add paths to the system PATH environment variable.
    :param paths: A comma separated list of paths to add.
    """
    path_list = []
    for path in paths.split(','):
        path_list.append(path)

    for path in path_list:
        os.environ['PATH'] += os.pathsep + path


def adjust_path_variable(args):
    """
    Adjusts the PATH variable if necessary by adding user specified paths (if any were specified) and adding KWStyle
    to the PATH if it is contained in the softwipe directory (which it is if the user did the auto-installation of it).
    :param args: The "args" Namespace as returned from parse_arguments().
    """
    user_paths = args.path[0] if args.path else None
    if user_paths:
        add_to_path_variable(user_paths)

    kwstyle_dir = os.path.join(util.get_softwipe_directory(), 'KWStyle')
    if os.path.isdir(kwstyle_dir):
        add_to_path_variable(os.path.join(kwstyle_dir, strings.SOFTWIPE_BUILD_DIR_NAME))


def compile_program(args, lines_of_code, cpp):
    """
    Run the automatic compilation of the target project.
    :param args: The "args" Namespace as returned from parse_arguments().
    :param lines_of_code: The lines of pure code count.
    :param cpp: Whether C++ is used or not. True if C++, False if C.
    :return: The compiler score.
    """
    print(strings.RUN_COMPILER_HEADER)
    program_dir_abs = os.path.abspath(args.programdir)
    command_file = args.commandfile

    if args.make:
        if command_file:
            score = compile_phase.compile_program_make(program_dir_abs, lines_of_code,
                                                       make_command_file=command_file[0])
        else:
            score = compile_phase.compile_program_make(program_dir_abs, lines_of_code)
    elif args.clang:
        if command_file:
            score = compile_phase.compile_program_clang(program_dir_abs, args.clang, lines_of_code, cpp,
                                                        clang_command_file=command_file[0])
        else:
            score = compile_phase.compile_program_clang(program_dir_abs, args.clang, lines_of_code, cpp)
    else:
        if command_file:
            score = compile_phase.compile_program_cmake(program_dir_abs, lines_of_code,
                                                        make_command_file=command_file[0])
        else:
            score = compile_phase.compile_program_cmake(program_dir_abs, lines_of_code)

    return score


def execute_program(program_dir_abs, executefile, cmake, lines_of_code):
    """
    Execute the program and parse the output of the clang sanitizers.
    :param program_dir_abs: The absolute path to the root directory of the target program.
    :param executefile: The executefile that contains a command line for executing the program.
    :param cmake: Whether CMake has been used for compilation or not.
    :param lines_of_code: The lines of pure code count.
    :return The weighted sanitizer error count.
    """
    weighted_error_count = execution_phase.run_execution(program_dir_abs, executefile, cmake, lines_of_code)
    return weighted_error_count


def compile_and_execute_program_with_sanitizers(args, lines_of_code, program_dir_abs, cpp, no_exec=False):
    """
    Automatically compile and execute the program
    :param args: The "args" Namespace as returned from parse_arguments().
    :param lines_of_code: The lines of pure code count.
    :param program_dir_abs: The absolute path to the root directory of the target program.
    :param cpp: Whether C++ is used or not. True if C++, False if C.
    :param no_exec: If True, skip execution of the program.
    :return The compiler + sanitizer score.
    """
    weighted_sum_of_compiler_warnings = compile_program(args, lines_of_code, cpp)
    if not no_exec:
        execute_file = args.executefile[0] if args.executefile else None
        weighted_sum_of_sanitizer_warnings = execute_program(program_dir_abs, execute_file, args.cmake, lines_of_code)
    else:
        weighted_sum_of_sanitizer_warnings = 0
        print('Warning: Program execution was skipped. Thus, clang sanitizer results are not available.')

    weighted_warning_rate = (weighted_sum_of_compiler_warnings + weighted_sum_of_sanitizer_warnings) / lines_of_code
    score = scoring.calculate_compiler_and_sanitizer_score(weighted_warning_rate)
    scoring.print_score(score, 'Compiler + Sanitizer')

    return score


def static_analysis(source_files, lines_of_code, cpp):
    """
    Run all the static analysis.
    :param source_files: The list of source files to analyze.
    :param lines_of_code: The lines of pure code count for the source_files.
    :param cpp: Whether C++ is used or not. True if C++, False if C.
    :return: All the static analysis scores: assertion_score, cppcheck_score, clang_tidy_score,
    cyclomatic_complexity_score, warning_score, unique_score, kwstyle_score.
    """
    assertion_score, cppcheck_score, clang_tidy_score, cyclomatic_complexity_score, warning_score, unique_score, \
    kwstyle_score = static_analysis_phase.run_static_analysis(source_files, lines_of_code, cpp)
    return assertion_score, cppcheck_score, clang_tidy_score, cyclomatic_complexity_score, warning_score, \
           unique_score, kwstyle_score


def main():
    args = parse_arguments()

    adjust_path_variable(args)

    automatic_tool_installation.check_if_all_required_tools_are_installed()

    cpp = True if args.cpp else False
    program_dir_abs = os.path.abspath(args.programdir)
    exclude = args.exclude[0] if args.exclude else None

    source_files = util.find_all_source_files(program_dir_abs, exclude)
    lines_of_code = util.count_lines_of_code(source_files)

    compiler_and_sanitizer_score = compile_and_execute_program_with_sanitizers(args, lines_of_code, program_dir_abs,
                                                                               cpp, args.no_execution)
    assertion_score, cppcheck_score, clang_tidy_score, cyclomatic_complexity_score, warning_score, \
    unique_score, kwstyle_score = static_analysis(source_files, lines_of_code, cpp)

    all_scores = [compiler_and_sanitizer_score, assertion_score, cppcheck_score, clang_tidy_score,
                  cyclomatic_complexity_score, warning_score, unique_score, kwstyle_score]
    overall_score = scoring.average_score(all_scores)
    scoring.print_score(overall_score, 'Overall program')


if __name__ == "__main__":
    main()
