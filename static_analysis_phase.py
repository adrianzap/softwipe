"""
This module contains all functions related to the static analysis phase. That is, the static analysis pipeline is
completely written down here.
"""


import subprocess
import os
import re

import strings
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
    cppcheck_call = [strings.TOOLS.CPPCHECK, '--enable=all', '--force']
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
    splint_call = [strings.TOOLS.SPLINT]
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
    flawfinder_call = [strings.TOOLS.FLAWFINDER, program_dir_abs]

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
    clang_tidy_call = [strings.TOOLS.CLANG_TIDY]
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


def get_lizard_output_object_from_lizard_output(output):
    output_lines = output.split('\n')
    final_line = output_lines[-2]  # This line contains the information we need
    split_final_line = final_line.split()

    avg_ccn = float(split_final_line[2])
    warning_cnt = int(split_final_line[5])

    lizard_output = output_classes.LizardOutput(avg_ccn, warning_cnt)
    return lizard_output


def run_lizard(source_files):
    """
    Runs Lizard to check cyclomatic complexity.
    :param source_files: The list of source files to analyze.
    :return:
    """
    # TODO Also use lizard for finding duplicates! Better than PMD CPD + easier to use :)
    # NOTE Although lizard can be used as a python module ("import lizard") it is actually easier to parse its output
    # (for now at least - this might of course change). This is because the module is not well documented so it's
    # hard to find out how exactly one can get _all_ information using it. Plus, this way we can check if it is
    # installed using shutil.which --> consistent with how we check for the other tools.
    print(strings.RUN_LIZARD_HEADER)

    lizard_call = [strings.TOOLS.LIZARD, '-l', 'cpp']
    for file in source_files:
        lizard_call.append(file)

    try:
        output = subprocess.check_output(lizard_call, universal_newlines=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:  # If warnings are generated, Lizard exits with exit code 1
        output = e.output  # Basically, this catches the exception and ignores it such that this tool doesn't crash
        # while still keeping the output of the command

    lizard_output = get_lizard_output_object_from_lizard_output(output)
    lizard_output.print_information()

    return lizard_output


def get_lines_and_tokens_from_found_line_in_cpd_output(line):
    split_line = line.split()
    lines = int(split_line[2])
    tokens = int(split_line[4][1:])  # [1:] cuts off the '(' where it says (n tokens)
    return lines, tokens


def get_occurrence_tupel_from_occurrence_line_in_cpd_output(line):
    split_line = line.split()
    line = split_line[3]
    # TODO Check how the output looks like if there are spaces in the path. Handle that case.
    file = os.path.abspath(split_line[5])
    return file, line


def get_code_duplicates_from_cpd_output(output):
    code_duplicates = []

    output_lines = output.split('\n')
    currently_parsing_a_duplicate = False
    cur_duplicate_lines = 0
    cur_duplicate_tokens = 0
    cur_duplicate_occurrences = []
    for line in output_lines:
        if not currently_parsing_a_duplicate:
            if line.startswith('Found'):
                currently_parsing_a_duplicate = True
                cur_duplicate_lines, cur_duplicate_tokens = get_lines_and_tokens_from_found_line_in_cpd_output(line)
        else:
            if line.startswith('Starting'):
                cur_duplicate_occurrences.append(get_occurrence_tupel_from_occurrence_line_in_cpd_output(line))
            else:
                cur_duplicate = output_classes.CodeDuplicate(cur_duplicate_lines, cur_duplicate_tokens,
                                                             cur_duplicate_occurrences)
                code_duplicates.append(cur_duplicate)
                currently_parsing_a_duplicate = False
                cur_duplicate_occurrences = []  # Reset the list

    return code_duplicates


def run_cpd(source_files, pmd_bin_dir):
    """
    Runs the PMD CPD (Copy-Paste detector).
    :param source_files: The list of source files to analyze.
    :param pmd_bin_dir: The PMD bin/ directory where the run.sh is located.
    :return: A list of output_classes.CodeDuplicate objects which contains information about duplicate pieces of code in
    the source files.
    """
    print(strings.RUN_CPD_HEADER)
    pmd_binary_abs = os.path.join(os.path.abspath(pmd_bin_dir), 'run.sh')  # TODO Maybe support Windows here, too?
    cpd_call = [pmd_binary_abs, 'cpd', '--minimum-tokens', '100', '--language', 'cpp', '--failOnViolation', 'false',
                '--files']
    for file in source_files:
        cpd_call.append(file)

    output = subprocess.check_output(cpd_call, universal_newlines=True, stderr=subprocess.STDOUT)
    code_duplicates = get_code_duplicates_from_cpd_output(output)
    for duplicate in code_duplicates:
        duplicate.print_information()

    return code_duplicates


def run_static_analysis(program_dir_abs, pmd_bin_dir, cpp, exclude):
    """
    Run all the static code analysis.
    :param program_dir_abs: The absolute path to the root directory of the program.
    :param pmd_bin_dir: The path to the bin directory of PMD.
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
    code_duplicates = run_cpd(source_files, pmd_bin_dir)
