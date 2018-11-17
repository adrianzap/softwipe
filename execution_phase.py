"""
This module contains all functions related to executing the program and analyzing the output of the clang sanitizers.
"""

import subprocess
import os

import strings
import compile_phase
import util


def build_command(program_dir_abs, executefile, cmake):
    """
    Build the full command that executes the program without the sanitizers causing it to halt when they find an error.
    :param program_dir_abs: The absolute path to the root directory of the target program.
    :param executefile: The executefile.
    :param cmake: Whether CMake has been used for compilation or not.
    :return: The full command as a list.
    """
    # Read file and create command as a list
    if os.path.isfile(executefile):
        file = open(executefile, 'r')
        lines = file.readlines()
        file.close()

        command_line = lines[0]
        command = command_line.split()
    else:
        command = ['a.out']  # Default to a.out

    # Make the executable an absolute path
    executable_dir = program_dir_abs
    if cmake:
        os.path.join(executable_dir, strings.SOFTWIPE_BUILD_DIR_NAME)
    full_executable_path = os.path.join(executable_dir, command[0])
    command[0] = full_executable_path

    return command


def get_asan_error_count_from_sanitizer_output_lines(output_lines):
    count = 0
    for line in output_lines:
        if line.startswith('==') and 'ERROR' in line:
            count += 1
    return count


def get_ubsan_error_count_from_sanitizer_output_lines(output_lines, program_dir_abs):
    count = 0
    for line in output_lines:
        # UBSan uses the same warning format as compiler warnings
        if compile_phase.line_is_warning_line(line, program_dir_abs):
            count += 1
    return count


def get_sanitizer_error_count_from_sanitizer_output(output, program_dir_abs):
    output_lines = output.split('\n')
    asan_error_count = get_asan_error_count_from_sanitizer_output_lines(output_lines)
    ubsan_error_count = get_ubsan_error_count_from_sanitizer_output_lines(output_lines, program_dir_abs)
    return asan_error_count, ubsan_error_count


def run_execution(program_dir_abs, executefile, cmake, lines_of_code):
    """
    Execute the program and parse the output of the clang sanitizers.
    :param program_dir_abs: The absolute path to the root directory of the target program.
    :param executefile: The executefile that contains a command line for executing the program.
    :param cmake: Whether CMake has been used for compilation or not.
    :param lines_of_code: The lines of pure code count.
    """
    print(strings.RUN_EXECUTION_WITH_SANITIZERS_HEADER)

    command = build_command(program_dir_abs, executefile, cmake)
    os.environ['ASAN_OPTIONS'] = 'halt_on_error=0'

    # Execute and get stderr, which contains the output of the sanitizers
    output = subprocess.run(command, universal_newlines=True, stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE).stderr
    asan_error_count, ubsan_error_count = get_sanitizer_error_count_from_sanitizer_output(output, program_dir_abs)
    asan_error_rate = asan_error_count / lines_of_code
    ubsan_error_rate = ubsan_error_count / lines_of_code

    print(strings.RESULT_ASAN_ERROR_RATE.format(asan_error_rate, asan_error_count, lines_of_code))
    print(strings.RESULT_UBSAN_ERROR_RATE.format(ubsan_error_rate, ubsan_error_count, lines_of_code))
    util.write_into_file_string(strings.RESULTS_FILENAME_SANITIZERS, output)

    return asan_error_count, ubsan_error_count
