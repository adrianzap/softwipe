#!/usr/bin/env python3

import argparse
import os

import strings
import compile_phase
import static_analysis_phase


def parse_arguments():
    parser = argparse.ArgumentParser(description="Check the software quality of a C program")

    parser.add_argument('programdir', help="the root directory of your target program")

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('-M', '--cmake', action='store_true', help='compile the program using cmake. This is the default '
                                                                 'option')
    mode.add_argument('-m', '--make', action='store_true', help='compile the program using make')
    mode.add_argument('-l', '--clang', nargs='+', metavar='target', help='compile the program using the clang/clang++ '
                                                                         'compiler. This option takes as arguments the'
                                                                         ' files to compile')

    parser.add_argument('-f', '--makecommandsfile', nargs=1, help='a file that contains the commands used to build '
                                                                  'the program via make. These commands must be '
                                                                  'written into the file line by line. E.g., '
                                                                  'it might contain the lines "./configure", "make '
                                                                  'all" and "make install", or just one line "make '
                                                                  'client", etc. depending on how your program is '
                                                                  'compiled. This option is only relevant when using '
                                                                  'the -m/--make option. If omitted, it will be '
                                                                  'assumed that a simple call of "make" works for '
                                                                  'compilation.')

    c = parser.add_mutually_exclusive_group()
    c.add_argument('-c', '--cc', action='store_true', help='use C. This is the default option')
    c.add_argument('-C', '--cpp', action='store_true', help='use C++')

    parser.add_argument('-p', '--pmdbindir', nargs=1, help='the path to the bin directory of PMD, where the PMD '
                                                           'run.sh is located')

    args = parser.parse_args()
    return args


def compile_program(args, cpp):
    print(strings.RUN_COMPILER_HEADER)
    program_dir_abs = os.path.abspath(args.programdir)
    make_commands_file = args.makecommandsfile

    if args.make:
        if make_commands_file:
            compiler_warning_list = compile_phase.compile_program_make(program_dir_abs, make_commands_file)
        else:
            compiler_warning_list = compile_phase.compile_program_make(program_dir_abs)
    elif args.clang:
        compiler_warning_list = compile_phase.compile_program_clang(program_dir_abs, args.clang, cpp)
    else:
        compiler_warning_list = compile_phase.compile_program_cmake(program_dir_abs)

    return compiler_warning_list


def static_analysis(args, cpp):
    program_dir_abs = os.path.abspath(args.programdir)
    pmd_bin_dir = args.pmdbindir[0] if args.pmdbindir else os.getcwd()
    static_analysis_phase.run_static_analysis(program_dir_abs, pmd_bin_dir, cpp)


def main():
    args = parse_arguments()
    # TODO Check if clang etc (all the tools we use in the pipeline) are installed and working here
    cpp = True if args.cpp else False
    # compiler_warning_list = compile_program(args, cpp)
    # valgrind / gcc mem sanity check?
    static_analysis(args, cpp)


if __name__ == "__main__":
    main()
