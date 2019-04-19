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
import compile_phase
import classifications
import scoring


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
    :return: The assertion score.
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

    score = scoring.calculate_assertion_score(assertion_rate)
    scoring.print_score(score, 'Assertion')
    return score


def get_cppcheck_warning_lines_from_cppcheck_output(output):
    warning_lines = []

    output_lines = output.split('\n')
    for line in output_lines:
        if line.startswith('['):  # Informative lines start with "[/path/to/file.c] (error/warning) ..."
            warning_lines.append(line)

    return warning_lines


def run_cppcheck(source_files, lines_of_code, cpp):
    """
    Runs cppcheck.
    :param source_files: The list of source files to analyze.
    :param lines_of_code: The lines of pure code count.
    :param cpp: Whether we're using C++ or not. True if C++ is used, False if C is used.
    :return: The Cppcheck score.
    """
    print(strings.RUN_CPPCHECK_HEADER)
    language = 'c++' if cpp else 'c'
    cppcheck_call = [TOOLS.CPPCHECK.exe_name, '--enable=all', '--force', '--language=' + language]
    cppcheck_call.extend(source_files)

    output = subprocess.check_output(cppcheck_call, universal_newlines=True, stderr=subprocess.STDOUT)
    warning_lines = get_cppcheck_warning_lines_from_cppcheck_output(output)
    cppcheck_output = output_classes.CppcheckOutput(warning_lines)

    weighted_cppcheck_rate = cppcheck_output.print_information(lines_of_code)
    util.write_into_file_list(strings.RESULTS_FILENAME_CPPCHECK, warning_lines)

    score = scoring.calculate_cppcheck_score(weighted_cppcheck_rate)
    scoring.print_score(score, 'Cppcheck')
    return score


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


def get_weighted_clang_tidy_warning_count_from_clang_tidy_warning_lines(warning_lines):
    warning_count = 0

    for line in warning_lines:
        if compile_phase.line_is_warning_line(line):
            warning_name = line.split()[-1][1:-1]
            warning_category = warning_name.split('-')[0]

            warning_level = 1
            if warning_category in classifications.CLANG_TIDY_WARNINGS:
                warning_level = classifications.CLANG_TIDY_WARNINGS[warning_category]

            warning_count += warning_level

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
    :return: The clang-tidy score.
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
    weighted_warning_count = get_weighted_clang_tidy_warning_count_from_clang_tidy_warning_lines(warning_lines)
    warning_rate = weighted_warning_count / lines_of_code

    print(strings.RESULT_WEIGHTED_CLANG_TIDY_WARNING_RATE.format(warning_rate, weighted_warning_count, lines_of_code))
    beautified_warning_lines = beautify_clang_tidy_warning_lines(warning_lines)
    util.write_into_file_list(strings.RESULTS_FILENAME_CLANG_TIDY, beautified_warning_lines)

    score = scoring.calculate_clang_tidy_score(warning_rate)
    scoring.print_score(score, 'Clang-tidy')
    return score


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
    unique_rate_line = output_lines[-2]

    unique_rate = get_actual_rate_from_lizard_duplicate_rate_line(unique_rate_line)

    lizard_output = output_classes.LizardOutput(avg_ccn, warning_cnt, unique_rate, function_count)
    return lizard_output


def run_lizard(source_files):
    """
    Runs Lizard.
    :param source_files: The list of source files to analyze.
    :return: The cyclomatic complexity score, warning score, and unique score
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
    cyclomatic_complexity_score, warning_score, unique_score = \
        lizard_output.print_information_and_return_scores()  # Also prints the scores
    util.write_into_file_string(strings.RESULTS_FILENAME_LIZARD, output)

    return cyclomatic_complexity_score, warning_score, unique_score


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
    :return: The KWStyle score.
    """
    print(strings.RUN_KWSTYLE_HEADER)

    softwipe_directory = os.path.dirname(os.path.realpath(__file__))
    kwstyle_xml = os.path.join(softwipe_directory, 'KWStyle.xml')
    kwstyle_call = [TOOLS.KWSTYLE.exe_name, '-v', '-xml', kwstyle_xml]

    output = ''
    # KWStyle only works properly when specifying just one single input file. Thus, iterate and call KWStyle again
    # for each source file, each time appending to the result output.
    for source_file in source_files:
        cur_kwstyle_call = kwstyle_call[::]
        cur_kwstyle_call.append(source_file)
        try:
            output += subprocess.check_output(cur_kwstyle_call, universal_newlines=True, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:  # Same as with the lizard call. KWStyle exits with status 1 by
            output += e.output  # default. So catch that, ignore the exception, and keep the output of the command
        
    warning_count = get_kwstyle_warning_count_from_kwstyle_output(output)
    warning_rate = warning_count / lines_of_code

    print(strings.RESULT_KWSTYLE_WARNING_RATE.format(warning_rate, warning_count, lines_of_code))
    util.write_into_file_string(strings.RESULTS_FILENAME_KWSTYLE, output)

    score = scoring.calculate_kwstyle_score(warning_rate)
    scoring.print_score(score, 'KWStyle')
    return score


def run_static_analysis(source_files, lines_of_code, cpp):
    """
    Run all the static code analysis.
    :param source_files: The list of source files to analyze.
    :param lines_of_code: The lines of pure code count for the source_files.
    :param cpp: Whether we're using C++ or not. True if C++ is used, False if C is used.
    :return All the scores: assertion_score, cppcheck_score, clang_tidy_score, cyclomatic_complexity_score,
    warning_score, unique_score, kwstyle_score.
    """
    assertion_score = check_assert_usage(source_files, lines_of_code)
    cppcheck_score = run_cppcheck(source_files, lines_of_code, cpp)
    clang_tidy_score = run_clang_tidy(source_files, lines_of_code, cpp)
    cyclomatic_complexity_score, warning_score, unique_score = run_lizard(source_files)
    kwstyle_score = run_kwstyle(source_files, lines_of_code)

    return assertion_score, cppcheck_score, clang_tidy_score, cyclomatic_complexity_score, warning_score, \
           unique_score, kwstyle_score
