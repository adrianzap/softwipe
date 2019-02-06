"""
This module contains all functions related to the static analysis phase. That is, the static analysis pipeline is
completely written down here.
"""


import subprocess
import re
import os

import strings
from tools_info import TOOLS
import output_classes
import util


def assertion_used_in_code_line(line):
    """
    Check whether a line of code contains an assertion. Finds both C assert() calls and C++ static_assert().
    :return: True if there is an assertion, else False.
    """
    # This regex should match all ways in which assertions could occur.
    # It spits out false positives for ultra specific cases: when someone literally puts "assert(" in a string or the
    # mid of a block comment. This is fine though.
    # Breakdown of the regex: The first two negative lookaheads "(?! )" exclude commented assertions. Then,
    # match assert( and static_assert( while allowing for whitespace or code (e.g. ";" or "}") before the call.
    regex = r'(?!^.*\/\/.*assert\s*\()(?!^.*\/\*.*assert\s*\()^.*(\W|^)(static_)?assert\s*\('
    return re.match(regex, line)


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

    assertion_rate = assert_count / lines_of_code

    detailled_result_string = strings.RESULT_ASSERTION_RATE_DETAILED.format(count=assert_count, loc=lines_of_code,
                                                                            rate=assertion_rate,
                                                                            percentage=100*assertion_rate)
    print(strings.RESULT_ASSERTION_RATE.format(assertion_rate, assert_count, lines_of_code))
    util.write_into_file_string(strings.RESULTS_FILENAME_ASSERTION_CHECK, detailled_result_string)

    return assertion_rate


def get_cppcheck_warning_lines_from_cppcheck_output(output):
    warning_lines = []

    output_lines = output.split('\n')
    for line in output_lines:
        if line.startswith('['):  # Informative lines start with "[/path/to/file.c] (error/warning) ..."
            warning_lines.append(line)

    return warning_lines


def run_cppcheck(source_files, lines_of_code):
    """
    Runs cppcheck.
    :param source_files: The list of source files to analyze.
    :param lines_of_code: The lines of pure code count.
    :return: A CppcheckOutput object that contains the amount of warnings for each cppcheck warning type.
    """
    # TODO cppcheck doesn't know about boost so for boost calls it outputs an error "invalid C code" --> ignore these
    #  errors
    print(strings.RUN_CPPCHECK_HEADER)
    cppcheck_call = [TOOLS.CPPCHECK.exe_name, '--enable=all', '--force']
    cppcheck_call.extend(source_files)

    output = subprocess.check_output(cppcheck_call, universal_newlines=True, stderr=subprocess.STDOUT)
    warning_lines = get_cppcheck_warning_lines_from_cppcheck_output(output)
    cppcheck_output = output_classes.CppcheckOutput(warning_lines)

    cppcheck_output.print_information(lines_of_code)
    util.write_into_file_list(strings.RESULTS_FILENAME_CPPCHECK, warning_lines)

    return cppcheck_output


def get_clang_tidy_warning_lines_from_clang_tidy_output(output):
    warning_lines = []

    output_lines = output.split('\n')
    do_add_warnings = False
    for line in output_lines:
        if util.clang_tidy_output_line_is_header(line):  # "n warnings generated."
            do_add_warnings = True

        if do_add_warnings:
            warning_lines.append(line)

        if util.clang_tidy_output_line_is_trailer(line):  # "Suppressed m warnings."
            do_add_warnings = False

    return warning_lines


def get_clang_tidy_warning_count_from_clang_tidy_warning_lines(warning_lines):
    total_warning_count = 0
    suppressed_warning_count = 0

    for line in warning_lines:
        if util.clang_tidy_output_line_is_header(line):  # "n warnings generated"
            count_on_this_line = int(line.split()[0])  # get n
            total_warning_count = count_on_this_line if \
                count_on_this_line > total_warning_count else total_warning_count

        elif util.clang_tidy_output_line_is_trailer(line):  # "Suppressed m warnings"
            suppressed_warning_count = int(line.split()[1])  # get m

    warning_count = total_warning_count - suppressed_warning_count  # n - m

    return warning_count


def beautify_clang_tidy_warning_lines(warning_lines):
    """
    Removes the "n warnings generated" headers and "Suppressed m warnings" trailer for a more beautiful output
    :param warning_lines: The clang tidy warning lines as output by
    get_clang_tidy_warning_lines_from_clang_tidy_output(), which contain the ugly headers and trailer.
    :return: The warning lines with the headers and trailer removed.
    """
    beautified_lines = []
    for line in warning_lines:
        if not (util.clang_tidy_output_line_is_header(line) or util.clang_tidy_output_line_is_trailer(line)):
            beautified_lines.append(line)

    return beautified_lines


def run_clang_tidy(source_files, lines_of_code, cpp):
    """
    Runs clang-tidy.
    :param source_files: The list of source files to analyze.
    :param lines_of_code: The lines of pure code count.
    :param cpp: Whether C++ is used or not. True if C++, false if C.
    :return: The amount of warnings clang-tidy outputs.
    """
    print(strings.RUN_CLANG_TIDY_HEADER)
    clang_tidy_call = [TOOLS.CLANG_TIDY.exe_name]
    clang_tidy_call.extend(source_files)

    # Create checks list
    clang_tidy_checks = strings.CLANG_TIDY_CHECKS_CPP if cpp else strings.CLANG_TIDY_CHECKS_C
    clang_tidy_call.append('-checks=' + clang_tidy_checks)

    try:
        output = subprocess.check_output(clang_tidy_call, universal_newlines=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        output = e.output
        # clang-tidy can exit with exit code 1 if there is no compilation database, which might be the case when
        # compiling with just clang. Thus, ignore the exception here.
    warning_lines = get_clang_tidy_warning_lines_from_clang_tidy_output(output)
    warning_count = get_clang_tidy_warning_count_from_clang_tidy_warning_lines(warning_lines)
    warning_rate = warning_count / lines_of_code

    print(strings.RESULT_CLANG_TIDY_WARNING_RATE.format(warning_rate, warning_count, lines_of_code))
    beautified_warning_lines = beautify_clang_tidy_warning_lines(warning_lines)
    util.write_into_file_list(strings.RESULTS_FILENAME_CLANG_TIDY, beautified_warning_lines)

    return warning_count


def get_actual_rate_from_lizard_duplicate_rate_line(line):
    percentage_string = line.split()[-1]  # Get the percentage
    rate = float(percentage_string[:-1]) / 100  # Remove the "%" character at the end
    return rate


def get_lizard_output_object_from_lizard_printed_output(output):
    output_lines = output.split('\n')

    # Get total number of functions and standard lizard information (CCN & warning count)
    function_count = 0
    currently_counting_functions = False
    function_counting_finished = False
    summary_line = None
    for i, output_line in enumerate(output_lines):
        # Function counting
        if currently_counting_functions:
            if output_line.endswith('analyzed.'):  # Stop counting at the right point
                currently_counting_functions = False
                function_counting_finished = True
            else:
                function_count += 1
        if output_line.startswith('--') and not function_counting_finished:  # Start counting after this
            currently_counting_functions = True

        # Getting the information
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

    lizard_output = output_classes.LizardOutput(avg_ccn, warning_cnt, duplicate_rate, unique_rate, function_count)
    return lizard_output


def run_lizard(source_files):
    """
    Runs Lizard.
    :param source_files: The list of source files to analyze.
    :return: A LizardOutput object that contains all the information we want from lizard.
    """
    # NOTE Although lizard can be used as a python module ("import lizard") it is actually easier to parse its output
    # (for now at least - this might of course change). This is because the module is not well documented so it's
    # hard to find out how exactly one can get _all_ information using it. Plus, this way we can check if it is
    # installed using shutil.which --> consistent with how we check for the other tools.
    print(strings.RUN_LIZARD_HEADER)

    lizard_call = [TOOLS.LIZARD.exe_name, '-Eduplicate', '-l', 'cpp']
    lizard_call.extend(source_files)

    try:
        output = subprocess.check_output(lizard_call, universal_newlines=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:  # If warnings are generated, Lizard exits with exit code 1
        output = e.output  # Basically, this catches the exception and ignores it such that this tool doesn't crash
        # while still keeping the output of the command

    lizard_output = get_lizard_output_object_from_lizard_printed_output(output)
    lizard_output.print_information()
    util.write_into_file_string(strings.RESULTS_FILENAME_LIZARD, output)

    return lizard_output


def get_kwstyle_warning_count_from_kwstyle_output(output):
    warning_count = 0

    output_lines = output.split('\n')
    for line in output_lines:
        if line.startswith('Error'):
            warning_count += 1

    return warning_count


def run_kwstyle(source_files, lines_of_code):
    """
    Runs KWStyle.
    :param source_files: The list of source files to analyze.
    :param lines_of_code: The lines of pure code count.
    :return: The amount of warnings KWStyle outputs.
    """
    print(strings.RUN_KWSTYLE_HEADER)

    softwipe_directory = os.path.dirname(os.path.realpath(__file__))
    kwstyle_xml = os.path.join(softwipe_directory, 'KWStyle.xml')
    kwstyle_call = [TOOLS.KWSTYLE.exe_name, '-v', '-xml', kwstyle_xml]
    kwstyle_call.extend(source_files)

    try:
        output = subprocess.check_output(kwstyle_call, universal_newlines=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:  # Same as with the lizard call. KWStyle exits with status 1 by default
        output = e.output  # So catch that, ignore the exception, and keep the output of the command
        
    warning_count = get_kwstyle_warning_count_from_kwstyle_output(output)
    warning_rate = warning_count / lines_of_code

    print(strings.RESULT_KWSTYLE_WARNING_RATE.format(warning_rate, warning_count, lines_of_code))
    util.write_into_file_string(strings.RESULTS_FILENAME_KWSTYLE, output)

    return warning_count


def run_static_analysis(source_files, lines_of_code, cpp):
    """
    Run all the static code analysis.
    :param source_files: The list of source files to analyze.
    :param lines_of_code: The lines of pure code count for the source_files.
    :param cpp: Whether we're using C++ or not. True if C++ is used, False if C is used.
    """
    # TODO How to return all the information that is generated here to the caller? One huge object?
    assertion_rate = check_assert_usage(source_files, lines_of_code)
    cppcheck_output = run_cppcheck(source_files, lines_of_code)
    clang_tidy_warning_rate = run_clang_tidy(source_files, lines_of_code, cpp)
    lizard_output = run_lizard(source_files)
    kwstyle_warnings = run_kwstyle(source_files, lines_of_code)
