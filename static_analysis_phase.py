"""
This module contains all functions related to the static analysis phase. That is, the static analysis pipeline is
completely written down here.
"""


import subprocess
import re
import os
import sys
from multiprocessing.pool import ThreadPool

import strings
from tools_info import TOOLS
import output_classes
import util
import compile_phase
import classifications
import scoring

skip_on_failure = False     #TODO: implement more elegantly?
cppcheck_working = True
infer_working = True

def assertion_used_in_code_line(line, custom_asserts=None):
    """
    Check whether a line of code contains an assertion. Finds both C assert() calls and C++ static_assert().
    :return: True if there is an assertion, else False.
    """
    # This regex should match all ways in which assertions could occur.
    # It spits out false positives for ultra specific cases: when someone literally puts "assert(" in a string or the
    # mid of a block comment. This is fine though.
    # Breakdown of the regex: The first two negative lookaheads "(?! )" exclude commented assertions. Then,
    # match assert( and static_assert( while allowing for whitespace or code (e.g. ";" or "}") before the call.
    # If there are any custom asserts, add them to "custom". The regex will look for (assert|custom_assert).
    custom = ''
    if custom_asserts:
        for custom_assert in custom_asserts:
            custom += '|' + custom_assert

    regex = r'(?!^.*\/\/.*(assert' + custom + ')\s*\()(?!^.*\/\*.*(assert' + custom + \
            ')\s*\()^.*(\W|^)((static_)?assert' + custom + ')\s*\('
    return re.match(regex, line)


def check_assert_usage(source_files, lines_of_code, custom_asserts=None):
    """
    Check how many assertions are used in the code.
    :param source_files: The list of files to count assertions in.
    :param lines_of_code: The total lines of code.
    :param custom_asserts: A list of custom assertions to be checked by the assertion check.
    :return: The assertion score.
    """

    # TODO: Remove all the prints from the static analysis functions for the sake of race conditions
    #print(strings.RUN_ASSERTION_CHECK_HEADER)
    assert_count = 0

    for file in source_files:
        f = open(file, 'r', encoding='latin-1')

        file_lines = f.readlines()
        for line in file_lines:
            if assertion_used_in_code_line(line, custom_asserts):
                assert_count += 1

        f.close()

    assertion_rate = assert_count / lines_of_code

    detailled_result_string = strings.RESULT_ASSERTION_RATE_DETAILED.format(count=assert_count, loc=lines_of_code,
                                                                            rate=assertion_rate,
                                                                            percentage=100*assertion_rate)

    #print(strings.RESULT_ASSERTION_RATE.format(assertion_rate, assert_count, lines_of_code))
    util.write_into_file_string(strings.RESULTS_FILENAME_ASSERTION_CHECK, detailled_result_string)

    score = scoring.calculate_assertion_score_absolute(assertion_rate)
    #scoring.print_score(score, 'Assertion')

    log = strings.RUN_ASSERTION_CHECK_HEADER + "\n"
    log += strings.RESULT_ASSERTION_RATE.format(assertion_rate, assert_count, lines_of_code) + "\n"
    log += strings.DETAILLED_RESULTS_WRITTEN_INTO.format(strings.RESULTS_FILENAME_ASSERTION_CHECK) + "\n"
    log += scoring.get_score_string(score, 'Assertion') + "\n"

    return score, log, True     #TODO: well that's awkward... but there should be no errors from out own code anyways, so..


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
    #print(strings.RUN_CPPCHECK_HEADER)
    language = 'c++' if cpp else 'c'
    cppcheck_call = [TOOLS.CPPCHECK.exe_name, '--enable=all', '--force', '--language=' + language,
                      "-v"] #TODO: find out the purpose of the --template=cppcheck1' which broke the output
    cppcheck_call.extend(source_files)

    try:
        output = subprocess.check_output(cppcheck_call, universal_newlines=True, stderr=subprocess.STDOUT)
        warning_lines = get_cppcheck_warning_lines_from_cppcheck_output(output)
        cppcheck_output = output_classes.CppcheckOutput(warning_lines)
    except subprocess.CalledProcessError as e:
        print("cppcheck failed!")
        print(strings.COMPILATION_CRASHED.format(e.returncode, e.output))
        if not skip_on_failure:
            raise
        return 0, "", False
    except Exception:   #catch the rest and exclude the analysis tool from the score
        if not skip_on_failure:
            raise
        else:
            return 0, "", False         #TODO: make a common format for the exclusion?

    weighted_cppcheck_rate, temp = cppcheck_output.get_information(lines_of_code)
    util.write_into_file_list(strings.RESULTS_FILENAME_CPPCHECK, warning_lines)

    score = scoring.calculate_cppcheck_score_absolute(weighted_cppcheck_rate)

    log = strings.RUN_CPPCHECK_HEADER + "\n"
    log += temp
    log += strings.DETAILLED_RESULTS_WRITTEN_INTO.format(strings.RESULTS_FILENAME_CPPCHECK) + "\n"
    log += scoring.get_score_string(score, 'Cppcheck') + "\n"

    return score, log, True


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


def run_clang_tidy(program_dir_abs, source_files, lines_of_code, cpp, num_tries=3):     #TODO: fix doc strings
    """
    Runs clang-tidy.
    :param program_dir_abs: The absolute path to the root directory of the target program.
    :param source_files: The list of source files to analyze.
    :param lines_of_code: The lines of pure code count.
    :param cpp: Whether C++ is used or not. True if C++, false if C.
    :param num_tries: The amount of times clang-tidy should be rerun if it runs into internal problems
    :return: The clang-tidy score.
    """
    #print(strings.RUN_CLANG_TIDY_HEADER)
    clang_tidy_call = [TOOLS.CLANG_TIDY.exe_name]
    clang_tidy_call.extend(source_files)

    # Create checks list
    clang_tidy_checks = strings.CLANG_TIDY_CHECKS_CPP if cpp else strings.CLANG_TIDY_CHECKS_C
    clang_tidy_call.append('-checks=' + clang_tidy_checks)
    clang_tidy_call.extend(['-p', program_dir_abs])

    try:
        output = subprocess.check_output(clang_tidy_call, universal_newlines=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        output = e.output

        if num_tries < 0:           #make clang-tidy return a failure status
            return 0, "", False

        if e.returncode == -11:     #clang-tidy seems to run into segfaults sometimes, so rerun it if that happens
            return run_clang_tidy(program_dir_abs, source_files, lines_of_code, cpp, num_tries=num_tries-1)
        # clang-tidy can exit with exit code 1 if there is no compilation database, which might be the case when
        # compiling with just clang. Thus, ignore the exception here.
    except Exception:   #catch the rest and exclude the analysis tool from the score
        if not skip_on_failure:
            raise
        else:
            return 0, "", False         #TODO: make a common format for the exclusion?

    warning_lines = get_clang_tidy_warning_lines_from_clang_tidy_output(output)
    weighted_warning_count = get_weighted_clang_tidy_warning_count_from_clang_tidy_warning_lines(warning_lines)
    warning_rate = weighted_warning_count / lines_of_code

    #print(strings.RESULT_WEIGHTED_CLANG_TIDY_WARNING_RATE.format(warning_rate, weighted_warning_count, lines_of_code))
    beautified_warning_lines = beautify_clang_tidy_warning_lines(warning_lines)
    util.write_into_file_list(strings.RESULTS_FILENAME_CLANG_TIDY, beautified_warning_lines)

    score = scoring.calculate_clang_tidy_score_absolute(warning_rate)
    #scoring.print_score(score, 'Clang-tidy')

    log = strings.RUN_CLANG_TIDY_HEADER + "\n"
    log += strings.RESULT_WEIGHTED_CLANG_TIDY_WARNING_RATE.format(warning_rate, weighted_warning_count, lines_of_code) + "\n"
    log += strings.DETAILLED_RESULTS_WRITTEN_INTO.format(strings.RESULTS_FILENAME_CLANG_TIDY) + "\n"
    log += scoring.get_score_string(score, 'Clang-tidy') + "\n"

    return score, log, True


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
    #print(strings.RUN_LIZARD_HEADER)

    lizard_call = [TOOLS.LIZARD.exe_name, '-Eduplicate', '-l', 'cpp']
    lizard_call.extend(source_files)

    try:
        output = subprocess.check_output(lizard_call, universal_newlines=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:  # If warnings are generated, Lizard exits with exit code 1
        output = e.output  # Basically, this catches the exception and ignores it such that this tool doesn't crash
                           # while still keeping the output of the command
    except Exception:   #catch the rest and exclude the analysis tool from the score
        if not skip_on_failure:
            raise
        else:
            return 0, 0, 0, "", False         #TODO: make a common format for the exclusion?


    lizard_output = get_lizard_output_object_from_lizard_printed_output(output)
    cyclomatic_complexity_score, warning_score, unique_score, temp = \
        lizard_output.get_information()  # Also prints the scores
    util.write_into_file_string(strings.RESULTS_FILENAME_LIZARD, output)

    log = strings.RUN_LIZARD_HEADER + "\n"
    log += strings.DETAILLED_RESULTS_WRITTEN_INTO.format(strings.RESULTS_FILENAME_LIZARD) + "\n"
    log += temp

    return cyclomatic_complexity_score, warning_score, unique_score, log, True


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
            output += e.output                      # default. So catch that, ignore the exception, and keep the output of the command
        except Exception:  # catch the rest and exclude the analysis tool from the score
            if not skip_on_failure:
                raise
            else:
                return 0, "", False  # TODO: make a common format for the exclusion?
        
    warning_count = get_kwstyle_warning_count_from_kwstyle_output(output)
    warning_rate = warning_count / lines_of_code

    #print(strings.RESULT_KWSTYLE_WARNING_RATE.format(warning_rate, warning_count, lines_of_code))
    util.write_into_file_string(strings.RESULTS_FILENAME_KWSTYLE, output)

    score = scoring.calculate_kwstyle_score_absolute(warning_rate)

    log = strings.RUN_KWSTYLE_HEADER + "\n"
    log += strings.RESULT_KWSTYLE_WARNING_RATE.format(warning_rate, warning_count, lines_of_code) + "\n"
    log += strings.DETAILLED_RESULTS_WRITTEN_INTO.format(strings.RESULTS_FILENAME_KWSTYLE) + "\n"
    log += scoring.get_score_string(score, 'KWStyle') + "\n"

    return score, log, True

def run_infer_analysis(program_dir_abs, lines_of_code, cmake):
    if cmake: program_dir_abs += "/infer_build/"  #TODO: make this with string constant

    record = False
    out = ""
    file_out = ""

    infer_analyze = ["infer", "analyze", "--keep-going"]   #TODO: maybe fix the error handling differently (not by the --keep-going flag)
    try:
        output = subprocess.check_output(infer_analyze, cwd=program_dir_abs, universal_newlines=True,
                                      stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(strings.COMPILATION_CRASHED.format(e.returncode, e.output))   #TODO: fix this
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(type(e).__name__, e.args)
        print(message)
        if not skip_on_failure:
            raise
        else:
            return 0, "", False
    except Exception:   #catch the rest and exclude the analysis tool from the score
        if not skip_on_failure:
            raise
        else:
            return 0, "", False         #TODO: make a common format for the exclusion?

    infer_out_path = find_file(program_dir_abs, "bugs.txt", directory="infer-out")
    if infer_out_path == "":
        return 0, "Could not find bugs.txt", False

    infer_warnings = 0

    with open(infer_out_path) as f:
        for line in f:
            file_out += line
            line = line.rstrip()
            if not line: continue
            if record:
                out += line + "\n"
                line = line.replace(" ", "").split(":")
                category = line[0]
                if category in classifications.INFER_WARNINGS:
                    factor = classifications.INFER_WARNINGS[category]
                else:
                    factor = 1
                if category != "":
                    infer_warnings += factor * int(line[-1])
            if "Summary of the reports" in line:
                record = True
            #TODO: the "no issues" case

    util.write_into_file_string(strings.RESULTS_FILENAME_INFER, file_out)

    infer_warning_rate = infer_warnings / lines_of_code
    score = scoring.calculate_infer_score_absolute(infer_warning_rate)

    log = strings.RUN_INFER_ANALYSIS_HEADER + "\n"
    log += out + "\n"
    log += "Weighted Infer warning rate: {} ({}/{})".format(infer_warnings / lines_of_code, infer_warnings, lines_of_code) + "\n"      #TODO: make and print filename to user
    log += scoring.get_score_string(score, 'Infer')

    return score, log, True

def find_file(path, file_name, directory=""):
    dirs = []
    for (_, dir, file) in os.walk(path):
        dirs.extend(dir)
        if directory == "":
            if file_name in file:
                return path + "/" + file_name
        else:
            if file_name in file and path.split("/")[-1] == directory:
                return path + "/" + file_name
        break
    for dir in dirs:
        file_path = find_file(path + "/" + dir, file_name, directory=directory)
        if file_path != "": return file_path

    return ""


def run_static_analysis(program_dir_abs, source_files, lines_of_code, cpp, custom_asserts=None, cmake=False, skip_on_failure_flag=True):        #TODO: fix that skip_on_failure_flag and add it to the cmd parser
    """
    Run all the static code analysis.
    :param program_dir_abs: The absolute path to the root directory of the target program.
    :param source_files: The list of source files to analyze.
    :param lines_of_code: The lines of pure code count for the source_files.
    :param cpp: Whether we're using C++ or not. True if C++ is used, False if C is used.
    :param custom_asserts: A list of custom assertions to be checked by the assertion check.
    :return All the scores: assertion_score, cppcheck_score, clang_tidy_score, cyclomatic_complexity_score,
    warning_score, unique_score, kwstyle_score.
    """
    '''assertion_score = check_assert_usage(source_files, lines_of_code, custom_asserts)
    cppcheck_score = run_cppcheck(source_files, lines_of_code, cpp)
    clang_tidy_score = run_clang_tidy(program_dir_abs, source_files, lines_of_code, cpp)
    cyclomatic_complexity_score, warning_score, unique_score = run_lizard(source_files)
    kwstyle_score = run_kwstyle(source_files, lines_of_code)'''

    thread_pool = ThreadPool(processes = 6)
    global skip_on_failure
    skip_on_failure = skip_on_failure_flag

    assertion_score_calc = thread_pool.apply_async(check_assert_usage, (source_files, lines_of_code, custom_asserts))
    cppcheck_score_calc = thread_pool.apply_async(run_cppcheck, (source_files, lines_of_code, cpp))
    clang_tidy_score_calc = thread_pool.apply_async(run_clang_tidy, (program_dir_abs, source_files, lines_of_code, cpp))
    lizard_score_calc = thread_pool.apply_async(run_lizard, (source_files, ))
    kwstyle_score_calc = thread_pool.apply_async(run_kwstyle, (source_files, lines_of_code))
    infer_score_calc = thread_pool.apply_async(run_infer_analysis, (program_dir_abs, lines_of_code, cmake))

    assertion_score, assertion_log, assertion_successful = assertion_score_calc.get()
    cppcheck_score, cppcheck_log, cppcheck_successful = cppcheck_score_calc.get()
    clang_tidy_score, clang_tidy_log, clang_successful = clang_tidy_score_calc.get()
    cyclomatic_complexity_score, warning_score, unique_score, lizard_log, lizard_successful = lizard_score_calc.get()
    kwstyle_score, kwstyle_log, kwstyle_successful = kwstyle_score_calc.get()
    infer_score, infer_log, infer_successful = infer_score_calc.get()

    """assertion_score, assertion_log, assertion_successful = check_assert_usage(source_files, lines_of_code, custom_asserts)
    cppcheck_score, cppcheck_log, cppcheck_successful = run_cppcheck(source_files, lines_of_code, cpp)
    clang_tidy_score, clang_tidy_log, clang_successful = run_clang_tidy(program_dir_abs, source_files, lines_of_code, cpp)
    cyclomatic_complexity_score, warning_score, unique_score, lizard_log, lizard_successful = run_lizard(source_files)
    kwstyle_score, kwstyle_log, kwstyle_successful = run_kwstyle(source_files, lines_of_code)
    # infer_score, infer_log, infer_successful = infer_score_calc.get()"""

    '''print(assertion_log)
    print(cppcheck_log)
    print(clang_tidy_log)
    print(lizard_log)
    print(kwstyle_log)
    #print(infer_log)
    print("")'''

    #TODO: think of a nice way to return tool output with a failure flag
    return [("assertions", assertion_score, assertion_log, assertion_successful), ("cppcheck", cppcheck_score, cppcheck_log, cppcheck_successful), ("clang_tidy", clang_tidy_score, clang_tidy_log, clang_successful), ("lizard_cyclomatic_complexity", cyclomatic_complexity_score, "", lizard_successful), ("lizard_warnings", warning_score, "", lizard_successful), \
            ("lizard_unique_code", unique_score, lizard_log, lizard_successful), ("kwstyle", kwstyle_score, kwstyle_log, kwstyle_successful), ("infer", infer_score, infer_log, infer_successful)] #TODO: infer_score
    #return assertion_score, cppcheck_score,0,0,0,0,0
