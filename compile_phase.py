"""
This module contains all functions related to the automatic compilation phase.
"""


import subprocess
import os
import re

import strings
import util


def create_build_directory(program_dir_abs, build_dir_name='build'):
    build_path = os.path.join(program_dir_abs, build_dir_name)
    os.makedirs(build_path, exist_ok=True)
    return build_path


def add_compiler_warning_flags_to_cmakelists_file(cmakelists_file):
    cmakelists_file = open(cmakelists_file, 'a')
    cmakelists_file.write('\n')
    cmakelists_file.write(strings.SET_CMAKE_CXX_FLAGS_COMPILER_WARNINGS + '\n')
    cmakelists_file.write(strings.SET_CMAKE_C_FLAGS_COMPILER_WARNINGS + '\n')
    cmakelists_file.close()


def remove_compiler_warning_flags_from_cmakelists_file(cmakelists_file):
    # Read the whole file
    cmakelists_file_read = open(cmakelists_file, 'r')
    lines = cmakelists_file_read.readlines()
    cmakelists_file_read.close()

    lines = lines[:-2]  # Remove the last two lines which is where the flags have been added
    lines[-1] = lines[-1][:-1]  # Remove the newline (\n) which has been added

    # Overwrite the file without the last line
    cmakelists_file_write = open(cmakelists_file, 'w')
    cmakelists_file_write.writelines(lines)
    cmakelists_file_write.close()


def run_cmake(program_dir_abs, build_path):
    """
    Run the cmake command for the program in program_dir_abs as if pwd would be build_path.
    :param program_dir_abs: The absolute path to the root directory of the target program.
    :param build_path: The build path in which CMake should build everything.
    """
    cmake_call = [strings.TOOLS.CMAKE, '-DCMAKE_CXX_COMPILER=' + strings.TOOLS.CLANGPP, '-DCMAKE_CC_COMPILER=' +
                  strings.TOOLS.CLANG, '-DCMAKE_EXPORT_COMPILE_COMMANDS=1', program_dir_abs]
    # '-DCMAKE_EXPORT_COMPILE_COMMANDS=1' exports the compilation database JSON that is required for most clang tools
    # NOTE verbosity may be enabled via '-DCMAKE_VERBOSE_MAKEFILE:BOOL=ON' and run_make(verbose=True) (this shows all
    # commands that are called by cmake & make
    output = subprocess.check_output(cmake_call, cwd=build_path, universal_newlines=True, stderr=subprocess.STDOUT)


def line_is_warning_line(line, program_dir_abs):
    regex = r'.+\.(c|cpp|h|hpp):[0-9]+:[0-9]+:.*'  # Matches e.g. 'foo.cpp:x:y: ...' or '/path/to/bar.c:x:y: ...'
    # because warning lines start with the file (foo or bar here), then the line (x) and column (y) which caused the
    # warning
    return line.startswith(program_dir_abs) or line.startswith(os.path.basename(program_dir_abs)) or re.match(regex,
                                                                                                              line)


def get_warning_lines_from_make_output(output, program_dir_abs):
    """
    Extract from the output of the make command just the lines that show the warnings. This includes lines that show
    the code, for example:
    badcode.cpp:42:15: warning: implicit conversion loses floating-point precision: 'double' to 'float' [-Wconversion]
    float b = a;
          ~   ^
    All of these lines will be put into the list that is returned.
    :param output: The output of make.
    :param program_dir_abs: The absolute path to the root directory of the target program.
    :return: A list of all warning lines, i.e. lines that are part of the description of warnings in the make output.
    """
    output_lines = output.split('\n')
    warning_lines = []
    do_add_warnings = False
    for line in output_lines:
        # At the first warning, start adding the lines to warning_lines
        if line_is_warning_line(line, program_dir_abs):
            do_add_warnings = True

        # After all warnings have been printed, it will print "n warning(s) generated.". So stop adding lines to
        # warning_lines at this point
        if line.endswith(("warnings generated.", "warning generated.")):
            # TODO Does it always end like this?! How about "omitted n warnings"?
            do_add_warnings = False

        if do_add_warnings:
            warning_lines.append(line)

    return warning_lines


def get_warning_list_from_warning_lines(warning_lines, program_dir_abs):
    """
    Extract from the warning lines just the names of the warnings, i.e. '-Wfoo'.
    :param warning_lines: The warning lines.
    :param program_dir_abs: The absolute path to the root directory of the target program.
    :return: A list of all warnings as strings. If the same warning occurs n times in the warning lines, it will be n
    times in this list, too.
    """
    warning_list = []

    for line in warning_lines:
        if line_is_warning_line(line, program_dir_abs):
            split_line = line.split()
            # The last word in the output of a warning is [-Wfoo] where foo is the name of the warning
            # Must check for the [] so that we don't parse notes (which are contained in the warning_lines)
            if split_line[-1].startswith('[') and split_line[-1].endswith(']'):
                warning_list.append(split_line[-1][1:-1])

    return warning_list


def run_compiledb(build_path, make_command):
    """
    Run compiledb (Compilation Database Generator) which creates the JSON compilation database (that is required for
    most clang tools) for make-based projects.
    :param build_path: The build path, where the Makefile is located.
    :param make_command: The make command that must be executed to build the program. Must be given as a list,
    e.g. ['make', 'mybuildtarget']. Compiledb uses the command to build the compilation database.
    """
    compiledb_call = [strings.TOOLS.COMPILEDB, '--no-build']
    for command in make_command:
        compiledb_call.append(command)
    subprocess.call(compiledb_call, cwd=build_path)


def run_make(program_dir_abs, build_path, cpp, make_flags=None, make_verbose=False):
    """
    Run the make command and print the warnings that it outputs while compiling.
    :param program_dir_abs: The absolute path to the root directory of the target program.
    :param build_path: The build path, where the Makefile is located.
    :param cpp: Whether C++ is used or not.
    :param make_flags: A list of options passed to the make command. E.g., if make_call_options=['-foobar'],
    then this method will call "make -foobar"
    :param make_verbose: Whether the make command output should be verbose or not.
    :return: A list which contains the names of all warnings that have been generated when compiling.
    """
    if make_flags is None:
        make_flags = []
    make_call = [strings.TOOLS.MAKE]
    for flag in make_flags:
        make_call.append(flag)
    if make_verbose:
        make_call.append('VERBOSE=1')
    if cpp:
        make_call.append("CXXFLAGS='-Weverything'")
    else:
        make_call.append("CFLAGS='-Weverything'")

    output = subprocess.check_output(make_call, cwd=build_path, universal_newlines=True, stderr=subprocess.STDOUT)
    warning_lines = get_warning_lines_from_make_output(output, program_dir_abs)
    warning_list = get_warning_list_from_warning_lines(warning_lines, program_dir_abs)

    util.print_lines(warning_lines)

    return warning_list


def parse_make_command_file_and_run_all_commands_in_it(make_command_file, program_dir_abs, working_directory, cpp):
    warning_list = []

    commands = open(make_command_file, 'r').readlines()
    for command in commands:
        if command.startswith('make'):
            split_command = command.split()
            make_flags = split_command[1:]
            cur_warning_list = run_make(program_dir_abs, working_directory, cpp, make_flags=make_flags)
            warning_list.append(cur_warning_list)

            run_compiledb(working_directory, split_command)
        else:
            split_command = command.split()
            subprocess.run(split_command, cwd=working_directory)

            if command.startswith('cd'):  # Change working directory if cd is used
                cd_target = ' '.join(split_command[1:])  # Use join to handle spaces
                if cd_target.startswith('/'):  # cd to an absolute path
                    working_directory = cd_target
                else:  # cd to a relative path
                    working_directory = os.path.join(program_dir_abs, cd_target)

    return warning_list


def compile_program_make(program_dir_abs, cpp, make_command_file=None):
    """
    Compile the program using Make (i.e. plain old Makefiles).
    :param program_dir_abs: The absolute path to the root directory of the target program, where the Makefile is
    located.
    :param cpp: Whether C++ is used or not.
    :param make_command_file: The path to a file containing the commands used to successfully compile the program
    using make.
    :return: A list which contains the names of all warnings that have been generated when compiling.
    """
    if make_command_file:
        working_directory = program_dir_abs  # This will be used as the build path, which might get changed
        warning_list = parse_make_command_file_and_run_all_commands_in_it(make_command_file, program_dir_abs,
                                                                          working_directory, cpp)
    else:
        warning_list = run_make(program_dir_abs, program_dir_abs, cpp)
        run_compiledb(program_dir_abs, ['make'])

    return warning_list


def compile_program_cmake(program_dir_abs, cpp):
    """
    Compile the program using CMake.
    :param program_dir_abs: The absolute path to the root directory of the target program, where the CMakeLists.txt
    is located.
    :param cpp Whether C++ is used or not.
    :return: A list which contains the names of all warnings that have been generated when compiling.
    """
    build_path = create_build_directory(program_dir_abs)
    cmakelists_file = os.path.join(program_dir_abs, 'CMakeLists.txt')
    add_compiler_warning_flags_to_cmakelists_file(cmakelists_file)
    run_cmake(program_dir_abs, build_path)
    warning_list = run_make(program_dir_abs, build_path, cpp)
    remove_compiler_warning_flags_from_cmakelists_file(cmakelists_file)

    return warning_list


def compile_program_clang(program_dir_abs, targets, cpp=False, clang_command_file=None):
    """
    Compile the program using clang.
    :param program_dir_abs: The absolute path to the root directory of the target program.
    :param targets: The source files that should be compiled.
    :param cpp: Whether we're doing C++ or not. True if C++ (so clang++ will be used), False if C (so clang will be
    used).
    :param clang_command_file: The path to a file containing compiler options used for compilation.
    :return: A list which contains the names of all warnings that have been generated when compiling.
    """
    compiler = strings.TOOLS.CLANGPP if cpp else strings.TOOLS.CLANG
    clang_call = [compiler]

    if clang_command_file:
        options = open(clang_command_file, 'r').read().split()
        for option in options:
            clang_call.append(option)

    warning_flags = strings.COMPILER_WARNING_FLAGS.split()
    for wflag in warning_flags:
        clang_call.append(wflag)

    for target in targets:
        target_abs = os.path.abspath(target)
        clang_call.append(target_abs)

    output = subprocess.check_output(clang_call, cwd=program_dir_abs, universal_newlines=True, stderr=subprocess.STDOUT)
    warning_lines = output.split('\n')
    warning_list = get_warning_list_from_warning_lines(warning_lines, program_dir_abs)

    util.print_lines(warning_lines)

    return warning_list
