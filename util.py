import os


def print_lines(lines):
    """
    Print all lines in the input to stdout.
    :param lines: A list of lines to print.
    """
    for line in lines:
        print(line)


def find_all_source_files(program_dir_abs):
    """
    Find all source files in program_dir_abs. Traverses the directory recursively and returns all source files,
    i.e. all *.c or *.cpp or *.h or *.hpp files.
    :param program_dir_abs: The absolute path to the root directory of the program.
    :return: A list containing absolute paths to all source files.
    """
    # TODO Should we really count header files, too? Or just pure source files?
    source_files = []

    c_source_file_ending = '.c'
    cpp_source_file_ending = '.cpp'
    c_header_file_ending = '.h'
    cpp_header_file_ending = '.hpp'

    for dirpath, dirs, files in os.walk(program_dir_abs):
        if dirpath.startswith((os.path.join(program_dir_abs, 'build'),
                               os.path.join(program_dir_abs, 'cmake-build-debug'))):
            continue

        for file in files:
            if file.endswith((c_source_file_ending, cpp_source_file_ending,
                              c_header_file_ending, cpp_header_file_ending)):
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
    if stripped_line.startswith('/*'):
        is_comment = True
        block_comment_has_started = True
    if block_comment_has_started:
        is_comment = True
        if stripped_line.startswith('*/'):
            block_comment_has_started = False

    return is_comment, block_comment_has_started


def count_lines_of_code_in_one_file(file):
    """
    Count the lines of code in one file. Ignores blank and comment lines.
    :param file: The path to the file to count lines in.
    :return: The count of total non-empty, non-comment code lines in the file.
    """
    lines_of_code = 0

    file_lines = open(file, 'r').readlines()
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
    # TODO Do this while iterating through the files for assert? Would be way faster
    # OR do this at the very beginning of the program. Might be useful for the total score at the end
    lines_of_code = 0

    for file in source_files:
        lines_of_code += count_lines_of_code_in_one_file(file)

    print()
    print('LOC:', lines_of_code)
    print()
    return lines_of_code
