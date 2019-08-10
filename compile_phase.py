"""
This module contains all functions related to the automatic compilation phase.
"""


import subprocess
import os
import shutil
import re
import sys

import strings
from tools_info import TOOLS
import util
import classifications


def create_build_directory(program_dir_abs, build_dir_name=strings.SOFTWIPE_BUILD_DIR_NAME):
    build_path = os.path.join(program_dir_abs, build_dir_name)
    os.makedirs(build_path, exist_ok=True)
    return build_path


def clear_directory(directory):
    for path in (os.path.join(directory, file) for file in os.listdir(directory)):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)


def build_cmake_call(program_dir_abs, compiler_flags):
    """
    Build the CMake call.
    :param program_dir_abs: The absolute path to the root directory of the target program.
    :param compiler_flags: The flags to be used for compilation. Typically, these should be strings.COMPILE_FLAGS or,
    if no_execution, strings.COMPILER_WARNING_FLAGS.
    :return: The full CMake call as a list.
    """
    # The cmake call activates the compiler warnings we want and the flags that activate the clang sanitizers twice to
    # ensure that they really get activated: via environment variable, and via a new build type. Both activation
    # methods are safe in that they do not affect the users code or the compilation process in a bad way.
    cmake_call = [TOOLS.CMAKE.exe_name, '-E', 'env', 'CXXFLAGS=' + compiler_flags,
                  'CFLAGS=' + compiler_flags, 'LDFLAGS=' + compiler_flags,  # set environment variables to activate
                  # the warnings
                  TOOLS.CMAKE.exe_name, '-DCMAKE_CXX_COMPILER=' + TOOLS.CLANGPP.exe_name, '-DCMAKE_CC_COMPILER=' +
                  TOOLS.CLANG.exe_name, '-DCMAKE_C_COMPILER=' + TOOLS.CLANG.exe_name,  # Ensure that clang is used
                  '-DCMAKE_EXPORT_COMPILE_COMMANDS=1',  # Ensure that the compilation database JSON that is required
                  # for most clang tools is exported
                  program_dir_abs
                  ]
    # NOTE verbosity may be enabled via '-DCMAKE_VERBOSE_MAKEFILE:BOOL=ON' and run_make(make_verbose=True) (this shows
    # all commands that are called by cmake & make, respectively.
    return cmake_call


def run_cmake(program_dir_abs, build_path, compiler_flags):
    """
    Run the cmake command for the program in program_dir_abs as if pwd would be build_path.
    :param program_dir_abs: The absolute path to the root directory of the target program.
    :param build_path: The build path in which CMake should build everything.
    :param compiler_flags: The flags to be used for compilation. Typically, these should be strings.COMPILE_FLAGS or,
    if no_execution, strings.COMPILER_WARNING_FLAGS.
    """
    cmake_call = build_cmake_call(program_dir_abs, compiler_flags)
    try:
        output = subprocess.check_output(cmake_call, cwd=build_path, universal_newlines=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(strings.COMPILATION_CRASHED.format(e.returncode, e.output))
        sys.exit(e.returncode)


def line_is_warning_line(line):
    regex = r'.+\.(c|cc|cpp|cxx|h|hpp|cu|cuh):[0-9]+:[0-9]+:\ warning:.+\[.+\]'  # Matches e.g. 'foo.cpp:x:y: ...' or
    # '/path/to/bar.c:x:y: ...' because warning lines start with the file (foo or bar here), then the line (x) and
    # column (y) which caused the warning
    return re.match(regex, line)


def get_warning_lines_from_make_output(output):
    """
    Extract from the output of the make command just the lines that show the warnings. This includes lines that show
    the code, for example:
    badcode.cpp:42:15: warning: implicit conversion loses floating-point precision: 'double' to 'float' [-Wconversion]
    float b = a;
          ~   ^
    All of these lines will be put into the list that is returned.
    :param output: The output of make.
    :return: A list of all warning lines, i.e. lines that are part of the description of warnings in the make output.
    """
    output_lines = output.split('\n')
    warning_lines = []
    do_add_warnings = False
    for line in output_lines:
        # At the first warning, start adding the lines to warning_lines
        if line_is_warning_line(line):
            do_add_warnings = True

        # After all warnings have been printed, it will print "n warning(s) generated.". So stop adding lines to
        # warning_lines at this point
        if line.endswith(("warnings generated.", "warning generated.")):
            # TODO Does it always end like this?! How about "omitted n warnings"?
            do_add_warnings = False

        if do_add_warnings:
            warning_lines.append(line)

    return warning_lines


def print_compilation_results(warning_lines, lines_of_code, append_to_file):
    must_be_fixed_warning_lines = []
    should_be_fixed_warning_lines = []
    could_be_fixed_warning_lines = []

    weighted_sum_of_warnings = 0
    number_of_warnings_in_level = [0] * 3

    cur_warning_level = 0
    for line in warning_lines:
        if line_is_warning_line(line):
            # Get the classified warning level
            split_line = line.split()
            warning_name = split_line[-1][1:-1]

            cur_warning_level = 1  # Default to 1
            if warning_name in classifications.COMPILER_WARNINGS:
                cur_warning_level = classifications.COMPILER_WARNINGS[warning_name]

            weighted_sum_of_warnings += cur_warning_level
            number_of_warnings_in_level[cur_warning_level - 1] += 1

        if cur_warning_level == 1:
            could_be_fixed_warning_lines.append(line)
        elif cur_warning_level == 2:
            should_be_fixed_warning_lines.append(line)
        elif cur_warning_level == 3:
            must_be_fixed_warning_lines.append(line)

    weighted_warning_rate = weighted_sum_of_warnings / lines_of_code

    print(strings.RESULT_WEIGHTED_COMPILER_WARNING_RATE.format(weighted_warning_rate, weighted_sum_of_warnings,
                                                               lines_of_code))
    
    print("  Number of level 3 warnings (must be fixed):",
          str(number_of_warnings_in_level[2]) + '/' + str(lines_of_code))
    print("  Number of level 2 warnings (should be fixed):",
          str(number_of_warnings_in_level[1]) + '/' + str(lines_of_code))
    print("  Number of level 1 warnings (could be fixed):",
          str(number_of_warnings_in_level[0]) + '/' + str(lines_of_code))
    
    util.write_into_file_list(strings.RESULTS_FILENAME_COMPILER_MUST_BE_FIXED, must_be_fixed_warning_lines,
                              append_to_file, True)
    util.write_into_file_list(strings.RESULTS_FILENAME_COMPILER_SHOULD_BE_FIXED, should_be_fixed_warning_lines,
                              append_to_file, True)
    util.write_into_file_list(strings.RESULTS_FILENAME_COMPILER_COULD_BE_FIXED, could_be_fixed_warning_lines,
                              append_to_file, False)

    return weighted_sum_of_warnings


def remove_excluded_paths_from_warning_lines(warning_lines, excluded_paths):
    new_warning_lines = []
    do_add_lines = True
    lines_to_remove = set()  # will contain indices of lines that should be removed later
    for i, line in enumerate(warning_lines):
        if line_is_warning_line(line):
            # if this is a warning for an excluded path
            if any(excluded_path in line for excluded_path in excluded_paths):
                do_add_lines = False
                # If lines before this one were "In file included from..." lines, remove those retrospectively
                # (that is, add them to lines_to_remove)
                cur_index = len(new_warning_lines) - 1  # index of last element in new_warning_lines
                while cur_index >= 0 and new_warning_lines[cur_index].startswith("In file included from"):
                    lines_to_remove.add(cur_index)
                    cur_index -= 1
            else:
                do_add_lines = True
        elif line.startswith("In file included from"):
            do_add_lines = True

        if do_add_lines:
            new_warning_lines.append(line)

    # Now, remove "In file included from..." lines that prepended excluded warning lines retrospectively
    lines_to_remove_list = sorted(lines_to_remove, reverse=True)  # Must iterate from highest to lowest index for
    # correct deletions, thus sort in reverse
    for i in lines_to_remove_list:
        del new_warning_lines[i]

    return new_warning_lines


def run_compiledb(build_path, make_command):
    """
    Run compiledb (Compilation Database Generator) which creates the JSON compilation database (that is required for
    most clang tools) for make-based projects.
    :param build_path: The build path, where the Makefile is located.
    :param make_command: The make command that must be executed to build the program. Must be given as a list,
    e.g. ['make', 'mybuildtarget']. Compiledb uses the command to build the compilation database.
    """
    compiledb_call = [TOOLS.COMPILEDB.exe_name, '--no-build']
    compiledb_call.extend(make_command)
    subprocess.check_output(compiledb_call, cwd=build_path)


def running_make_clean(make_flags):
    return make_flags.strip().startswith('clean')


def run_make(build_path, lines_of_code, excluded_paths, dont_check_for_warnings=False, make_flags='',
             make_verbose=False, append_to_file=False):
    """
    Run the make command and print the warnings that it outputs while compiling.
    :param build_path: The build path, where the Makefile is located.
    :param lines_of_code: The lines of pure code count.
    :param excluded_paths: A tupel containing the paths to be excluded.
    :param dont_check_for_warnings: Do not check for warnings. Useful for automatically building a dependency,
    in which case you don't want warnings to be extracted from the compilation.
    :param make_flags: A string containing arguments passed to the make command. E.g., if make_flags='-foo BAR',
    then this method will call "make -foo BAR"
    :param make_verbose: Whether the make command output should be verbose or not.
    :param append_to_file: If True, append to the softwipe_compilation_results.txt file rather than writing it.
    Useful when running multiple make commands for the compilation to not overwrite previous results.
    :return: The weighted sum of compiler warnings, or None if not checking for warnings.
    """
    if make_flags is None:
        make_flags = []
    make_call = TOOLS.MAKE.exe_name + ' ' + make_flags
    if make_verbose:
        make_call += ' VERBOSE=1'

    # We must use shell=True here, else setting CFLAGS etc. won't work properly.
    try:
        output = subprocess.check_output(make_call, cwd=build_path, universal_newlines=True, stderr=subprocess.STDOUT,
                                         shell=True)
    except subprocess.CalledProcessError as e:
        if not running_make_clean(make_flags):
            print(strings.COMPILATION_CRASHED.format(e.returncode, e.output))
            sys.exit(e.returncode)

    if not (dont_check_for_warnings or running_make_clean(make_flags)):  # Don't look for warnings when running
        # "make clean" :)
        warning_lines = get_warning_lines_from_make_output(output)

        warning_lines = remove_excluded_paths_from_warning_lines(warning_lines, excluded_paths)

        weighted_sum_of_warnings = print_compilation_results(warning_lines, lines_of_code, append_to_file)
    else:
        weighted_sum_of_warnings = None

    return weighted_sum_of_warnings


def parse_make_command_file_and_run_all_commands_in_it(make_command_file, program_dir_abs, working_directory,
                                                       lines_of_code, compiler_flags, excluded_paths):
    commands = open(make_command_file, 'r').readlines()
    have_already_written_into_file = False
    weighted_sum_of_warnings = 0
    for command in commands:
        command = command.rstrip()  # Remove trailing newline from the command to prevent issues with the make_flags
        if command.startswith('make'):
            make_flags = command[4:]

            make_flags += ' ' + strings.create_make_flags(compiler_flags=compiler_flags)

            append_to_file = True if have_already_written_into_file else False
            r = run_make(working_directory, lines_of_code, excluded_paths, make_flags=make_flags,
                         append_to_file=append_to_file)
            if r:
                weighted_sum_of_warnings += r
            have_already_written_into_file = True

            run_compiledb(working_directory, command.split())
        else:
            split_command = command.split()
            subprocess.run(split_command, cwd=working_directory, stdout=subprocess.DEVNULL)

            if command.startswith('cd'):  # Change working directory if cd is used
                cd_target = ' '.join(split_command[1:])  # Use join to handle spaces
                if cd_target.startswith('/'):  # cd to an absolute path
                    working_directory = cd_target
                else:  # cd to a relative path
                    working_directory = os.path.join(program_dir_abs, cd_target)

    return weighted_sum_of_warnings


def compile_program_make(program_dir_abs, lines_of_code, compiler_flags, excluded_paths, make_command_file=None):
    """
    Compile the program using Make (i.e. plain old Makefiles).
    :param program_dir_abs: The absolute path to the root directory of the target program, where the Makefile is
    located.
    :param lines_of_code: The lines of pure code count.
    :param compiler_flags: The flags to be used for compilation. Typically, these should be strings.COMPILE_FLAGS or,
    if no_execution, strings.COMPILER_WARNING_FLAGS.
    :param excluded_paths: A tupel containing the paths to be excluded.
    :param make_command_file: The path to a file containing the commands used to successfully compile the program
    using make.
    :return The weighted sum of compiler warnings.
    """
    try:
        run_make(program_dir_abs, lines_of_code, excluded_paths, make_flags='clean')
    except subprocess.CalledProcessError:
        print(strings.NO_MAKE_CLEAN_TARGET_FOUND)

    if make_command_file:
        working_directory = program_dir_abs  # This will be used as the build path, which might get changed
        weighted_sum_of_warnings = parse_make_command_file_and_run_all_commands_in_it(make_command_file,
                                                                                      program_dir_abs,
                                                                                      working_directory,
                                                                                      lines_of_code, compiler_flags,
                                                                                      excluded_paths)
    else:
        weighted_sum_of_warnings = run_make(program_dir_abs, lines_of_code, excluded_paths,
                                            make_flags=strings.create_make_flags(compiler_flags=compiler_flags))
        run_compiledb(program_dir_abs, [TOOLS.MAKE.exe_name])

    return weighted_sum_of_warnings


def compile_program_cmake(program_dir_abs, lines_of_code, compiler_flags, excluded_paths, dont_check_for_warnings=False,
                          make_command_file=None):
    """
    Compile the program using CMake.
    :param program_dir_abs: The absolute path to the root directory of the target program, where the CMakeLists.txt
    is located.
    :param lines_of_code: The lines of pure code count.
    :param compiler_flags: The flags to be used for compilation. Typically, these should be strings.COMPILE_FLAGS or,
    if no_execution, strings.COMPILER_WARNING_FLAGS.
    :param excluded_paths: A tupel containing the paths to be excluded.
    :param dont_check_for_warnings: Do not check for warnings. Useful for automatically building a dependency,
    in which case you don't want warnings to be extracted from the compilation.
    :param make_command_file: The path to a file containing the commands used to successfully compile the program
    using make.
    :return The weighted sum of compiler warnings.
    """
    build_path = create_build_directory(program_dir_abs)
    clear_directory(build_path)  # If the path already existed, it should be cleared to ensure a fresh compilation
    run_cmake(program_dir_abs, build_path, compiler_flags)
    if make_command_file:
        weighted_sum_of_warnings = parse_make_command_file_and_run_all_commands_in_it(make_command_file,
                                                                                      program_dir_abs, build_path,
                                                                                      lines_of_code, compiler_flags,
                                                                                      excluded_paths)
    else:
        weighted_sum_of_warnings = run_make(build_path, lines_of_code, excluded_paths, dont_check_for_warnings,
                                            make_flags=strings.create_make_flags(compiler_flags=compiler_flags))

    return weighted_sum_of_warnings


def compile_program_clang(program_dir_abs, targets, lines_of_code, compiler_flags, excluded_paths, cpp=False):
    """
    Compile the program using clang.
    :param program_dir_abs: The absolute path to the root directory of the target program.
    :param targets: The source files that should be compiled.
    :param lines_of_code: The lines of pure code count.
    :param compiler_flags: The flags to be used for compilation. Typically, these should be strings.COMPILE_FLAGS or,
    if no_execution, strings.COMPILER_WARNING_FLAGS.
    :param excluded_paths: A tupel containing the paths to be excluded.
    :param cpp: Whether we're doing C++ or not. True if C++ (so clang++ will be used), False if C (so clang will be
    used).
    :return The weighted sum of compiler warnings.
    """
    compiler = TOOLS.CLANGPP.exe_name if cpp else TOOLS.CLANG.exe_name
    clang_call = [compiler, '-o', strings.SOFTWIPE_COMPILED_EXE_NAME]

    compile_flags = compiler_flags.split()
    clang_call.extend(compile_flags)

    for target in targets:
        target_abs = os.path.abspath(target)
        clang_call.append(target_abs)

    try:
        output = subprocess.check_output(clang_call, cwd=program_dir_abs, universal_newlines=True,
                                         stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(strings.COMPILATION_CRASHED.format(e.returncode, e.output))
        sys.exit(e.returncode)
    warning_lines = output.split('\n')

    warning_lines = remove_excluded_paths_from_warning_lines(warning_lines, excluded_paths)

    weighted_sum_of_warnings = print_compilation_results(warning_lines, lines_of_code, False)
    return weighted_sum_of_warnings
