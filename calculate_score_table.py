#!/usr/bin/env python3
"""
Calculates the code quality benchmark using scoring.py.
This script parses the rates from files containing the output of softwipe for each program that should be included in
the benchmark. It then recalculates the scores according to the current scoring.py. Then, it prints a csv containing
all scores.
"""

import argparse
import os
import scoring


###########################################################
# If you add a new program to the benchmark, add the name #
# of its folder in the results directory to this list!    #
###########################################################
FOLDERS = ['dawg', 'mrbayes', 'raxml-ng', 'sf', 'hyperphylo', 'kahypar', 'ms', 'repeatscounter', 'tcoffee', 'bpp',
           'indelible', 'mafft', 'prank', 'seq-gen', 'genesis', 'athena', 'gadget', 'iqtree', 'clustal', 'phyml',
           'minimap', 'samtools', 'vsearch', 'swarm', 'cellcoal']
SOFTWIPE_OUTPUT_FILE_NAME = 'softwipe_output.txt'


def parse_arguments():
    parser = argparse.ArgumentParser(description="Calculate the code quality benchmark (i.e., the scores) and output "
                                                 "a csv containing all scores.")
    parser.add_argument('result_directory', nargs=1, help='the directory where all result folders are saved in. For '
                                                          'each program that should be included in the benchmark, '
                                                          'a folder should exist in this directory that contains the '
                                                          'output of softwipe in a file called '
                                                          '"' + SOFTWIPE_OUTPUT_FILE_NAME + '"')
    args = parser.parse_args()
    return args


def get_result_rates(result_directory, folder):
    cur_folder = os.path.join(result_directory, folder)
    cur_file = os.path.join(cur_folder, SOFTWIPE_OUTPUT_FILE_NAME)
    cur_lines = open(cur_file, 'r').readlines()  # Softwipe output lines

    # Init
    compiler_and_sanitizer_rate = 0.0  # Special treatment because we may have to add multiple values for this score
    assertion_rate = cppcheck_rate = clang_tidy_rate = ccn = lizard_rate = unique_rate = kwstyle_rate = None

    # Iterate through the softwipe output
    for line in cur_lines:
        split_line = line.split()

        # Compiler and sanitizer rate treatment
        if line.startswith('Weighted compiler warning rate:'):
            compiler_and_sanitizer_rate += float(split_line[4])
        elif line.startswith(('AddressSanitizer error rate:', 'UndefinedBehaviorSanitizer error rate:')):
            compiler_and_sanitizer_rate += float(split_line[3])

        # All other rates
        elif line.startswith('Assertion rate:'):
            assertion_rate = float(split_line[2])
        elif line.startswith('Total weighted Cppcheck warning rate:'):
            cppcheck_rate = float(split_line[5])
        elif line.startswith('Weighted Clang-tidy warning rate:'):
            clang_tidy_rate = float(split_line[4])
        elif line.startswith('Average cyclomatic complexity:'):
            ccn = float(split_line[3])
        elif line.startswith('Lizard warning rate (~= rate of functions that are too complex):'):
            lizard_rate = float(split_line[11])
        elif line.startswith('Unique code rate:'):
            unique_rate = float(split_line[3])
        elif line.startswith('KWStyle warning rate:'):
            kwstyle_rate = float(split_line[3])

    return compiler_and_sanitizer_rate, assertion_rate, cppcheck_rate, clang_tidy_rate, ccn, lizard_rate, \
        unique_rate, kwstyle_rate


def calculate_scores(result_directory):
    # Init
    scores = {
        'compiler_and_sanitizer': {},
        'assertions': {},
        'cppcheck': {},
        'clang_tidy': {},
        'cyclomatic_complexity': {},
        'lizard_warnings': {},
        'unique': {},
        'kwstyle': {},
        'overall': {}
    }

    for score in scores:
        for folder in FOLDERS:
            scores[score][folder] = None

    # Get all the scores
    for folder in FOLDERS:
        # Get rates
        compiler_and_sanitizer_rate, assertion_rate, cppcheck_rate, clang_tidy_rate, ccn, lizard_rate, unique_rate, \
            kwstyle_rate = get_result_rates(result_directory, folder)

        # Get scores
        scores['compiler_and_sanitizer'][folder] = scoring.calculate_compiler_and_sanitizer_score(
            compiler_and_sanitizer_rate)
        scores['assertions'][folder] = scoring.calculate_assertion_score(assertion_rate)
        scores['cppcheck'][folder] = scoring.calculate_cppcheck_score(cppcheck_rate)
        scores['clang_tidy'][folder] = scoring.calculate_clang_tidy_score(clang_tidy_rate)
        scores['cyclomatic_complexity'][folder] = scoring.calculate_cyclomatic_complexity_score(ccn)
        scores['lizard_warnings'][folder] = scoring.calculate_lizard_warning_score(lizard_rate)
        scores['unique'][folder] = scoring.calculate_unique_score(unique_rate)
        scores['kwstyle'][folder] = scoring.calculate_kwstyle_score(kwstyle_rate)

        # Calculate the overall score
        list_of_scores = [scores[score][folder] for score in scores.keys() if score != 'overall']
        scores['overall'][folder] = scoring.average_score(list_of_scores)

    return scores


def print_score_csv(scores):
    print('program', end=',')
    for score in scores:
        if score != 'overall':
            print(score, end=',')
        else:
            print(score)
    for folder in FOLDERS:
        print(folder, end=',')
        for score in scores:
            if score != 'overall':
                print(scores[score][folder], end=',')
            else:
                print(scores[score][folder])


def main():
    args = parse_arguments()
    result_directory = os.path.abspath(args.result_directory[0])
    scores = calculate_scores(result_directory)
    print_score_csv(scores)


if __name__ == "__main__":
    main()
