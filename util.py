"""
This module contains utility functions.
"""

import os
import strings


def write_into_file_string(file_name, content, append=False):
    """
    Writes 'content' string into a file specified by 'file_name'. The file will be created if it does not exist.
    :param file_name: path of the file to write into
    :param content: string to write into file
    :param append: bool telling to overwrite the file or append to file
    """
    write_mode = 'a+' if append else 'w+'
    with open(file_name, write_mode) as file:
        file.write(content)


def write_into_file_list(file_name, content, append=False):
    """
    Writes the elements of 'content' into a file specified by 'file_name'. The file will be created if it does not exist.
    :param file_name: path of the file to write into
    :param content: lst of elements to write into file. The elements will be used like strings.
    :param append: bool telling to overwrite the file or append to file
    """
    content_as_string = ''
    for line in content:
        content_as_string += line
        content_as_string += '\n'
    write_into_file_string(file_name, content_as_string, append)


def print_lines(lines):
    """
    Print all lines in the input to stdout.
    :param lines: A lst of lines to print.
    """
    for line in lines:
        print(line)


def get_excluded_paths(program_dir_abs, exclude):
    """
    Return the paths (files and dirs) that should be excluded from being analyzed by softwipe.
    :param program_dir_abs: The absolute path to the root directory of the program.
    :param exclude: A comma separated lst of files and directories to exclude, as given via command line (-x option).
    :return: A tupel containing all excluded paths.
    """
    excluded_paths = (os.path.join(program_dir_abs, 'build'), os.path.join(program_dir_abs, 'cmake-build-debug'),
                      os.path.join(program_dir_abs, 'compile'), os.path.join(program_dir_abs,
                                                                             strings.SOFTWIPE_BUILD_DIR_NAME))
    if exclude:
        for path in exclude.split(','):
            excluded_paths += (os.path.abspath(path),)

    return excluded_paths


def find_all_source_files(program_dir_abs, excluded_paths):
    """
    Find all source files in program_dir_abs. Traverses the directory recursively and returns all source files,
    i.e. all *.c or *.cpp or *.h or *.hpp files.
    :param program_dir_abs: The absolute path to the root directory of the program.
    :param excluded_paths: A tupel containing the paths to be excluded. The tupel should be obtained via the
    get_excluded_paths() function.
    :return: A lst containing absolute paths to all source files.
    """
    source_files = []
    source_file_endings = ('.c', '.cc', '.cpp', '.cxx', '.h', '.hpp')

    for dirpath, _, files in os.walk(program_dir_abs):
        if dirpath.startswith(excluded_paths):
            continue

        for file in files:
            file_abspath = os.path.join(dirpath, file)
            if file_abspath.startswith(excluded_paths):
                continue
            if file.endswith(source_file_endings):
                source_files.append(os.path.join(dirpath, file))

    return source_files


def line_is_empty(line):
    return line.strip() == ''


def line_is_comment(line, block_comment_has_started):
    """
    Checks whether a line is a comment line. Function is used to read a code file line by line counting the lines of code.
    :param line: string to check
    :param block_comment_has_started: was a block comment started before this line?
    :return: 1. true/false - whether line is a comment or not
             2. true - if a block comment has started (or is continued)
                false - if line not part of block comment (or block comment has ended)
    """
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
    :param source_files: The lst of files to count lines in.
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


def split_in_chunks(lst, size):
    """
    Splits a list into chunks of 'size'.
    :param lst: list to split into chunks
    :param size: chunk size
    :return: chunk generator
    """
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def find_file(path, file_name, directory=""):
    """
    Finds file 'file_name' in 'path' and its subdirectories and returns full path to that file.
    If 'directory' is specified, the function tries to find 'directory/file_name'
    and is only successful if 'file_name' is found in this exact constellation.
    :param path: path to start looking for the file in
    :param file_name: file to find
    :param directory: immediate upper directory of the file to find
    :return: full path to 'file_name' if successful
    """
    dirs = []
    for (_, folder, file) in os.walk(path):
        dirs.extend(folder)
        if directory == "":
            if file_name in file:
                return path + "/" + file_name
        else:
            if file_name in file and path.split("/")[-1] == directory:
                return path + "/" + file_name
        break
    for folder in dirs:
        file_path = find_file(path + "/" + folder, file_name, directory=directory)
        if file_path != "":
            return file_path

    return ""
