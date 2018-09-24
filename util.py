"""
This module contains utility functions.
"""


import os
import sys
import inspect
import shutil
import platform
import subprocess

import tools_info
import strings


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
                      os.path.join(program_dir_abs, 'compile'))
    if exclude:
        for x in exclude.split(','):
            excluded_paths += (x,)

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
    # TODO Do this while iterating through the files for assert? Would be way faster
    # OR do this at the very beginning of the program. Might be useful for the total score at the end
    lines_of_code = 0

    for file in source_files:
        lines_of_code += count_lines_of_code_in_one_file(file)

    print()
    print('LOC:', lines_of_code)
    print()
    return lines_of_code


def detect_user_os():
    """
    Detect the users OS.
    :return: The name of the OS.
    """
    detected_os = None
    system = platform.system()
    if system == 'Linux':
        distro = platform.linux_distribution()
        detected_os = distro[0]
    else:
        detected_os = system
    return detected_os


def get_package_install_command_for_os(user_os):
    command = None
    if user_os == strings.OS_MACOS:
        command = ['brew', 'install']
    elif user_os == strings.OS_DEBIAN or user_os == strings.OS_UBUNTU:
        command = ['apt-get', 'install']
    return command


def print_missing_tools(missing_tools):
    print('Failed to find the following tools:')
    for missing_tool in missing_tools:
        print('  ' + missing_tool.install_name, '(install via:', missing_tool.install_via.name.lower() + ')')

    print('Make sure all tools are installed on your system and accessible. Either put their location into your '
          'PATH or provide a full path to each tool as its exe_name in tools_info.py.')


def print_and_run_install_command(install_command):
    for c in install_command:
        print(c, end=' ')
    print()
    subprocess.run(install_command)
    print()


def handle_clang_tidy_installation(package_install_command):
    """
    Special treatment for clang-tidy. Homebrew includes clang-tidy in llvm, apt-get has a separate package for
    clang-tidy. Thus, when using apt-get, do the extra installation.
    """
    if package_install_command[0] == 'apt-get':
        clang_tidy_install_command = package_install_command[:]
        clang_tidy_install_command.append('clang-tidy')

        print_and_run_install_command(clang_tidy_install_command)


def auto_tool_install(missing_tools, package_install_command):
    pip_install_command = ['python', '-m', 'pip', 'install']
    for tool in missing_tools:
        install_command = []
        if tool.install_via == tools_info.Via.PACKAGE_MANAGER:
            install_command = package_install_command[:]
        elif tool.install_via == tools_info.Via.PIP:
            install_command = pip_install_command[:]
        install_command.append(tool.install_name)

        print_and_run_install_command(install_command)

        if tool.exe_name == 'clang-tidy':
            handle_clang_tidy_installation(package_install_command)


def auto_install_prompt(missing_tools, package_install_command):
    print('I can automatically install the missing tools for you! Shall I? (Y/n)')
    while True:
        user_in = input('>>> ')
        if user_in == 'Y':
            auto_tool_install(missing_tools, package_install_command)
            sys.exit(0)
        elif user_in == 'n':
            sys.exit(1)
        else:
            print('Please answer with "Y" (Yes) or "n" (no)!')


def check_if_all_required_tools_are_installed():
    """
    Check if clang etc. (all the tools used in the pipeline) are installed on the system and can be used. If
    something is missing, print a warning and exit.
    """
    tools = [tool for tool in inspect.getmembers(tools_info.TOOLS) if not tool[0].startswith('_')]
    missing_tools = []
    for tool in tools:
        which_result = shutil.which(tool[1].exe_name)
        if which_result is None:  # if the tool is not installed / not accessible
            missing_tools.append(tool[1])

    if missing_tools:
        print_missing_tools(missing_tools)

        user_os = detect_user_os()
        package_install_command = get_package_install_command_for_os(user_os)
        if package_install_command is None:
            sys.exit(1)

        auto_install_prompt(missing_tools, package_install_command)
