#!/usr/bin/env python3
"""
Calculates the code quality benchmark using scoring.py.
This script parses the rates from files containing the output of softwipe for each program that should be included in
the benchmark. It then recalculates the scores according to the current scoring.py. Then, it prints a csv containing
all scores.
"""

import argparse
import os

import softwipe.scoring

###########################################################
# If you add a new program to the benchmark, add the name #
# of its folder in the results directory to this lst!    #
###########################################################
# FOLDERS = ['dawg', 'mrbayes', 'raxml-ng', 'sf', 'hyperphylo', 'kahypar', 'ms', 'repeatscounter', 'tcoffee', 'bpp',
#           'indelible', 'mafft', 'prank', 'seq-gen', 'genesis', 'athena', 'gadget', 'iqtree', 'clustal', 'phyml',
#           'minimap', 'samtools', 'vsearch', 'swarm', 'cellcoal', 'treerecs']
FOLDERS = ['BGSA-1.0/original/BGSA_CPU', 'bindash-1.0', 'copmem-0.2', 'crisflash', 'cryfa-18.06', 'defor', 'dna-nn-0.1',
           'dr_sasa_n', 'emeraLD', 'ExpansionHunter', 'fastspar', 'HLA-LA/src', 'lemon', 'naf-1.1.0/ennaf',
           'naf-1.1.0/unnaf', 'ngsTools/ngsLD', 'ntEdit-1.2.3', 'PopLDdecay', 'virulign-1.0.1', 'axe-0.3.3', 'prequal',
           'IQ-TREE-2.0-rc1', 'candy-kingdom', 'glucose-3-drup', 'covid-sim-0.13.0']  # TODO: add SPRING

SOFTWIPE_OUTPUT_FILE_NAME = "sw_batch.txt"

LOC_KEY = "loc"
FUNCTIONS_KEY = "functions"
COMPILER_AND_SANITIZER_KEY = "compiler_and_sanitizer"
COMPILER_KEY = "compiler"
SANITIZER_KEY = "sanitizer"
ASSERTIONS_KEY = "assertions"
CPPCHECK_KEY = "cppcheck"
CLANG_TIDY_KEY = "clang_tidy"
CYCLOMATIC_COMPLEXITY_KEY = "cyclomatic_complexity"
LIZARD_WARNINGS_KEY = "lizard_warnings"
UNIQUE_KEY = "unique"
KWSTYLE_KEY = "kwstyle"
INFER_KEY = "infer"

SCORE_KEYS = [LOC_KEY, FUNCTIONS_KEY, COMPILER_KEY, SANITIZER_KEY, COMPILER_AND_SANITIZER_KEY, ASSERTIONS_KEY,
              CPPCHECK_KEY, CLANG_TIDY_KEY, CYCLOMATIC_COMPLEXITY_KEY, LIZARD_WARNINGS_KEY,
              UNIQUE_KEY, KWSTYLE_KEY, INFER_KEY]


def parse_arguments():
    parser = argparse.ArgumentParser(description="Calculate the code quality benchmark (i.e., the scores) and output "
                                                 "a csv containing all scores.")
    parser.add_argument('result_directory', nargs=1, help='the directory where all result folders are saved in. For '
                                                          'each program that should be included in the benchmark, '
                                                          'a folder should exist in this directory that contains the '
                                                          'output of softwipe in a file called '
                                                          '"' + SOFTWIPE_OUTPUT_FILE_NAME + '"')
    parser.add_argument('-A', '--absolute', action='store_true', help='create a table with absolute values rather '
                                                                      'than scores')
    # parser.add_argument('-o', help='output file to store the scores')
    parser.add_argument('--only-overall-scores', action='store_true',
                        help='flag only implemented for easier comparison of different '
                             'scoring techniques')

    args = parser.parse_args()
    return args


def get_result_rates(result_directory, folder):
    cur_folder = os.path.join(result_directory, folder)
    cur_file = os.path.join(cur_folder, SOFTWIPE_OUTPUT_FILE_NAME)
    cur_lines = open(cur_file, 'r').readlines()  # Softwipe output lines

    # Init
    compiler_and_sanitizer_rate = 0.0  # Special treatment because we may have to add multiple values for this score
    assertion_rate = cppcheck_rate = clang_tidy_rate = ccn = lizard_rate = unique_rate = kwstyle_rate = infer_rate = None

    # fill the failed_tools lst with all the available analysis tools and remove the ones that are not available in the report
    # this allows accepting half-finished reports without provoking reading or calculation errors
    failed_tools = [COMPILER_KEY, SANITIZER_KEY, COMPILER_AND_SANITIZER_KEY, INFER_KEY, ASSERTIONS_KEY, CPPCHECK_KEY,
                    CLANG_TIDY_KEY, CYCLOMATIC_COMPLEXITY_KEY, LIZARD_WARNINGS_KEY, UNIQUE_KEY, KWSTYLE_KEY, None]

    # Iterate through the softwipe output
    for line in cur_lines:
        split_line = line.split()

        # Compiler and sanitizer rate treatment
        if line.startswith('Weighted compiler warning rate:'):
            compiler_and_sanitizer_rate += float(split_line[4])
            if COMPILER_KEY in failed_tools: failed_tools.remove(COMPILER_KEY)
            if COMPILER_AND_SANITIZER_KEY in failed_tools: failed_tools.remove(COMPILER_AND_SANITIZER_KEY)
        elif line.startswith(('AddressSanitizer error rate:', 'UndefinedBehaviorSanitizer error rate:')):
            compiler_and_sanitizer_rate += float(split_line[3])
            if SANITIZER_KEY in failed_tools: failed_tools.remove(SANITIZER_KEY)

        # All other rates
        elif line.startswith('Assertion rate:'):
            assertion_rate = float(split_line[2])
            if ASSERTIONS_KEY in failed_tools: failed_tools.remove(ASSERTIONS_KEY)
            if COMPILER_AND_SANITIZER_KEY in failed_tools: failed_tools.remove(COMPILER_AND_SANITIZER_KEY)
        elif line.startswith('Total weighted Cppcheck warning rate:'):
            cppcheck_rate = float(split_line[5])
            if CPPCHECK_KEY in failed_tools: failed_tools.remove(CPPCHECK_KEY)
        elif line.startswith('Weighted Clang-tidy warning rate:'):
            clang_tidy_rate = float(split_line[4])
            if CLANG_TIDY_KEY in failed_tools: failed_tools.remove(CLANG_TIDY_KEY)
        elif line.startswith('Average cyclomatic complexity:'):
            ccn = float(split_line[3])
            if CYCLOMATIC_COMPLEXITY_KEY in failed_tools: failed_tools.remove(CYCLOMATIC_COMPLEXITY_KEY)
        elif line.startswith('Lizard warning rate (~= rate of functions that are too complex):'):
            lizard_rate = float(split_line[11])
            if LIZARD_WARNINGS_KEY in failed_tools: failed_tools.remove(LIZARD_WARNINGS_KEY)
        elif line.startswith('Unique code rate:'):
            unique_rate = float(split_line[3])
            if UNIQUE_KEY in failed_tools: failed_tools.remove(UNIQUE_KEY)
        elif line.startswith('KWStyle warning rate:'):
            kwstyle_rate = float(split_line[3])
            if KWSTYLE_KEY in failed_tools: failed_tools.remove(KWSTYLE_KEY)
        elif line.startswith('Weighted Infer warning rate:'):
            infer_rate = float(split_line[4])
            if INFER_KEY in failed_tools: failed_tools.remove(INFER_KEY)


    return compiler_and_sanitizer_rate, assertion_rate, cppcheck_rate, clang_tidy_rate, ccn, lizard_rate, \
           unique_rate, kwstyle_rate, infer_rate, failed_tools


def get_result_values(result_directory, folder):
    def get_absolute_value(abs_by_loc):
        return int(abs_by_loc.split('/')[0][1:])

    cur_folder = os.path.join(result_directory, folder)
    cur_file = os.path.join(cur_folder, SOFTWIPE_OUTPUT_FILE_NAME)
    cur_lines = open(cur_file, 'r').readlines()  # Softwipe output lines

    # Init
    sanitizer_warnings = 0
    loc = functions = compiler_warnings = assertions = cppcheck_warnings = clang_tidy_warnings = \
        ccn = lizard_warnings = unique = kwstyle_warnings = infer_warnings = None

    failed_tools = [COMPILER_KEY, SANITIZER_KEY, INFER_KEY, ASSERTIONS_KEY, CPPCHECK_KEY, COMPILER_AND_SANITIZER_KEY,
                    CLANG_TIDY_KEY, CYCLOMATIC_COMPLEXITY_KEY, LIZARD_WARNINGS_KEY, UNIQUE_KEY, KWSTYLE_KEY, None]

    # Iterate through the softwipe output
    for line in cur_lines:
        split_line = line.split()

        if line.startswith('Lines of pure'):
            loc = int(split_line[-1])
        elif line.startswith('Weighted compiler warning rate:'):
            compiler_warnings = get_absolute_value(split_line[-1])
            if COMPILER_KEY in failed_tools: failed_tools.remove(COMPILER_KEY)
            if COMPILER_AND_SANITIZER_KEY in failed_tools: failed_tools.remove(COMPILER_AND_SANITIZER_KEY)
        elif line.startswith(('AddressSanitizer error rate:', 'UndefinedBehaviorSanitizer error rate:')):
            sanitizer_warnings += get_absolute_value(split_line[-1])
            if SANITIZER_KEY in failed_tools: failed_tools.remove(SANITIZER_KEY)
            if COMPILER_AND_SANITIZER_KEY in failed_tools: failed_tools.remove(COMPILER_AND_SANITIZER_KEY)
        elif line.startswith('Assertion rate:'):
            assertions = get_absolute_value(split_line[-1])
            if ASSERTIONS_KEY in failed_tools: failed_tools.remove(ASSERTIONS_KEY)
        elif line.startswith('Total weighted Cppcheck warning rate:'):
            cppcheck_warnings = get_absolute_value(split_line[-1])
            if CPPCHECK_KEY in failed_tools: failed_tools.remove(CPPCHECK_KEY)
        elif line.startswith('Weighted Clang-tidy warning rate:'):
            clang_tidy_warnings = get_absolute_value(split_line[-1])
            if CLANG_TIDY_KEY in failed_tools: failed_tools.remove(CLANG_TIDY_KEY)
        elif line.startswith('Average cyclomatic complexity:'):
            ccn = float(split_line[-1])
            if CYCLOMATIC_COMPLEXITY_KEY in failed_tools: failed_tools.remove(CYCLOMATIC_COMPLEXITY_KEY)
        elif line.startswith('Lizard warning rate (~= rate of functions that are too complex):'):
            functions = int(split_line[-1].split('/')[1][:-1])
            lizard_warnings = get_absolute_value(split_line[-1])
            if LIZARD_WARNINGS_KEY in failed_tools: failed_tools.remove(LIZARD_WARNINGS_KEY)
        elif line.startswith('Unique code rate:'):
            unique = float(split_line[-1])
            if UNIQUE_KEY in failed_tools: failed_tools.remove(UNIQUE_KEY)
        elif line.startswith('KWStyle warning rate:'):
            kwstyle_warnings = get_absolute_value(split_line[-1])
            if KWSTYLE_KEY in failed_tools: failed_tools.remove(KWSTYLE_KEY)
        elif line.startswith('Weighted Infer warning rate:'):
            infer_warnings = get_absolute_value(split_line[-1])
            if INFER_KEY in failed_tools: failed_tools.remove(INFER_KEY)

    return loc, functions, compiler_warnings, sanitizer_warnings, assertions, cppcheck_warnings, clang_tidy_warnings, \
           ccn, lizard_warnings, unique, kwstyle_warnings, infer_warnings, failed_tools


def calculate_scores(result_directory, absolute):
    # Init
    if absolute:
        scores = {
            'loc': {},
            'functions': {},
            'compiler': {},
            'sanitizer': {},
            'assertions': {},
            'cppcheck': {},
            'clang_tidy': {},
            'cyclomatic_complexity': {},
            'lizard_warnings': {},
            'unique': {},
            'kwstyle': {},
            'infer': {}
        }
    else:
        scores = {
            'overall': {},
            'compiler_and_sanitizer': {},
            'assertions': {},
            'cppcheck': {},
            'clang_tidy': {},
            'cyclomatic_complexity': {},
            'lizard_warnings': {},
            'unique': {},
            'kwstyle': {},
            'infer': {}
        }

    failed_tools_dict = {}

    for score in scores:
        for folder in FOLDERS:
            scores[score][folder] = None

    # Get all the scores
    for folder in FOLDERS:

        if absolute:
            # Get values
            loc, functions, compiler_warnings, sanitizer_warnings, assertions, cppcheck_warnings, clang_tidy_warnings, \
            ccn, lizard_warnings, unique, kwstyle_warnings, infer_warnings, failed_tools = get_result_values(
                result_directory, folder)

            scores['loc'][folder] = loc
            scores['functions'][folder] = functions
            scores['compiler'][folder] = compiler_warnings
            scores['sanitizer'][folder] = sanitizer_warnings
            scores['assertions'][folder] = assertions
            scores['cppcheck'][folder] = cppcheck_warnings
            scores['clang_tidy'][folder] = clang_tidy_warnings
            scores['cyclomatic_complexity'][folder] = ccn
            scores['lizard_warnings'][folder] = lizard_warnings
            scores['unique'][folder] = unique
            scores['kwstyle'][folder] = kwstyle_warnings
            scores['infer'][folder] = infer_warnings

        else:
            # Get rates
            compiler_and_sanitizer_rate, assertion_rate, cppcheck_rate, clang_tidy_rate, ccn, lizard_rate, \
            unique_rate, kwstyle_rate, infer_rate, failed_tools = get_result_rates(result_directory, folder)

            # Get scores
            if COMPILER_KEY not in failed_tools: scores['compiler_and_sanitizer'][folder] = scoring.calculate_compiler_and_sanitizer_score_absolute(compiler_and_sanitizer_rate)
            if ASSERTIONS_KEY not in failed_tools: scores['assertions'][folder] = scoring.calculate_assertion_score_absolute(assertion_rate)
            if CPPCHECK_KEY not in failed_tools: scores['cppcheck'][folder] = scoring.calculate_cppcheck_score_absolute(cppcheck_rate)
            if CLANG_TIDY_KEY not in failed_tools: scores['clang_tidy'][folder] = scoring.calculate_clang_tidy_score_absolute(clang_tidy_rate)
            if CYCLOMATIC_COMPLEXITY_KEY not in failed_tools: scores['cyclomatic_complexity'][folder] = scoring.calculate_cyclomatic_complexity_score_absolute(ccn)
            if LIZARD_WARNINGS_KEY not in failed_tools: scores['lizard_warnings'][folder] = scoring.calculate_lizard_warning_score_absolute(lizard_rate)
            if UNIQUE_KEY not in failed_tools: scores['unique'][folder] = scoring.calculate_unique_score_absolute(unique_rate)
            if KWSTYLE_KEY not in failed_tools: scores['kwstyle'][folder] = scoring.calculate_kwstyle_score_absolute(kwstyle_rate)
            if INFER_KEY not in failed_tools: scores['infer'][folder] = scoring.calculate_infer_score_absolute(infer_rate)

            # Calculate the overall score
            list_of_scores = [scores[score][folder] for score in scores.keys()
                              if score != 'overall' and score not in failed_tools]
            if None in list_of_scores: list_of_scores = []

            if list_of_scores:
                scores['overall'][folder] = scoring.average_score(list_of_scores)
            else:
                scores['overall'][folder] = -1

        failed_tools_dict[folder] = failed_tools

    return scores, failed_tools_dict


def print_score_csv(scores, absolute, failed_tools, print_only_overall=False):
    if absolute:
        last_column = 'infer'
        space_pattern = [17, 8, 11, 10, 11, 12, 10, 12, 23, 17, 20, 9, 7]
    else:
        last_column = 'infer'
        space_pattern = [22, 9, 24, 12, 10, 12, 23, 17, 8, 9, 7]

    print('program', end=',')
    for score in scores:
        if score != last_column:
            print(score, end=',')
        else:
            print(score)
    for folder in FOLDERS:
        if not print_only_overall:
            print("| {}".format(folder).ljust(space_pattern[0]), end="|")
            counter = 1

            for score in scores:
                if score in failed_tools[folder]:
                    value = "N/A"
                    print(" {}".format(value).ljust(space_pattern[counter]), end="|")
                else:
                    if scores[score][folder] is not None:
                        value = round(scores[score][folder], 4) if absolute else round(scores[score][folder], 1)
                    else:
                        value = "N/A"

                    if absolute:
                        print(" {}".format(value).ljust(space_pattern[counter]), end="|")
                    else:
                        print(" {0:0.1f}".format(value).ljust(space_pattern[counter]), end="|")

                counter += 1
            print("")
        else:
            print(round(scores['overall'][folder], 1))


def main():
    args = parse_arguments()
    result_directory = os.path.abspath(args.result_directory[0])
    absolute = True if args.absolute else False
    print_only_overall = True if args.only_overall_scores else False
    scores, failed_tools = calculate_scores(result_directory, absolute)
    print_score_csv(scores, absolute, failed_tools=failed_tools, print_only_overall=print_only_overall)


if __name__ == "__main__":
    main()
