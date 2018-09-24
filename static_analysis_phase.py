"""
This module contains all functions related to the static analysis phase. That is, the static analysis pipeline is
completely written down here.
"""


import subprocess
import re

import strings
from tools_info import TOOLS
import output_classes
import util


def assertion_used_in_code_line(line):
    """
    Check whether a line of code contains an assertion. Finds both C assert() calls and C++ static_assert().
    :return: True if there is an assertion, else False.
    """
    # This regex should match _all_ ways in which assertions could occur.
    # It spits out false positives for ultra specific cases: when someone literally puts "assert(" in a string or the
    # mid of a block comment etc. This is fine though.
    # Breakdown of the regex: The first two negative lookaheads "(?! )" exclude commented assertions. Then,
    # match assert( and static_assert( while allowing for whitespace or code (e.g. ";" or "}") before the call.
    regex = r'(?!^.*\/\/.*assert\s*\()(?!^.*\/\*.*assert\s*\()^.*(\W|^)(static_)?assert\s*\('
    line_includes_assertion = False
    if re.match(regex, line):
        line_includes_assertion = True
    return line_includes_assertion


def check_assert_usage(source_files, lines_of_code):
    """
    Check how many assertions are used in the code.
    :param source_files: The list of files to count assertions in.
    :param lines_of_code: The total lines of code.
    :return: The amount of assertions relative to the total lines of code.
    """
    print(strings.RUN_ASSERTION_CHECK_HEADER)
    assert_count = 0

    for file in source_files:
        f = open(file, 'r', encoding='latin-1')

        file_lines = f.readlines()
        for line in file_lines:
            if assertion_used_in_code_line(line):
                assert_count += 1

        f.close()

    amount_of_assertions = assert_count / lines_of_code

    print("Found", assert_count, "assertions in", lines_of_code, "lines of code (excluding blank lines and comment "
                                                                 "lines).")
    print("That's", str(100 * amount_of_assertions), "%.")

    return amount_of_assertions


def get_cppcheck_warning_lines_from_cppcheck_output(output):
    warning_lines = []

    output_lines = output.split('\n')
    for line in output_lines:
        if line.startswith('['):  # Informative lines start with "[/path/to/file.c] (error/warning) ..."
            warning_lines.append(line)

    return warning_lines


def get_cppcheck_warning_type_list_from_warning_lines(warning_lines):
    warning_type_list = []

    for line in warning_lines:
        split_line = line.split()
        warning_type = [substring for substring in split_line if substring.startswith('(') and substring.endswith(
            ')')][0]
        warning_type_list.append(warning_type)

    return warning_type_list


def run_cppcheck(source_files):
    """
    Runs cppcheck.
    :param source_files: The list of source files to analyze.
    :return: A list of the types of warnings cppcheck outputs. E.g., if cppcheck outputs 2 (warning),
    1 (performance), and 4 (style), then this list looks like this: [(warning), (warning), (performance), (style),
    (style), (style), (style)].
    """
    # TODO The return value of this (that list) is a bit awkward... Think about a better way to do this!
    # TODO cppcheck doesn't know about boost so for boost calls it outputs an error "invalid C code" --> ignore these
    #  errors
    print(strings.RUN_CPPCHECK_HEADER)
    cppcheck_call = [TOOLS.CPPCHECK.exe_name, '--enable=all', '--force']
    for file in source_files:
        cppcheck_call.append(file)

    output = subprocess.check_output(cppcheck_call, universal_newlines=True, stderr=subprocess.STDOUT)
    warning_lines = get_cppcheck_warning_lines_from_cppcheck_output(output)
    warning_type_list = get_cppcheck_warning_type_list_from_warning_lines(warning_lines)

    util.print_lines(warning_lines)

    return warning_type_list


def run_splint(source_files):
    """
    Runs splint.
    :param source_files: The list of source files to analyze.
    """
    # TODO Do we really want Splint?
    # TODO If yes, parse the output.
    print(strings.RUN_SPLINT_HEADER)
    splint_call = [TOOLS.SPLINT.exe_name]
    for file in source_files:
        splint_call.append(file)

    subprocess.call(splint_call, universal_newlines=True, stderr=subprocess.STDOUT)


def get_flawfinder_warning_lines_from_flawfinder_output(output):
    warning_lines = []

    output_lines = output.split('\n')
    do_add_warnings = False
    for line in output_lines:
        if line.startswith('ANALYSIS SUMMARY'):
            do_add_warnings = False

        if do_add_warnings:
            warning_lines.append(line)

        if line.startswith('FINAL RESULTS'):
            do_add_warnings = True

    return warning_lines


def get_flawfinder_warning_level_counts_from_flawfinder_output(output):
    """
    :return: A list of integers where each integer is the count of the warning level that corresponds to its position in
    the list. For instance, warning_level_counts[0] = 12 means that we have 12 warnings of level 0,
    warning_level_counts[4] = 42 means that we have 42 warning of level 4 etc. Flawfinder warnings go from 0 (not
    dangerous) to 5 (very dangerous)
    """
    warning_level_counts = []

    output_lines = output.split('\n')
    do_check_for_hits_level = False
    for line in output_lines:
        if line.startswith('ANALYSIS SUMMARY'):
            do_check_for_hits_level = True

        if do_check_for_hits_level:
            if line.startswith('Hits@level ='):  # If this is the line that shows the warning level counts
                warning_level_counts = line.split()[3::2]

    return warning_level_counts


def run_flawfinder(program_dir_abs):
    """
    Runs Flawfinder.
    :param program_dir_abs: The absolute path to the root directory of the target program.
    :return: A list of integers where each integer is the count of the warning level that corresponds to its position in
    the list. For more detail about this list, see the doc of the
    get_flawfinder_warning_level_counts_from_flawfinder_output function.
    """
    print(strings.RUN_FLAWFINDER_HEADER)
    flawfinder_call = [TOOLS.FLAWFINDER.exe_name, program_dir_abs]

    output = subprocess.check_output(flawfinder_call, universal_newlines=True, stderr=subprocess.STDOUT)
    warning_lines = get_flawfinder_warning_lines_from_flawfinder_output(output)
    warning_level_counts = get_flawfinder_warning_level_counts_from_flawfinder_output(output)

    util.print_lines(warning_lines)

    return warning_level_counts


def get_clang_tidy_warning_lines_from_clang_tidy_output(output):
    warning_lines = []

    output_lines = output.split('\n')
    do_add_warnings = False
    for line in output_lines:
        if line.endswith('generated.'):  # "n warnings generated."
            do_add_warnings = True

        if do_add_warnings:
            warning_lines.append(line)

        if line.startswith('Suppressed'):  # "Suppressed m warnings."
            do_add_warnings = False

    return warning_lines


def get_clang_tidy_warning_count_from_clang_tidy_warning_lines(warning_lines):
    total_warning_count = 0
    supressed_warning_count = 0

    for line in warning_lines:
        if line.endswith('generated.'):  # "n warnings generated"
            count_on_this_line = int(line.split()[0])  # get n
            total_warning_count = count_on_this_line if count_on_this_line > total_warning_count else total_warning_count
        elif line.startswith('Suppressed'):  # "Suppressed m warnings"
            supressed_warning_count = int(line.split()[1])  # get m

    warning_count = total_warning_count - supressed_warning_count  # n - m

    return warning_count


def run_clang_tidy(source_files, cpp):
    """
    Runs clang-tidy.
    :param source_files: The list of source files to analyze.
    :param cpp: Whether C++ is used or not. True if C++, false if C.
    :return: The amount of warnings clang-tidy outputs.
    """
    print(strings.RUN_CLANG_TIDY_HEADER)
    clang_tidy_call = [TOOLS.CLANG_TIDY.exe_name]
    for file in source_files:
        clang_tidy_call.append(file)

    # Create checks list
    clang_tidy_checks = '-*,bugprone-*,clang-analyzer-*,misc-*,modernize-*,mpi-*,performance-*,readability-*'
    if cpp:
        clang_tidy_checks += ',boost-*,cppcoreguidelines-*'
    clang_tidy_call.append('-checks=' + clang_tidy_checks)

    output = subprocess.check_output(clang_tidy_call, universal_newlines=True, stderr=subprocess.STDOUT)
    warning_lines = get_clang_tidy_warning_lines_from_clang_tidy_output(output)
    warning_count = get_clang_tidy_warning_count_from_clang_tidy_warning_lines(warning_lines)

    util.print_lines(warning_lines)

    return warning_count


def get_actual_rate_from_lizard_duplicate_rate_line(line):
    percentage_string = line.split()[-1]  # Get the percentage
    rate = float(percentage_string[:-1]) / 100  # Remove the "%" character at the end
    return rate


def get_lizard_output_object_from_lizard_printed_output(output):
    output_lines = output.split('\n')

    # Get standard lizard information: CCN & warning count
    summary_line = None
    for i, output_line in enumerate(output_lines):
        if output_line.startswith('Total nloc'):
            summary_line = output_lines[i + 2]  # This line contains the information we need
    split_summary_line = summary_line.split()

    avg_ccn = float(split_summary_line[2])
    warning_cnt = int(split_summary_line[5])

    # Get -Eduplicate information
    duplicate_rate_line = output_lines[-3]
    unique_rate_line = output_lines[-2]

    duplicate_rate = get_actual_rate_from_lizard_duplicate_rate_line(duplicate_rate_line)
    unique_rate = get_actual_rate_from_lizard_duplicate_rate_line(unique_rate_line)

    lizard_output = output_classes.LizardOutput(avg_ccn, warning_cnt, duplicate_rate, unique_rate)
    return lizard_output


def run_lizard(source_files):
    """
    Runs Lizard to check cyclomatic complexity.
    :param source_files: The list of source files to analyze.
    :return:
    """
    # NOTE Although lizard can be used as a python module ("import lizard") it is actually easier to parse its output
    # (for now at least - this might of course change). This is because the module is not well documented so it's
    # hard to find out how exactly one can get _all_ information using it. Plus, this way we can check if it is
    # installed using shutil.which --> consistent with how we check for the other tools.
    print(strings.RUN_LIZARD_HEADER)

    lizard_call = [TOOLS.LIZARD.exe_name, '-Eduplicate', '-l', 'cpp']
    for file in source_files:
        lizard_call.append(file)

    try:
        output = subprocess.check_output(lizard_call, universal_newlines=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:  # If warnings are generated, Lizard exits with exit code 1
        output = e.output  # Basically, this catches the exception and ignores it such that this tool doesn't crash
        # while still keeping the output of the command

    lizard_output = get_lizard_output_object_from_lizard_printed_output(output)
    lizard_output.print_information()

    return lizard_output


def run_static_analysis(program_dir_abs, cpp, exclude):
    """
    Run all the static code analysis.
    :param program_dir_abs: The absolute path to the root directory of the program.
    :param cpp: Whether we're using C++ or not. True if C++ is used, False if C is used.
    :param exclude: A comma separated list of files and directories to exclude from being analyzed.
    """
    # TODO How to return all the information that is generated here to the caller? One huge object?
    source_files = util.find_all_source_files(program_dir_abs, exclude)
    lines_of_code = util.count_lines_of_code(source_files)

    amount_of_assertions = check_assert_usage(source_files, lines_of_code)
    cppcheck_warning_type_list = run_cppcheck(source_files)
    if not cpp:
        run_splint(source_files)
    flawfinder_warning_level_counts = run_flawfinder(program_dir_abs)
    clang_tidy_warning_count = run_clang_tidy(source_files, cpp)
    lizard_output = run_lizard(source_files)
