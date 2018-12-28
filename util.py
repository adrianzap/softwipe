"""
This module contains utility functions.
"""


import os
import re

import strings


def write_into_file_string(file_name, content):
    file = open(file_name, 'w')
    file.write(content)
    file.close()
    print(strings.DETAILLED_RESULTS_WRITTEN_INTO.format(file_name))
    print()


def write_into_file_list(file_name, content):
    content_as_string = ''
    for line in content:
        content_as_string += line
        content_as_string += '\n'
    write_into_file_string(file_name, content_as_string)


def print_lines(lines):
    """
    Print all lines in the input to stdout.
    :param lines: A list of lines to print.
    """
    for line in lines:
        print(line)


def find_all_source_files(program_dir_abs, exclude):
    """
    Find all source files in program_dir_abs. Traverses the directory recursively and returns all source files,
    i.e. all *.c or *.cpp or *.h or *.hpp files.
    :param program_dir_abs: The absolute path to the root directory of the program.
    :param exclude: A comma separated list of files and directories to exclude from being found.
    :return: A list containing absolute paths to all source files.
    """
    source_files = []

    source_file_endings = ('.c', '.cc', '.cpp', '.cxx', '.h', '.hpp')

    excluded_paths = (os.path.join(program_dir_abs, 'build'), os.path.join(program_dir_abs, 'cmake-build-debug'),
                      os.path.join(program_dir_abs, 'compile'), os.path.join(program_dir_abs,
                                                                             strings.SOFTWIPE_BUILD_DIR_NAME))
    if exclude:
        for x in exclude.split(','):
            excluded_paths += (os.path.abspath(x),)

    for dirpath, dirs, files in os.walk(program_dir_abs):
        if dirpath.startswith(excluded_paths):
            continue

        for file in files:
            if file.endswith(source_file_endings):
                source_files.append(os.path.join(dirpath, file))

    return source_files


def line_is_empty(line):
    return line.strip() == ''


def line_is_comment(line, block_comment_has_started):
    is_comment = False

    # One-line comments ("// comment" or "/* comment */")
    stripped_line = line.strip()
    if stripped_line.startswith('//') or (stripped_line.startswith('/*') and stripped_line.endswith('*/')):
        is_comment = True

    # Block (or multi-line) comments ("/* \n comment \n comment \n */")
    elif stripped_line.startswith('/*'):
        block_comment_has_started = True

    if block_comment_has_started:
        is_comment = True
        if stripped_line.endswith('*/'):
            block_comment_has_started = False

    return is_comment, block_comment_has_started


def count_lines_of_code_in_one_file(file):
    """
    Count the lines of code in one file. Ignores blank and comment lines.
    :param file: The path to the file to count lines in.
    :return: The count of total non-empty, non-comment code lines in the file.
    """
    lines_of_code = 0

    file_lines = open(file, 'r', encoding='latin-1').readlines()
    block_comment_has_started = False
    for line in file_lines:
        is_comment, block_comment_has_started = line_is_comment(line, block_comment_has_started)
        if line_is_empty(line) or is_comment:
            continue
        lines_of_code += 1

    return lines_of_code


def count_lines_of_code(source_files):
    """
    Count the lines of code in source files. Ignores blank and comment lines.
    :param source_files: The list of files to count lines in.
    :return: The count of total non-empty, non-comment code lines in the files.
    """
    lines_of_code = 0

    for file in source_files:
        lines_of_code += count_lines_of_code_in_one_file(file)

    print(strings.LINES_OF_PURE_CODE_ARE.format(lines_of_code))
    print()

    return lines_of_code


def get_softwipe_directory():
    """
    Get the directory where softwipe is located.
    :return: The softwipe directory.
    """
    return os.path.dirname(os.path.realpath(__file__))


def clang_tidy_output_line_is_header(line):
    return line.strip().endswith('generated.')


def clang_tidy_output_line_is_trailer(line):
    return line.startswith('Suppressed')
