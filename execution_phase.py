"""
This module contains all functions related to executing the program and analyzing the output of the clang sanitizers.
"""

import os
import re
import subprocess

import strings
import util


class ExecutionFailedException(Exception):
    pass


def build_command(program_dir_abs, executefile, cmake):
    """
    Build the full command that executes the program without the sanitizers causing it to halt when they find an error.
    :param program_dir_abs: The absolute path to the root directory of the target program.
    :param executefile: The executefile.
    :param cmake: Whether CMake has been used for compilation or not.
    :return: The full command as a list.
    """
    # Read file and create command as a list
    if executefile is not None and os.path.isfile(executefile):
        file = open(executefile, 'r')
        lines = file.readlines()
        file.close()

        command_line = lines[0]
        command = command_line.split()
        command2 = None  # Not used here
    else:
        command = ['a.out']  # Default to a.out...
        command2 = [strings.SOFTWIPE_COMPILED_EXE_NAME]  # ... or softwipe_compiled_exe.out
        print(strings.USER_DID_NOT_SPECIFY_EXECUTE_FILE_USING_AOUT_NOW)

    # Make the executable an absolute path
    executable_dir = program_dir_abs
    if cmake:
        executable_dir = os.path.join(executable_dir, strings.SOFTWIPE_BUILD_DIR_NAME)
    full_executable_path = os.path.join(executable_dir, command[0])
    command[0] = full_executable_path

    if command2 is not None:
        full_executable_path2 = os.path.join(executable_dir, command2[0])
        command2[0] = full_executable_path2

    return command, command2


def get_asan_error_count_from_sanitizer_output_lines(output_lines):
    count = 0
    for line in output_lines:
        if line.startswith('==') and 'ERROR' in line:
            count += 1
    return count


def get_ubsan_error_count_from_sanitizer_output_lines(output_lines):
    count = 0
    for line in output_lines:
        # Match a regex similar to the one in line_is_warning_line
        regex = r'.+\.(c|cc|cpp|cxx|h|hpp):[0-9]+:[0-9]+:\ runtime\ error:.+'
        if re.match(regex, line):
            count += 1
    return count


def get_sanitizer_error_count_from_sanitizer_output(output):
    output_lines = output.split('\n')
    asan_error_count = get_asan_error_count_from_sanitizer_output_lines(output_lines)
    ubsan_error_count = get_ubsan_error_count_from_sanitizer_output_lines(output_lines)
    return asan_error_count, ubsan_error_count


def run_execution(program_dir_abs, executefile, cmake, lines_of_code):
    """
    Execute the program and parse the output of the clang sanitizers.
    :param program_dir_abs: The absolute path to the root directory of the target program.
    :param executefile: The executefile that contains a command line for executing the program.
    :param cmake: Whether CMake has been used for compilation or not.
    :param lines_of_code: The lines of pure code count.
    :return The weighted sum of sanitizer errors.
    """
    print(strings.RUN_EXECUTION_WITH_SANITIZERS_HEADER)

    command, command2 = build_command(program_dir_abs, executefile, cmake)
    os.environ['ASAN_OPTIONS'] = 'halt_on_error=0'

    # Execute and get stderr, which contains the output of the sanitizers
    try:
        output = subprocess.run(command, universal_newlines=True, stdout=subprocess.DEVNULL,
                                stderr=subprocess.PIPE).stderr
    except FileNotFoundError as e1:
        if command2 is not None:
            try:
                output = subprocess.run(command2, universal_newlines=True, stdout=subprocess.DEVNULL,
                                        stderr=subprocess.PIPE).stderr
            except FileNotFoundError as e2:
                print(e1)
                print(strings.EXECUTION_FILE_NOT_FOUND.format(command[0]))
                print(e2)
                print(strings.EXECUTION_FILE_NOT_FOUND.format(command2[0]))
                raise ExecutionFailedException
        else:
            print(e1)
            print(strings.EXECUTION_FILE_NOT_FOUND.format(command[0]))
            raise ExecutionFailedException

    asan_error_count, ubsan_error_count = get_sanitizer_error_count_from_sanitizer_output(output)
    asan_error_rate = asan_error_count / lines_of_code
    ubsan_error_rate = ubsan_error_count / lines_of_code

    print(strings.RESULT_ASAN_ERROR_RATE.format(asan_error_rate, asan_error_count, lines_of_code))
    print(strings.RESULT_UBSAN_ERROR_RATE.format(ubsan_error_rate, ubsan_error_count, lines_of_code))
    util.write_into_file_string(strings.RESULTS_FILENAME_SANITIZERS, output)

    weighted_error_count = 3 * asan_error_count + 3 * ubsan_error_count
    return weighted_error_count
